"""Beacon IND Readiness API."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from assessment import (
    MAX_POINTS,
    QUESTIONS,
    band_copy,
    band_from_percentage,
    compute_percentage,
    derive_gaps,
    points_for_answer,
    recommended_steps,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow common local Next.js ports; override with CORS_ORIGINS if needed.
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

DEFAULT_CALENDLY_URL = "https://calendly.com/beaconone-org/30min"

app = FastAPI(
    title="Beacon IND Readiness Assessment",
    description="Self-assessment API for IND filing readiness (lead magnet).",
    version="1.0.0",
)

_origins = os.getenv("CORS_ORIGINS", "").strip()
if _origins:
    allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]
else:
    allow_origins = DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionOut(BaseModel):
    id: str
    section: str
    order: int
    text: str
    options: list[dict[str, Any]]


class AssessmentRequest(BaseModel):
    email: EmailStr | None = None
    answers: dict[str, str] = Field(default_factory=dict)


class CriticalGap(BaseModel):
    message: str
    risk_note: str


class AssessmentResponse(BaseModel):
    percentage: float
    band: str
    band_title: str
    band_description: str
    weighted_points: float
    max_points: float
    critical_gaps: list[CriticalGap]
    recommended_steps: list[str]
    calendly_url: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/questions", response_model=list[QuestionOut])
def list_questions() -> list[QuestionOut]:
    out: list[QuestionOut] = []
    for q in QUESTIONS:
        out.append(
            QuestionOut(
                id=q.id,
                section=q.section,
                order=q.order,
                text=q.text,
                options=[{"id": o.id, "label": o.label} for o in q.options],
            )
        )
    return out


@app.post("/api/assess", response_model=AssessmentResponse)
def assess(body: AssessmentRequest) -> AssessmentResponse:
    required_ids = {q.id for q in QUESTIONS}
    missing = required_ids - set(body.answers.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing answers for: {', '.join(sorted(missing))}",
        )

    extra = set(body.answers.keys()) - required_ids
    if extra:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown question ids: {', '.join(sorted(extra))}",
        )

    for q in QUESTIONS:
        allowed = {o.id for o in q.options}
        val = body.answers[q.id]
        if val not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid option for {q.id}: {val}",
            )

    if body.email:
        logger.info("Assessment submission email=%s", body.email)

    weighted = sum(
        points_for_answer(qid, body.answers[qid]) for qid in required_ids
    )
    pct = compute_percentage(body.answers)
    band = band_from_percentage(pct)
    title, desc = band_copy(band)
    gaps_raw = derive_gaps(body.answers)
    gaps = [CriticalGap(**g) for g in gaps_raw]

    return AssessmentResponse(
        percentage=pct,
        band=band,
        band_title=title,
        band_description=desc,
        weighted_points=round(weighted, 2),
        max_points=MAX_POINTS,
        critical_gaps=gaps,
        recommended_steps=recommended_steps(gaps_raw),
        calendly_url=os.getenv("CALENDLY_URL") or DEFAULT_CALENDLY_URL,
    )
