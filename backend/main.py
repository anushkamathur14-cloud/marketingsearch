"""FastAPI server for search ads ML recommendations demo."""

from __future__ import annotations

import json
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models import bid_optimizer, budget_allocator, keyword_recommender

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "saved_models"

_models_loaded = False
_bid_regressor = None
_bid_classifier = None
_kw_classifier = None
_st_classifier = None
_budget_model = None
_keywords_df: Optional[pd.DataFrame] = None
_search_df: Optional[pd.DataFrame] = None
_campaigns_df: Optional[pd.DataFrame] = None


def _train_if_needed() -> None:
    if (MODEL_DIR / "bid_regressor.joblib").exists():
        return
    print("Models not found — training on synthetic data (first run)...")
    subprocess.run([sys.executable, "train_models.py"], cwd=BASE_DIR, check=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _train_if_needed()
    yield


app = FastAPI(
    title="Search Ads ML Automation",
    description="ML-powered bid, keyword, and budget recommendations for search advertising",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _campaign_summaries() -> list[dict]:
    assert _campaigns_df is not None
    campaigns = (
        _campaigns_df.groupby("campaign", as_index=False)
        .agg(
            {
                "daily_budget": "mean",
                "spend_7d": "mean",
                "conversions_7d": "mean",
                "revenue_7d": "mean",
                "roas": "mean",
                "cpa": "mean",
                "impression_share": "mean",
                "lost_is_budget": "mean",
            }
        )
        .to_dict(orient="records")
    )
    for c in campaigns:
        c["daily_budget"] = round(c["daily_budget"], 2)
        c["spend_7d"] = round(c["spend_7d"], 2)
        c["conversions_7d"] = int(round(c["conversions_7d"]))
        c["revenue_7d"] = round(c["revenue_7d"], 2)
        c["roas"] = round(c["roas"], 2)
        c["cpa"] = round(c["cpa"], 2)
        c["impression_share"] = round(c["impression_share"], 3)
        c["lost_is_budget"] = round(c["lost_is_budget"], 3)
    return campaigns


def _ensure_models() -> None:
    global _models_loaded, _bid_regressor, _bid_classifier
    global _kw_classifier, _st_classifier, _budget_model
    global _keywords_df, _search_df, _campaigns_df

    if _models_loaded:
        return

    if not (MODEL_DIR / "bid_regressor.joblib").exists():
        raise HTTPException(
            status_code=503,
            detail="Models not trained. Run: python train_models.py",
        )

    _bid_regressor, _bid_classifier = bid_optimizer.load_models(MODEL_DIR)
    _kw_classifier, _st_classifier = keyword_recommender.load_models(MODEL_DIR)
    _budget_model = budget_allocator.load_model(MODEL_DIR)
    _keywords_df = pd.read_csv(DATA_DIR / "keywords.csv")
    _search_df = pd.read_csv(DATA_DIR / "search_terms.csv")
    _campaigns_df = pd.read_csv(DATA_DIR / "campaigns.csv")
    _models_loaded = True


class BidInput(BaseModel):
    keyword: str = ""
    campaign: str = ""
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    ctr: float = Field(ge=0, le=1)
    conversions: int = Field(ge=0)
    conversion_rate: float = Field(ge=0, le=1)
    avg_cpc: float = Field(gt=0)
    cost: float = Field(ge=0)
    quality_score: int = Field(ge=1, le=10)
    competition_index: float = Field(ge=0, le=1)
    impression_share: float = Field(ge=0, le=1)


class BudgetPortfolioInput(BaseModel):
    total_budget: Optional[float] = None


@app.get("/")
def root():
    return {"service": "Search Ads ML Automation API", "docs": "/docs", "health": "/api/health"}


@app.get("/api/health")
def health():
    trained = (MODEL_DIR / "bid_regressor.joblib").exists()
    metrics = {}
    metrics_path = MODEL_DIR / "training_metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
    return {"status": "ok", "models_trained": trained, "metrics": metrics}


@app.get("/api/overview")
def overview():
    _ensure_models()
    assert _keywords_df is not None and _campaigns_df is not None

    total_spend = float(_keywords_df["cost"].sum())
    total_conversions = int(_keywords_df["conversions"].sum())
    avg_roas = float(_campaigns_df["roas"].mean())

    return {
        "campaigns": int(_campaigns_df["campaign"].nunique()),
        "keywords": len(_keywords_df),
        "total_spend": round(total_spend, 2),
        "total_conversions": total_conversions,
        "avg_roas": round(avg_roas, 2),
        "campaign_names": sorted(_campaigns_df["campaign"].unique().tolist()),
    }


@app.get("/api/recommendations/bids")
def bid_recommendations(limit: int = 20, action: Optional[str] = None):
    _ensure_models()
    assert _keywords_df is not None and _bid_regressor is not None and _bid_classifier is not None

    recs = []
    for _, row in _keywords_df.iterrows():
        rec = bid_optimizer.recommend(row.to_dict(), _bid_regressor, _bid_classifier)
        if action and rec["action"] != action:
            continue
        recs.append(rec)

    recs.sort(key=lambda r: abs(r["bid_change_pct"]), reverse=True)
    return {"recommendations": recs[:limit], "total": len(recs)}


@app.post("/api/recommendations/bids/predict")
def predict_bid(payload: BidInput):
    _ensure_models()
    assert _bid_regressor is not None and _bid_classifier is not None
    return bid_optimizer.recommend(payload.model_dump(), _bid_regressor, _bid_classifier)


@app.get("/api/recommendations/keywords")
def keyword_recommendations(limit: int = 20, action: Optional[str] = None):
    _ensure_models()
    assert _keywords_df is not None and _search_df is not None
    assert _kw_classifier is not None and _st_classifier is not None

    kw_recs = [
        keyword_recommender.recommend_keyword(row.to_dict(), _kw_classifier)
        for _, row in _keywords_df.iterrows()
    ]
    st_recs = [
        keyword_recommender.recommend_search_term(row.to_dict(), _st_classifier)
        for _, row in _search_df.iterrows()
    ]

    all_recs = kw_recs + st_recs
    actionable = {"scale", "pause", "add_negative", "add_keyword"}

    filtered = [r for r in all_recs if r["action"] in actionable]
    if action:
        filtered = [r for r in filtered if r["action"] == action]

    filtered.sort(key=lambda r: r["confidence"], reverse=True)
    return {"recommendations": filtered[:limit], "total": len(filtered)}


@app.get("/api/recommendations/budgets")
def budget_recommendations():
    _ensure_models()
    assert _budget_model is not None
    return budget_allocator.allocate_portfolio(_campaign_summaries(), _budget_model)


@app.post("/api/recommendations/budgets/optimize")
def optimize_budgets(payload: BudgetPortfolioInput):
    _ensure_models()
    assert _budget_model is not None
    return budget_allocator.allocate_portfolio(
        _campaign_summaries(), _budget_model, total_budget=payload.total_budget
    )
