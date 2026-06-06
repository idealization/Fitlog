# Fitlog API Service

This folder starts the backend side of the service.

The current implementation contains:

- recommendation domain core
- FastAPI app foundation
- health endpoint
- recommendation endpoints that call the domain core
- demo data used until persistence is implemented

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
- Recommendation request/response schemas

## Not Implemented Yet

- database persistence
- authentication
- image upload and AI job processing
- push notification scheduler
