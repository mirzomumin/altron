from uuid import UUID

from fastapi import (
    APIRouter,
    Response,
)

from src.core.config import settings
from src.db.session import SessionDep
from src.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    GetUserDetailResponse,
    GetUserListResponse,
    LoginRequest,
    LoginResponse,
)
from src.services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["User"],
)


@router.post("/login")
async def login(
    data: LoginRequest,
    db: SessionDep,
    response: Response,
) -> LoginResponse:
    session_id, session = await UserService.login(
        data,
        db,
    )

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_EXPIRE_SECONDS,
        expires=session.expires_at,
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAME_SITE,
        path="/",
    )

    return {
        "message": "Logged in successfully",
    }


@router.post("")
async def create_user(
    data: CreateUserRequest,
    db: SessionDep,
) -> CreateUserResponse:
    return await UserService.create(data, db)


@router.get("")
async def get_user_list(
    db: SessionDep,
) -> list[GetUserListResponse]:
    result = await UserService.list(db)
    return result


@router.get("/{id}")
async def get_user_detail(
    id: UUID,
    db: SessionDep,
) -> GetUserDetailResponse:
    result = await UserService.get(id, db)
    return result
