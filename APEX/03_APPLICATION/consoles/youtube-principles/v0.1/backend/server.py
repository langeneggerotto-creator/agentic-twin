#!/usr/bin/env python3
"""
APEX YouTube Principles Extraction Server v0.1

Serves the single-page frontend (web/index.html) and exposes
POST /api/analyze, which runs the ingestion + extraction pipeline in
pipeline.py against pasted YouTube URLs.

Run with:
    uvicorn backend.server:app --reload --app-dir "APEX/03_APPLICATION/consoles/youtube-principles/v0.1"
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import pipeline

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="APEX YouTube Principles Extraction Console")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    urls: List[str]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    urls = [u.strip() for u in request.urls if u.strip()]
    reports = pipeline.analyze_urls(urls)
    return {"reports": reports}


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
