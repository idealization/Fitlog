# Fitlog

AI wardrobe and outfit recommendation service.

## Current Status

This repository currently contains:

- Product requirements in `requirements/service_requirements.md`
- AI-DLC elaboration outputs in `requirements/ai_dlc`
- A P0 construction unit: the recommendation domain core under `services/api`
- U2 API foundation: FastAPI app shell, health route, recommendation routes, and API schemas
- U3 Closet CRUD: in-memory closet item repository and CRUD API

## AI-DLC Progress

- Inception / Elaborate: complete for MVP baseline
- Construction / Execute: U3 Closet CRUD complete; U4 image analysis job contract is next
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

## Local Verification

Run the backend domain tests:

```bash
python3 -m unittest discover services/api/tests
```

## Next Unit

The next recommended construction unit after U3 is image analysis job contract:

- upload URL contract
- analysis job state model
- worker-facing event contract
- placeholder route tests
