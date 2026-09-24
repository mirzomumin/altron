from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Role
from src.repositories.role import RoleRepository
from tests.factories import PermissionFactory, RoleFactory

URL = "/api/v1/roles"


async def test_list_is_empty_without_roles(client: AsyncClient) -> None:
    response = await client.get(URL)

    assert response.status_code == 200
    assert response.json() == []


async def test_list_returns_every_role(
    client: AsyncClient,
    role_factory: type[RoleFactory],
) -> None:
    await role_factory.create(name="admin")
    await role_factory.create(name="manager")

    response = await client.get(URL)

    assert response.status_code == 200
    assert {role["name"] for role in response.json()} == {"admin", "manager"}


async def test_list_includes_permissions(
    client: AsyncClient,
    role_factory: type[RoleFactory],
    permission_factory: type[PermissionFactory],
) -> None:
    await role_factory.create(
        name="admin",
        permissions=[await permission_factory.create(code="user:read")],
    )

    response = await client.get(URL)

    assert response.status_code == 200
    [role] = response.json()
    assert [perm["code"] for perm in role["permissions"]] == ["user:read"]


# `RoleRepository.list` accepts filters that no endpoint passes yet, so they are
# covered directly rather than through GET /roles.


async def test_repository_list_ignores_empty_filters(
    db: AsyncSession,
    role_factory: type[RoleFactory],
) -> None:
    await role_factory.create(name="admin")

    roles = await RoleRepository.list(db, filters=[])

    assert [role.name for role in roles] == ["admin"]


async def test_repository_list_applies_filters(
    db: AsyncSession,
    role_factory: type[RoleFactory],
) -> None:
    await role_factory.create(name="admin", is_default=True)
    await role_factory.create(name="manager", is_default=False)

    roles = await RoleRepository.list(db, filters=[Role.is_default.is_(True)])

    assert [role.name for role in roles] == ["admin"]


async def test_repository_list_returns_empty_when_nothing_matches(
    db: AsyncSession,
    role_factory: type[RoleFactory],
) -> None:
    await role_factory.create(name="admin")

    roles = await RoleRepository.list(db, filters=[Role.name == "nobody"])

    assert roles == []
