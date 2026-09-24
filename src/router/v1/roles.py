from uuid import UUID

from fastapi import APIRouter

from src.db.session import SessionDep
from src.schemas.role import (
    CreateRoleRequest,
    CreateRoleResponse,
    UpdateRoleRequest,
    UpdateRoleResponse,
)
from src.services.role import RoleService

router = APIRouter(
    prefix="/roles",
    tags=["Role"],
)


@router.post("")
async def create_role(
    data: CreateRoleRequest,
    db: SessionDep,
) -> CreateRoleResponse:
    return await RoleService.add(data, db)


@router.get("")
async def get_role_list(db: SessionDep) -> list[CreateRoleResponse]:
    return await RoleService.list(db)


@router.put("/{id}")
async def update_role(
    id: UUID,
    data: UpdateRoleRequest,
    db: SessionDep,
) -> UpdateRoleResponse:
    return await RoleService.update(id, data, db)
