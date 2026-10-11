from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Table,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.db.base import BaseModel

if TYPE_CHECKING:
    from src.models import Customer, Item, User


submissions = Table(
    "submissions",
    BaseModel.metadata,
    Column(
        "user_id",
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "application_id",
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "is_approved",
        Boolean,
        default=False,
    ),
    Column(
        "approved_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    Index("ix_submissions_application_id", "application_id"),
)


class Application(BaseModel):
    __tablename__ = "applications"

    cid: Mapped[int]  # id из органа сертификации
    number: Mapped[str] = mapped_column(String(20))  # номер заявки
    customer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "customers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )  # компания заявитель
    qty: Mapped[int] = mapped_column(
        SmallInteger()
    )  # количество предметов (препаратов)
    received_date: Mapped[date]  # дата поступления заявки (ТРИС)
    sampling_date: Mapped[date | None]

    customer: Mapped[Customer] = relationship(
        back_populates="applications",
        lazy="raise_on_sql",
    )

    submitters: Mapped[list[User]] = relationship(
        secondary="submissions",
        back_populates="applications",
        lazy="raise_on_sql",
    )

    items: Mapped[list[Item]] = relationship(
        back_populates="application",
        lazy="raise_on_sql",
    )
