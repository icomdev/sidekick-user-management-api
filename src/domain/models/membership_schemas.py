import datetime

from pydantic import BaseModel, Field

from src.domain.models.entities.enums import GroupRole


class AddMemberRequest(BaseModel):
    entra_object_id: str = Field(..., min_length=1, max_length=36)
    role: GroupRole = GroupRole.USER


class UpdateMemberRoleRequest(BaseModel):
    role: GroupRole


class MemberResponse(BaseModel):
    entra_object_id: str
    display_name: str
    email: str
    role: GroupRole
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class MemberListResponse(BaseModel):
    members: list[MemberResponse]
