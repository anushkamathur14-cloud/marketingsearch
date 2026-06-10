# Search Ads ML Automation Demo

A demo platform showing how machine learning can automate search advertising decisions — bid optimization, keyword management, and budget allocation.

## What it does

| Module | Model | Input | Output |
|--------|-------|-------|--------|
| **Bid Optimizer** | Gradient Boosting Regressor + Random Forest | Impressions, CTR, conversions, quality score, competition | Optimal CPC bid + action (increase/decrease/hold) |
| **Keyword Intelligence** | Random Forest Classifier | Keyword & search term performance | Scale, pause, add negative, or promote to keyword |
| **Budget Allocator** | Gradient Boosting Regressor | Campaign ROAS, CPA, impression share, lost IS | Recommended daily budget per campaign |

Data is **synthetic** (simulated Google Ads-style metrics for a running-shoes retailer) so the demo runs without API credentials.

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
python train_models.py
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## API endpoints

- `GET /api/health` — model status and training metrics
- `GET /api/overview` — account summary stats
- `GET /api/recommendations/bids?limit=20&action=increase`
- `GET /api/recommendations/keywords?limit=20&action=scale`
- `GET /api/recommendations/budgets`
- `POST /api/recommendations/budgets/optimize` — `{ "total_budget": 1500 }`

## Project structure

```
backend/
  data/generate_synthetic.py   # Simulated campaign data
  models/
    bid_optimizer.py           # Bid recommendation ML
    keyword_recommender.py     # Keyword/search term ML
    budget_allocator.py        # Budget allocation ML
  train_models.py              # Train & save all models
  main.py                      # FastAPI server
frontend/
  src/App.jsx                  # Dashboard UI
```

## Next steps for production

- Connect to Google Ads API / Microsoft Ads API for live data
- Replace synthetic labels with historical bid change outcomes
- Add A/B testing framework to validate recommendations
- Deploy models with MLflow or similar for versioning
- Add automated rules engine to apply recommendations with guardrails
