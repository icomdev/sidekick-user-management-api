import datetime

from pydantic import BaseModel, Field


class RegisterAgentRequest(BaseModel):
    agent_external_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    group_id: int


class AssignAgentToGroupRequest(BaseModel):
    agent_id: int


class AgentResponse(BaseModel):
    id: int
    agent_external_id: str
    name: str
    created_by: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
