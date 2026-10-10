import asyncio

from sqlalchemy import select

from src.core.permissions import Permission as PermissionCode
from src.db.session import AsyncSessionLocal
from src.models.permission import Permission

PERMISSION_DESCRIPTIONS = {
    PermissionCode.USER_READ: "Read users",
    PermissionCode.USER_CREATE: "Create users",
    PermissionCode.USER_UPDATE: "Update users",
    PermissionCode.USER_DELETE: "Delete users",
    PermissionCode.ROLE_READ: "Read roles",
    PermissionCode.ROLE_CREATE: "Create roles",
    PermissionCode.ROLE_UPDATE: "Update roles",
    PermissionCode.ROLE_DELETE: "Delete roles",
}


async def seed_permissions() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Permission))
        existing_permissions = {
            permission.code: permission for permission in result.scalars().all()
        }

        for permission_code in PermissionCode:
            code = permission_code.value

            if code in existing_permissions:
                continue

            db.add(
                Permission(
                    code=code,
                    description=PERMISSION_DESCRIPTIONS.get(permission_code),
                )
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_permissions())
