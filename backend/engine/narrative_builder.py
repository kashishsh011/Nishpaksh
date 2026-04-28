"""
narrative_builder.py
--------------------
Constructs the prompt for Gemini API and handles the response.
Uses the centralised gemini_client with task="narrative" routing.

System instruction encodes:
- Indian legal context (DPDP Act, Articles 14/15/16)
- Audience: HR managers, not data scientists
- Tone: direct, plain language, no jargon
- Output format: 4 JSON sections
"""

import json
from engine.gemini_client import call_gemini, parse_json_response

SYSTEM_INSTRUCTION = """You are Nishpaksh, India's hiring bias auditor. You write plain-language audit reports for HR managers — not data scientists, not lawyers.

Your reports:
- Explain findings in plain English (or simple business language)
- Always translate metric numbers into human meaning: not "DPD: 0.23" but "your process rejects qualified applicants from [group] at 2.3x the rate of [group]"
- Reference Indian law accurately: DPDP Act 2023, Articles 14, 15, 16 of the Indian Constitution
- Never use jargon without immediately explaining it
- Are factual, not accusatory - you are measuring patterns, not judging intent

Output exactly 4 JSON objects in an array: executive_summary, proxy_findings, legal_implications, recommendations.
Return ONLY valid JSON array. No preamble. No markdown fences. No extra text."""


def build_prompt(
    proxy_findings: list[dict],
    bias_metrics: dict,
    mitigation_metrics: dict,
    company_name: str = "the company",
) -> str:
    return f"""Generate an audit report for {company_name}.

PROXY FINDINGS:
{json.dumps(proxy_findings, indent=2)}

BIAS METRICS:
{json.dumps(bias_metrics, indent=2)}

MITIGATION RESULTS:
{json.dumps(mitigation_metrics, indent=2)}

Write 4 sections. Each section: section key (string), heading (string), text (2-4 paragraphs, plain language).
Return JSON array: [{{"section": "executive_summary", "heading": "...", "text": "..."}}, ...]"""


def _build_dpdp_checklist(proxy_findings: list, bias_metrics: dict) -> list:
    checklist = []

    if any(f.get("severity") == "high" for f in proxy_findings):
        checklist.append({
            "article": "DPDP Act Section 4(1)(b)",
            "description": "Personal data processed for automated decisions must not discriminate on prohibited grounds",
            "status": "non_compliant",
        })


    dir_ratio = bias_metrics.get("disparate_impact_ratio", 1.0)
    if dir_ratio < 0.8:  # Standard 80% rule
        checklist.append({
            "article": "Article 14 — Equality before law",
            "description": "Equal protection against arbitrary differential treatment in employment",
            "status": "at_risk",
        })

    if any(f.get("proxy_type") == "caste" for f in proxy_findings):
        checklist.append({
            "article": "Article 15 — Prohibition of discrimination",
            "description": "No discrimination on grounds of religion, race, caste, sex or place of birth",
            "status": "non_compliant" if any(f.get("severity") == "high" for f in proxy_findings) else "at_risk",
        })

    checklist.append({
        "article": "Article 16 — Equal opportunity in employment",
        "description": "No discrimination in employment based on religion, race, caste, sex, or place of origin",
        "status": "review_required",
    })

    return checklist


def generate_narrative(
    proxy_findings: list,
    bias_metrics: dict,
    mitigation_metrics: dict,
    company_name: str = "the company",
) -> dict:
    prompt = build_prompt(proxy_findings, bias_metrics, mitigation_metrics, company_name)

    raw = call_gemini(
        prompt=prompt,
        task="narrative",
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.3,
        max_output_tokens=4000,
    )

    # Parse response
    paragraphs = []
    model_used = "gemini (via task router)"

    if raw is not None:
        parsed = parse_json_response(raw)
        if parsed is not None:
            paragraphs = parsed if isinstance(parsed, list) else [parsed]
        else:
            # Raw text couldn't be parsed as JSON — wrap as single paragraph
            paragraphs = [{"section": "narrative", "heading": "Audit Findings", "text": raw}]

    dpdp_checklist = _build_dpdp_checklist(proxy_findings, bias_metrics)

    if not paragraphs:
        raise ValueError("GEMINI_API_KEY not configured or all models failed — narrative generation unavailable")

    return {
        "narrative_paragraphs": paragraphs,
        "dpdp_checklist": dpdp_checklist,
        "model_used": model_used,
    }
