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

## AI-DLC Progress

- Inception / Elaborate: complete for MVP baseline
- Construction / Execute: U12 image upload storage adapter complete; U13 mobile photo picker upload integration is next
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

The next recommended construction unit is mobile photo picker upload integration:

- add a mobile image picker dependency and permission flow
- upload selected image bytes to the ticket `uploadUrl`
- continue into the existing analysis review screen
