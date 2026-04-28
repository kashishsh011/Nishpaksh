"""
test_proxy_detector.py
----------------------
Unit tests for proxy detection — caste, SES, and class.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.proxy_detector import (
    _extract_surname,
    _severity,
    _normalize_college,
)


class TestExtractSurname:
    def test_full_name(self):
        assert _extract_surname("Rahul Sharma") == "Sharma"

    def test_single_name(self):
        assert _extract_surname("Madonna") == "Madonna"

    def test_none_input(self):
        assert _extract_surname(None) is None

    def test_empty_string(self):
        assert _extract_surname("") is None

    def test_title_case(self):
        assert _extract_surname("mohd ansari") == "Ansari"

    def test_three_part_name(self):
        assert _extract_surname("Smt. Lakshmi Reddy") == "Reddy"


class TestSeverity:
    def test_high(self):
        assert _severity(3.5) == "high"

    def test_medium(self):
        assert _severity(2.0) == "medium"

    def test_compliant(self):
        assert _severity(1.2) == "compliant"

    def test_boundary_high(self):
        assert _severity(3.0) == "high"

    def test_boundary_medium(self):
        assert _severity(1.5) == "medium"


class TestNormalizeCollege:
    def test_basic(self):
        result = _normalize_college("IIT Delhi")
        assert "iit" in result
        assert "delhi" in result

    def test_removes_filler(self):
        result = _normalize_college("Indian Institute of Technology Bombay")
        assert "of" not in result.split()

    def test_none_input(self):
        assert _normalize_college(None) == ""

    def test_whitespace(self):
        result = _normalize_college("  BITS   Pilani  ")
        assert result == "bits pilani"


class TestProxyDetectionIntegration:
    """Integration tests using the synthetic dataset if available."""

    @pytest.fixture
    def synthetic_df(self):
        fixture_path = Path(__file__).parent / "fixtures" / "synthetic_hiring_500.csv"
        if fixture_path.exists():
            return pd.read_csv(fixture_path)
        pytest.skip("Synthetic dataset not found")

    def test_detect_proxies_returns_list(self, synthetic_df):
        from engine.proxy_detector import detect_proxies
        findings = detect_proxies(
            synthetic_df,
            "outcome",
            "hired",
            ["candidate_name", "pincode", "college"],
        )
        assert isinstance(findings, list)

    def test_findings_have_required_fields(self, synthetic_df):
        from engine.proxy_detector import detect_proxies
        findings = detect_proxies(
            synthetic_df,
            "outcome",
            "hired",
            ["candidate_name", "pincode", "college"],
        )
        required = {"id", "column", "proxy_type", "severity", "disparity_ratio",
                     "affected_hire_rate", "comparison_hire_rate"}
        for f in findings:
            assert required.issubset(f.keys()), f"Missing fields in finding: {f.get('id')}"

    def test_severity_values_valid(self, synthetic_df):
        from engine.proxy_detector import detect_proxies
        findings = detect_proxies(
            synthetic_df,
            "outcome",
            "hired",
            ["candidate_name", "pincode", "college"],
        )
        for f in findings:
            assert f["severity"] in ("high", "medium", "compliant")

    def test_proxy_types_valid(self, synthetic_df):
        from engine.proxy_detector import detect_proxies
        findings = detect_proxies(
            synthetic_df,
            "outcome",
            "hired",
            ["candidate_name", "pincode", "college"],
        )
        valid_types = {"caste", "socioeconomic", "class"}
        for f in findings:
            assert f["proxy_type"] in valid_types
