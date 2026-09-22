import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_password
from src.models import User

URL = "/api/v1/users"


async def test_create_returns_generated_credentials(client: AsyncClient) -> None:
    response = await client.post(
        URL,
        json={"first_name": "John", "last_name": "Doe"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "john-doe"
    assert len(body["password"]) == 16


async def test_create_includes_patronymic_in_username(client: AsyncClient) -> None:
    response = await client.post(
        URL,
        json={
            "first_name": "John",
            "last_name": "Doe",
            "patronymic": "Hermanson",
        },
    )

    assert response.json()["username"] == "john-doe-hermanson"


async def test_create_normalizes_names(client: AsyncClient) -> None:
    response = await client.post(
        URL,
        json={"first_name": "  Ján O'Neil ", "last_name": "D'Öe"},
    )

    assert response.json()["username"] == "jnoneil-de"


async def test_create_persists_active_user_with_hashed_password(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    response = await client.post(
        URL,
        json={"first_name": "John", "last_name": "Doe"},
    )
    body = response.json()

    user = await db.scalar(select(User).where(User.username == body["username"]))

    assert user is not None
    assert user.is_active is True
    assert user.first_name == "John"
    assert user.patronymic == ""
    assert user.password_hash != body["password"]
    assert verify_password(body["password"], user.password_hash)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty"),
        pytest.param({"first_name": "John"}, id="missing-last-name"),
        pytest.param({"last_name": "Doe"}, id="missing-first-name"),
        pytest.param({"first_name": "John", "last_name": None}, id="null-last-name"),
        pytest.param(
            {"first_name": "J" * 256, "last_name": "Doe"},
            id="first-name-too-long",
        ),
    ],
)
async def test_create_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict,
) -> None:
    response = await client.post(URL, json=payload)

    assert response.status_code == 422


@pytest.mark.xfail(
    reason="Duplicate names hit the unique index on users.username and surface "
    "as an unhandled IntegrityError instead of a 409",
    strict=True,
)
async def test_create_duplicate_names_returns_conflict(client: AsyncClient) -> None:
    payload = {"first_name": "John", "last_name": "Doe"}
    await client.post(URL, json=payload)

    response = await client.post(URL, json=payload)

    assert response.status_code == 409
