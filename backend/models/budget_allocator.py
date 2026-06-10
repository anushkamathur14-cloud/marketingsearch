"""Budget allocation model for search ad campaigns."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = [
    "daily_budget",
    "spend_7d",
    "conversions_7d",
    "revenue_7d",
    "roas",
    "cpa",
    "impression_share",
    "lost_is_budget",
]


def train(campaign_df: pd.DataFrame, model_dir: Path) -> dict:
    model_dir.mkdir(parents=True, exist_ok=True)
    X = campaign_df[FEATURE_COLS]
    y = campaign_df["recommended_budget"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)),
        ]
    )
    model.fit(X_train, y_train)
    r2 = model.score(X_test, y_test)
    joblib.dump(model, model_dir / "budget_regressor.joblib")
    return {"budget_r2": round(r2, 4)}


def load_model(model_dir: Path):
    return joblib.load(model_dir / "budget_regressor.joblib")


def _priority(roas: float, lost_is_budget: float) -> str:
    if roas >= 3.0 and lost_is_budget >= 0.2:
        return "high"
    if roas >= 2.0:
        return "medium"
    if roas < 1.0:
        return "reduce"
    return "low"


def recommend(row: dict, model) -> dict:
    features = np.array([[row[c] for c in FEATURE_COLS]])
    recommended = float(model.predict(features)[0])
    current = row["daily_budget"]
    change = recommended - current
    change_pct = (change / current) * 100 if current else 0

    return {
        "campaign": row["campaign"],
        "current_budget": round(current, 2),
        "recommended_budget": round(recommended, 2),
        "budget_change": round(change, 2),
        "budget_change_pct": round(change_pct, 1),
        "priority": _priority(row["roas"], row["lost_is_budget"]),
        "metrics": {
            "spend_7d": round(row["spend_7d"], 2),
            "conversions_7d": int(row["conversions_7d"]),
            "revenue_7d": round(row["revenue_7d"], 2),
            "roas": round(row["roas"], 2),
            "cpa": round(row["cpa"], 2),
            "impression_share": round(row["impression_share"], 3),
            "lost_is_budget": round(row["lost_is_budget"], 3),
        },
        "rationale": _rationale(row, change_pct),
    }


def _rationale(row: dict, change_pct: float) -> str:
    roas = row["roas"]
    lost = row["lost_is_budget"]
    if change_pct > 10:
        if lost > 0.2:
            return f"Strong ROAS ({roas}x) with {lost:.0%} impression share lost to budget — increase to capture demand."
        return f"Above-target ROAS ({roas}x) — scale budget to maximize profitable conversions."
    if change_pct < -10:
        return f"Underperforming ROAS ({roas}x) — reduce budget and reallocate to higher-return campaigns."
    return f"Stable performance at {roas}x ROAS — minor adjustment recommended."


def allocate_portfolio(campaigns: list[dict], model, total_budget: Optional[float] = None) -> dict:
    recommendations = [recommend(c, model) for c in campaigns]
    total_recommended = sum(r["recommended_budget"] for r in recommendations)

    if total_budget and total_recommended > 0:
        scale = total_budget / total_recommended
        for r in recommendations:
            r["recommended_budget"] = round(r["recommended_budget"] * scale, 2)
            r["budget_change"] = round(r["recommended_budget"] - r["current_budget"], 2)
            current = r["current_budget"]
            r["budget_change_pct"] = round((r["budget_change"] / current) * 100, 1) if current else 0

    return {
        "recommendations": recommendations,
        "total_current_budget": round(sum(r["current_budget"] for r in recommendations), 2),
        "total_recommended_budget": round(sum(r["recommended_budget"] for r in recommendations), 2),
    }
