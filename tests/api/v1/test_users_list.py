from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.models.user import UserPosition
from src.repositories.user import UserRepository
from tests.factories import CustomerFactory, UserFactory

URL = "/api/v1/users"

EXPECTED_FIELDS = {
    "id",
    "username",
    "first_name",
    "last_name",
    "patronymic",
    "is_active",
    "position",
    "customer_id",
}


async def test_list_is_empty_without_users(client: AsyncClient) -> None:
    response = await client.get(URL)

    assert response.status_code == 200
    assert response.json() == []


async def test_list_returns_every_user(
    client: AsyncClient, user_factory: type[UserFactory]
) -> None:
    await user_factory.create(username="john-doe")
    await user_factory.create(username="jane-roe", first_name="Jane", last_name="Roe")

    response = await client.get(URL)

    assert response.status_code == 200
    usernames = {user["username"] for user in response.json()}
    assert usernames == {"john-doe", "jane-roe"}


async def test_list_includes_inactive_users(
    client: AsyncClient, user_factory: type[UserFactory]
) -> None:
    await user_factory.create(username="john-doe", is_active=False)

    [user] = (await client.get(URL)).json()

    assert user["is_active"] is False


async def test_list_exposes_only_public_fields(
    client: AsyncClient,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", patronymic="Hermanson")

    [user] = (await client.get(URL)).json()

    assert set(user) == EXPECTED_FIELDS
    assert user["patronymic"] == "Hermanson"


async def test_list_exposes_position_and_customer(
    client: AsyncClient,
    user_factory: type[UserFactory],
) -> None:
    user = await user_factory.create(username="john-doe", position=UserPosition.HEAD)

    [payload] = (await client.get(URL)).json()

    assert payload["position"] == "head"
    assert payload["customer_id"] == str(user.customer_id)


async def test_list_filters_by_customer(
    client: AsyncClient,
    user_factory: type[UserFactory],
    customer_factory: type[CustomerFactory],
) -> None:
    acme = await customer_factory.create(name="Acme")
    await user_factory.create(username="john-doe", customer=acme)
    await user_factory.create(username="jane-roe")

    response = await client.get(URL, params={"customer_id": str(acme.id)})

    assert [user["username"] for user in response.json()] == ["john-doe"]


async def test_list_filters_by_position(
    client: AsyncClient,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", position=UserPosition.MANAGER)
    await user_factory.create(username="jane-roe")

    response = await client.get(URL, params={"position": "manager"})

    assert [user["username"] for user in response.json()] == ["john-doe"]


async def test_list_rejects_unknown_position(client: AsyncClient) -> None:
    response = await client.get(URL, params={"position": "janitor"})

    assert response.status_code == 422


# `UserRepository.list` accepts filters that no endpoint passes yet, so they are
# covered directly rather than through GET /users.


async def test_repository_list_returns_every_user(
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe")
    await user_factory.create(username="jane-roe")

    users = await UserRepository.list(db)

    assert {user.username for user in users} == {"john-doe", "jane-roe"}


async def test_repository_list_ignores_empty_filters(
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe")

    users = await UserRepository.list(db, filters=[])

    assert [user.username for user in users] == ["john-doe"]


async def test_repository_list_applies_a_single_filter(
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", is_active=True)
    await user_factory.create(username="jane-roe", is_active=False)

    users = await UserRepository.list(db, filters=[User.is_active.is_(True)])

    assert [user.username for user in users] == ["john-doe"]


async def test_repository_list_combines_filters_with_and(
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", last_name="Doe", is_active=True)
    await user_factory.create(username="jane-doe", last_name="Doe", is_active=False)
    await user_factory.create(username="jane-roe", last_name="Roe", is_active=True)

    users = await UserRepository.list(
        db,
        filters=[User.last_name == "Doe", User.is_active.is_(True)],
    )

    assert [user.username for user in users] == ["john-doe"]


async def test_repository_list_returns_empty_when_nothing_matches(
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe")

    users = await UserRepository.list(db, filters=[User.username == "nobody"])

    assert users == []
