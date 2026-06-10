"""Bid recommendation model for search ads keywords."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = [
    "impressions",
    "clicks",
    "ctr",
    "conversions",
    "conversion_rate",
    "avg_cpc",
    "cost",
    "quality_score",
    "competition_index",
    "impression_share",
]

BID_ACTIONS = ["decrease", "hold", "increase"]


def train(keyword_df: pd.DataFrame, model_dir: Path) -> dict:
    model_dir.mkdir(parents=True, exist_ok=True)
    X = keyword_df[FEATURE_COLS]
    y_bid = keyword_df["optimal_bid"]
    y_action = keyword_df["bid_action"]

    X_train, X_test, y_train, y_test = train_test_split(X, y_bid, test_size=0.2, random_state=42)
    _, _, y_action_train, y_action_test = train_test_split(
        X, y_action, test_size=0.2, random_state=42
    )

    regressor = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(n_estimators=120, max_depth=4, random_state=42)),
        ]
    )
    regressor.fit(X_train, y_train)
    bid_r2 = regressor.score(X_test, y_test)

    classifier = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
            ),
        ]
    )
    classifier.fit(X_train, y_action_train)
    action_acc = classifier.score(X_test, y_action_test)

    joblib.dump(regressor, model_dir / "bid_regressor.joblib")
    joblib.dump(classifier, model_dir / "bid_classifier.joblib")

    return {"bid_r2": round(bid_r2, 4), "action_accuracy": round(action_acc, 4)}


def load_models(model_dir: Path) -> tuple:
    regressor = joblib.load(model_dir / "bid_regressor.joblib")
    classifier = joblib.load(model_dir / "bid_classifier.joblib")
    return regressor, classifier


def recommend(row: dict, regressor, classifier) -> dict:
    features = np.array([[row[c] for c in FEATURE_COLS]])
    optimal_bid = float(regressor.predict(features)[0])
    action = classifier.predict(features)[0]
    current_bid = row["avg_cpc"]
    change_pct = ((optimal_bid - current_bid) / current_bid) * 100 if current_bid else 0

    confidence = min(0.95, 0.55 + abs(change_pct) / 100)

    return {
        "keyword": row.get("keyword", ""),
        "campaign": row.get("campaign", ""),
        "current_bid": round(current_bid, 2),
        "recommended_bid": round(optimal_bid, 2),
        "bid_change_pct": round(change_pct, 1),
        "action": action,
        "confidence": round(confidence, 2),
        "metrics": {
            "impressions": int(row["impressions"]),
            "clicks": int(row["clicks"]),
            "ctr": round(row["ctr"], 4),
            "conversions": int(row["conversions"]),
            "conversion_rate": round(row["conversion_rate"], 4),
            "quality_score": int(row["quality_score"]),
            "impression_share": round(row["impression_share"], 3),
        },
    }
