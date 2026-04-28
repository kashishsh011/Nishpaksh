"""report.py — POST /report"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any
from datetime import date

router = APIRouter()


class ReportRequest(BaseModel):
    company_name: str = "the company"
    proxy_findings: list[dict[str, Any]]
    bias_metrics: dict[str, Any]
    mitigation_metrics: dict[str, Any]
    narrative_paragraphs: list[dict[str, Any]]
    dpdp_checklist: list[dict[str, Any]]


@router.post("/report")
async def generate_report(body: ReportRequest):
    from report.pdf_builder import generate_pdf
    try:
        pdf_bytes = generate_pdf(
            company_name=body.company_name,
            findings=body.proxy_findings,
            metrics={"before": body.bias_metrics, "after": body.mitigation_metrics},
            narrative=body.narrative_paragraphs,
            checklist=body.dpdp_checklist,
            overall_hire_rate=0.0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    filename = f"nishpaksh_audit_{date.today().isoformat()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )