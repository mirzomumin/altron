from uuid import UUID

from pydantic import BaseModel, Field

from src.models.user import UserPosition
from src.schemas.customer import CustomerResponse
from src.schemas.role import CreateRoleResponse


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
    position: UserPosition = UserPosition.SPECIALIST
    customer_id: UUID


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
    position: UserPosition
    customer_id: UUID


############## Get User Detail ################
class GetUserDetailResponse(GetUserListResponse):
    customer: CustomerResponse
    roles: list[CreateRoleResponse]
