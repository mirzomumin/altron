# Altron

A FastAPI service with cookie-based session authentication and a role/permission
model, built on async SQLAlchemy + PostgreSQL.

- **Runtime:** Python 3.14, FastAPI, Uvicorn
- **Database:** PostgreSQL 18 via SQLAlchemy 2 (async, `asyncpg`), migrations with Alembic
- **Auth:** Argon2 password hashing (`pwdlib`), opaque session ids stored as SHA-256 hashes
- **Tooling:** `uv` for dependency management, `pytest` + `factory_boy` for tests, `ruff` via pre-commit

## Requirements

- [uv](https://docs.astral.sh/uv/) (installs and pins Python 3.14 itself)
- Docker + Docker Compose (for the local PostgreSQL instance), or a PostgreSQL server you already run

## Getting started

### 1. Install dependencies

```bash
uv sync
```

This creates `.venv/` from `uv.lock` and installs both runtime and dev dependency groups.

### 2. Create the `.env` file

`.env` is git-ignored, so create it in the project root. These values match the
Docker Compose setup below:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/altron_db
DB_USER=postgres
DB_PASS=postgres
DB_NAME=altron_db

SESSION_COOKIE_NAME=session_id
SESSION_EXPIRE_SECONDS=604800

COOKIE_SECURE=false
COOKIE_HTTP_ONLY=true
COOKIE_SAME_SITE=lax

REDIS_URL=redis://localhost:6379/0
```

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | yes | — | Async SQLAlchemy DSN (`postgresql+asyncpg://…`) |
| `DB_USER`, `DB_PASS`, `DB_NAME` | for Compose | — | Credentials the `postgres` container is created with |
| `SESSION_COOKIE_NAME` | no | `session_id` | Name of the session cookie |
| `SESSION_EXPIRE_SECONDS` | no | `604800` (7 days) | Session lifetime |
| `COOKIE_SECURE` | no | `true` | Set to `false` for local HTTP development |
| `COOKIE_HTTP_ONLY` | no | `true` | `HttpOnly` flag on the session cookie |
| `COOKIE_SAME_SITE` | no | `lax` | `SameSite` policy |
| `REDIS_URL` | no | `None` | Reserved; not used by the current code |

Settings are loaded by `src/core/config.py` (pydantic-settings); unknown keys are ignored.

### 3. Start PostgreSQL

```bash
docker compose up -d
```

Compose reads `DB_USER` / `DB_PASS` / `DB_NAME` from `.env` and exposes the
database on `localhost:5432` with a `postgres_data` volume.

### 4. Apply migrations

```bash
uv run alembic upgrade head
```

Alembic takes its URL from `settings.DATABASE_URL` (see `alembic/env.py`), so the
placeholder in `alembic.ini` is never used.

To create a new migration after changing the models:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

### 5. Run the API

```bash
make web
```

or directly:

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- API root: <http://localhost:8000/api/v1>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Endpoints

All routes are mounted under `/api/v1`.

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/users` | Create a user; the generated username and password are returned once |
| `GET` | `/api/v1/users` | List users |
| `GET` | `/api/v1/users/{id}` | User detail, including roles and their permissions |
| `POST` | `/api/v1/users/login` | Log in and receive the session cookie |

Usernames are derived from the name fields (`first-last[-patronymic]`, normalized
to lowercase ASCII) and the initial password is randomly generated — see
`src/core/security.py`.

## Tests

The test suite needs a reachable PostgreSQL server. `tests/conftest.py` takes
`DATABASE_URL`, swaps the database name for `<db>_test`, creates it if missing and
builds the schema from the models (no migrations). Set `TEST_DATABASE_URL` to
point somewhere else instead.

```bash
make test          # uv run pytest
```

Each test runs inside an outer transaction that is rolled back afterwards, so the
test database stays clean between tests.

> `make test-cov` also exists but requires `pytest-cov`, which is not in the
> dependency groups yet — add it with `uv add --dev pytest-cov` before using it.

## Linting and formatting

```bash
uv run pre-commit install      # once, to enable the git hook
uv run pre-commit run --all-files
```

Ruff handles linting (with import sorting) and formatting; `alembic/` is excluded.

## CI

`.github/workflows/ci.yml` runs on pull requests targeting `main`:

- **Lint** — `uv sync --locked`, then `pre-commit run --all-files`
- **Test** — spins up a `postgres:18-alpine` service and runs `uv run pytest`

## Project structure

```
.
├── alembic/                     # Migration environment
│   ├── env.py                   # Reads DATABASE_URL from src.core.config
│   └── versions/                # Migration scripts
├── alembic.ini
├── docker-compose.yaml          # Local PostgreSQL 18 service
├── Makefile                     # web / test / test-cov shortcuts
├── pyproject.toml               # Dependencies and pytest configuration
├── uv.lock
├── src/
│   ├── main.py                  # FastAPI app; mounts the /api router
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings, .env)
│   │   ├── permissions.py       # Permission code enum
│   │   └── security.py          # Password/session hashing, username generation
│   ├── db/
│   │   ├── base.py              # Declarative Base + BaseModel (uuid7 id, timestamps)
│   │   └── session.py           # Async engine, sessionmaker, SessionDep
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py              # User
│   │   ├── role.py              # Role + user_roles / role_permissions tables
│   │   ├── permission.py        # Permission
│   │   └── session.py           # UserSession
│   ├── repositories/            # Data access (plain SQLAlchemy statements)
│   │   ├── user.py
│   │   └── session.py
│   ├── schemas/                 # Pydantic request/response models
│   │   └── user.py
│   ├── services/                # Business logic, HTTP error mapping
│   │   ├── user.py
│   │   └── session.py
│   └── router/
│       ├── __init__.py          # /api prefix
│       └── v1/
│           ├── __init__.py      # /v1 prefix
│           └── users.py         # /users endpoints
└── tests/
    ├── conftest.py              # Test DB, transactional session, HTTP client fixtures
    ├── factories.py             # factory_boy factories for User/Role/Permission
    ├── api/v1/                  # Endpoint tests
    └── unit/                    # Unit tests (security helpers)
```

### Layering

Requests flow `router → service → repository → model`:

- **router** — HTTP concerns only (path/query parsing, cookies, response models)
- **service** — orchestration, validation and `HTTPException` mapping, transaction commits
- **repository** — SQLAlchemy statements, no HTTP awareness
- **model** — table definitions and relationships

Relationships are declared `lazy="raise_on_sql"`, so anything a response needs
must be eager-loaded explicitly in the repository (e.g. `selectinload(User.roles)`).
