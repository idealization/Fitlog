# Fitlog API Service

This folder starts the backend side of the service.

The current implementation contains:

- recommendation domain core
- FastAPI app foundation
- health endpoint
- closet item CRUD endpoints
- upload ticket and image analysis job endpoints
- recommendation endpoints that call the domain core
- persisted recommendation history, feedback, and wear logs
- demo recommendation data
- SQLite-backed persistence option

## Setup

```bash
python3 -m venv ../../.venv
. ../../.venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Run

From the repository root:

```bash
uvicorn app.main:app --app-dir services/api --reload
```

To persist data locally:

```bash
FITLOG_REPOSITORY_BACKEND=sqlite FITLOG_DATABASE_URL=sqlite:///./fitlog.db uvicorn app.main:app --app-dir services/api --reload
```

## Test

```bash
python -m unittest discover services/api/tests
```

## Implemented

- Closet item domain model
- Weather snapshot model
- Style request model
- Outfit candidate generation
- Weather, style, trend, fixed item, and exclusion scoring
- FastAPI app shell
- Closet item CRUD routes with in-memory repository
- Image analysis upload/job routes with in-memory repository
- SQLAlchemy models and SQLite-backed repositories
- Alembic initial migration
- Recommendation route fallback to stored closet items
- Persisted recommendation retrieval, save, wear, and feedback routes
- Recommendation request/response schemas

## Not Implemented Yet

- authentication
- image upload and AI job processing
- push notification scheduler
