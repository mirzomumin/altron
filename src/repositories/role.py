from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql._typing import _ColumnExpressionArgument

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
        permission_ids: list[UUID],
        db: AsyncSession,
    ) -> None:
        stmt = insert(role_permissions)
        await db.execute(
            stmt,
            [
                {"role_id": role.id, "permission_id": perm_id}
                for perm_id in permission_ids
            ],
        )

    @staticmethod
    async def delete_permissions(
        role: Role,
        permission_ids: list[UUID],
        db: AsyncSession,
    ) -> None:
        stmt = delete(role_permissions).where(
            role_permissions.c.role_id == role.id,
            role_permissions.c.permission_id.in_(
                [perm_id for perm_id in permission_ids]
            ),
        )
        await db.execute(stmt)

    @staticmethod
    async def list(
        db: AsyncSession,
        filters: list[_ColumnExpressionArgument[bool]] | None = None,
    ) -> list[Role]:
        query = (
            select(Role).options(selectinload(Role.permissions)).where(*(filters or []))
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        id: UUID,
        values: dict,
        db: AsyncSession,
    ) -> Role:
        stmt = update(Role).where(Role.id == id).values(**values).returning(Role)
        result = await db.execute(stmt)
        return result.scalar_one()
