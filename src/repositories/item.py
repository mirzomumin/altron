from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.item import Item


class ItemRepository:
    @staticmethod
    async def bulk_add(values: list[dict], db: AsyncSession) -> None:
        await db.execute(insert(Item), values)
