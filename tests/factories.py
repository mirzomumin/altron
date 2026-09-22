import factory
from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory

from src.core.security import generate_username, hash_password
from src.models import Permission, Role, User

DEFAULT_PASSWORD = "s3cret-password"


class BaseFactory(AsyncSQLAlchemyFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"


class PermissionFactory(BaseFactory):
    class Meta:
        model = Permission

    code = factory.Sequence(lambda n: f"resource:action-{n}")
    description = factory.LazyAttribute(lambda obj: f"Can {obj.code}")


class RoleFactory(BaseFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"role-{n}")
    description = "Administrator"
    is_default = False


class UserFactory(BaseFactory):
    class Meta:
        model = User

    class Params:
        # Transient: never reaches the model, only feeds `password_hash`.
        password = DEFAULT_PASSWORD

    first_name = "John"
    last_name = factory.Sequence(lambda n: f"Doe{n}")
    patronymic = ""
    username = factory.LazyAttribute(
        lambda obj: generate_username(obj.first_name, obj.last_name, obj.patronymic)
    )
    password_hash = factory.LazyAttribute(lambda obj: hash_password(obj.password))
    is_active = True
