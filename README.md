# Search Ads ML Automation Demo

ML-powered search advertising automation — bid optimization, keyword intelligence, and budget allocation.

**Repository:** [github.com/anushkamathur14-cloud/marketingsearch](https://github.com/anushkamathur14-cloud/marketingsearch)

## What it does

| Module | Model | Input | Output |
|--------|-------|-------|--------|
| **Bid Optimizer** | Gradient Boosting Regressor + Random Forest | Impressions, CTR, conversions, quality score, competition | Optimal CPC bid + action (increase/decrease/hold) |
| **Keyword Intelligence** | Random Forest Classifier | Keyword & search term performance | Scale, pause, add negative, or promote to keyword |
| **Budget Allocator** | Gradient Boosting Regressor | Campaign ROAS, CPA, impression share, lost IS | Recommended daily budget per campaign |

Data is **synthetic** (simulated Google Ads-style metrics for a running-shoes retailer) so the demo runs without API credentials.

## Quick start

### One-command setup (macOS / Linux)

```bash
git clone https://github.com/anushkamathur14-cloud/marketingsearch.git
cd marketingsearch
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/start.sh
```

Open **http://localhost:5173**

### Manual setup

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Models train automatically on first startup if they don't exist yet.

**Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Model status and training metrics |
| GET | `/api/overview` | Account summary stats |
| GET | `/api/recommendations/bids?limit=20&action=increase` | Bid recommendations |
| POST | `/api/recommendations/bids/predict` | Predict bid for custom input |
| GET | `/api/recommendations/keywords?limit=20&action=scale` | Keyword/search term actions |
| GET | `/api/recommendations/budgets` | Budget allocation by campaign |
| POST | `/api/recommendations/budgets/optimize` | `{ "total_budget": 1500 }` |

Interactive API docs: **http://localhost:8000/docs**

## Deploy on Railway (full stack)

Deploy both services from this repo. Full step-by-step guide: **[RAILWAY.md](./RAILWAY.md)**

### Quick summary

1. Create a Railway project from this repo
2. **Service `api`** — root directory `backend`, generate a public domain
3. **Service `web`** — root directory `frontend`, add variable:
   ```
   VITE_API_URL=https://${{api.RAILWAY_PUBLIC_DOMAIN}}
   ```
4. Generate a public domain for `web` and open it

The backend trains models during the build phase (~30s). The frontend rebuilds whenever `VITE_API_URL` changes.

### Local dev vs production

| Environment | API routing |
|-------------|-------------|
| Local (`npm run dev`) | Vite proxy → `localhost:8000` |
| Railway | `VITE_API_URL` → `api` service domain |

## Architecture

```
Synthetic Data  →  scikit-learn Models  →  FastAPI  →  React Dashboard
(generate)         (train + predict)        (REST)      (recommendations)
```

## Project structure

```
backend/
  railway.toml                 # Railway deploy config
  nixpacks.toml
  requirements.txt
  data/generate_synthetic.py   # Simulated campaign data
  models/
    bid_optimizer.py           # Bid recommendation ML
    keyword_recommender.py     # Keyword/search term ML
    budget_allocator.py        # Budget allocation ML
  train_models.py              # Train & save all models
  main.py                      # FastAPI server (auto-trains on first run)
frontend/
  railway.toml                 # Railway deploy config
  nixpacks.toml
  src/App.jsx                  # Dashboard UI
scripts/
  setup.sh                     # Install deps + train models
  start.sh                     # Run backend + frontend together
```

## Next steps for production

- Connect to [Google Ads API](https://developers.google.com/google-ads/api/docs/start) for live data
- Replace synthetic labels with historical bid change outcomes
- Add A/B testing framework to validate recommendations
- Deploy models with MLflow or similar for versioning
- Add automated rules engine to apply recommendations with guardrails
