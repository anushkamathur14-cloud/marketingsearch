# Deploy to Railway (full stack)

Deploy both the **API** and **dashboard** from this monorepo as two Railway services in one project.

Repo: [github.com/anushkamathur14-cloud/marketingsearch](https://github.com/anushkamathur14-cloud/marketingsearch)

## 1. Create the Railway project

1. Go to [railway.app/new](https://railway.app/new)
2. Choose **Deploy from GitHub repo**
3. Select `anushkamathur14-cloud/marketingsearch`

Railway creates one service from the repo root — this deploys the **API** automatically (no root directory change needed for the first service).

> **If you already deployed and got "No start command detected":** open the service → **Settings** → confirm **Root Directory** is empty (repo root), then click **Redeploy**. Or set Root Directory to `backend` and redeploy.

## 2. Deploy the API (backend)

1. Open the first service → **Settings**
2. Set **Service Name** to `api`
3. Set **Root Directory** to `backend` ← **required**
4. Under **Networking**, click **Generate Domain**
5. Redeploy — Railway builds from `backend/Dockerfile` which:
   - Installs Python + pip + dependencies
   - Trains ML models
   - Starts FastAPI on `$PORT`

> **Do not use Nixpacks for this project.** The Dockerfile avoids the `No module named pip` build error.
   - Install Python 3.11 + dependencies
   - Train ML models on synthetic data (`python train_models.py`)
   - Start FastAPI on `$PORT`

Verify: open `https://<api-domain>/api/health` — you should see `"models_trained": true`.

## 3. Add the frontend service

1. In the same Railway project, click **+ New** → **GitHub Repo**
2. Select the same `marketingsearch` repo again
3. Set **Service Name** to `web`
4. Set **Root Directory** to `frontend`
5. Go to **Variables** and add:

   | Variable | Value |
   |----------|-------|
   | `VITE_API_URL` | `https://${{api.RAILWAY_PUBLIC_DOMAIN}}` |

   Railway resolves `${{api.RAILWAY_PUBLIC_DOMAIN}}` to the backend's public domain at **build time**.

6. Under **Networking**, click **Generate Domain** for the frontend
7. Deploy

Open the frontend domain — the dashboard should load with live ML recommendations.

## 4. Service overview

```
┌─────────────────────────────────────────────────────┐
│  Railway Project: marketingsearch                   │
│                                                     │
│  ┌──────────────┐         ┌───────────────────┐    │
│  │  web         │  HTTPS  │  api              │    │
│  │  (frontend)  │ ──────► │  (FastAPI + ML)   │    │
│  │  root:       │         │  root: backend    │    │
│  │  frontend    │         │                   │    │
│  └──────────────┘         └───────────────────┘    │
└─────────────────────────────────────────────────────┘
```

| Service | Root dir | Port | Public URL |
|---------|----------|------|------------|
| `api` | `backend` | `$PORT` (auto) | `/api/health`, `/docs` |
| `web` | `frontend` | `$PORT` (auto) | Dashboard UI |

## 5. Redeploying

- **Backend code changes** → redeploy `api` only
- **Frontend code changes** → redeploy `web` only
- **Backend URL changed** → redeploy `web` (rebuilds with updated `VITE_API_URL`)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Frontend shows "Cannot reach the API" | Check `VITE_API_URL` on `web` service; redeploy frontend |
| Backend 503 on first request | Models still training — wait ~30s or check deploy logs |
| Build fails: `No module named pip` | Set Root Directory to `backend` and redeploy (uses Dockerfile, not Nixpacks) |
| Build fails: "No start command detected" | Set Root Directory to `backend` and redeploy |
| CORS errors | Backend allows all origins — if issues persist, verify `VITE_API_URL` has no trailing slash |

## Local development

Local dev is unchanged — no Railway needed:

```bash
./scripts/setup.sh
./scripts/start.sh
```

Frontend uses the Vite proxy to `localhost:8000` when `VITE_API_URL` is not set.
