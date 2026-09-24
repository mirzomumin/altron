from uuid import UUID

from pydantic import BaseModel, Field


####################### Create Role ########################
class Permission(BaseModel):
    id: UUID


class CreateRoleRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(default="", max_length=255)
    permissions: list[Permission]


class PermissionResponse(BaseModel):
    id: UUID
    code: str
    description: str | None


class CreateRoleResponse(CreateRoleRequest):
    id: UUID
    is_default: bool
    permissions: list[PermissionResponse]
