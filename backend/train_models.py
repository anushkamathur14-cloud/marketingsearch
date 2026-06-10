"""Train all ML models on synthetic search ads data."""

from __future__ import annotations

import json
from pathlib import Path

from data.generate_synthetic import generate_all
from models.bid_optimizer import train as train_bid
from models.budget_allocator import train as train_budget
from models.keyword_recommender import train as train_keyword

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "saved_models"


def main() -> None:
    print("Generating synthetic data...")
    datasets = generate_all(DATA_DIR)

    print("Training bid optimizer...")
    bid_metrics = train_bid(datasets["keywords"], MODEL_DIR)

    print("Training keyword recommender...")
    kw_metrics = train_keyword(datasets["keywords"], datasets["search_terms"], MODEL_DIR)

    print("Training budget allocator...")
    budget_metrics = train_budget(datasets["campaigns"], MODEL_DIR)

    metrics = {**bid_metrics, **kw_metrics, **budget_metrics}
    (MODEL_DIR / "training_metrics.json").write_text(json.dumps(metrics, indent=2))

    print("\nTraining complete:")
    for name, value in metrics.items():
        print(f"  {name}: {value}")


if __name__ == "__main__":
    main()
