# Fitlog API Service

This folder starts the backend side of the service.

The current implementation contains:

- recommendation domain core
- FastAPI app foundation
- health endpoint
- closet item CRUD endpoints
- upload ticket and image analysis job endpoints
- local image upload storage endpoint
- image analysis worker and provider adapter endpoint
- recommendation endpoints that call the domain core
- persisted recommendation history, feedback, and wear logs
- notification settings and morning recommendation scheduler endpoints
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

To write uploaded image bytes somewhere other than `.fitlog/storage`:

```bash
FITLOG_UPLOAD_STORAGE_ROOT=/tmp/fitlog-uploads uvicorn app.main:app --app-dir services/api --reload
```

The local provider is selected by default. Unsupported values fail during app startup:

```bash
FITLOG_IMAGE_ANALYSIS_PROVIDER=deterministic uvicorn app.main:app --app-dir services/api --reload
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
- Local upload storage adapter and raw `PUT /closet-items/uploads/{uploadId}/object` completion endpoint
- Image analysis provider contract with stored binary input and deterministic local implementation
- SQLAlchemy models and SQLite-backed repositories
- Alembic initial migration
- Recommendation route fallback to stored closet items
- Persisted recommendation retrieval, save, wear, and feedback routes
- Notification settings, morning recommendation due-run, weather fallback, and push placeholder
- Recommendation request/response schemas

## Not Implemented Yet

- authentication
- cloud object storage adapter
- real vision model and illustration provider integration
- APNs/FCM push provider integration
