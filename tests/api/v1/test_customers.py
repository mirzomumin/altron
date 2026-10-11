from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Application, Customer, User
from tests.factories import ApplicationFactory, CustomerFactory, UserFactory

URL = "/api/v1/customers"


################### Create ###################
async def test_create_returns_the_customer(
    client: AsyncClient, db: AsyncSession
) -> None:
    response = await client.post(URL, json={"name": "Acme"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Acme"
    customer = await db.get(Customer, body["id"])
    assert customer is not None


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty"),
        pytest.param({"name": ""}, id="blank-name"),
        pytest.param({"name": "a" * 256}, id="name-too-long"),
    ],
)
async def test_create_rejects_invalid_payload(
    client: AsyncClient, payload: dict
) -> None:
    response = await client.post(URL, json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("name", ["Acme", "acme", "ACME"])
async def test_create_duplicate_name_returns_conflict(
    client: AsyncClient,
    customer_factory: type[CustomerFactory],
    name: str,
) -> None:
    await customer_factory.create(name="Acme")

    response = await client.post(URL, json={"name": name})

    assert response.status_code == 409
    assert response.json()["detail"] == "Customer already exists"


################### List / Detail ###################
async def test_list_returns_customers_sorted_by_name(
    client: AsyncClient, customer_factory: type[CustomerFactory]
) -> None:
    await customer_factory.create(name="Zeta")
    await customer_factory.create(name="Acme")

    response = await client.get(URL)

    assert response.status_code == 200
    assert [customer["name"] for customer in response.json()] == ["Acme", "Zeta"]


@pytest.mark.parametrize(
    ("search", "expected"),
    [
        pytest.param("acme", ["Acme", "Acme Labs"], id="prefix-case-insensitive"),
        pytest.param("LABS", ["Acme Labs"], id="substring-upper-case"),
        pytest.param("zzz", [], id="no-match"),
        pytest.param("", ["Acme", "Acme Labs", "Zeta"], id="empty-returns-all"),
    ],
)
async def test_list_searches_by_name(
    client: AsyncClient,
    customer_factory: type[CustomerFactory],
    search: str,
    expected: list[str],
) -> None:
    for name in ("Zeta", "Acme Labs", "Acme"):
        await customer_factory.create(name=name)

    response = await client.get(URL, params={"name": search})

    assert response.status_code == 200
    assert [customer["name"] for customer in response.json()] == expected


@pytest.mark.parametrize("search", ["%", "_", "\\"])
async def test_list_search_treats_wildcards_literally(
    client: AsyncClient,
    customer_factory: type[CustomerFactory],
    search: str,
) -> None:
    await customer_factory.create(name="Acme")
    await customer_factory.create(name=f"100{search} Pure")

    response = await client.get(URL, params={"name": search})

    assert [customer["name"] for customer in response.json()] == [f"100{search} Pure"]


async def test_detail_returns_the_customer(
    client: AsyncClient, customer_factory: type[CustomerFactory]
) -> None:
    customer = await customer_factory.create(name="Acme")

    response = await client.get(f"{URL}/{customer.id}")

    assert response.status_code == 200
    assert response.json() == {"id": str(customer.id), "name": "Acme"}


async def test_detail_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.get(f"{URL}/{uuid4()}")

    assert response.status_code == 404


################### Update ###################
async def test_update_changes_name(
    client: AsyncClient,
    db: AsyncSession,
    customer_factory: type[CustomerFactory],
) -> None:
    customer = await customer_factory.create(name="Acme")

    response = await client.put(f"{URL}/{customer.id}", json={"name": "Acme LLC"})

    assert response.status_code == 200
    assert response.json()["name"] == "Acme LLC"
    await db.refresh(customer)
    assert customer.name == "Acme LLC"


async def test_update_to_another_customers_name_returns_conflict(
    client: AsyncClient, customer_factory: type[CustomerFactory]
) -> None:
    customer = await customer_factory.create(name="Acme")
    await customer_factory.create(name="Zeta")

    response = await client.put(f"{URL}/{customer.id}", json={"name": "zeta"})

    assert response.status_code == 409


async def test_update_can_change_the_case_of_its_own_name(
    client: AsyncClient, customer_factory: type[CustomerFactory]
) -> None:
    customer = await customer_factory.create(name="acme")

    response = await client.put(f"{URL}/{customer.id}", json={"name": "Acme"})

    assert response.status_code == 200
    assert response.json()["name"] == "Acme"


async def test_update_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.put(f"{URL}/{uuid4()}", json={"name": "Acme"})

    assert response.status_code == 404


################### Delete ###################
async def test_delete_removes_customer_with_its_users_and_applications(
    client: AsyncClient,
    db: AsyncSession,
    customer_factory: type[CustomerFactory],
    user_factory: type[UserFactory],
    application_factory: type[ApplicationFactory],
) -> None:
    customer = await customer_factory.create(name="Acme")
    await user_factory.create(username="john-doe", customer=customer)
    await application_factory.create(customer=customer)

    response = await client.delete(f"{URL}/{customer.id}")

    assert response.status_code == 204
    db.expunge_all()
    assert await db.get(Customer, customer.id) is None
    assert await db.scalar(select(User).where(User.customer_id == customer.id)) is None
    assert (
        await db.scalar(
            select(Application).where(Application.customer_id == customer.id)
        )
        is None
    )


async def test_delete_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.delete(f"{URL}/{uuid4()}")

    assert response.status_code == 404
