from httpx import AsyncClient

URL = "/api/v1/users"

EXPECTED_FIELDS = {
    "id",
    "username",
    "first_name",
    "last_name",
    "patronymic",
    "is_active",
}


async def test_list_is_empty_without_users(client: AsyncClient) -> None:
    response = await client.get(URL)

    assert response.status_code == 200
    assert response.json() == []


async def test_list_returns_every_user(client: AsyncClient, make_user) -> None:
    await make_user(username="john-doe")
    await make_user(username="jane-roe", first_name="Jane", last_name="Roe")

    response = await client.get(URL)

    assert response.status_code == 200
    usernames = {user["username"] for user in response.json()}
    assert usernames == {"john-doe", "jane-roe"}


async def test_list_includes_inactive_users(client: AsyncClient, make_user) -> None:
    await make_user(username="john-doe", is_active=False)

    [user] = (await client.get(URL)).json()

    assert user["is_active"] is False


async def test_list_exposes_only_public_fields(
    client: AsyncClient,
    make_user,
) -> None:
    await make_user(username="john-doe", patronymic="Hermanson")

    [user] = (await client.get(URL)).json()

    assert set(user) == EXPECTED_FIELDS
    assert user["patronymic"] == "Hermanson"
