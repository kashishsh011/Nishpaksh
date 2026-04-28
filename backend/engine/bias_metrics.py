"""
bias_metrics.py
---------------
Pure-pandas implementation of bias metrics — no sklearn or fairlearn required.
This is actually more appropriate for a DATA audit (we measure the data, not a model).

Metrics computed directly from observed hiring rates:

1. Demographic Parity Difference (DPD)
   = max(selection_rate_by_group) - min(selection_rate_by_group)
   Threshold: DPD > 0.1 is concern; > 0.2 is audit-grade

2. Equalized Odds Difference (EOD)
   = approximated as max TPR spread across groups
   (true positive rate = hired among "qualified" candidates, proxied by skill_score >= median)

3. Disparate Impact Ratio (DIR)
   = min(selection_rate) / max(selection_rate)
   4/5ths rule: DIR < 0.80 = prima facie adverse impact

Mitigation: reweighing — simulated by equalizing selection rates (shows what fair outcome looks like).
"""

import pandas as pd
import numpy as np
from typing import Optional

from engine.normalizer import make_outcome_binary


def compute_bias_metrics(
    df: pd.DataFrame,
    outcome_column: str,
    outcome_positive_value: str,
    sensitive_column: str,
    feature_columns: list[str],
) -> dict:
    """
    Computes bias metrics directly from observed hiring data.
    Returns bias_metrics + mitigation_metrics dicts.
    """
    df = df.copy().dropna(subset=[outcome_column, sensitive_column])

    y = make_outcome_binary(df[outcome_column], outcome_positive_value)
    sensitive = df[sensitive_column].astype(str)

    # Group stats
    group_df = pd.DataFrame({"y": y, "sensitive": sensitive})
    group_stats = group_df.groupby("sensitive")["y"].agg(["mean", "count"]).rename(
        columns={"mean": "hire_rate", "count": "n"}
    )
    # Adaptive minimum sample — scales with dataset size
    # For tiny datasets (<30 rows), allow groups with just 2 members
    min_sample = max(2, min(5, len(df) // 10))
    group_stats = group_stats[group_stats["n"] >= min_sample]

    if group_stats.empty or len(group_stats) < 2:
        return _empty_metrics(sensitive_column)

    sr_values = group_stats["hire_rate"].values
    max_sr = float(sr_values.max())
    min_sr = float(sr_values.min())

    dpd = round(max_sr - min_sr, 3)
    dir_ratio = round(min_sr / max_sr, 3) if max_sr > 0 else 0.0

    # Equalized Odds proxy: TPR among "qualified" (skill >= median if col exists)
    skill_col = _find_skill_col(df, feature_columns)
    if skill_col:
        median_skill = df[skill_col].median()
        qualified = df[skill_col] >= median_skill
        q_df = pd.DataFrame({"y": y[qualified.values], "sensitive": sensitive[qualified.values]})
        q_stats = q_df.groupby("sensitive")["y"].mean()
        q_vals = q_stats.values
        eod = round(float(q_vals.max() - q_vals.min()), 3) if len(q_vals) >= 2 else dpd
    else:
        eod = dpd  # fallback

    # Overall accuracy proxy (selection rate vs overall rate)
    overall_rate = float(y.mean())
    accuracy = round(1.0 - abs(overall_rate - 0.5), 3)  # Simplified

    by_group = {
        str(idx): {
            "selection_rate": round(float(row["hire_rate"]), 3),
            "true_positive_rate": round(float(row["hire_rate"]), 3),  # same as hire rate without model
        }
        for idx, row in group_stats.iterrows()
    }

    # ── Real reweighing mitigation ──────────────────────────────────────
    # Compute group weights: w_g = overall_rate / group_rate
    # Then compute re-weighted selection rates and derive corrected metrics
    reweighed = _compute_reweighing(group_stats, overall_rate, y, sensitive, skill_col, df)
    dpd_after = reweighed["dpd"]
    dir_after = reweighed["dir"]
    eod_after = reweighed["eod"]
    acc_after = reweighed["accuracy"]

    return {
        "model_accuracy": accuracy,
        "demographic_parity_difference": dpd,
        "equalized_odds_difference": eod,
        "disparate_impact_ratio": dir_ratio,
        "disparate_impact_flag": dir_ratio < 0.80,
        "disparate_impact_legal_threshold": 0.80,
        "by_group": {sensitive_column: by_group},
        "mitigation_metrics": {
            "method": "reweighing",
            "demographic_parity_difference_after": dpd_after,
            "equalized_odds_difference_after": eod_after,
            "disparate_impact_ratio_after": dir_after,
            "accuracy_after": acc_after,
            "accuracy_delta": round(acc_after - accuracy, 3),
        },
    }


def _compute_reweighing(
    group_stats: pd.DataFrame,
    overall_rate: float,
    y: pd.Series,
    sensitive: pd.Series,
    skill_col: Optional[str],
    df: pd.DataFrame,
) -> dict:
    """
    Real reweighing mitigation.
    Weight each group by (overall_rate / group_rate) for positive outcomes
    and ((1 - overall_rate) / (1 - group_rate)) for negative outcomes.
    Then recompute DPD, EOD, DIR from the re-weighted selection rates.
    """
    # Compute sample weights
    weights = pd.Series(1.0, index=y.index)
    for grp, row in group_stats.iterrows():
        grp_rate = row["hire_rate"]
        mask_pos = (sensitive == grp) & (y == 1)
        mask_neg = (sensitive == grp) & (y == 0)

        if grp_rate > 0:
            weights.loc[mask_pos] = overall_rate / grp_rate
        if grp_rate < 1:
            weights.loc[mask_neg] = (1 - overall_rate) / (1 - grp_rate)

    # Re-weighted selection rates per group
    rw_rates = {}
    for grp in group_stats.index:
        mask = sensitive == grp
        if mask.sum() == 0:
            continue
        w_grp = weights[mask]
        y_grp = y[mask]
        rw_rates[grp] = float((y_grp * w_grp).sum() / w_grp.sum())

    if len(rw_rates) < 2:
        return {"dpd": None, "dir": None, "eod": None, "accuracy": None}

    rw_values = list(rw_rates.values())
    max_rw = max(rw_values)
    min_rw = min(rw_values)

    dpd_after = round(max_rw - min_rw, 3)
    dir_after = round(min_rw / max_rw, 3) if max_rw > 0 else 0.0

    # Re-weighted EOD (TPR among qualified, if skill col exists)
    eod_after = dpd_after  # fallback
    if skill_col and skill_col in df.columns:
        try:
            median_skill = df[skill_col].median()
            qualified = df[skill_col] >= median_skill
            rw_tpr = {}
            for grp in group_stats.index:
                mask = (sensitive == grp) & qualified
                if mask.sum() == 0:
                    continue
                w_q = weights[mask]
                y_q = y[mask]
                rw_tpr[grp] = float((y_q * w_q).sum() / w_q.sum())
            if len(rw_tpr) >= 2:
                eod_after = round(max(rw_tpr.values()) - min(rw_tpr.values()), 3)
        except Exception:
            pass

    # Accuracy proxy: overall re-weighted selection rate distance from 0.5
    rw_overall = float((y * weights).sum() / weights.sum())
    acc_after = round(1.0 - abs(rw_overall - 0.5), 3)

    return {"dpd": dpd_after, "dir": dir_after, "eod": eod_after, "accuracy": acc_after}


def _find_skill_col(df: pd.DataFrame, feature_columns: list[str]) -> Optional[str]:
    """Find a numeric score/skill column for TPR proxy."""
    for col in feature_columns:
        if col not in df.columns:
            continue
        if any(k in col.lower() for k in ["skill", "score", "rating", "grade", "gpa", "cgpa"]):
            try:
                pd.to_numeric(df[col])
                return col
            except Exception:
                pass
    return None


def _empty_metrics(sensitive_column: str) -> dict:
    return {
        "model_accuracy": None,
        "demographic_parity_difference": None,
        "equalized_odds_difference": None,
        "disparate_impact_ratio": None,
        "disparate_impact_flag": False,
        "disparate_impact_legal_threshold": 0.80,
        "by_group": {sensitive_column: {}},
        "mitigation_metrics": {
            "method": "reweighing",
            "demographic_parity_difference_after": None,
            "equalized_odds_difference_after": None,
            "disparate_impact_ratio_after": None,
            "accuracy_after": None,
            "accuracy_delta": None,
        },
    }
