"""
parser.py
---------
CSV ingestion + column type detection heuristics.

Detected types:
  name      — looks like a person name (mixed alpha, spaces, high cardinality)
  binary    — exactly 2 unique non-null values (hired/rejected, 0/1, yes/no)
  categorical — low-cardinality string column (≤ 30 unique values)
  numeric   — all values parseable as numbers
  pincode   — 6-digit numeric strings (India pin codes)
  unknown   — fallback
"""

import pandas as pd
import numpy as np
import uuid
from typing import Optional


def load_csv(file_bytes: bytes) -> pd.DataFrame:
    """Parse raw CSV bytes into a DataFrame."""
    import io
    return pd.read_csv(io.BytesIO(file_bytes))


def detect_column_type(series: pd.Series) -> str:
    """Heuristic column type detection."""
    col = series.dropna()
    if col.empty:
        return "unknown"

    col_str = col.astype(str).str.strip()

    # Pincode: 6-digit numeric strings
    if col_str.str.match(r"^\d{6}$").mean() > 0.7:
        return "pincode"

    # Try numeric
    try:
        pd.to_numeric(col)
        return "numeric"
    except (ValueError, TypeError):
        pass

    # Check unique ratio
    unique_ratio = col.nunique() / len(col)

    # Binary: exactly 2 unique values
    if col.nunique() == 2:
        return "binary"

    # Name: high cardinality string with spaces (likely person names)
    if unique_ratio > 0.5 and col_str.str.contains(" ").mean() > 0.3:
        return "name"

    # Categorical: low cardinality
    if col.nunique() <= 30:
        return "categorical"

    return "unknown"


def get_column_info(df: pd.DataFrame, col: str) -> dict:
    """Build column metadata dict for a single column."""
    series = df[col]
    detected_type = detect_column_type(series)
    sample = series.dropna().astype(str).unique()[:5].tolist()
    null_pct = round(float(series.isna().mean()), 4)
    return {
        "name": col,
        "detected_type": detected_type,
        "sample_values": sample,
        "null_pct": null_pct,
    }


def parse_upload(file_bytes: bytes) -> tuple[str, pd.DataFrame, dict]:
    """
    Main entry point for upload router.
    Returns (file_id, dataframe, response_dict).

    The response now includes smart suggestions for:
      - suggested_outcome: { column, positive_value, confidence, method }
      - suggested_sensitive: [{ column, reason, confidence }]
    """
    df = load_csv(file_bytes)
    file_id = str(uuid.uuid4())

    columns = [get_column_info(df, col) for col in df.columns]
    preview = df.head(5).fillna("").astype(str).to_dict(orient="records")

    # Smart auto-detection via normalizer
    from engine.normalizer import detect_outcome_column, detect_sensitive_columns

    outcome_suggestion = detect_outcome_column(df)
    outcome_col_name = outcome_suggestion["column"] if outcome_suggestion else None
    sensitive_suggestions = detect_sensitive_columns(df, outcome_col_name)

    response = {
        "file_id": file_id,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns,
        "preview_rows": preview,
        # Smart suggestions
        "suggested_outcome": outcome_suggestion,
        "suggested_sensitive": sensitive_suggestions,
    }
    return file_id, df, response
