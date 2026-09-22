from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from src.models.role import Role
from src.models.user import User


class UserRepository:
    @staticmethod
    async def add(db: AsyncSession, values: dict) -> User:
        stmt = insert(User).values(**values).returning(User)
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(id: UUID, db: AsyncSession) -> User:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        filters: list[_ColumnExpressionArgument[bool]] | None = None,
    ) -> list[User]:
        query = select(User).where(*(filters or []))
        result = await db.execute(query)
        return result.scalars().all()
