import hashlib
import re
import secrets
import string

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def generate_password(length: int = 16) -> str:
    if length < 8:
        raise ValueError("Password length must be at least 8")

    characters = string.ascii_letters + string.digits + string.punctuation

    return "".join(secrets.choice(characters) for _ in range(length))


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)


def hash_session_id(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def generate_username(
    first_name: str,
    last_name: str,
    patronymic: str,
) -> str:
    def normalize(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]", "", value)
        return value

    first_name = normalize(first_name)
    last_name = normalize(last_name)
    patronymic = normalize(patronymic)

    # Preferred format
    username = f"{first_name}-{last_name}"
    if patronymic:
        username = f"{username}-{patronymic}"

    return username
