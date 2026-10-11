from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import BaseModel

if TYPE_CHECKING:
    from src.models import Application, Customer, Role, UserSession


class UserPosition(str, Enum):
    HEAD = "head"
    DEPUTY_HEAD = "deputy_head"
    SPECIALIST = "specialist"
    INDEPENDENT_EXPERT = "independent_exprt"
    MANAGER = "manager"
    CUSTOMER = "customer"


class User(BaseModel):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    patronymic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )

    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    position: Mapped[UserPosition] = mapped_column(
        SQLAlchemyEnum(UserPosition, name="user_position"),
        nullable=False,
        default=UserPosition.SPECIALIST,
    )

    customer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "customers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )  # компания заявитель

    roles: Mapped[list[Role]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="raise_on_sql",
    )

    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise_on_sql",
    )

    customer: Mapped[Customer] = relationship(
        back_populates="users",
        lazy="raise_on_sql",
    )

    applications: Mapped[list[Application]] = relationship(
        secondary="submissions",
        back_populates="submitters",
        lazy="raise_on_sql",
    )

    @property
    def permission_codes(self) -> set[str]:
        return {
            permission.code for role in self.roles for permission in role.permissions
        }
