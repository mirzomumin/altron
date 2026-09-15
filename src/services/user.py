from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    verify_password,
    generate_username,
    generate_password,
    hash_password,
)
from src.models.user import User
from src.models.session import UserSession
from src.schemas.user import LoginRequest, CreateUserRequest
from src.services.session import UserSessionService


class UserService:

    @staticmethod
    async def login(
        data: LoginRequest,
        db: AsyncSession,
    ) ->  tuple[str, UserSession]:
        stmt = select(User).where(
            User.username == data.username
        )
        result = await db.execute(stmt)

        user = result.scalar_one_or_none()
        if (
            user is None
            or not verify_password(
                data.password,
                user.password_hash,
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        session_id, session = await UserSessionService.create(
            db,
            user.id,
        )
        return session_id, session

    @staticmethod
    async def create(
        data: CreateUserRequest,
        db: AsyncSession,
    ) -> dict:
        username = generate_username(data.first_name, data.last_name, data.surname)
        password = generate_password()
        user = User(
            username=username,
            password_hash=hash_password(password),
            first_name=data.first_name,
            last_name=data.last_name,
            surname=data.surname,
        )
        db.add(user)
        await db.commit()

        return {"username": username, "password": password}

    @staticmethod
    async def list(db: AsyncSession) -> list[User]:
        stmt = select(User)
        users = await db.scalars(stmt)
        return users.all()
