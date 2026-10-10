from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Customer
from src.repositories.customer import CustomerRepository
from src.schemas.customer import CreateCustomerRequest, UpdateCustomerRequest


class CustomerService:
    @staticmethod
    async def add(
        data: CreateCustomerRequest,
        db: AsyncSession,
    ) -> Customer:
        customer_data = data.model_dump()

        customers = await CustomerRepository.list(
            db,
            filters=[func.lower(Customer.name) == func.lower(customer_data["name"])],
        )
        if len(customers) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer already exists",
            )

        customer = await CustomerRepository.add(customer_data, db)
        await db.commit()
        return customer

    @staticmethod
    async def list(db: AsyncSession, name: str | None = None) -> list[Customer]:
        filters = []
        if name:
            filters.append(Customer.name.icontains(name, autoescape=True))
        return await CustomerRepository.list(db, filters=filters)

    @staticmethod
    async def get(id: UUID, db: AsyncSession) -> Customer:
        customer = await CustomerRepository.get_by_id(id, db)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
            )

        return customer

    @staticmethod
    async def update(
        id: UUID,
        data: UpdateCustomerRequest,
        db: AsyncSession,
    ) -> Customer:
        await CustomerService.get(id, db)
        customer_data = data.model_dump()

        customers = await CustomerRepository.list(
            db,
            filters=[
                func.lower(Customer.name) == func.lower(customer_data["name"]),
                Customer.id != id,
            ],
        )
        if len(customers) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer already exists",
            )

        customer = await CustomerRepository.update(id, customer_data, db)
        await db.commit()
        return customer

    @staticmethod
    async def delete(id: UUID, db: AsyncSession) -> None:
        await CustomerService.get(id, db)
        await CustomerRepository.delete(id, db)
        await db.commit()
