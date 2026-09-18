from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.session import UserSession


class UserSessionRepository:
    @staticmethod
    async def add(db: AsyncSession, values: dict) -> UserSession:
        stmt = insert(UserSession).values(**values).returning(UserSession)
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def delete(db: AsyncSession, session_id_hash: str) -> None:
        stmt = delete(UserSession).where(UserSession.session_id_hash == session_id_hash)
        await db.execute(stmt)
