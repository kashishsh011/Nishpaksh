"""upload.py — POST /upload"""
from fastapi import APIRouter, UploadFile, File, Request, HTTPException

router = APIRouter()


@router.post("/upload")
async def upload_csv(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    from engine.parser import parse_upload
    try:
        file_id, df, response = parse_upload(contents)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {str(e)}")

    request.app.state.file_store[file_id] = df
    return response
