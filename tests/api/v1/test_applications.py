from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Application, Customer
from src.models.application import submissions
from tests.factories import ApplicationFactory, CustomerFactory, UserFactory

URL = "/api/v1/applications"


@pytest.fixture
async def customer(customer_factory: type[CustomerFactory]) -> Customer:
    return await customer_factory.create(name="Acme")


def _payload(customer: Customer, **overrides) -> dict:
    return {
        "cid": 101,
        "number": "A-2026-001",
        "customer_id": str(customer.id),
        "qty": 3,
        "received_at": "2026-10-01",
        **overrides,
    }


async def _stored_submitter_ids(db: AsyncSession, application_id) -> set:
    result = await db.execute(
        select(submissions.c.user_id).where(
            submissions.c.application_id == application_id
        )
    )
    return set(result.scalars().all())


################### Create ###################
async def test_create_returns_the_application(
    client: AsyncClient, customer: Customer
) -> None:
    response = await client.post(URL, json=_payload(customer))

    assert response.status_code == 200
    body = response.json()
    assert body["cid"] == 101
    assert body["number"] == "A-2026-001"
    assert body["qty"] == 3
    assert body["received_at"] == "2026-10-01"
    assert body["customer"] == {"id": str(customer.id), "name": "Acme"}
    assert body["submitters"] == []


async def test_create_attaches_submitters_and_ignores_unknown_ones(
    client: AsyncClient,
    db: AsyncSession,
    customer: Customer,
    user_factory: type[UserFactory],
) -> None:
    user = await user_factory.create(username="john-doe")

    response = await client.post(
        URL,
        json=_payload(
            customer, submitters=[{"id": str(user.id)}, {"id": str(uuid4())}]
        ),
    )

    assert response.status_code == 200
    assert [s["username"] for s in response.json()["submitters"]] == ["john-doe"]
    assert await _stored_submitter_ids(db, response.json()["id"]) == {user.id}


async def test_create_returns_404_for_unknown_customer(client: AsyncClient) -> None:
    response = await client.post(
        URL,
        json={
            "cid": 1,
            "number": "A-1",
            "customer_id": str(uuid4()),
            "qty": 1,
            "received_at": "2026-10-01",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"number": "x" * 21}, id="number-too-long"),
        pytest.param({"number": ""}, id="blank-number"),
        pytest.param({"qty": 0}, id="zero-qty"),
        pytest.param({"qty": 40000}, id="qty-overflows-smallint"),
        pytest.param({"received_at": "not-a-date"}, id="malformed-date"),
        pytest.param({"cid": None}, id="null-cid"),
    ],
)
async def test_create_rejects_invalid_payload(
    client: AsyncClient, customer: Customer, overrides: dict
) -> None:
    response = await client.post(URL, json=_payload(customer, **overrides))

    assert response.status_code == 422


################### List / Detail ###################
async def test_list_returns_newest_first_with_customer(
    client: AsyncClient,
    application_factory: type[ApplicationFactory],
) -> None:
    await application_factory.create(number="old", received_at=date(2026, 1, 1))
    await application_factory.create(number="new", received_at=date(2026, 5, 1))

    response = await client.get(URL)

    assert response.status_code == 200
    body = response.json()
    assert [app["number"] for app in body] == ["new", "old"]
    assert "submitters" not in body[0]
    assert set(body[0]["customer"]) == {"id", "name"}


async def test_list_filters_by_customer(
    client: AsyncClient,
    customer: Customer,
    application_factory: type[ApplicationFactory],
) -> None:
    await application_factory.create(number="mine", customer=customer)
    await application_factory.create(number="theirs")

    response = await client.get(URL, params={"customer_id": str(customer.id)})

    assert [app["number"] for app in response.json()] == ["mine"]


async def test_detail_includes_submitters(
    client: AsyncClient,
    db: AsyncSession,
    application_factory: type[ApplicationFactory],
    user_factory: type[UserFactory],
) -> None:
    user = await user_factory.create(username="john-doe")
    application = await application_factory.create()
    await db.execute(
        submissions.insert().values(application_id=application.id, user_id=user.id)
    )
    await db.commit()

    response = await client.get(f"{URL}/{application.id}")

    assert response.status_code == 200
    [submitter] = response.json()["submitters"]
    assert submitter["id"] == str(user.id)
    assert submitter["position"] == "specialist"


async def test_detail_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.get(f"{URL}/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


################### Update ###################
async def test_update_changes_fields_and_syncs_submitters(
    client: AsyncClient,
    db: AsyncSession,
    customer: Customer,
    application_factory: type[ApplicationFactory],
    user_factory: type[UserFactory],
) -> None:
    kept = await user_factory.create(username="kept")
    removed = await user_factory.create(username="removed")
    added = await user_factory.create(username="added")
    application = await application_factory.create(submitters=[kept, removed])

    response = await client.put(
        f"{URL}/{application.id}",
        json=_payload(
            customer,
            number="A-2026-999",
            submitters=[{"id": str(kept.id)}, {"id": str(added.id)}],
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["number"] == "A-2026-999"
    assert body["customer"]["id"] == str(customer.id)
    assert {s["username"] for s in body["submitters"]} == {"kept", "added"}
    assert await _stored_submitter_ids(db, application.id) == {kept.id, added.id}


async def test_update_returns_404_for_unknown_customer(
    client: AsyncClient,
    application_factory: type[ApplicationFactory],
) -> None:
    application = await application_factory.create()

    response = await client.put(
        f"{URL}/{application.id}",
        json={
            "cid": 1,
            "number": "A-1",
            "customer_id": str(uuid4()),
            "qty": 1,
            "received_at": "2026-10-01",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


async def test_update_returns_404_for_unknown_id(
    client: AsyncClient, customer: Customer
) -> None:
    response = await client.put(f"{URL}/{uuid4()}", json=_payload(customer))

    assert response.status_code == 404


################### Delete ###################
async def test_delete_removes_application_and_its_submissions(
    client: AsyncClient,
    db: AsyncSession,
    application_factory: type[ApplicationFactory],
    user_factory: type[UserFactory],
) -> None:
    user = await user_factory.create(username="john-doe")
    application = await application_factory.create(submitters=[user])

    response = await client.delete(f"{URL}/{application.id}")

    assert response.status_code == 204
    db.expunge_all()
    assert await db.get(Application, application.id) is None
    assert await _stored_submitter_ids(db, application.id) == set()


async def test_delete_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.delete(f"{URL}/{uuid4()}")

    assert response.status_code == 404
