from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.permission import PermissionResponse


####################### Create Role ########################
class Permission(BaseModel):
    id: UUID


class CreateRoleRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(default="", max_length=255)
    permissions: list[Permission]


class CreateRoleResponse(CreateRoleRequest):
    id: UUID
    is_default: bool
    permissions: list[PermissionResponse]


################### Update Role ############################
class UpdateRoleRequest(CreateRoleRequest):
    pass


class UpdateRoleResponse(CreateRoleResponse):
    pass
