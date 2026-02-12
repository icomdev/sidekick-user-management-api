import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.entities.agent import Agent
from src.domain.models.entities.enums import GroupRole
from src.domain.models.entities.group import Group
from src.domain.models.entities.group_agent import GroupAgent
from src.domain.models.entities.group_membership import GroupMembership
from src.domain.models.entities.user import User

logger = logging.getLogger(__name__)


class AgentService:
    async def register_agent(
        self,
        session: AsyncSession,
        agent_external_id: str,
        name: str,
        group_id: int,
        created_by: str,
    ) -> Agent:
        """Register a new agent and assign it to the specified group."""
        # Verify group exists
        result = await session.execute(select(Group).where(Group.id == group_id))
        if result.scalar_one_or_none() is None:
            raise ValueError("group_not_found")

        agent = Agent(
            agent_external_id=agent_external_id,
            name=name,
            created_by=created_by,
        )
        session.add(agent)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            raise ValueError("duplicate_agent") from None

        # Assign agent to group
        group_agent = GroupAgent(
            group_id=group_id,
            agent_id=agent.id,
            added_by=created_by,
        )
        session.add(group_agent)
        await session.commit()
        await session.refresh(agent)

        logger.info(
            "Registered agent id=%s external_id=%s in group_id=%s",
            agent.id,
            agent_external_id,
            group_id,
        )
        return agent

    async def assign_agent_to_group(
        self,
        session: AsyncSession,
        group_id: int,
        agent_id: int,
        added_by: str,
    ) -> GroupAgent:
        """Assign an existing agent to an additional group."""
        # Verify group exists
        result = await session.execute(select(Group).where(Group.id == group_id))
        if result.scalar_one_or_none() is None:
            raise ValueError("group_not_found")

        # Verify agent exists
        result = await session.execute(select(Agent).where(Agent.id == agent_id))
        if result.scalar_one_or_none() is None:
            raise ValueError("agent_not_found")

        group_agent = GroupAgent(
            group_id=group_id,
            agent_id=agent_id,
            added_by=added_by,
        )
        session.add(group_agent)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise ValueError("duplicate_assignment") from None

        await session.refresh(group_agent)
        logger.info(
            "Assigned agent_id=%s to group_id=%s",
            agent_id,
            group_id,
        )
        return group_agent

    async def remove_agent_from_group(
        self,
        session: AsyncSession,
        group_id: int,
        agent_id: int,
    ) -> bool:
        """Remove an agent from a group."""
        result = await session.execute(
            select(GroupAgent).where(
                GroupAgent.group_id == group_id,
                GroupAgent.agent_id == agent_id,
            )
        )
        group_agent = result.scalar_one_or_none()
        if group_agent is None:
            raise ValueError("assignment_not_found")

        await session.delete(group_agent)
        await session.commit()
        logger.info("Removed agent_id=%s from group_id=%s", agent_id, group_id)
        return True

    async def list_agents_in_group(
        self,
        session: AsyncSession,
        group_id: int,
    ) -> list[Agent]:
        """List all agents assigned to a group."""
        # Verify group exists
        result = await session.execute(select(Group).where(Group.id == group_id))
        if result.scalar_one_or_none() is None:
            raise ValueError("group_not_found")

        result = await session.execute(
            select(Agent)
            .join(GroupAgent, GroupAgent.agent_id == Agent.id)
            .where(GroupAgent.group_id == group_id)
        )
        return list(result.scalars().all())

    async def get_admin_groups(
        self,
        session: AsyncSession,
        entra_object_id: str,
    ) -> list[Group]:
        """Return groups where the user has admin role."""
        result = await session.execute(
            select(Group)
            .join(GroupMembership, GroupMembership.group_id == Group.id)
            .where(
                GroupMembership.entra_object_id == entra_object_id,
                GroupMembership.role == GroupRole.ADMIN,
            )
        )
        return list(result.scalars().all())

    async def get_user_agents(
        self,
        session: AsyncSession,
        entra_object_id: str,
        *,
        is_superadmin: bool = False,
    ) -> list[dict]:
        """Return all agents accessible to a user with their group info.

        For superadmins, returns all agents with all their group assignments.
        For regular users, returns agents from groups they belong to.

        Returns a list of dicts with agent fields plus a 'groups' list.
        """
        if is_superadmin:
            # Superadmins see all agents with all group assignments
            result = await session.execute(
                select(Agent, Group.id, Group.name)
                .join(GroupAgent, GroupAgent.agent_id == Agent.id)
                .join(Group, Group.id == GroupAgent.group_id)
                .order_by(Agent.id, Group.id)
            )
        else:
            # Verify user exists
            user_result = await session.execute(
                select(User).where(User.entra_object_id == entra_object_id)
            )
            if user_result.scalar_one_or_none() is None:
                raise ValueError("user_not_found")

            # Regular users see agents from their groups
            result = await session.execute(
                select(Agent, Group.id, Group.name)
                .join(GroupAgent, GroupAgent.agent_id == Agent.id)
                .join(Group, Group.id == GroupAgent.group_id)
                .join(
                    GroupMembership,
                    GroupMembership.group_id == GroupAgent.group_id,
                )
                .where(GroupMembership.entra_object_id == entra_object_id)
                .order_by(Agent.id, Group.id)
            )

        rows = result.all()

        # Deduplicate agents and collect their groups
        agents_map: dict[int, dict] = {}
        for agent, group_id, group_name in rows:
            if agent.id not in agents_map:
                agents_map[agent.id] = {
                    "id": agent.id,
                    "agent_external_id": agent.agent_external_id,
                    "name": agent.name,
                    "created_by": agent.created_by,
                    "created_at": agent.created_at,
                    "groups": [],
                }
            group_entry = {"group_id": group_id, "group_name": group_name}
            if group_entry not in agents_map[agent.id]["groups"]:
                agents_map[agent.id]["groups"].append(group_entry)

        return list(agents_map.values())
