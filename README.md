# Altron

A FastAPI service for tracking certification applications — customers, their
applications and items, and the normative documents (with lab tests) items are
checked against. It has cookie-based session authentication and a role/permission
model, and is built on async SQLAlchemy + PostgreSQL.

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
docker compose up -d      # or: make db
```

Compose reads `DB_USER` / `DB_PASS` / `DB_NAME` from `.env` and exposes the
database on `localhost:5432` with a `postgres_data` volume.

### 4. Apply migrations

```bash
uv run alembic upgrade head
```

Alembic takes its URL from `settings.DATABASE_URL` (see `alembic/env.py`), so the
placeholder in `alembic.ini` is never used.

### 5. Seed permissions

```bash
uv run python -m scripts.seed_permissions
```

Inserts every code from the `Permission` enum in `src/core/permissions.py` that is
not in the `permissions` table yet (safe to re-run). Run it again whenever a new
permission code is added.

To create a new migration after changing the models:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

### 6. Run the API

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

### Users

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/users` | Create a user for a customer; the generated username and password are returned once |
| `GET` | `/api/v1/users` | List users; filter with `?customer_id=` and/or `?position=` |
| `GET` | `/api/v1/users/{id}` | User detail, including the customer, roles and their permissions |
| `POST` | `/api/v1/users/login` | Log in and receive the session cookie |

Usernames are derived from the name fields (`first-last[-patronymic]`, normalized
to lowercase ASCII) and the initial password is randomly generated — see
`src/core/security.py`. Every user belongs to a customer (`customer_id`) and has a
`position`: `head`, `deputy_head`, `specialist` (default), `independent_exprt`,
`manager` or `customer`.

### Roles and permissions

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/roles` | Create a role with a list of permission ids |
| `GET` | `/api/v1/roles` | List roles with their permissions |
| `PUT` | `/api/v1/roles/{id}` | Update a role's name, description and permissions |
| `GET` | `/api/v1/permissions` | List permissions (populated by the seed script) |

Permission codes follow `<resource>:<action>` (e.g. `application:create`) for the
`user`, `role`, `customer` and `application` resources.

### Customers

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/customers` | Create a customer (names are unique; duplicates return `409`) |
| `GET` | `/api/v1/customers` | List customers; filter by name with `?name=` |
| `GET` | `/api/v1/customers/{id}` | Customer detail |
| `PUT` | `/api/v1/customers/{id}` | Rename a customer |
| `DELETE` | `/api/v1/customers/{id}` | Delete a customer — cascades to its users and applications |

### Applications

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/applications` | Create an application with its items and submitters |
| `GET` | `/api/v1/applications` | List applications; filter with `?customer_id=` |
| `GET` | `/api/v1/applications/{id}` | Application detail, including customer, submitters and items |
| `PUT` | `/api/v1/applications/{id}` | Update application fields and its submitter list |
| `DELETE` | `/api/v1/applications/{id}` | Delete an application and its items |

On create, `items` must contain exactly `qty` entries (one per preparation, each
with a `name`). Submitters are given as `[{"id": "<user id>"}]`; unknown user ids
are silently skipped. `PUT` replaces the submitter set but does not touch items.

### Norm documents

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/norm-documents` | Create a normative document together with its lab tests |

`expiry_date` (optional) must not be earlier than `approved_date`, and lab test
names must be unique within a document. Each lab test has a `name`, a `method`
and a `lab_type` of `own` or `subcontracted`.

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
├── Makefile                     # web / test / test-cov / db shortcuts
├── pyproject.toml               # Dependencies and pytest configuration
├── uv.lock
├── scripts/
│   └── seed_permissions.py      # Inserts missing Permission rows
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
│   │   ├── user.py              # User + UserPosition enum
│   │   ├── role.py              # Role + user_roles / role_permissions tables
│   │   ├── permission.py        # Permission
│   │   ├── session.py           # UserSession
│   │   ├── customer.py          # Customer
│   │   ├── application.py       # Application + submissions (user ↔ application) table
│   │   ├── item.py              # Item (application line) + SeedMethod enum
│   │   └── norm_document.py     # NormDocument, LabTest + LabType enum
│   ├── repositories/            # Data access (plain SQLAlchemy statements), one module per model
│   ├── schemas/                 # Pydantic request/response models, one module per resource
│   ├── services/                # Business logic, HTTP error mapping, one module per resource
│   └── router/
│       ├── __init__.py          # /api prefix
│       └── v1/
│           ├── __init__.py      # /v1 prefix, includes the routers below
│           ├── users.py         # /users
│           ├── roles.py         # /roles
│           ├── permissions.py   # /permissions
│           ├── customers.py     # /customers
│           ├── applications.py  # /applications
│           └── norm_documents.py  # /norm-documents
└── tests/
    ├── conftest.py              # Test DB, transactional session, HTTP client fixtures
    ├── factories.py             # factory_boy factories for the models
    ├── api/v1/                  # Endpoint tests
    └── unit/                    # Unit tests (security helpers)
```

### Data model

- A **customer** has many **users** and **applications**; deleting a customer cascades to both.
- An **application** has many **items** and many submitting **users** (via the `submissions` table, which also stores `is_approved` / `approved_at`).
- An **item** optionally references a **norm document** (`SET NULL` on delete) and carries certification/monitoring fields (producer, TN VED code, series, seed method, certificate number, …).
- A **norm document** has many **lab tests**; test names are unique per document.
- **Users** get **roles**, and roles get **permissions**, through `user_roles` / `role_permissions`.

### Layering

Requests flow `router → service → repository → model`:

- **router** — HTTP concerns only (path/query parsing, cookies, response models)
- **service** — orchestration, validation and `HTTPException` mapping, transaction commits
- **repository** — SQLAlchemy statements, no HTTP awareness
- **model** — table definitions and relationships

Relationships are declared `lazy="raise_on_sql"`, so anything a response needs
must be eager-loaded explicitly in the repository (e.g. `selectinload(User.roles)`).
