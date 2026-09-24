from fastapi import APIRouter

from src.db.session import SessionDep
from src.repositories.role import RoleRepository
from src.schemas.role import CreateRoleRequest, CreateRoleResponse

router = APIRouter(
    prefix="/roles",
    tags=["Role"],
)


@router.post("")
async def create_role(
    data: CreateRoleRequest,
    db: SessionDep,
) -> CreateRoleResponse:
    return await RoleRepository.add(data, db)
