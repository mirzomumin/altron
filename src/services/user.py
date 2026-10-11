from uuid import UUID

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    generate_password,
    generate_username,
    hash_password,
    verify_password,
)
from src.models.session import UserSession
from src.models.user import User, UserPosition
from src.repositories.user import UserRepository
from src.schemas.user import CreateUserRequest, LoginRequest
from src.services.customer import CustomerService
from src.services.session import UserSessionService


class UserService:
    @staticmethod
    async def login(
        data: LoginRequest,
        db: AsyncSession,
    ) -> tuple[str, UserSession]:
        user = await UserRepository.get_by_username(db, data.username)

        if user is None or not verify_password(data.password, user.password_hash):
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
        await CustomerService.get(data.customer_id, db)

        username = generate_username(data.first_name, data.last_name, data.patronymic)
        password = generate_password()

        user_data = {
            "username": username,
            "password_hash": hash_password(password),
            "first_name": data.first_name,
            "last_name": data.last_name,
            "patronymic": data.patronymic,
            "position": data.position,
            "customer_id": data.customer_id,
        }

        try:
            await UserRepository.add(db, user_data)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User '{username}' already exists",
            ) from None

        return {"username": username, "password": password}

    @staticmethod
    async def list(
        db: AsyncSession,
        customer_id: UUID | None = None,
        position: UserPosition | None = None,
    ) -> list[User]:
        filters = []
        if customer_id is not None:
            filters.append(User.customer_id == customer_id)
        if position is not None:
            filters.append(User.position == position)
        return await UserRepository.list(db, filters=filters)

    @staticmethod
    async def get(id: UUID, db: AsyncSession) -> User:
        user = await UserRepository.get_by_id(id, db)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user
