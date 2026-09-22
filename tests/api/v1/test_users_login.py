import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import hash_session_id
from src.models import UserSession
from tests.factories import DEFAULT_PASSWORD, UserFactory

URL = "/api/v1/users/login"
PASSWORD = DEFAULT_PASSWORD


async def test_login_succeeds_with_valid_credentials(
    client: AsyncClient,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", password=PASSWORD)

    response = await client.post(
        URL,
        json={"username": "john-doe", "password": PASSWORD},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logged in successfully"}


async def test_login_stores_hashed_session_for_the_user(
    client: AsyncClient,
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    user = await user_factory.create(username="john-doe", password=PASSWORD)

    await client.post(URL, json={"username": "john-doe", "password": PASSWORD})

    session = await db.scalar(select(UserSession).where(UserSession.user_id == user.id))
    assert session is not None
    assert len(session.session_id_hash) == 64
    assert session.revoked_at is None
    assert session.expires_at is not None


async def test_login_sets_session_cookie(
    client: AsyncClient,
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", password=PASSWORD)

    response = await client.post(
        URL,
        json={"username": "john-doe", "password": PASSWORD},
    )

    cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
    assert cookie is not None

    stored = await db.scalar(
        select(UserSession).where(
            UserSession.session_id_hash == hash_session_id(cookie)
        )
    )
    assert stored is not None, "the cookie value must be the raw session id"


async def test_login_rejects_wrong_password(
    client: AsyncClient,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", password=PASSWORD)

    response = await client.post(
        URL,
        json={"username": "john-doe", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_login_creates_no_session_for_wrong_password(
    client: AsyncClient,
    db: AsyncSession,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", password=PASSWORD)

    await client.post(URL, json={"username": "john-doe", "password": "nope"})

    assert await db.scalar(select(func.count()).select_from(UserSession)) == 0


async def test_login_rejects_unknown_username(client: AsyncClient) -> None:
    response = await client.post(
        URL,
        json={"username": "nobody", "password": PASSWORD},
    )

    assert response.status_code == 401


async def test_login_rejects_inactive_user(
    client: AsyncClient,
    user_factory: type[UserFactory],
) -> None:
    await user_factory.create(username="john-doe", password=PASSWORD, is_active=False)

    response = await client.post(
        URL,
        json={"username": "john-doe", "password": PASSWORD},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User is inactive"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty"),
        pytest.param({"username": "john-doe"}, id="missing-password"),
        pytest.param({"password": PASSWORD}, id="missing-username"),
    ],
)
async def test_login_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict,
) -> None:
    response = await client.post(URL, json=payload)

    assert response.status_code == 422
