from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.norm_document import NormDocument


class NormDocumentRepository:
    @staticmethod
    async def get_by_id(id: UUID, db: AsyncSession) -> NormDocument:
        stmt = (
            select(NormDocument)
            .options(selectinload(NormDocument.lab_tests))
            .where(NormDocument.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def add(values: dict, db: AsyncSession) -> NormDocument:
        stmt = insert(NormDocument).values(**values).returning(NormDocument)
        result = await db.execute(stmt)
        return result.scalar_one()
