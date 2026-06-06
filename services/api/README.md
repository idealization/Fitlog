# Fitlog API Service

This folder starts the backend side of the service. The current implementation is intentionally small and dependency-free: it contains the recommendation domain core that can later be wrapped by FastAPI.

## Test

```bash
python3 -m unittest discover services/api/tests
```

## Implemented

- Closet item domain model
- Weather snapshot model
- Style request model
- Outfit candidate generation
- Weather, style, trend, fixed item, and exclusion scoring

## Not Implemented Yet

- FastAPI routes
- database persistence
- authentication
- image upload and AI job processing
- push notification scheduler

