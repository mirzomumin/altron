from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from src.models.permission import Permission


class PermissionRepository:
    @staticmethod
    async def list(
        db: AsyncSession,
        filters: list[_ColumnExpressionArgument[bool]] | None = None,
    ) -> list[Permission]:
        query = select(Permission).where(*(filters or []))
        result = await db.execute(query)
        return result.scalars().all()
