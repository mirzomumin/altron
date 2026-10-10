from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from src.models.customer import Customer


class CustomerRepository:
    @staticmethod
    async def get_by_id(id: UUID, db: AsyncSession) -> Customer:
        stmt = select(Customer).where(Customer.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def add(values: dict, db: AsyncSession) -> Customer:
        stmt = insert(Customer).values(**values).returning(Customer)
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def delete(id: UUID, db: AsyncSession) -> None:
        stmt = delete(Customer).where(Customer.id == id)
        await db.execute(stmt)

    @staticmethod
    async def list(
        db: AsyncSession,
        filters: list[_ColumnExpressionArgument[bool]] | None = None,
    ) -> list[Customer]:
        query = select(Customer).where(*(filters or [])).order_by(Customer.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        id: UUID,
        values: dict,
        db: AsyncSession,
    ) -> Customer:
        stmt = (
            update(Customer)
            .where(Customer.id == id)
            .values(**values)
            .returning(Customer)
        )
        result = await db.execute(stmt)
        return result.scalar_one()
