# Fitlog Mobile

React Native Expo app foundation for Fitlog.

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

