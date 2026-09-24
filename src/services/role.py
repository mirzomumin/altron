from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.models.role import Role
from src.repositories.permission import PermissionRepository
from src.repositories.role import RoleRepository
from src.schemas.role import CreateRoleRequest, UpdateRoleRequest


class RoleService:
    @staticmethod
    async def add(
        data: CreateRoleRequest,
        db: AsyncSession,
    ) -> Role:
        permission_data = data.model_dump(include={"permissions"})
        role_data = data.model_dump(exclude={"permissions"})

        permissions = await PermissionRepository.list(
            db,
            filters=[
                Permission.id.in_(
                    [perm["id"] for perm in permission_data["permissions"]]
                ),
            ],
        )

        roles = await RoleRepository.list(
            db, filters=[func.lower(Role.name) == func.lower(role_data["name"])]
        )
        if len(roles) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already exists",
            )

        role = await RoleRepository.add(role_data, db)
        if permissions:
            permission_ids = [perm.id for perm in permissions]
            await RoleRepository.add_permissions(role, permission_ids, db)

        await db.commit()
        return await RoleRepository.get_by_id(role.id, db)

    @staticmethod
    async def list(db: AsyncSession) -> list[Role]:
        return await RoleRepository.list(db)

    @staticmethod
    async def update(id: UUID, data: UpdateRoleRequest, db: AsyncSession) -> Role:
        role = await RoleRepository.get_by_id(id, db)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )

        permission_data = data.model_dump(include={"permissions"})
        role_data = data.model_dump(exclude={"permissions"})

        permissions = await PermissionRepository.list(
            db,
            filters=[
                Permission.id.in_(
                    [perm["id"] for perm in permission_data["permissions"]]
                ),
            ],
        )

        roles = await RoleRepository.list(
            db,
            filters=[
                func.lower(Role.name) == func.lower(role_data["name"]),
                Role.id != id,
            ],
        )
        if len(roles) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already exists",
            )

        current_perm_ids = {perm.id for perm in role.permissions}
        new_perm_ids = {perm.id for perm in permissions}

        to_delete = current_perm_ids - new_perm_ids
        to_add = new_perm_ids - current_perm_ids

        if to_add:
            await RoleRepository.add_permissions(role, to_add, db)
        if to_delete:
            await RoleRepository.delete_permissions(role, to_delete, db)

        await RoleRepository.update(role.id, role_data, db)
        await db.commit()

        db.expire(role)
        return await RoleRepository.get_by_id(id, db)
