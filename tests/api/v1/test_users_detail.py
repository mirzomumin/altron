from uuid import uuid4

import pytest
from httpx import AsyncClient

URL = "/api/v1/users"


async def test_detail_returns_the_user(client: AsyncClient, make_user) -> None:
    user = await make_user(username="john-doe", patronymic="Hermanson")

    response = await client.get(f"{URL}/{user.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["username"] == "john-doe"
    assert body["patronymic"] == "Hermanson"
    assert body["roles"] == []


async def test_detail_includes_roles_and_permissions(
    client: AsyncClient,
    make_user,
    make_role,
) -> None:
    role = await make_role(
        name="admin",
        permissions=["user:read", "user:create"],
    )
    user = await make_user(username="john-doe", roles=[role])

    response = await client.get(f"{URL}/{user.id}")

    assert response.status_code == 200
    [payload] = response.json()["roles"]
    assert payload["name"] == "admin"
    assert payload["is_default"] is False
    assert {permission["code"] for permission in payload["permissions"]} == {
        "user:read",
        "user:create",
    }


async def test_detail_rejects_malformed_id(client: AsyncClient) -> None:
    response = await client.get(f"{URL}/not-a-uuid")

    assert response.status_code == 422


@pytest.mark.xfail(
    reason="UserService.get returns None for a missing user, which fails response "
    "validation instead of returning 404",
    strict=True,
)
async def test_detail_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.get(f"{URL}/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.xfail(
    reason="Role.description and Permission.description are nullable in the model "
    "but typed `str` in the response schema, so a NULL description 500s",
    strict=True,
)
async def test_detail_handles_role_without_description(
    client: AsyncClient,
    make_user,
    make_role,
) -> None:
    role = await make_role(name="admin", description=None)
    user = await make_user(username="john-doe", roles=[role])

    response = await client.get(f"{URL}/{user.id}")

    assert response.status_code == 200
