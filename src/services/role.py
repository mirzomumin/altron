from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission
from src.models.role import Role
from src.repositories.permission import PermissionRepository
from src.repositories.role import RoleRepository
from src.schemas.role import CreateRoleRequest


class RoleService:
    @staticmethod
    async def create(
        data: CreateRoleRequest,
        db: AsyncSession,
    ) -> Role:
        permission_data = data.model_dump(include={"permissions"})
        role_data = data.model_dump(exclude={"permissions"})

        permissions = await PermissionRepository.list(
            db,
            filters=[
                Permission.id.in_([perm["id"] for perm in permission_data]),
            ],
        )

        role = await RoleRepository.add(role_data, db)
        if permissions:
            await RoleRepository.add_permissions(role, permissions, db)

        await db.commit()
        return await RoleRepository.get_by_id(role.id, db)

    # @staticmethod
    # async def list(db: AsyncSession) -> list[User]:
    #     return await UserRepository.list(db)

    # @staticmethod
    # async def get(id: UUID, db: AsyncSession) -> User:
    #     user = await UserRepository.get_by_id(id, db)

    #     if user is None:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="User not found",
    #         )

    #     return user
