import pytest

from src.core.security import (
    generate_password,
    generate_session_id,
    generate_username,
    hash_password,
    hash_session_id,
    verify_password,
)


def test_generate_password_respects_length() -> None:
    assert len(generate_password()) == 16
    assert len(generate_password(32)) == 32


def test_generate_password_rejects_short_length() -> None:
    with pytest.raises(ValueError, match="at least 8"):
        generate_password(7)


def test_generate_password_is_random() -> None:
    assert generate_password() != generate_password()


def test_hash_password_is_salted_and_verifiable() -> None:
    password = "s3cret-password"
    first = hash_password(password)
    second = hash_password(password)

    assert first != password
    assert first != second
    assert verify_password(password, first)
    assert not verify_password("other-password", first)


def test_session_id_hash_is_deterministic_sha256() -> None:
    session_id = generate_session_id()

    assert hash_session_id(session_id) == hash_session_id(session_id)
    assert len(hash_session_id(session_id)) == 64
    assert hash_session_id(session_id) != hash_session_id(generate_session_id())


@pytest.mark.parametrize(
    ("first_name", "last_name", "patronymic", "expected"),
    [
        ("John", "Doe", "", "john-doe"),
        ("John", "Doe", "Hermanson", "john-doe-hermanson"),
        ("  John  ", " Doe ", "  ", "john-doe"),
        ("JOHN", "DOE", "", "john-doe"),
        ("Ján", "O'Neil", "", "jn-oneil"),
        ("John2", "Doe3", "", "john2-doe3"),
    ],
)
def test_generate_username(
    first_name: str,
    last_name: str,
    patronymic: str,
    expected: str,
) -> None:
    assert generate_username(first_name, last_name, patronymic) == expected
