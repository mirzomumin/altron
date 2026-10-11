from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy import (
    ForeignKey,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.db.base import BaseModel

if TYPE_CHECKING:
    from src.models import Application, NormDocument


class SeedMethod(str, Enum):
    STERILIZATION = "sterilization"
    MICROBIOLOGY = "microbiology"


class Item(BaseModel):
    __tablename__ = "items"

    name: Mapped[str] = mapped_column(String(255))

    # fields in certification
    producer: Mapped[str | None] = mapped_column(String(100))
    tnved_code: Mapped[str | None] = mapped_column(String(16))
    series: Mapped[str | None] = mapped_column(String(64))
    expiry_date: Mapped[date | None]
    batch_qty: Mapped[int | None] = mapped_column(SmallInteger())
    unit: Mapped[str | None]
    reg_no: Mapped[str | None] = mapped_column(String(64))
    norm_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "norm_documents.id",
            ondelete="SET NULL",
        ),
        index=True,
    )
    cert_scheme: Mapped[str | None] = mapped_column(String(16))
    unit_price: Mapped[int | None]
    is_rx: Mapped[bool] = mapped_column(default=False)
    ref_price: Mapped[int | None]

    # fields in monitoring
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "applications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    seed_method: Mapped[SeedMethod | None] = mapped_column(
        SQLAlchemyEnum(SeedMethod, name="seed_method"),
    )
    seeded_at: Mapped[datetime | None]
    issue_date: Mapped[date | None]
    planned_protocol_date: Mapped[datetime | None]
    actual_protocol_date: Mapped[datetime | None]
    note: Mapped[str | None] = mapped_column(String(255))

    cert_number: Mapped[str | None]
    cert_issue_date: Mapped[date | None]

    norm_document: Mapped[NormDocument] = relationship(
        back_populates="lab_tests",
        lazy="raise_on_sql",
    )
    application: Mapped[Application] = relationship(
        back_populates="items",
        lazy="raise_on_sql",
    )
