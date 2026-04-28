"""audit.py — POST /audit"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AuditRequest(BaseModel):
    file_id: str
    outcome_column: str
    outcome_positive_value: str
    sensitive_columns: list[str]


@router.post("/audit")
async def run_audit(body: AuditRequest, request: Request):
    df = request.app.state.file_store.get(body.file_id)
    if df is None:
        raise HTTPException(status_code=404, detail="file_id not found — please re-upload")

    from engine.proxy_detector import detect_proxies
    from engine.bias_metrics import compute_bias_metrics

    # Proxy detection
    try:
        proxy_findings = detect_proxies(
            df,
            body.outcome_column,
            body.outcome_positive_value,
            body.sensitive_columns,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy detection failed: {str(e)}")

    # Bias metrics — use the first non-name, non-outcome sensitive column for Fairlearn
    # (Fairlearn needs a single categorical sensitive attribute)
    sensitive_for_fairlearn = None
    for col in body.sensitive_columns:
        if col in df.columns and col != body.outcome_column:
            col_lower = col.lower()
            # Prefer gender/explicit categorical over name/pincode for Fairlearn
            if any(k in col_lower for k in ["gender", "sex", "caste", "religion", "category"]):
                sensitive_for_fairlearn = col
                break
    if not sensitive_for_fairlearn:
        # Fall back to first available sensitive column
        for col in body.sensitive_columns:
            if col in df.columns and col != body.outcome_column:
                sensitive_for_fairlearn = col
                break

    bias_metrics = {}
    mitigation_metrics = {}
    if sensitive_for_fairlearn:
        try:
            result = compute_bias_metrics(
                df,
                body.outcome_column,
                body.outcome_positive_value,
                sensitive_for_fairlearn,
                list(df.columns),
            )
            mitigation_metrics = result.pop("mitigation_metrics", {})
            bias_metrics = result
        except Exception as e:
            # Non-fatal — return empty metrics with error note
            bias_metrics = {"error": str(e)}
            mitigation_metrics = {}

    return {
        "proxy_findings": proxy_findings,
        "bias_metrics": bias_metrics,
        "mitigation_metrics": mitigation_metrics,
    }
