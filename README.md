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
- U18 Real vision provider integration: OpenAI vision, strict schema validation, retries, and provider failure handling
- U19 Mobile live vision readiness: HEIC normalization, dependency lockfile, TypeScript checks, and iOS/Android bundles
- U20 Runnable local app acceptance: Expo Web, local CORS, and browser-verified core flows

## AI-DLC Progress

- Inception / Elaborate: complete for MVP baseline
- Construction / Execute: U20 runnable local app acceptance complete; U21 device and live provider acceptance is next
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

Run with real OpenAI vision analysis:

```bash
export FITLOG_IMAGE_ANALYSIS_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
export FITLOG_OPENAI_VISION_MODEL=gpt-5.4-mini
uvicorn app.main:app --app-dir services/api --reload
```

## Mobile Setup

The mobile app lives in `apps/mobile`. Dependencies are pinned in `package-lock.json`.

```bash
cd apps/mobile
npm install
npm run typecheck
npm run start
```

Run the browser app against the local API:

```bash
cd apps/mobile
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run web -- --port 8081
```

Open `http://127.0.0.1:8081`.

## Local Verification

Run the backend domain tests:

```bash
python3 -m unittest discover services/api/tests
```

## Next Unit

U21 is device and live provider acceptance:

- run the camera flow on an iOS or Android device
- execute one real OpenAI analysis with a configured API key
- verify capture, normalization, upload, review, and closet save as one acceptance flow

## When You Can Try It

- Now: run the backend and inspect the complete API flow at `http://127.0.0.1:8000/docs`. Deterministic mode works without credentials.
- Now with an API key: select the `openai` provider to analyze actual JPEG, PNG, WebP, or GIF image pixels.
- Now: use the running Fitlog web MVP at `http://127.0.0.1:8081`; recommendation, closet registration, feedback, and notification settings are connected to the local API.
- Now: mobile dependencies install cleanly, TypeScript passes, and iOS, Android, and web bundles build.
- After U21: the camera-to-closet path becomes the first fully verified hands-on mobile milestone with a live provider request.
- Public beta still needs authentication, cloud storage, live weather, push delivery, deployment, and privacy hardening.
