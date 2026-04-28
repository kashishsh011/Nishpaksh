"""narrative.py — POST /narrative"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

router = APIRouter()


class NarrativeRequest(BaseModel):
    company_name: str = "the company"
    file_id: str
    proxy_findings: list[dict[str, Any]]
    bias_metrics: dict[str, Any]
    mitigation_metrics: dict[str, Any]


@router.post("/narrative")
async def generate_narrative(body: NarrativeRequest):
    from engine.narrative_builder import generate_narrative
    try:
        result = generate_narrative(
            proxy_findings=body.proxy_findings,
            bias_metrics=body.bias_metrics,
            mitigation_metrics=body.mitigation_metrics,
            company_name=body.company_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Narrative generation failed: {str(e)}")

    return result
