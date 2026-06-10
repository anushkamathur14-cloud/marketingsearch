"""Generate synthetic search ads performance data for model training."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

CAMPAIGNS = [
    "Brand Search",
    "Non-Brand - Running Shoes",
    "Non-Brand - Trail Gear",
    "Competitor Conquest",
    "Retargeting - Cart Abandoners",
]

KEYWORDS = [
    "running shoes",
    "best trail runners",
    "marathon training shoes",
    "nike running shoes",
    "brooks ghost 15",
    "waterproof hiking boots",
    "ultra marathon gear",
    "carbon plate shoes",
    "wide fit running shoes",
    "cheap running shoes",
    "running shoes near me",
    "best shoes for flat feet",
    "trail running backpack",
    "gait analysis near me",
    "free shipping running shoes",
]

SEARCH_TERMS = KEYWORDS + [
    "how to start running",
    "running shoe reviews 2024",
    "what shoes do marathoners wear",
    "running shoes for beginners",
    "trail shoes vs road shoes",
    "running shoe sale",
    "used running shoes",
    "running shoe return policy",
    "running shoe sizing guide",
    "best budget trail shoes",
]


def _keyword_features(n: int) -> pd.DataFrame:
    impressions = RNG.integers(500, 50000, n)
    ctr = RNG.uniform(0.01, 0.12, n)
    clicks = (impressions * ctr).astype(int)
    conversion_rate = RNG.uniform(0.005, 0.08, n)
    conversions = (clicks * conversion_rate).astype(int)
    avg_cpc = RNG.uniform(0.35, 4.50, n)
    cost = clicks * avg_cpc
    quality_score = RNG.integers(3, 11, n)
    competition = RNG.uniform(0.2, 1.0, n)
    impression_share = RNG.uniform(0.15, 0.95, n)

    optimal_bid = (
        avg_cpc
        * (1 + 0.15 * (conversion_rate / 0.04 - 1))
        * (1 + 0.1 * (quality_score / 10 - 0.5))
        * (1 - 0.08 * competition)
    )
    optimal_bid = np.clip(optimal_bid, 0.25, 8.0)

    bid_action = np.where(
        optimal_bid > avg_cpc * 1.08,
        "increase",
        np.where(optimal_bid < avg_cpc * 0.92, "decrease", "hold"),
    )

    keyword_action = RNG.choice(
        ["scale", "maintain", "pause", "add_negative"],
        n,
        p=[0.25, 0.45, 0.15, 0.15],
    )
    low_conv = conversion_rate < 0.01
    high_conv = conversion_rate > 0.05
    keyword_action = np.where(high_conv & (clicks > 20), "scale", keyword_action)
    keyword_action = np.where(low_conv & (cost > 50), "pause", keyword_action)
    keyword_action = np.where(
        (impressions > 1000) & (conversions == 0) & (cost > 30),
        "add_negative",
        keyword_action,
    )

    return pd.DataFrame(
        {
            "keyword": RNG.choice(KEYWORDS, n),
            "campaign": RNG.choice(CAMPAIGNS, n),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": ctr,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
            "avg_cpc": avg_cpc,
            "cost": cost,
            "quality_score": quality_score,
            "competition_index": competition,
            "impression_share": impression_share,
            "optimal_bid": optimal_bid,
            "bid_action": bid_action,
            "keyword_action": keyword_action,
        }
    )


def _search_term_features(n: int) -> pd.DataFrame:
    impressions = RNG.integers(100, 20000, n)
    ctr = RNG.uniform(0.005, 0.10, n)
    clicks = (impressions * ctr).astype(int)
    conversion_rate = RNG.uniform(0.0, 0.07, n)
    conversions = (clicks * conversion_rate).astype(int)
    cost = clicks * RNG.uniform(0.30, 3.50, n)

    action = RNG.choice(
        ["add_keyword", "add_negative", "monitor", "ignore"],
        n,
        p=[0.20, 0.15, 0.45, 0.20],
    )
    action = np.where(
        (conversions >= 2) & (conversion_rate > 0.03),
        "add_keyword",
        action,
    )
    action = np.where(
        (impressions > 500) & (conversions == 0) & (cost > 25),
        "add_negative",
        action,
    )

    return pd.DataFrame(
        {
            "search_term": RNG.choice(SEARCH_TERMS, n),
            "campaign": RNG.choice(CAMPAIGNS, n),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": ctr,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
            "cost": cost,
            "search_term_action": action,
        }
    )


def _campaign_features(n: int = 60) -> pd.DataFrame:
    rows = []
    for _ in range(n):
        campaign = str(RNG.choice(CAMPAIGNS))
        spend = float(RNG.uniform(800, 12000))
        conversions = int(RNG.integers(5, 120))
        revenue = conversions * float(RNG.uniform(45, 180))
        roas = revenue / spend if spend else 0
        impression_share = float(RNG.uniform(0.2, 0.85))
        lost_is_budget = float(RNG.uniform(0.05, 0.45))
        current_budget = float(RNG.uniform(50, 500))

        if roas > 3.5:
            budget_multiplier = RNG.uniform(1.15, 1.45)
        elif roas > 2.0:
            budget_multiplier = RNG.uniform(0.95, 1.15)
        elif roas > 1.0:
            budget_multiplier = RNG.uniform(0.75, 0.95)
        else:
            budget_multiplier = RNG.uniform(0.50, 0.80)

        if lost_is_budget > 0.25 and roas > 2.5:
            budget_multiplier *= 1.1

        recommended_budget = round(current_budget * budget_multiplier, 2)

        rows.append(
            {
                "campaign": campaign,
                "daily_budget": current_budget,
                "spend_7d": round(spend, 2),
                "conversions_7d": conversions,
                "revenue_7d": round(revenue, 2),
                "roas": round(roas, 2),
                "cpa": round(spend / max(conversions, 1), 2),
                "impression_share": round(impression_share, 3),
                "lost_is_budget": round(lost_is_budget, 3),
                "recommended_budget": recommended_budget,
            }
        )
    return pd.DataFrame(rows)


def generate_all(output_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    output_dir = output_dir or Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    keyword_df = _keyword_features(800)
    search_df = _search_term_features(600)
    campaign_df = _campaign_features()

    keyword_df.to_csv(output_dir / "keywords.csv", index=False)
    search_df.to_csv(output_dir / "search_terms.csv", index=False)
    campaign_df.to_csv(output_dir / "campaigns.csv", index=False)

    summary = {
        "keywords": len(keyword_df),
        "search_terms": len(search_df),
        "campaigns": len(campaign_df),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return {"keywords": keyword_df, "search_terms": search_df, "campaigns": campaign_df}


if __name__ == "__main__":
    data = generate_all()
    print(f"Generated {len(data['keywords'])} keyword rows, {len(data['search_terms'])} search terms, {len(data['campaigns'])} campaigns")
