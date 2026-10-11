from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from src.models.application import Application, submissions


class ApplicationRepository:
    @staticmethod
    async def get_by_id(id: UUID, db: AsyncSession) -> Application:
        stmt = (
            select(Application)
            .options(
                selectinload(Application.customer),
                selectinload(Application.submitters),
            )
            .where(Application.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def add(values: dict, db: AsyncSession) -> Application:
        stmt = insert(Application).values(**values).returning(Application)
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def delete(id: UUID, db: AsyncSession) -> None:
        stmt = delete(Application).where(Application.id == id)
        await db.execute(stmt)

    @staticmethod
    async def add_submitters(
        application: Application,
        user_ids: list[UUID],
        db: AsyncSession,
    ) -> None:
        stmt = insert(submissions)
        await db.execute(
            stmt,
            [
                {"application_id": application.id, "user_id": user_id}
                for user_id in user_ids
            ],
        )

    @staticmethod
    async def delete_submitters(
        application: Application,
        user_ids: list[UUID],
        db: AsyncSession,
    ) -> None:
        stmt = delete(submissions).where(
            submissions.c.application_id == application.id,
            submissions.c.user_id.in_(list(user_ids)),
        )
        await db.execute(stmt)

    @staticmethod
    async def list(
        db: AsyncSession,
        filters: list[_ColumnExpressionArgument[bool]] | None = None,
    ) -> list[Application]:
        query = (
            select(Application)
            .options(selectinload(Application.customer))
            .where(*(filters or []))
            .order_by(Application.received_date.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        id: UUID,
        values: dict,
        db: AsyncSession,
    ) -> Application:
        stmt = (
            update(Application)
            .where(Application.id == id)
            .values(**values)
            .returning(Application)
        )
        result = await db.execute(stmt)
        return result.scalar_one()
