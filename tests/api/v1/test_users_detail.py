from uuid import uuid4

from httpx import AsyncClient

from tests.factories import PermissionFactory, RoleFactory, UserFactory

URL = "/api/v1/users"


async def test_detail_returns_the_user(
    client: AsyncClient, user_factory: type[UserFactory]
) -> None:
    user = await user_factory.create(username="john-doe", patronymic="Hermanson")

    response = await client.get(f"{URL}/{user.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["username"] == "john-doe"
    assert body["patronymic"] == "Hermanson"
    assert body["roles"] == []


async def test_detail_includes_roles_and_permissions(
    client: AsyncClient,
    user_factory: type[UserFactory],
    role_factory: type[RoleFactory],
    permission_factory: type[PermissionFactory],
) -> None:
    role = await role_factory.create(
        name="admin",
        permissions=[
            await permission_factory.create(code="user:read"),
            await permission_factory.create(code="user:create"),
        ],
    )
    user = await user_factory.create(username="john-doe", roles=[role])

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


async def test_detail_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.get(f"{URL}/{uuid4()}")

    assert response.status_code == 404


async def test_detail_handles_role_without_description(
    client: AsyncClient,
    user_factory: type[UserFactory],
    role_factory: type[RoleFactory],
) -> None:
    role = await role_factory.create(name="admin", description="")
    user = await user_factory.create(username="john-doe", roles=[role])

    response = await client.get(f"{URL}/{user.id}")

    assert response.status_code == 200
