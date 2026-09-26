from fastapi import APIRouter

from src.db.session import SessionDep
from src.schemas.permission import (
    PermissionResponse,
)
from src.services.permission import PermissionService

router = APIRouter(
    prefix="/permissions",
    tags=["Permission"],
)


@router.get("")
async def get_permission_list(
    db: SessionDep,
) -> list[PermissionResponse]:
    return await PermissionService.list(db)
