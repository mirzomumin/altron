from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import (
    generate_session_id,
    hash_session_id,
)
from src.models.session import UserSession


class UserSessionService:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
    ) -> tuple[str, UserSession]:

        session_id = generate_session_id()

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                seconds=settings.SESSION_EXPIRE_SECONDS
            )
        )

        session = UserSession(
            session_id_hash=hash_session_id(
                session_id
            ),
            user_id=user_id,
            expires_at=expires_at,
        )

        db.add(session)

        await db.commit()
        await db.refresh(session)

        return session_id, session

    @staticmethod
    async def delete(
        db: AsyncSession,
        session_id: str,
    ) -> None:

        stmt = delete(UserSession).where(
            UserSession.session_id_hash
            == hash_session_id(session_id)
        )

        await db.execute(stmt)
        await db.commit()