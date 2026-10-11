from uuid import UUID

from fastapi import APIRouter, status

from src.db.session import SessionDep
from src.schemas.application import (
    CreateApplicationRequest,
    CreateApplicationResponse,
    GetApplicationDetailResponse,
    GetApplicationListResponse,
    UpdateApplicationRequest,
    UpdateApplicationResponse,
)
from src.services.application import ApplicationService

router = APIRouter(
    prefix="/applications",
    tags=["Application"],
)


@router.post("")
async def create_application(
    data: CreateApplicationRequest,
    db: SessionDep,
) -> CreateApplicationResponse:
    return await ApplicationService.add(data, db)


@router.get("")
async def get_application_list(
    db: SessionDep,
    customer_id: UUID | None = None,
) -> list[GetApplicationListResponse]:
    return await ApplicationService.list(db, customer_id)


@router.get("/{id}")
async def get_application_detail(
    id: UUID,
    db: SessionDep,
) -> GetApplicationDetailResponse:
    return await ApplicationService.get(id, db)


@router.put("/{id}")
async def update_application(
    id: UUID,
    data: UpdateApplicationRequest,
    db: SessionDep,
) -> UpdateApplicationResponse:
    return await ApplicationService.update(id, data, db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    id: UUID,
    db: SessionDep,
) -> None:
    await ApplicationService.delete(id, db)
