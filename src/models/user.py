from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import BaseModel

if TYPE_CHECKING:
    from src.models import Role, UserSession


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

    @property
    def permission_codes(self) -> set[str]:
        return {
            permission.code for role in self.roles for permission in role.permissions
        }
