from uuid import UUID

from pydantic import BaseModel, Field


################# Login ######################
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    message: str = "Logged in successfully"


################ Create User ##################
class CreateUserRequest(BaseModel):
    first_name: str = Field(..., max_length=255, title="John")
    last_name: str = Field(..., max_length=255, title="Doe")
    patronymic: str | None = Field(default="", title="Hermanson")


class CreateUserResponse(BaseModel):
    username: str
    password: str


############### Get User List #################
class GetUserListResponse(BaseModel):
    id: UUID
    username: str
    first_name: str
    last_name: str
    patronymic: str
    is_active: bool


############## Get User Detail ################
class PermissionResponse(BaseModel):
    id: UUID
    code: str
    description: str


class Role(BaseModel):
    id: UUID
    name: str
    description: str
    is_default: bool
    permissions: list[PermissionResponse]


class GetUserDetailResponse(GetUserListResponse):
    roles: list[Role]
