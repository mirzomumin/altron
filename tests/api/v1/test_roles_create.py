from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Role
from tests.factories import PermissionFactory, RoleFactory

URL = "/api/v1/roles"


async def test_create_returns_the_role(client: AsyncClient) -> None:
    response = await client.post(
        URL,
        json={"name": "admin", "description": "Administrator", "permissions": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "admin"
    assert body["description"] == "Administrator"
    assert body["is_default"] is False
    assert body["permissions"] == []


async def test_create_attaches_permissions(
    client: AsyncClient,
    permission_factory: type[PermissionFactory],
) -> None:
    read = await permission_factory.create(code="user:read")
    create = await permission_factory.create(code="user:create")

    response = await client.post(
        URL,
        json={
            "name": "admin",
            "permissions": [{"id": str(read.id)}, {"id": str(create.id)}],
        },
    )

    assert response.status_code == 200
    assert {perm["code"] for perm in response.json()["permissions"]} == {
        "user:read",
        "user:create",
    }


async def test_create_ignores_unknown_permissions(
    client: AsyncClient,
    permission_factory: type[PermissionFactory],
) -> None:
    read = await permission_factory.create(code="user:read")

    response = await client.post(
        URL,
        json={
            "name": "admin",
            "permissions": [{"id": str(read.id)}, {"id": str(uuid4())}],
        },
    )

    assert response.status_code == 200
    assert [perm["code"] for perm in response.json()["permissions"]] == ["user:read"]


async def test_create_persists_the_role(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    response = await client.post(URL, json={"name": "admin", "permissions": []})

    role = await db.scalar(select(Role).where(Role.name == "admin"))
    assert role is not None
    assert str(role.id) == response.json()["id"]
    assert role.description == ""


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty"),
        pytest.param({"permissions": []}, id="missing-name"),
        pytest.param({"name": "admin"}, id="missing-permissions"),
        pytest.param({"name": "a" * 101, "permissions": []}, id="name-too-long"),
        pytest.param(
            {"name": "admin", "description": "d" * 256, "permissions": []},
            id="description-too-long",
        ),
        pytest.param(
            {"name": "admin", "permissions": [{"id": "not-a-uuid"}]},
            id="malformed-permission-id",
        ),
    ],
)
async def test_create_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict,
) -> None:
    response = await client.post(URL, json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("admin", id="same-case"),
        pytest.param("Admin", id="capitalized"),
        pytest.param("ADMIN", id="upper-case"),
    ],
)
async def test_create_duplicate_name_returns_conflict(
    client: AsyncClient,
    db: AsyncSession,
    role_factory: type[RoleFactory],
    name: str,
) -> None:
    await role_factory.create(name="admin")

    response = await client.post(URL, json={"name": name, "permissions": []})

    assert response.status_code == 409
    assert response.json()["detail"] == "Role already exists"
    assert len((await db.scalars(select(Role))).all()) == 1
