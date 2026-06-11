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
- U6 Persisted recommendation API: recommendation history, saved/worn status, feedback, and wear logs
- U9 Morning notification scheduler: notification settings, due-run scheduler, weather fallback, and push placeholder
- U7 Mobile app foundation: Expo app shell, API client, closet, recommendation, and notification settings screens
- U8 Recommendation UI hardening: mobile item creation, upload job entry, candidate switching, feedback, and action states
- U10 Image analysis worker stub: queued job processing, placeholder closet item draft, and illustration storage contract
- U11 Mobile image analysis review flow: analysis worker call, editable closet item draft, and save-to-closet handoff
- U12 Image upload storage adapter: local raw upload endpoint, byte/checksum validation, and file-backed storage root
- U13 Mobile photo picker upload integration: image selection, preview, raw upload, and analysis review handoff
- U14 Camera capture flow: camera permission, clothing photo capture, preview, and shared analysis handoff
- U15 Upload readiness enforcement: persisted completion metadata and missing-object analysis rejection
- U16 Image quality retake guidance: quality issue codes, user review status, retake actions, and explicit save override
- U17 Image analysis provider adapter: stored image byte delivery, provider interface, and environment-based selection

## AI-DLC Progress

- Inception / Elaborate: complete for MVP baseline
- Construction / Execute: U17 image analysis provider adapter complete; U18 real vision provider integration is next
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

Change the local upload storage root if needed:

```bash
FITLOG_UPLOAD_STORAGE_ROOT=.fitlog/storage uvicorn app.main:app --app-dir services/api --reload
```

Select the local image analysis provider explicitly if needed:

```bash
FITLOG_IMAGE_ANALYSIS_PROVIDER=deterministic uvicorn app.main:app --app-dir services/api --reload
```

## Mobile Setup

The mobile app lives in `apps/mobile`. This Codex environment has `node` but no `npm`, `pnpm`, `yarn`, or `corepack`; install dependencies once a package manager is available.

```bash
cd apps/mobile
npm install
npm run start
```

## Local Verification

Run the backend domain tests:

```bash
python3 -m unittest discover services/api/tests
```

## Next Unit

The next recommended construction unit is real vision provider integration:

- connect one real vision model behind the U17 provider contract
- validate and normalize provider responses into the existing analysis schema
- add timeout, retry, credential, and provider failure handling

## When You Can Try It

- Now: run the backend and inspect the complete API flow at `http://127.0.0.1:8000/docs`. Analysis uses deterministic demo data.
- After mobile dependencies are installed: run the Expo app against the local API and try camera/gallery registration on a simulator or device.
- After U18: the registration flow can analyze actual image pixels, which is the first meaningful photo-analysis MVP milestone.
- Public beta still needs authentication, cloud storage, live weather, push delivery, deployment, and privacy hardening.
