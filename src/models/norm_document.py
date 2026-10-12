from datetime import date
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy import (
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.db.base import BaseModel

if TYPE_CHECKING:
    from src.models import Item


class LabType(str, Enum):
    OWN = "own"
    SUBCONTRACTED = "subcontracted"


class NormDocument(BaseModel):
    __tablename__ = "norm_documents"

    name: Mapped[str] = mapped_column(String(255))
    approved_date: Mapped[date]
    expiry_date: Mapped[date | None]

    lab_tests: Mapped[list[LabTest]] = relationship(
        back_populates="norm_document",
        lazy="raise_on_sql",
    )
    items: Mapped[list[Item]] = relationship(
        back_populates="norm_document",
        lazy="raise_on_sql",
    )


class LabTest(BaseModel):
    __tablename__ = "lab_tests"
    __table_args__ = (
        UniqueConstraint(
            "norm_document_id",
            "name",
            name="uq_lab_tests_norm_document_id_name",
        ),
    )

    name: Mapped[str] = mapped_column(String(100))
    method: Mapped[str] = mapped_column(String(255))
    lab_type: Mapped[LabType] = mapped_column(
        SQLAlchemyEnum(LabType, name="lab_type"),
    )

    norm_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "norm_documents.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    norm_document: Mapped[NormDocument] = relationship(
        back_populates="lab_tests",
        lazy="raise_on_sql",
    )
