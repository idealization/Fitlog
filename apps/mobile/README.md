# Fitlog Mobile

React Native Expo app foundation for Fitlog.

The closet screen now supports selecting a real image from the gallery or capturing one with the camera, previewing its metadata, uploading the image bytes, running the analysis worker, editing the generated closet item draft, and saving it to the closet. Camera permission denial leaves the gallery flow available. Low-quality results explain the detected issue and offer retake, alternate photo, or explicit save-override actions.

## Setup

This environment currently has the Codex-bundled `node` binary but no `npm`, `pnpm`, `yarn`, or `corepack`. Once a package manager is available:

```bash
cd apps/mobile
npm install
npm run start
```

Configure the backend URL:

```bash
cp .env.example .env
```

For local iOS simulator networking, use your Mac LAN IP or Expo tunnel if `127.0.0.1` does not reach the FastAPI server.
