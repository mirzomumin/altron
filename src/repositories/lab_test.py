from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.norm_document import LabTest


class LabTestRepository:
    @staticmethod
    async def bulk_add(values: list[dict], db: AsyncSession) -> None:
        await db.execute(insert(LabTest), values)
