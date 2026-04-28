"""
proxy_detector.py
-----------------
Detects India-specific proxy discrimination in hiring datasets.

Three proxy types are detected:

1. CASTE PROXY (via surname analysis)
   - Loads data/surname_caste_map.csv
   - Extracts last name from candidate_name column
   - Maps to caste groups: upper_hindu, obc, sc_st, muslim, christian, sikh, other
   - Falls back to Gemini classification for surnames not in the static CSV
   - Computes hire rate by caste group
   - Flags if any group's hire rate is < 60% of highest group's rate

2. SOCIOECONOMIC PROXY (via pin code)
   - Loads data/pincode_ses_map.csv
   - Maps each pin code to SES tier: tier_1 (metro affluent), tier_2 (urban mid), tier_3 (rural/peri-urban)
   - Computes hire rate by tier
   - Flags if tier_3 rate < 70% of tier_1 rate

3. CLASS PROXY (via college tier)
   - Loads data/college_tier_map.csv
   - Normalises college names
   - Falls back to Gemini classification for colleges not in the static CSV
   - Maps to: iit_iim, nit_bits, state_university, private_ranked, private_unranked
   - Computes hire rate by tier

Severity scoring:
  disparity_ratio >= 3.0  → 'high'
  disparity_ratio >= 1.5  → 'medium'
  disparity_ratio < 1.5   → 'compliant'
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Optional

from engine.gemini_client import call_gemini, parse_json_response
from engine.normalizer import make_outcome_binary

DATA_DIR = Path(__file__).parent.parent / "data"


def load_reference_tables():
    surname_map = pd.read_csv(DATA_DIR / "surname_caste_map.csv")
    pincode_map = pd.read_csv(DATA_DIR / "pincode_ses_map.csv", dtype={"pincode": str})
    college_map = pd.read_csv(DATA_DIR / "college_tier_map.csv")
    return surname_map, pincode_map, college_map

def _detect_class_proxy_from_tier(df, tier_col, outcome_col, positive_val) -> Optional[dict]:
    """Use an existing college_tier column directly — no name mapping needed."""
    df = df.copy()
    df["_outcome_bin"] = make_outcome_binary(df[outcome_col], positive_val)
    df["_tier"] = df[tier_col].astype(str).str.strip()

    min_proxy_sample = max(2, min(5, len(df) // 10))
    group_stats = (
        df.groupby("_tier")["_outcome_bin"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "hire_rate", "count": "n"})
        .query(f"n >= {min_proxy_sample}")
    )

    if len(group_stats) < 2:
        return None

    max_rate = group_stats["hire_rate"].max()
    min_idx = group_stats["hire_rate"].idxmin()
    min_row = group_stats.loc[min_idx]
    max_idx = group_stats["hire_rate"].idxmax()

    ratio = max_rate / min_row["hire_rate"] if min_row["hire_rate"] > 0 else 0
    sev = _severity(ratio)

    if sev == "compliant":
        return None

    return {
        "id": f"proxy-class-{tier_col}",
        "column": tier_col,
        "proxy_type": "class",
        "proxy_mechanism": "college_tier_direct",
        "affected_group": f"{min_idx} college graduates",
        "comparison_group": f"{max_idx} college graduates",
        "affected_hire_rate": round(float(min_row["hire_rate"]), 3),
        "comparison_hire_rate": round(float(max_rate), 3),
        "disparity_ratio": round(float(ratio), 2),
        "sample_size_affected": int(min_row["n"]),
        "severity": sev,
        "legal_note": "Class-based indirect discrimination; potential DPDP Act Section 4(1)(b) exposure",
    }


def detect_proxies(
    df: pd.DataFrame,
    outcome_column: str,
    outcome_positive_value: str,
    sensitive_columns: list[str],
) -> list[dict]:
    """
    Main entry point. Returns list of proxy_finding dicts.
    """
    surname_map, pincode_map, college_map = load_reference_tables()
    findings = []

    for col in sensitive_columns:
        if col not in df.columns:
            continue

        col_lower = col.lower()

        # Detect column purpose by name heuristics
        if any(k in col_lower for k in ["name", "candidate", "applicant"]):
            result = _detect_caste_proxy(df, col, outcome_column, outcome_positive_value, surname_map)
            if result:
                findings.append(result)

        elif any(k in col_lower for k in ["pin", "pincode", "postal", "zip"]):
            result = _detect_ses_proxy(df, col, outcome_column, outcome_positive_value, pincode_map)
            if result:
                findings.append(result)

        elif any(k in col_lower for k in ["college", "university", "institution", "school", "degree", "education"]):
            # If a pre-mapped tier column already exists (e.g. "college_tier"), use it directly
            tier_col_candidates = [c for c in df.columns if "tier" in c.lower()]
            if tier_col_candidates:
                result = _detect_class_proxy_from_tier(
                    df, tier_col_candidates[0], outcome_column, outcome_positive_value
                )
            else:
                result = _detect_class_proxy(df, col, outcome_column, outcome_positive_value, college_map)
            if result:
                findings.append(result)

    return findings


def analyze_bias_patterns(metrics: dict) -> str:
    """
    Use Gemini to analyze bias metrics and identify suspicious patterns.
    Returns a plain-English analysis string.
    """
    prompt = f"""You are a bias auditor reviewing hiring data from an Indian company.
Given these computed bias metrics: {json.dumps(metrics, indent=2)}

Identify the 2-3 most statistically suspicious patterns.
Be specific: name affected groups, percentages, and which Indian legal thresholds are breached.
Keep your response under 150 words. Plain English only, no jargon."""

    result = call_gemini(prompt=prompt, task="analyze", temperature=0.3, max_output_tokens=400)
    if result is None:
        return "Pattern analysis unavailable — please check API quota."
    return result


import json


def _extract_surname(name: str) -> Optional[str]:
    """Extract last word as surname. Handles None, single names, initials."""
    if not isinstance(name, str):
        return None
    parts = name.strip().split()
    return parts[-1].title() if parts else None


def _severity(ratio: float) -> str:
    if ratio >= 3.0:
        return "high"
    elif ratio >= 1.5:
        return "medium"
    return "compliant"


# ── Gemini-powered classification for unknowns ─────────────────────────


def _classify_surnames_with_gemini(unknown_surnames: list[str]) -> dict[str, str]:
    """
    Batch-classify unknown surnames using Gemini.
    Returns dict mapping surname -> community.
    """
    if not unknown_surnames:
        return {}

    # Deduplicate
    unique = list(set(unknown_surnames))
    if len(unique) > 100:
        unique = unique[:100]  # cap to avoid huge prompts

    surname_list = ", ".join(unique)
    prompt = f"""Classify each Indian surname by likely community of origin.
Return ONLY a valid JSON object, no explanation, no markdown.
Format: {{"surname": "community"}}
Communities: Upper-Caste-Hindu, OBC, SC, ST, Muslim, Christian, Sikh, Unknown
Surnames: {surname_list}"""

    result = call_gemini(prompt=prompt, task="classify", temperature=0.1, max_output_tokens=1500)
    parsed = parse_json_response(result)

    if parsed is None or not isinstance(parsed, dict):
        return {s: "unknown" for s in unknown_surnames}

    # Normalize community names to match our internal taxonomy
    community_map = {
        "upper-caste-hindu": "upper_hindu",
        "upper caste hindu": "upper_hindu",
        "obc": "obc",
        "sc": "sc_st",
        "st": "sc_st",
        "sc/st": "sc_st",
        "muslim": "muslim",
        "christian": "christian",
        "sikh": "sikh",
        "unknown": "unknown",
    }

    normalized = {}
    for surname, community in parsed.items():
        c_lower = community.lower().strip()
        normalized[surname.title()] = community_map.get(c_lower, "unknown")

    return normalized


def _classify_colleges_with_gemini(unknown_colleges: list[str]) -> dict[str, str]:
    """
    Batch-classify unknown colleges using Gemini.
    Returns dict mapping college_name -> tier.
    """
    if not unknown_colleges:
        return {}

    unique = list(set(unknown_colleges))
    if len(unique) > 80:
        unique = unique[:80]

    college_list = ", ".join(unique)
    prompt = f"""Classify each Indian college/university by selectivity tier.
Return ONLY a valid JSON object, no explanation, no markdown.
Format: {{"college_name": "tier"}}
Tiers: Tier-1 (IIT/IIM/AIIMS/NIT-top), Tier-2 (state-top/private-reputed), Tier-3 (others), Unknown
Colleges: {college_list}"""

    result = call_gemini(prompt=prompt, task="classify", temperature=0.1, max_output_tokens=1500)
    parsed = parse_json_response(result)

    if parsed is None or not isinstance(parsed, dict):
        return {c: "unknown" for c in unknown_colleges}

    # Normalize tier names to match internal taxonomy
    tier_map = {
        "tier-1": "iit_iim",
        "tier 1": "iit_iim",
        "tier-2": "state_university",
        "tier 2": "state_university",
        "tier-3": "private_unranked",
        "tier 3": "private_unranked",
        "unknown": "unknown",
    }

    normalized = {}
    for college, tier in parsed.items():
        t_lower = tier.lower().strip()
        # Try exact match first, then prefix match
        mapped = tier_map.get(t_lower)
        if mapped is None:
            for k, v in tier_map.items():
                if k in t_lower:
                    mapped = v
                    break
        normalized[college] = mapped or "unknown"

    return normalized


# ── Proxy Detection Functions ──────────────────────────────────────────


def _detect_caste_proxy(df, col, outcome_col, positive_val, surname_map) -> Optional[dict]:
    """Surname → caste group → hire rate comparison. Falls back to Gemini for unknowns."""
    df = df.copy()
    df["_surname"] = df[col].apply(_extract_surname)
    df["_outcome_bin"] = make_outcome_binary(df[outcome_col], positive_val)

    # Merge with surname map
    surname_col = "surname"
    if surname_col not in surname_map.columns:
        surname_col = surname_map.columns[0]

    merged = df.merge(
        surname_map.rename(columns={surname_col: "_surname"}),
        on="_surname",
        how="left",
    )

    caste_col = "caste_group" if "caste_group" in merged.columns else merged.columns[-1]
    merged["_caste_group"] = merged[caste_col].fillna("unknown")

    # Gemini fallback for unknown surnames
    unknown_mask = merged["_caste_group"] == "unknown"
    unknown_surnames = merged.loc[unknown_mask, "_surname"].dropna().unique().tolist()

    gemini_used = False
    if unknown_surnames:
        gemini_classifications = _classify_surnames_with_gemini(unknown_surnames)
        if gemini_classifications:
            gemini_used = True
            merged.loc[unknown_mask, "_caste_group"] = merged.loc[unknown_mask, "_surname"].map(
                lambda s: gemini_classifications.get(s, "unknown") if isinstance(s, str) else "unknown"
            )

    # Adaptive minimum sample size
    min_proxy_sample = max(3, min(10, len(merged) // 10))

    # Hire rate by group (exclude 'unknown' if sample too small)
    group_stats = (
        merged.groupby("_caste_group")["_outcome_bin"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "hire_rate", "count": "n"})
        .query(f"n >= {min_proxy_sample}")
    )

    # Drop unknown group from analysis if it exists
    if "unknown" in group_stats.index and len(group_stats) > 2:
        group_stats = group_stats.drop("unknown", errors="ignore")

    if len(group_stats) < 2:
        return None

    max_rate = group_stats["hire_rate"].max()
    min_idx = group_stats["hire_rate"].idxmin()
    min_row = group_stats.loc[min_idx]
    max_idx = group_stats["hire_rate"].idxmax()

    ratio = max_rate / min_row["hire_rate"] if min_row["hire_rate"] > 0 else 0
    sev = _severity(ratio)

    if sev == "compliant":
        return None

    finding = {
        "id": f"proxy-caste-{col}",
        "column": col,
        "proxy_type": "caste",
        "proxy_mechanism": "surname_analysis",
        "affected_group": f"{min_idx}-origin surnames",
        "comparison_group": f"{max_idx}-origin surnames",
        "affected_hire_rate": round(float(min_row["hire_rate"]), 3),
        "comparison_hire_rate": round(float(max_rate), 3),
        "disparity_ratio": round(float(ratio), 2),
        "sample_size_affected": int(min_row["n"]),
        "severity": sev,
        "legal_note": "Pattern consistent with indirect caste discrimination under Article 15 of the Constitution of India",
    }

    if gemini_used:
        finding["ai_enhanced"] = True
        finding["proxy_mechanism"] = "surname_analysis + gemini_classification"

    return finding


def _detect_ses_proxy(df, col, outcome_col, positive_val, pincode_map) -> Optional[dict]:
    """Pin code → SES tier → hire rate comparison."""
    df = df.copy()
    df["_pincode"] = df[col].astype(str).str.strip().str.zfill(6)
    df["_outcome_bin"] = make_outcome_binary(df[outcome_col], positive_val)

    pin_col = "pincode" if "pincode" in pincode_map.columns else pincode_map.columns[0]
    merged = df.merge(
        pincode_map.rename(columns={pin_col: "_pincode"}),
        on="_pincode",
        how="left",
    )

    tier_col = "ses_tier" if "ses_tier" in merged.columns else "tier"
    merged["_tier"] = merged.get(tier_col, pd.Series(dtype=str)).fillna("unknown")

    # Adaptive minimum sample size
    min_proxy_sample = max(3, min(10, len(merged) // 10))

    group_stats = (
        merged.groupby("_tier")["_outcome_bin"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "hire_rate", "count": "n"})
        .query(f"n >= {min_proxy_sample}")
    )

    if "tier_1" not in group_stats.index or "tier_3" not in group_stats.index:
        return None

    t1_rate = group_stats.loc["tier_1", "hire_rate"]
    t3_rate = group_stats.loc["tier_3", "hire_rate"]

    if t3_rate == 0:
        return None

    ratio = t1_rate / t3_rate
    sev = _severity(ratio)

    if sev == "compliant":
        return None

    return {
        "id": f"proxy-ses-{col}",
        "column": col,
        "proxy_type": "socioeconomic",
        "proxy_mechanism": "pincode_ses_mapping",
        "affected_group": "Tier-3 SES pin codes (rural/peri-urban)",
        "comparison_group": "Tier-1 SES pin codes (metro affluent)",
        "affected_hire_rate": round(float(t3_rate), 3),
        "comparison_hire_rate": round(float(t1_rate), 3),
        "disparity_ratio": round(float(ratio), 2),
        "sample_size_affected": int(group_stats.loc["tier_3", "n"]),
        "severity": sev,
        "legal_note": "Indirect geographic discrimination may implicate DPDP Act Section 4(1)(b)",
    }


def _normalize_college(name: str) -> str:
    """Lowercase, strip, remove common suffixes for matching."""
    if not isinstance(name, str):
        return ""
    name = name.lower().strip()
    # Remove common filler words
    for word in ["the", "of", "institute", "technology", "engineering", "and", "&"]:
        name = re.sub(rf"\b{word}\b", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _detect_class_proxy(df, col, outcome_col, positive_val, college_map) -> Optional[dict]:
    """College name → tier → hire rate comparison. Falls back to Gemini for unknowns."""
    df = df.copy()
    df["_college_norm"] = df[col].apply(_normalize_college)
    df["_outcome_bin"] = make_outcome_binary(df[outcome_col], positive_val)

    # Normalize college_map
    name_col = college_map.columns[0]
    tier_col = college_map.columns[1]
    college_map = college_map.copy()
    college_map["_college_norm"] = college_map[name_col].apply(_normalize_college)

    merged = df.merge(college_map[["_college_norm", tier_col]], on="_college_norm", how="left")
    merged["_tier"] = merged[tier_col].fillna("unknown")

    # Gemini fallback for unknown colleges
    unknown_mask = merged["_tier"] == "unknown"
    unknown_colleges = df.loc[unknown_mask.values, col].dropna().unique().tolist()

    gemini_used = False
    if unknown_colleges:
        gemini_classifications = _classify_colleges_with_gemini(unknown_colleges)
        if gemini_classifications:
            gemini_used = True
            # Build a mapping from original college name to tier
            college_to_tier = {}
            for orig_name, tier in gemini_classifications.items():
                college_to_tier[_normalize_college(orig_name)] = tier
            merged.loc[unknown_mask, "_tier"] = merged.loc[unknown_mask, "_college_norm"].map(
                lambda n: college_to_tier.get(n, "unknown")
            )

    # Adaptive minimum sample size
    min_proxy_sample = max(2, min(5, len(merged) // 10))

    group_stats = (
        merged.groupby("_tier")["_outcome_bin"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "hire_rate", "count": "n"})
        .query(f"n >= {min_proxy_sample}")
    )

    known = group_stats[group_stats.index != "unknown"]
    if len(known) < 2:
        return None

    max_rate = known["hire_rate"].max()
    min_idx = known["hire_rate"].idxmin()
    min_row = known.loc[min_idx]
    max_idx = known["hire_rate"].idxmax()

    ratio = max_rate / min_row["hire_rate"] if min_row["hire_rate"] > 0 else 0
    sev = _severity(ratio)

    if sev == "compliant":
        return None

    finding = {
        "id": f"proxy-class-{col}",
        "column": col,
        "proxy_type": "class",
        "proxy_mechanism": "college_tier_mapping",
        "affected_group": f"{min_idx} college graduates",
        "comparison_group": f"{max_idx} college graduates",
        "affected_hire_rate": round(float(min_row["hire_rate"]), 3),
        "comparison_hire_rate": round(float(max_rate), 3),
        "disparity_ratio": round(float(ratio), 2),
        "sample_size_affected": int(min_row["n"]),
        "severity": sev,
        "legal_note": "Class-based indirect discrimination; potential DPDP Act Section 4(1)(b) exposure",
    }

    if gemini_used:
        finding["ai_enhanced"] = True
        finding["proxy_mechanism"] = "college_tier_mapping + gemini_classification"

    return finding
