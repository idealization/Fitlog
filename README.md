# Fitlog

AI wardrobe and outfit recommendation service.

## Current Status

This repository currently contains:

- Product requirements in `requirements/service_requirements.md`
- AI-DLC elaboration outputs in `requirements/ai_dlc`
- A P0 construction unit: the recommendation domain core under `services/api`
- U2 API foundation: FastAPI app shell, health route, recommendation routes, and API schemas
- U3 Closet CRUD: in-memory closet item repository and CRUD API
- U4 Image analysis job contract: upload ticket, analysis job creation, job status, and worker event payload
- U5 Persistence foundation: SQLAlchemy models, SQLite repository backend, and Alembic initial migration

## AI-DLC Progress

- Inception / Elaborate: complete for MVP baseline
- Construction / Execute: U5 persistence foundation complete; U6 persisted recommendation API is next
- Delivery / Check: unit and API tests added
- Operations: not started

## Backend Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r services/api/requirements-dev.txt
```

Run the API locally:

```bash
uvicorn app.main:app --app-dir services/api --reload
```

Run with SQLite persistence:

```bash
FITLOG_REPOSITORY_BACKEND=sqlite FITLOG_DATABASE_URL=sqlite:///./fitlog.db uvicorn app.main:app --app-dir services/api --reload
```

## Local Verification

Run the backend domain tests:

```bash
python3 -m unittest discover services/api/tests
```

## Next Unit

The next recommended construction unit is persisted recommendation API:

- recommendation request history
- persisted outfit candidates
- feedback persistence
- recommendation endpoints backed by saved recommendations
