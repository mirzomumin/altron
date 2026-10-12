from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import LabTest, NormDocument
from src.services.norm_document import NormDocumentService
from tests.factories import NormDocumentFactory

URL = "/api/v1/norm-documents"


def _payload(**overrides) -> dict:
    return {
        "name": "GOST 12345-2020",
        "approved_date": "2026-01-15",
        "expiry_date": "2031-01-15",
        "lab_tests": [
            {"name": "Sterility", "method": "Membrane filtration", "lab_type": "own"},
            {
                "name": "Endotoxins",
                "method": "LAL test",
                "lab_type": "subcontracted",
            },
        ],
        **overrides,
    }


async def test_create_returns_document_with_lab_tests(client: AsyncClient) -> None:
    response = await client.post(URL, json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "GOST 12345-2020"
    assert body["approved_date"] == "2026-01-15"
    assert body["expiry_date"] == "2031-01-15"
    assert [(t["name"], t["method"], t["lab_type"]) for t in body["lab_tests"]] == [
        ("Sterility", "Membrane filtration", "own"),
        ("Endotoxins", "LAL test", "subcontracted"),
    ]


async def test_create_persists_lab_tests_linked_to_document(
    client: AsyncClient, db: AsyncSession
) -> None:
    response = await client.post(URL, json=_payload())

    document_id = response.json()["id"]
    result = await db.execute(
        select(LabTest.name).where(LabTest.norm_document_id == document_id)
    )
    assert set(result.scalars().all()) == {"Sterility", "Endotoxins"}


async def test_create_without_lab_tests_and_expiry_date(client: AsyncClient) -> None:
    response = await client.post(
        URL, json={"name": "GOST 1", "approved_date": "2026-01-15"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["expiry_date"] is None
    assert body["lab_tests"] == []


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"name": ""}, id="blank-name"),
        pytest.param({"name": "x" * 256}, id="name-too-long"),
        pytest.param({"approved_date": "not-a-date"}, id="malformed-date"),
        pytest.param({"expiry_date": "2025-01-01"}, id="expiry-before-approval"),
        pytest.param(
            {"lab_tests": [{"name": "A", "method": "M", "lab_type": "external"}]},
            id="unknown-lab-type",
        ),
        pytest.param(
            {"lab_tests": [{"name": "A", "lab_type": "own"}]},
            id="missing-method",
        ),
        pytest.param(
            {
                "lab_tests": [
                    {"name": "A", "method": "M1", "lab_type": "own"},
                    {"name": "A", "method": "M2", "lab_type": "own"},
                ]
            },
            id="duplicate-lab-test-names",
        ),
    ],
)
async def test_create_rejects_invalid_payload(
    client: AsyncClient, db: AsyncSession, overrides: dict
) -> None:
    response = await client.post(URL, json=_payload(**overrides))

    assert response.status_code == 422
    assert (await db.execute(select(NormDocument))).first() is None


# `NormDocumentService.get` has no endpoint of its own yet, so it is covered
# directly rather than through the API.


async def test_service_get_returns_document_with_lab_tests(
    client: AsyncClient, db: AsyncSession
) -> None:
    document_id = (await client.post(URL, json=_payload())).json()["id"]
    db.expunge_all()

    document = await NormDocumentService.get(document_id, db)

    assert document.name == "GOST 12345-2020"
    assert {lab_test.name for lab_test in document.lab_tests} == {
        "Sterility",
        "Endotoxins",
    }


async def test_service_get_returns_document_without_lab_tests(
    db: AsyncSession,
    norm_document_factory: type[NormDocumentFactory],
) -> None:
    created = await norm_document_factory.create(name="GOST 1")

    document = await NormDocumentService.get(created.id, db)

    assert document.id == created.id
    assert document.lab_tests == []


async def test_service_get_raises_404_for_unknown_id(db: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await NormDocumentService.get(uuid4(), db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Norm document not found"
