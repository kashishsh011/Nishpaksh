"""
normalizer.py
-------------
Universal outcome column detection and value normalisation.

Handles the full variety of hiring dataset formats:
  Column names:  outcome, hired, is_hired, selected, result, decision, status, label, etc.
  Values:        1/0, Yes/No, True/False, hired/not_hired, Selected/Rejected, Pass/Fail, etc.

Also provides a single `make_outcome_binary()` function used by inspector,
bias_metrics, and proxy_detector to ensure consistent outcome parsing.
"""

import pandas as pd
from typing import Optional


# ── Column-name aliases (lowercase) ──────────────────────────────────────

OUTCOME_COLUMN_ALIASES = [
    "outcome", "hired", "is_hired", "selected", "result", "decision",
    "status", "hire_flag", "offer_made", "label", "target",
    "is_selected", "shortlisted", "offer", "accepted", "rejected",
    "hire", "hire_status", "selection", "selection_status",
]

# ── Positive outcome values (lowercase, stripped) ────────────────────────

POSITIVE_VALUES = {
    "1", "yes", "true", "hired", "selected", "accepted", "approved",
    "pass", "passed", "offer", "offered", "shortlisted", "y", "t",
    "positive", "success", "admit", "admitted",
}

NEGATIVE_VALUES = {
    "0", "no", "false", "not_hired", "not hired", "rejected", "denied",
    "fail", "failed", "not_selected", "not selected", "declined", "n", "f",
    "negative", "not_offered", "not offered", "waitlisted",
}


def detect_outcome_column(df: pd.DataFrame) -> Optional[dict]:
    """
    Auto-detect the outcome column from a DataFrame.
    Returns dict with { column, positive_value, confidence, method } or None.

    Detection strategy (in priority order):
      1. Column name matches a known alias AND is binary → highest confidence
      2. Column name matches a known alias → high confidence
      3. Binary column whose values look like outcome values → medium confidence
      4. Any binary column → low confidence
    """
    candidates = []

    for col in df.columns:
        col_lower = col.lower().strip().replace(" ", "_")
        series = df[col].dropna()
        if series.empty:
            continue

        n_unique = series.nunique()
        name_match = any(alias == col_lower or alias in col_lower for alias in OUTCOME_COLUMN_ALIASES)

        # Check if values look like outcome values
        sample_vals = set(series.astype(str).str.strip().str.lower().unique())
        has_positive = bool(sample_vals & POSITIVE_VALUES)
        has_negative = bool(sample_vals & NEGATIVE_VALUES)
        values_look_like_outcome = has_positive or has_negative

        if name_match and n_unique == 2:
            candidates.append({
                "column": col,
                "confidence": 0.95,
                "method": "name_match + binary",
            })
        elif name_match and n_unique <= 5 and values_look_like_outcome:
            candidates.append({
                "column": col,
                "confidence": 0.85,
                "method": "name_match + outcome_values",
            })
        elif name_match:
            candidates.append({
                "column": col,
                "confidence": 0.65,
                "method": "name_match",
            })
        elif n_unique == 2 and values_look_like_outcome:
            candidates.append({
                "column": col,
                "confidence": 0.60,
                "method": "binary + outcome_values",
            })
        elif n_unique == 2:
            candidates.append({
                "column": col,
                "confidence": 0.30,
                "method": "binary_column",
            })

    if not candidates:
        return None

    # Pick the highest-confidence candidate
    best = max(candidates, key=lambda c: c["confidence"])

    # Detect positive value for the chosen column
    pos_val = detect_positive_value(df[best["column"]])
    best["positive_value"] = pos_val
    return best


def detect_positive_value(series: pd.Series) -> str:
    """
    Given an outcome column, determine which value represents the positive outcome.

    Strategy:
      1. Check unique values against known positive/negative lists
      2. For numeric columns (0/1), positive = 1
      3. For boolean columns, positive = True
      4. Fallback: pick the less-frequent value (minority class = "hired")
    """
    vals = series.dropna()
    if vals.empty:
        return "1"

    unique_raw = vals.unique()
    unique_lower = [str(v).strip().lower() for v in unique_raw]
    unique_raw_str = [str(v).strip() for v in unique_raw]

    # Direct match against known positive values
    for raw, lower in zip(unique_raw_str, unique_lower):
        if lower in POSITIVE_VALUES:
            return raw  # Return the original casing/format

    # Numeric: 1 is positive
    try:
        numeric = pd.to_numeric(vals)
        if set(numeric.unique()) <= {0, 1, 0.0, 1.0}:
            return "1"
    except (ValueError, TypeError):
        pass

    # Boolean
    if vals.dtype == bool:
        return "True"

    # Fallback: infer from negative values — the other one is positive
    for i, lower in enumerate(unique_lower):
        if lower in NEGATIVE_VALUES and len(unique_raw_str) == 2:
            # Return the other value
            other_idx = 1 - i
            return unique_raw_str[other_idx]

    # Last resort: minority class (usually "hired" is less common)
    if len(unique_raw) == 2:
        counts = vals.value_counts()
        return str(counts.idxmin())

    return unique_raw_str[0] if unique_raw_str else "1"


def make_outcome_binary(
    series: pd.Series,
    positive_value: str,
) -> pd.Series:
    """
    Convert any outcome column to binary 0/1 integers.
    Handles all formats: string, numeric, boolean, mixed case.

    This is the SINGLE source of truth for outcome parsing.
    All backend modules (inspector, bias_metrics, proxy_detector) should use this.
    """
    pos_lower = str(positive_value).strip().lower()

    # Try numeric path first (handles 1/0, 1.0/0.0)
    try:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().mean() > 0.9:
            pos_num = float(pos_lower) if pos_lower.replace(".", "").isdigit() else None
            if pos_num is not None:
                return (numeric == pos_num).astype(int)
    except (ValueError, TypeError):
        pass

    # String comparison path (handles all text formats)
    return (
        series.astype(str).str.strip().str.lower() == pos_lower
    ).astype(int)


def detect_sensitive_columns(df: pd.DataFrame, outcome_col: Optional[str] = None) -> list[dict]:
    """
    Auto-detect which columns are likely sensitive/demographic attributes.
    Returns list of { column, reason, confidence }.
    """
    from engine.parser import detect_column_type

    SENSITIVE_NAME_KEYWORDS = [
        "gender", "sex", "caste", "religion", "category", "community",
        "college", "university", "institution", "school", "education",
        "name", "candidate", "applicant",
        "pin", "pincode", "postal", "zip", "location", "city", "state",
        "age", "race", "ethnicity", "disability", "marital",
    ]

    results = []
    for col in df.columns:
        if col == outcome_col:
            continue
        col_lower = col.lower().strip()
        col_type = detect_column_type(df[col])

        # Name columns
        if col_type == "name":
            results.append({"column": col, "reason": "person_name", "confidence": 0.9})
            continue

        # Pincode columns
        if col_type == "pincode":
            results.append({"column": col, "reason": "geographic_proxy", "confidence": 0.9})
            continue

        # Column name matches sensitive keywords
        name_match = [k for k in SENSITIVE_NAME_KEYWORDS if k in col_lower]
        if name_match and col_type in ("binary", "categorical"):
            results.append({
                "column": col,
                "reason": f"keyword_match: {name_match[0]}",
                "confidence": 0.85,
            })
            continue

        # Categorical with low cardinality — potential demographic
        if col_type == "categorical" and name_match:
            results.append({
                "column": col,
                "reason": f"categorical + keyword: {name_match[0]}",
                "confidence": 0.70,
            })

    return results
