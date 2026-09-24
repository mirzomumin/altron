from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.role import role_permissions
from tests.factories import PermissionFactory, RoleFactory

URL = "/api/v1/roles"


async def _stored_permission_ids(db: AsyncSession, role_id) -> set:
    result = await db.execute(
        select(role_permissions.c.permission_id).where(
            role_permissions.c.role_id == role_id
        )
    )
    return set(result.scalars().all())


async def test_update_changes_name_and_description(
    client: AsyncClient,
    role_factory: type[RoleFactory],
) -> None:
    role = await role_factory.create(name="admin", description="Administrator")

    response = await client.put(
        f"{URL}/{role.id}",
        json={"name": "superadmin", "description": "Root", "permissions": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(role.id)
    assert body["name"] == "superadmin"
    assert body["description"] == "Root"


async def test_update_adds_and_removes_permissions(
    client: AsyncClient,
    db: AsyncSession,
    role_factory: type[RoleFactory],
    permission_factory: type[PermissionFactory],
) -> None:
    kept = await permission_factory.create(code="user:read")
    removed = await permission_factory.create(code="user:delete")
    added = await permission_factory.create(code="user:create")
    role = await role_factory.create(name="admin", permissions=[kept, removed])

    response = await client.put(
        f"{URL}/{role.id}",
        json={
            "name": "admin",
            "permissions": [{"id": str(kept.id)}, {"id": str(added.id)}],
        },
    )

    assert response.status_code == 200
    assert {perm["code"] for perm in response.json()["permissions"]} == {
        "user:read",
        "user:create",
    }
    assert await _stored_permission_ids(db, role.id) == {kept.id, added.id}


async def test_update_leaves_other_roles_permissions_untouched(
    client: AsyncClient,
    db: AsyncSession,
    role_factory: type[RoleFactory],
    permission_factory: type[PermissionFactory],
) -> None:
    shared = await permission_factory.create(code="user:read")
    role = await role_factory.create(name="admin", permissions=[shared])
    other = await role_factory.create(name="manager", permissions=[shared])

    await client.put(f"{URL}/{role.id}", json={"name": "admin", "permissions": []})

    assert await _stored_permission_ids(db, other.id) == {shared.id}


async def test_update_with_empty_permissions_clears_them(
    client: AsyncClient,
    db: AsyncSession,
    role_factory: type[RoleFactory],
    permission_factory: type[PermissionFactory],
) -> None:
    role = await role_factory.create(
        name="admin",
        permissions=[await permission_factory.create(code="user:read")],
    )

    response = await client.put(
        f"{URL}/{role.id}",
        json={"name": "admin", "permissions": []},
    )

    assert response.status_code == 200
    assert response.json()["permissions"] == []
    assert await _stored_permission_ids(db, role.id) == set()


async def test_update_ignores_unknown_permissions(
    client: AsyncClient,
    role_factory: type[RoleFactory],
) -> None:
    role = await role_factory.create(name="admin")

    response = await client.put(
        f"{URL}/{role.id}",
        json={"name": "admin", "permissions": [{"id": str(uuid4())}]},
    )

    assert response.status_code == 200
    assert response.json()["permissions"] == []


async def test_update_is_committed(
    client: AsyncClient,
    db: AsyncSession,
    role_factory: type[RoleFactory],
) -> None:
    role = await role_factory.create(name="admin")

    await client.put(
        f"{URL}/{role.id}",
        json={"name": "superadmin", "permissions": []},
    )
    await db.rollback()

    await db.refresh(role)
    assert role.name == "superadmin"


async def test_update_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.put(
        f"{URL}/{uuid4()}",
        json={"name": "admin", "permissions": []},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found"


async def test_update_rejects_malformed_id(client: AsyncClient) -> None:
    response = await client.put(
        f"{URL}/not-a-uuid",
        json={"name": "admin", "permissions": []},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty"),
        pytest.param({"permissions": []}, id="missing-name"),
        pytest.param({"name": "admin"}, id="missing-permissions"),
        pytest.param({"name": "a" * 101, "permissions": []}, id="name-too-long"),
    ],
)
async def test_update_rejects_invalid_payload(
    client: AsyncClient,
    role_factory: type[RoleFactory],
    payload: dict,
) -> None:
    role = await role_factory.create(name="admin")

    response = await client.put(f"{URL}/{role.id}", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("manager", id="same-case"),
        pytest.param("Manager", id="capitalized"),
        pytest.param("MANAGER", id="upper-case"),
    ],
)
async def test_update_to_another_roles_name_returns_conflict(
    client: AsyncClient,
    db: AsyncSession,
    role_factory: type[RoleFactory],
    permission_factory: type[PermissionFactory],
    name: str,
) -> None:
    permission = await permission_factory.create(code="user:read")
    role = await role_factory.create(name="admin", permissions=[permission])
    await role_factory.create(name="manager")

    response = await client.put(
        f"{URL}/{role.id}",
        json={"name": name, "permissions": []},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Role already exists"
    await db.refresh(role)
    assert role.name == "admin"
    assert await _stored_permission_ids(db, role.id) == {permission.id}


async def test_update_keeping_own_name_is_not_a_conflict(
    client: AsyncClient,
    role_factory: type[RoleFactory],
) -> None:
    role = await role_factory.create(name="admin", description="Administrator")

    response = await client.put(
        f"{URL}/{role.id}",
        json={"name": "admin", "description": "Root", "permissions": []},
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Root"


async def test_update_can_change_the_case_of_its_own_name(
    client: AsyncClient,
    role_factory: type[RoleFactory],
) -> None:
    role = await role_factory.create(name="admin")

    response = await client.put(
        f"{URL}/{role.id}",
        json={"name": "Admin", "permissions": []},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Admin"
