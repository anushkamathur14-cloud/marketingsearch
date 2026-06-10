"""Keyword and search term recommendation model."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

KEYWORD_FEATURE_COLS = [
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

SEARCH_TERM_FEATURE_COLS = [
    "impressions",
    "clicks",
    "ctr",
    "conversions",
    "conversion_rate",
    "cost",
]

KEYWORD_ACTIONS = ["scale", "maintain", "pause", "add_negative"]
SEARCH_TERM_ACTIONS = ["add_keyword", "add_negative", "monitor", "ignore"]


def train(keyword_df: pd.DataFrame, search_df: pd.DataFrame, model_dir: Path) -> dict:
    model_dir.mkdir(parents=True, exist_ok=True)

    X_kw = keyword_df[KEYWORD_FEATURE_COLS]
    y_kw = keyword_df["keyword_action"]
    X_train, X_test, y_train, y_test = train_test_split(
        X_kw, y_kw, test_size=0.2, random_state=42, stratify=y_kw
    )

    kw_classifier = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", RandomForestClassifier(n_estimators=120, max_depth=8, random_state=42)),
        ]
    )
    kw_classifier.fit(X_train, y_train)
    kw_acc = kw_classifier.score(X_test, y_test)

    X_st = search_df[SEARCH_TERM_FEATURE_COLS]
    y_st = search_df["search_term_action"]
    X_train_st, X_test_st, y_train_st, y_test_st = train_test_split(
        X_st, y_st, test_size=0.2, random_state=42, stratify=y_st
    )

    st_classifier = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", RandomForestClassifier(n_estimators=120, max_depth=8, random_state=42)),
        ]
    )
    st_classifier.fit(X_train_st, y_train_st)
    st_acc = st_classifier.score(X_test_st, y_test_st)

    joblib.dump(kw_classifier, model_dir / "keyword_classifier.joblib")
    joblib.dump(st_classifier, model_dir / "search_term_classifier.joblib")

    return {"keyword_accuracy": round(kw_acc, 4), "search_term_accuracy": round(st_acc, 4)}


def load_models(model_dir: Path) -> tuple:
    kw = joblib.load(model_dir / "keyword_classifier.joblib")
    st = joblib.load(model_dir / "search_term_classifier.joblib")
    return kw, st


def _explain_action(action: str) -> str:
    explanations = {
        "scale": "High conversion efficiency — increase bids and expand match types.",
        "maintain": "Stable performer — keep current settings and monitor weekly.",
        "pause": "Poor ROI — pause keyword and reallocate spend elsewhere.",
        "add_negative": "Irrelevant traffic — add as negative keyword to reduce waste.",
        "add_keyword": "Converting search term — promote to exact/phrase match keyword.",
        "monitor": "Insufficient data — continue gathering impressions before acting.",
        "ignore": "Low volume, neutral performance — no action needed.",
    }
    return explanations.get(action, "")


def recommend_keyword(row: dict, classifier) -> dict:
    features = np.array([[row[c] for c in KEYWORD_FEATURE_COLS]])
    action = classifier.predict(features)[0]
    proba = classifier.predict_proba(features)[0]
    classes = list(classifier.named_steps["model"].classes_)
    confidence = float(max(proba))

    return {
        "type": "keyword",
        "keyword": row.get("keyword", ""),
        "campaign": row.get("campaign", ""),
        "action": action,
        "confidence": round(confidence, 2),
        "rationale": _explain_action(action),
        "metrics": {
            "impressions": int(row["impressions"]),
            "clicks": int(row["clicks"]),
            "conversions": int(row["conversions"]),
            "conversion_rate": round(row["conversion_rate"], 4),
            "cost": round(row["cost"], 2),
            "quality_score": int(row["quality_score"]),
        },
        "probabilities": {
            cls: round(float(p), 3) for cls, p in zip(classes, proba)
        },
    }


def recommend_search_term(row: dict, classifier) -> dict:
    features = np.array([[row[c] for c in SEARCH_TERM_FEATURE_COLS]])
    action = classifier.predict(features)[0]
    proba = classifier.predict_proba(features)[0]
    classes = list(classifier.named_steps["model"].classes_)
    confidence = float(max(proba))

    return {
        "type": "search_term",
        "search_term": row.get("search_term", ""),
        "campaign": row.get("campaign", ""),
        "action": action,
        "confidence": round(confidence, 2),
        "rationale": _explain_action(action),
        "metrics": {
            "impressions": int(row["impressions"]),
            "clicks": int(row["clicks"]),
            "conversions": int(row["conversions"]),
            "conversion_rate": round(row["conversion_rate"], 4),
            "cost": round(row["cost"], 2),
        },
        "probabilities": {
            cls: round(float(p), 3) for cls, p in zip(classes, proba)
        },
    }
