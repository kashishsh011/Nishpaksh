"""inspect.py — POST /inspect"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


class InspectRequest(BaseModel):
    file_id: str
    outcome_column: str
    outcome_positive_value: str
    sensitive_columns: list[str]


@router.post("/inspect")
async def inspect_dataset(body: InspectRequest, request: Request):
    df = request.app.state.file_store.get(body.file_id)
    if df is None:
        raise HTTPException(status_code=404, detail="file_id not found — please re-upload")

    from engine.inspector import compute_distributions
    try:
        result = compute_distributions(
            df,
            body.outcome_column,
            body.outcome_positive_value,
            body.sensitive_columns,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inspection failed: {str(e)}")

    return result
