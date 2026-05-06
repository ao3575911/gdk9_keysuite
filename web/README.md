# GDk9 KeySuite Web App

Production-minded Next.js playground and developer guide for the GDk9 KeySuite runtime.

The app is intentionally UI-only. It does not reimplement reducer semantics or grammar behavior. When a KeySuite API server is configured, the playground posts token arrays to `POST /v1/process`. Without an API server, it uses labeled demo responses for known sample streams only.

## Install

```bash
cd web
npm install
```

## Run the Python API

From the repository root:

```bash
source .venv/bin/activate
uvicorn keysuite.api:create_app --factory --reload --host 127.0.0.1 --port 8000
```

If API keys are configured with `KEYSUITE_API_KEYS`, also set `KEYSUITE_API_KEY` for the web app.

## Run the Web App

```bash
cd web
cp .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Environment

```bash
KEYSUITE_API_BASE_URL=http://127.0.0.1:8000
KEYSUITE_API_KEY=
```

`KEYSUITE_API_BASE_URL` is read by the Next.js route handler, not by the browser UI. `NEXT_PUBLIC_KEYSUITE_API_BASE_URL` is also accepted for local convenience, but the server-side variable is preferred.

## Verification

```bash
cd web
npm run lint
npm run typecheck
npm run build
```

From the repository root, keep the Python contract checks green:

```bash
pytest -q
keysuite conformance conformance/vectors
keysuite run --tokens "C C . 3 3 SPACE"
```

Expected CLI output:

```text
CC→33
```
