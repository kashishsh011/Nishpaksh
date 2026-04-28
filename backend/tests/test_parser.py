"""
test_parser.py
--------------
Unit tests for CSV parsing and column type detection.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.parser import detect_column_type, parse_upload, get_column_info


class TestDetectColumnType:
    """Tests for the heuristic column type detector."""

    def test_binary_column(self):
        s = pd.Series(["hired", "rejected", "hired", "rejected", "hired"])
        assert detect_column_type(s) == "binary"

    def test_binary_numeric(self):
        # Integer 0/1 passes pd.to_numeric check first → classified as "numeric"
        s = pd.Series([0, 1, 1, 0, 1, 0, 1])
        assert detect_column_type(s) == "numeric"

    def test_numeric_column(self):
        s = pd.Series([85, 90, 72, 68, 95, 42])
        assert detect_column_type(s) == "numeric"

    def test_pincode_column(self):
        s = pd.Series(["400001", "110002", "560003", "600001", "700001"])
        assert detect_column_type(s) == "pincode"

    def test_name_column(self):
        s = pd.Series([
            "Rahul Sharma", "Priya Mehta", "Imran Khan",
            "Sunita Devi", "John DSouza", "Gurpreet Singh",
            "Ananya Iyer", "Mohd Ansari", "Kavya Saxena", "Raju Mahato",
        ])
        assert detect_column_type(s) == "name"

    def test_categorical_column(self):
        s = pd.Series(["Male", "Female", "Male", "Female", "Male"] * 10)
        assert detect_column_type(s) == "binary"  # 2 unique = binary

    def test_categorical_multi(self):
        s = pd.Series(["A", "B", "C", "D", "E"] * 3)
        assert detect_column_type(s) == "categorical"

    def test_empty_column(self):
        s = pd.Series([None, None, None], dtype=object)
        assert detect_column_type(s) == "unknown"

    def test_single_value(self):
        s = pd.Series(["constant"] * 10)
        assert detect_column_type(s) == "categorical"


class TestParseUpload:
    """Tests for the full upload parsing pipeline."""

    def _make_csv_bytes(self, df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")

    def test_basic_csv_parse(self):
        df = pd.DataFrame({
            "name": ["Rahul Sharma", "Priya Mehta", "Imran Khan", "John DSouza", "Sunita Devi"],
            "score": [85, 90, 72, 68, 95],
            "outcome": ["hired", "hired", "rejected", "hired", "rejected"],
        })
        file_id, parsed_df, response = parse_upload(self._make_csv_bytes(df))

        assert file_id  # non-empty UUID
        assert len(parsed_df) == 5
        assert response["row_count"] == 5
        assert response["column_count"] == 3
        assert len(response["columns"]) == 3
        assert len(response["preview_rows"]) == 5

    def test_column_info_structure(self):
        df = pd.DataFrame({
            "candidate_name": ["Rahul Sharma", "Priya Mehta"],
            "pincode": ["400001", "110002"],
            "outcome": ["hired", "rejected"],
        })
        _, _, response = parse_upload(self._make_csv_bytes(df))

        for col in response["columns"]:
            assert "name" in col
            assert "detected_type" in col
            assert "sample_values" in col
            assert "null_pct" in col
            assert col["detected_type"] in ["name", "binary", "categorical", "numeric", "pincode", "unknown"]

    def test_preview_rows_limited_to_5(self):
        df = pd.DataFrame({
            "x": list(range(100)),
            "y": ["a"] * 100,
        })
        _, _, response = parse_upload(self._make_csv_bytes(df))
        assert len(response["preview_rows"]) == 5

    def test_null_percentage(self):
        df = pd.DataFrame({
            "col": [1, None, 3, None, 5, None, 7, None, 9, None],
        })
        info = get_column_info(df, "col")
        assert info["null_pct"] == 0.5
