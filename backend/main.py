"""
main.py
-------
FastAPI entry point for Nishpaksh API.
In-memory file store used for hackathon scope (no database required).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routers import upload, inspect, audit, narrative, report

app = FastAPI(
    title="Nishpaksh API",
    description="India's hiring bias auditor — proxy detection, Fairlearn metrics, Gemini narrative",
    version="1.0.0",
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory file store: key=file_id (UUID), value=pandas DataFrame
FILE_STORE: dict = {}
app.state.file_store = FILE_STORE

app.include_router(upload.router)
app.include_router(inspect.router)
app.include_router(audit.router)
app.include_router(narrative.router)
app.include_router(report.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "nishpaksh-api"}
