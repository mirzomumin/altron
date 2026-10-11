from uuid import UUID

from fastapi import APIRouter, Query, status

from src.db.session import SessionDep
from src.schemas.customer import (
    CreateCustomerRequest,
    CreateCustomerResponse,
    CustomerResponse,
    UpdateCustomerRequest,
    UpdateCustomerResponse,
)
from src.services.customer import CustomerService

router = APIRouter(
    prefix="/customers",
    tags=["Customer"],
)


@router.post("")
async def create_customer(
    data: CreateCustomerRequest,
    db: SessionDep,
) -> CreateCustomerResponse:
    return await CustomerService.add(data, db)


@router.get("")
async def get_customer_list(
    db: SessionDep,
    name: str | None = Query(default=None, max_length=255),
) -> list[CustomerResponse]:
    return await CustomerService.list(db, name)


@router.get("/{id}")
async def get_customer_detail(
    id: UUID,
    db: SessionDep,
) -> CustomerResponse:
    return await CustomerService.get(id, db)


@router.put("/{id}")
async def update_customer(
    id: UUID,
    data: UpdateCustomerRequest,
    db: SessionDep,
) -> UpdateCustomerResponse:
    return await CustomerService.update(id, data, db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    id: UUID,
    db: SessionDep,
) -> None:
    await CustomerService.delete(id, db)
