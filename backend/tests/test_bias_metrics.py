"""
test_bias_metrics.py
--------------------
Unit tests for bias metric computations and real reweighing mitigation.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.bias_metrics import compute_bias_metrics


def _make_biased_df(n=200):
    """Create a DataFrame with known bias: group A hired 80%, group B hired 20%."""
    rng = np.random.default_rng(42)
    groups = (["A"] * (n // 2)) + (["B"] * (n // 2))
    outcomes = []
    for g in groups:
        rate = 0.80 if g == "A" else 0.20
        outcomes.append("hired" if rng.random() < rate else "rejected")
    return pd.DataFrame({
        "group": groups,
        "outcome": outcomes,
        "skill_score": rng.integers(40, 100, size=n),
    })


def _make_fair_df(n=200):
    """Create a DataFrame with no bias: both groups hired at ~50%."""
    rng = np.random.default_rng(42)
    groups = (["X"] * (n // 2)) + (["Y"] * (n // 2))
    outcomes = ["hired" if rng.random() < 0.50 else "rejected" for _ in groups]
    return pd.DataFrame({
        "group": groups,
        "outcome": outcomes,
        "skill_score": rng.integers(40, 100, size=n),
    })


class TestBiasMetrics:
    """Tests for DPD, EOD, DIR computations."""

    def test_biased_dpd_is_high(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        assert result["demographic_parity_difference"] is not None
        assert result["demographic_parity_difference"] > 0.3  # big gap

    def test_biased_dir_below_threshold(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        assert result["disparate_impact_ratio"] is not None
        assert result["disparate_impact_ratio"] < 0.80  # 4/5ths rule violated
        assert result["disparate_impact_flag"] is True

    def test_fair_dir_above_threshold(self):
        df = _make_fair_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        # Fair data should have DIR close to 1.0
        if result["disparate_impact_ratio"] is not None:
            assert result["disparate_impact_ratio"] > 0.60

    def test_by_group_structure(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        assert "group" in result["by_group"]
        group_data = result["by_group"]["group"]
        assert "A" in group_data
        assert "B" in group_data
        assert "selection_rate" in group_data["A"]

    def test_eod_computed(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        assert result["equalized_odds_difference"] is not None
        assert result["equalized_odds_difference"] > 0

    def test_empty_groups_return_none(self):
        # Only one group → can't compute metrics
        df = pd.DataFrame({
            "group": ["A"] * 20,
            "outcome": ["hired"] * 10 + ["rejected"] * 10,
        })
        result = compute_bias_metrics(df, "outcome", "hired", "group", [])
        assert result["demographic_parity_difference"] is None


class TestMitigationMetrics:
    """Tests for real reweighing mitigation."""

    def test_mitigation_reduces_dpd(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        before_dpd = result["demographic_parity_difference"]
        after_dpd = result["mitigation_metrics"]["demographic_parity_difference_after"]
        assert after_dpd is not None
        assert after_dpd < before_dpd  # reweighing should reduce DPD

    def test_mitigation_improves_dir(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        before_dir = result["disparate_impact_ratio"]
        after_dir = result["mitigation_metrics"]["disparate_impact_ratio_after"]
        assert after_dir is not None
        assert after_dir > before_dir  # DIR should improve (closer to 1.0)

    def test_mitigation_method_is_reweighing(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        assert result["mitigation_metrics"]["method"] == "reweighing"

    def test_accuracy_delta_present(self):
        df = _make_biased_df()
        result = compute_bias_metrics(df, "outcome", "hired", "group", ["skill_score"])
        assert result["mitigation_metrics"]["accuracy_delta"] is not None
