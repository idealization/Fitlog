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

Open the browser build directly:

```bash
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run web -- --port 8081
```

Then visit `http://127.0.0.1:8081`. The dependency graph is pinned in `package-lock.json`. Expo SDK 56 compatibility and iOS, Android, and web exports are verified.

For an iPhone or Android device on the same Wi-Fi, stop the existing local servers and run:

```bash
./scripts/start_device_dev.sh
```

Open the printed `exp://` URL with Expo Go. The script binds the API to the local network and injects the matching API URL into the Expo bundle.

Configure the backend URL:

```bash
cp .env.example .env
```

For local iOS simulator networking, use your Mac LAN IP or Expo tunnel if `127.0.0.1` does not reach the FastAPI server.
