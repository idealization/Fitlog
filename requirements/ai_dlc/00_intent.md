# 00. Intent State

## Intent

Build Fitlog, an AI wardrobe app that lets users digitize their own clothes from photos, turn each item into a consistent illustration, and receive outfit recommendations based on weather, style intent, trends, and wardrobe history.

## Source Context

- Primary requirements: `requirements/service_requirements.md`
- AI-DLC elaboration outputs: `requirements/ai_dlc/*.md`

## AI-DLC Interpretation

This project does not currently include an installed AI-DLC plugin or project-specific `.ai-dlc` settings. The workflow is therefore represented in repository files and mapped to the commonly used AI-DLC pattern:

- Inception / Elaborate: clarify intent, scope, domain, success criteria
- Construction / Execute: implement small verifiable units
- Delivery / Check: run tests, document residual risk, prepare next unit
- Operations: deployment, monitoring, feedback loops after app foundation exists

## Current State

- Inception / Elaborate: complete for the MVP baseline
- Construction / Execute: U17 Image analysis provider adapter complete; next unit is U18 Real vision provider integration
- Delivery / Check: active through unit tests, API tests, and quality checklist
- Operations: not started

## Units of Work

```mermaid
flowchart TD
    U0["U0: AI-DLC requirements elaboration"] --> U1["U1: Recommendation domain core"]
    U1 --> U2["U2: API project foundation (complete)"]
    U2 --> U3["U3: Closet item CRUD API (complete)"]
    U2 --> U4["U4: Image analysis job contract (complete)"]
    U3 --> U5["U5: Persistence foundation (complete)"]
    U4 --> U5
    U5 --> U6["U6: Persisted recommendation API (complete)"]
    U6 --> U9["U9: Morning notification scheduler (complete)"]
    U9 --> U7["U7: Mobile app foundation (complete)"]
    U7 --> U8["U8: Recommendation UI hardening (complete)"]
    U8 --> U10["U10: Image analysis worker stub (complete)"]
    U10 --> U11["U11: Mobile image analysis review flow (complete)"]
    U11 --> U12["U12: Image upload storage adapter (complete)"]
    U12 --> U13["U13: Mobile photo picker upload integration (complete)"]
    U13 --> U14["U14: Camera capture flow (complete)"]
    U14 --> U15["U15: Upload readiness enforcement (complete)"]
    U15 --> U16["U16: Image quality retake guidance (complete)"]
    U16 --> U17["U17: Image analysis provider adapter (complete)"]
    U17 --> U18["U18: Real vision provider integration"]
```

## Machine-Checkable Success Criteria

- Recommendation core has deterministic unit tests.
- Recommendation core excludes unavailable closet items.
- Recommendation core respects fixed and excluded item constraints.
- Recommendation core reacts to cold, hot, and rainy weather.
- Recommendation core produces user-facing explanation strings.
- P0 backend and mobile work should be linked back to a backlog item in `06_delivery_backlog.md`.
- API job contracts expose machine-readable status and worker event payloads.
- SQLite persistence preserves closet items and image analysis jobs across app instances.
- Recommendation responses expose stable ids and can be retrieved, saved, marked worn, and given feedback.
- Morning scheduler creates at most one recommendation per local date and queues a placeholder push dispatch.
- Mobile shell can call closet, recommendation, morning run, and notification settings API contracts.
- Mobile recommendation and closet screens expose creation, upload-job entry, feedback, save, and wear flows.
- Image analysis worker can process a queued job into a persisted placeholder closet item draft and illustration contract.
- Mobile closet registration can run image analysis, show an editable draft, and save that draft as a closet item.
- Image upload tickets expose a local PUT upload path that validates content type, byte size, and checksum before analysis.
- Mobile closet registration can select a real image, upload its bytes, and continue into the analysis review flow.
- Mobile closet registration can request camera permission, capture a clothing photo, and reuse the upload and analysis review flow.
- Analysis jobs are created only after upload completion metadata is persisted and the stored image object exists.
- Low-quality analysis results expose machine-readable reasons, require user review, and offer retake or explicit override actions.
- The image worker reads stored image bytes and delegates analysis through an environment-selected provider contract.

## Critical Human Decisions Still Open

- Final app stack: React Native Expo + FastAPI selected for MVP
- Authentication provider
- Image generation provider
- Weather API provider
- Brand name: Fitlog selected
- Visual direction
- MVP launch region
