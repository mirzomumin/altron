from fastapi import (
    APIRouter,
    Depends,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_db
from src.schemas.user import (
    LoginRequest,
    LoginResponse,
    CreateUserRequest,
    CreateUserResponse,
    GetUserListResponse,
)
from src.services.user import UserService


router = APIRouter(
    prefix="/users",
    tags=["User"],
)


@router.post("/login")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    session_id, session = await UserService.login(
        data,
        db,
    )

    response = Response()
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
    db: AsyncSession = Depends(get_db),
) -> CreateUserResponse:
    return await UserService.create(data, db)


@router.get("")
async def get_user_list(
    db: AsyncSession = Depends(get_db),
) -> list[GetUserListResponse]:
    result = await UserService.list(db)
    return result
