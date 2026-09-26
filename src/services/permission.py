from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.repositories.permission import PermissionRepository


class PermissionService:
    @staticmethod
    async def list(db: AsyncSession) -> list[Permission]:
        return await PermissionRepository.list(db)
