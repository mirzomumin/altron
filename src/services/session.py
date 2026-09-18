from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import (
    generate_session_id,
    hash_session_id,
)
from src.models.session import UserSession
from src.repositories.session import UserSessionRepository


class UserSessionService:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
    ) -> tuple[str, UserSession]:
        session_id = generate_session_id()
        expires_at = datetime.now(UTC) + timedelta(
            seconds=settings.SESSION_EXPIRE_SECONDS
        )
        session_data = {
            "session_id_hash": hash_session_id(session_id),
            "user_id": user_id,
            "expires_at": expires_at,
        }
        session = await UserSessionRepository.add(db, session_data)

        await db.commit()
        await db.refresh(session)
        return session_id, session

    @staticmethod
    async def delete(
        db: AsyncSession,
        session_id: str,
    ) -> None:
        session_id_hash = hash_session_id(session_id)
        await UserSessionRepository.delete(db, session_id_hash)
        await db.commit()
