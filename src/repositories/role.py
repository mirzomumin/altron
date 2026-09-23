from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.permission import Permission
from src.models.role import Role, role_permissions


class RoleRepository:
    @staticmethod
    async def get_by_id(id: UUID, db: AsyncSession) -> Role:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def add(values: dict, db: AsyncSession) -> Role:
        stmt = insert(Role).values(**values).returning(Role)
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def delete(id: UUID, db: AsyncSession) -> None:
        stmt = delete(Role).where(Role.id == id)
        await db.execute(stmt)

    @staticmethod
    async def add_permissions(
        role: Role,
        permissions: list[Permission],
        db: AsyncSession,
    ) -> None:
        stmt = insert(role_permissions)
        await db.execute(
            stmt,
            [{"role_id": role.id, "permission_id": perm.id} for perm in permissions],
        )

    @staticmethod
    async def delete_permissions(
        role: Role,
        permissions: list[Permission],
        db: AsyncSession,
    ) -> None:
        stmt = delete(role_permissions).where(
            role_permissions.c.role_id == role.id,
            role_permissions.c.permission_id.in_([perm.id for perm in permissions]),
        )
        await db.execute(stmt)
