from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    generate_password,
    generate_username,
    hash_password,
    verify_password,
)
from src.models.session import UserSession
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.user import CreateUserRequest, LoginRequest
from src.services.session import UserSessionService


class UserService:
    @staticmethod
    async def login(
        data: LoginRequest,
        db: AsyncSession,
    ) -> tuple[str, UserSession]:
        user = await UserRepository.get_by_username(db, data.username)
        is_pass_verified = verify_password(data.password, user.password_hash)

        if user is None or not is_pass_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        session_id, session = await UserSessionService.create(db, user.id)
        return session_id, session

    @staticmethod
    async def create(
        data: CreateUserRequest,
        db: AsyncSession,
    ) -> dict:
        username = generate_username(data.first_name, data.last_name, data.patronymic)
        password = generate_password()

        user_data = {
            "username": username,
            "password_hash": hash_password(password),
            "first_name": data.first_name,
            "last_name": data.last_name,
            "patronymic": data.patronymic,
        }

        await UserRepository.add(db, user_data)
        await db.commit()
        return {"username": username, "password": password}

    @staticmethod
    async def list(db: AsyncSession) -> list[User]:
        return await UserRepository.list(db)
