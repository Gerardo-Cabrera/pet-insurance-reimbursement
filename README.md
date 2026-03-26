# Pet Insurance Reimbursement

Full stack solution for the pet insurance reimbursement technical test.

## Stack

- Backend: Django 5, Django REST Framework, Simple JWT, drf-spectacular, Celery-ready workflow
- Frontend: Vue 3, Vite, Vue Router, Axios
- Database: SQLite by default locally, PostgreSQL in Docker Compose
- Async simulation: `sync`, `thread`, or `celery` modes

## What is implemented

- Email-based authentication with JWT
- Roles: `CUSTOMER`, `SUPPORT`, `ADMIN`
- Pet CRUD with ownership filtering, protected delete and automatic 1-year coverage window
- Claim creation with invoice upload
- Duplicate invoice prevention using SHA-256 file hash
- Coverage validation for `invoice_date` and `date_of_event`
- Claim workflow:
  - create -> `PROCESSING`
  - automatic validation -> `IN_REVIEW` or `REJECTED`
  - support decision -> `APPROVED` or `REJECTED`
- Responsive Vue frontend for customer and support flows
- Support queue for approval and rejection
- Public health endpoint at `/api/health/`
- Docker Compose healthchecks tuned to reduce unnecessary backend traffic
- PostgreSQL-backed Docker runtime with persistent volume storage
- Swagger docs at `/api/docs/`
- Backend test suite for the critical flow

## PDF coverage checklist

- Business context: implemented with pet registration, invoice upload and support review flow.
- Backend API with Django REST Framework: implemented.
- Simple frontend with Vue: implemented.
- Basic role-based access control: implemented with `CUSTOMER`, `SUPPORT`, `ADMIN`.
- Basic async processing simulation: implemented with `thread` by default, `sync` for tests and optional `celery`.
- Optional OpenAPI / Swagger: implemented at `/api/docs/`.
- User entity: implemented with unique email auth and role field.
- Pet entity: implemented with owner, species, birth date, coverage dates and created timestamp.
- Pet coverage rule: `coverage_end` is derived from `coverage_start + 365 days`.
- Claim entity: implemented with owner, pet, invoice file, invoice date, event date, amount, status and review notes.
- Duplicate invoice prevention via file hash: implemented with SHA-256.
- Required flow:
  - claim is created in `PROCESSING`
  - processor validates coverage
  - valid claim moves to `IN_REVIEW`
  - invalid claim moves to `REJECTED`
  - support can approve or reject
- Proper status transitions: implemented.
- Ownership checks: implemented.
- Basic tests: implemented and passing.
- Simple support UI: implemented.
- Docker and Compose: implemented, now fully parameterized through environment files.

## Assumptions and trade-offs

- Registration creates only `CUSTOMER` users. `SUPPORT` and `ADMIN` users should be created from Django admin or shell.
- `coverage_end` is derived from `coverage_start + 365 days`.
- Coverage is evaluated by the processor after the claim is created. Out-of-coverage claims are automatically moved to `REJECTED`.
- The document mentions `SUBMITTED`, but the required flow starts directly in `PROCESSING`, so the API uses `PROCESSING` as the first active state.
- Pets with claim history cannot be deleted. This avoids accidental loss of reimbursement history.
- SQLite is kept as the simplest local default outside Docker, while Docker Compose uses PostgreSQL for a more realistic runtime.

## Local setup

### Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py createsuperuser
.venv/bin/python backend/manage.py runserver
```

Backend API: `http://127.0.0.1:8000`

Important:

- The project reads plain environment variables from the shell or Docker Compose.
- `backend/.env.example` is a reference template. If you want to use it locally, export those variables before starting Django.
- If no database variables are provided locally, Django falls back to SQLite at `backend/db.sqlite3`.
- Default runtime mode is `thread`, so claims stay briefly in `PROCESSING` before moving to the next status.
- In Docker Compose, `DJANGO_ALLOWED_HOSTS` should include `backend` because the frontend container reaches Django through the internal service hostname.

Example:

```bash
set -a
source backend/.env.example
set +a
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend app: `http://127.0.0.1:5173`

The Vite proxy already points `/api` and `/media` to the Django server.
Inside Docker Compose, that proxy target is overridden with `FRONTEND_PROXY_TARGET=http://backend:8000`.

## Tests

```bash
cd backend
../.venv/bin/pytest
```

Current verification baseline:

- Backend API tests: `19 passed`
- Django checks: `manage.py check` OK
- OpenAPI schema generation: OK
- Frontend build: `npm run build` OK

## API shortcuts

- Health: `GET /api/health/`
- Register: `POST /api/auth/register/`
- Login: `POST /api/token/`
- Refresh token: `POST /api/token/refresh/`
- Me: `GET /api/auth/me/`
- Pets: `GET|POST /api/pets/`, `PUT|DELETE /api/pets/{id}/`
- Claims: `GET|POST /api/claims/`
- Approve claim: `POST /api/claims/{id}/approve/`
- Reject claim: `POST /api/claims/{id}/reject/`
- Swagger: `GET /api/docs/`
- OpenAPI schema: `GET /api/schema/`

## OpenAPI / Swagger

Swagger UI is available at:

- `http://127.0.0.1:8000/api/docs/` when using the backend directly
- `http://127.0.0.1:5173/api/docs/` when using the frontend dev server or Docker Compose proxy

Recommended testing flow in the browser:

1. Call `POST /api/auth/register/` or use an existing user.
2. Call `POST /api/token/` and copy the `access` token.
3. Click `Authorize` in Swagger and paste `Bearer <access_token>`.
4. Test protected endpoints such as pets, claims, and support review actions.

The OpenAPI docs include tags, summaries, descriptions and request examples for auth, pets, claims, review actions and the health endpoint.

## Docker

Create the env files first:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp backend/.env.worker.example backend/.env.worker
```

Then start the stack:

```bash
docker compose up --build
```

This starts:

- Django API on `8000`
- Vue app on `5173`
- PostgreSQL as the main application database
- Redis as an internal service for optional Celery communication

Compose now includes healthchecks for `postgres`, `redis`, `backend`, and `frontend`.
The frontend healthcheck only verifies the Vite app itself, while the backend healthcheck keeps validating `/api/health/`.
This avoids sending redundant health traffic from the frontend to Django.

Quick status check:

```bash
docker compose ps
```

Expected result:

- `postgres` healthy
- `redis` healthy
- `backend` healthy
- `frontend` healthy

Data persistence in Docker:

- business data is stored in PostgreSQL
- PostgreSQL data persists in the named volume `postgres_data`
- local non-Docker development still uses SQLite unless you explicitly provide database env vars

If you want to run a real Celery worker instead of thread-based processing:

```bash
docker compose --profile celery up --build
```

In that mode:

- `backend` can stay in `thread` mode for local simplicity, or you can switch it to `celery` in `backend/.env`
- `worker` consumes tasks from Redis
- `docker-compose.yml` itself stays free of hardcoded secrets and environment values

## Demo users

Use the registration form for a customer account.

For support/admin accounts:

```bash
.venv/bin/python backend/manage.py createsuperuser
```

Then assign the `SUPPORT` role from Django admin if needed.
