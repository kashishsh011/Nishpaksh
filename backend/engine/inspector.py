"""
inspector.py
------------
Distribution stats per column + hire rate by group + skew detection.
"""

import pandas as pd
import numpy as np
from typing import Optional

from engine.normalizer import make_outcome_binary


def compute_distributions(
    df: pd.DataFrame,
    outcome_column: str,
    outcome_positive_value: str,
    sensitive_columns: list[str],
) -> dict:
    """
    Compute per-column hire rate distributions and skew flags.
    Returns the full /inspect response dict.
    """
    df = df.copy()
    df["_outcome_bin"] = make_outcome_binary(df[outcome_column], outcome_positive_value)

    usable = df[df[outcome_column].notna()]
    total_rows = len(df)
    usable_rows = len(usable)
    hire_rate_overall = round(float(usable["_outcome_bin"].mean()), 3)

    column_distributions = []

    for col in sensitive_columns:
        if col not in df.columns or col == outcome_column:
            continue
        dist = _column_distribution(df, col, "_outcome_bin", hire_rate_overall)
        # Only include distributions that actually have data
        if dist and dist.get("distribution") and len(dist["distribution"]) > 0:
            column_distributions.append(dist)

    return {
        "dataset_health": {
            "total_rows": total_rows,
            "usable_rows": usable_rows,
            "hire_rate_overall": hire_rate_overall,
        },
        "column_distributions": column_distributions,
    }


def _column_distribution(
    df: pd.DataFrame, col: str, outcome_bin_col: str, overall_rate: float
) -> Optional[dict]:
    """Build distribution stats for a single column."""
    series = df[col].dropna().astype(str)
    n_unique = series.nunique()

    # Adaptive minimum sample size — scales with dataset size
    # For tiny datasets (<30 rows), allow groups with just 2 members
    # For larger datasets, require at least 5
    n_rows = len(series)
    min_sample = max(2, min(5, n_rows // 10))

    # For high-cardinality columns (names, etc.): group by surname initial
    # Triggers when >50% of values are unique AND there are more than 5 unique values
    unique_ratio = n_unique / max(len(series), 1)
    if unique_ratio > 0.5 and n_unique > 5:
        # Extract surname (last word) and bucket by first letter
        surnames = series.str.strip().str.split().str[-1].str[0].str.upper()
        surnames = surnames.fillna("?")
        bucketed_df = df.loc[surnames.index].copy()
        bucketed_df["_bucket"] = surnames.values
        grouped = (
            bucketed_df.groupby("_bucket")[outcome_bin_col]
            .agg(["sum", "count"])
            .rename(columns={"sum": "hired", "count": "total"})
        )
        grouped["hire_rate"] = (grouped["hired"] / grouped["total"]).round(3)
        grouped = grouped[grouped["total"] >= max(1, min_sample - 1)]  # Adaptive threshold for buckets
        
        distribution = [
            {"label": f"Surname '{label}...'", "count": int(row["total"]), "hire_rate": float(row["hire_rate"])}
            for label, row in grouped.iterrows()
        ]
        
        if not distribution:
            return None
            
        min_rate = min(d["hire_rate"] for d in distribution)
        max_rate = max(d["hire_rate"] for d in distribution)
        skew_flag = False
        skew_reason = None
        if min_rate < overall_rate * 0.5 and max_rate > 0:
            skew_flag = True
            min_label = min(distribution, key=lambda x: x["hire_rate"])["label"]
            max_label = max(distribution, key=lambda x: x["hire_rate"])["label"]
            skew_reason = f"{min_label} has {round(min_rate*100)}% vs {max_label} at {round(max_rate*100)}%"
        
        return {
            "column": f"{col} (by surname initial)",
            "type": "name",
            "skew_flag": skew_flag,
            "skew_reason": skew_reason,
            "distribution": sorted(distribution, key=lambda x: x["hire_rate"]),
        }

    col_type = "categorical"
    try:
        pd.to_numeric(df[col])
        col_type = "numeric"
    except Exception:
        pass

    # Group stats
    grouped = (
        df.groupby(col)["_outcome_bin"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "hired", "count": "total"})
    )
    grouped["hire_rate"] = (grouped["hired"] / grouped["total"]).round(3)
    grouped = grouped[grouped["total"] >= min_sample]  # Adaptive minimum sample

    distribution = [
        {"label": str(label), "count": int(row["total"]), "hire_rate": float(row["hire_rate"])}
        for label, row in grouped.iterrows()
    ]

    # Skew detection: if any group hire rate < 50% of overall
    skew_flag = False
    skew_reason = None
    if distribution:
        min_rate = min(d["hire_rate"] for d in distribution)
        max_rate = max(d["hire_rate"] for d in distribution)
        if min_rate < overall_rate * 0.5 and max_rate > 0:
            skew_flag = True
            min_label = min(distribution, key=lambda x: x["hire_rate"])["label"]
            max_label = max(distribution, key=lambda x: x["hire_rate"])["label"]
            min_pct = round(min_rate * 100)
            max_pct = round(max_rate * 100)
            skew_reason = (
                f"'{min_label}' group has {min_pct}% hire rate vs "
                f"'{max_label}' at {max_pct}% — a {round(max_rate/min_rate, 1)}× gap"
            )

    return {
        "column": col,
        "type": col_type,
        "skew_flag": skew_flag,
        "skew_reason": skew_reason,
        "distribution": distribution,
    }
