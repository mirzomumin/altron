from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    message: str = "Logged in successfully"


class CreateUserRequest(BaseModel):
    first_name: str = Field(..., max_length=255, title="John")
    last_name: str = Field(..., max_length=255, title="Doe")
    patronymic: str | None = Field(default="", title="Hermanson")


class CreateUserResponse(BaseModel):
    username: str
    password: str


class GetUserListResponse(BaseModel):
    id: UUID
    username: str
    first_name: str
    last_name: str
    patronymic: str
    is_active: bool
