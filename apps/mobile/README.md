# Fitlog Mobile

React Native Expo app foundation for Fitlog.

The closet screen supports gallery selection and camera capture, normalizes unsupported inputs such as HEIC to JPEG, uploads the image, runs analysis, and saves an editable draft. Camera permission denial leaves the gallery flow available. Low-quality results explain the detected issue and offer retake, alternate photo, or explicit save-override actions.

## Setup

```bash
cd apps/mobile
npm install
npm run typecheck
npm run start
```

The dependency graph is pinned in `package-lock.json`. Expo SDK compatibility and both iOS and Android Metro exports were verified for U19.

Configure the backend URL:

```bash
cp .env.example .env
```

For local iOS simulator networking, use your Mac LAN IP or Expo tunnel if `127.0.0.1` does not reach the FastAPI server.
