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
    from report.pdf_builder import build_pdf
    try:
        pdf_bytes = build_pdf(
            company_name=body.company_name,
            proxy_findings=body.proxy_findings,
            bias_metrics=body.bias_metrics,
            mitigation_metrics=body.mitigation_metrics,
            narrative_paragraphs=body.narrative_paragraphs,
            dpdp_checklist=body.dpdp_checklist,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    filename = f"nishpaksh_audit_{date.today().isoformat()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
