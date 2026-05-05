"""Beacon IND Readiness API."""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

load_dotenv(Path(__file__).resolve().parent / ".env")

from admin_api import router as admin_router
from assessment import QUESTIONS
from assessment_core import build_assessment_report, label_answers
from db import Base, engine
from email_send import send_assessment_report_email
from models_db import Submission  # noqa: F401
from report_html import build_report_html
from risk_snapshot import compute_risk_snapshot
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local dev origins — always allowed.
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
_DEFAULT_VERCEL_REGEX = r"https://.*\.vercel\.app"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Beacon IND Readiness Assessment",
    description="Self-assessment API for IND filing readiness (lead magnet).",
    version="1.0.0",
    lifespan=lifespan,
)

_extra = os.getenv("CORS_ORIGINS", "").strip()
_extra_origins = [o.strip() for o in _extra.split(",") if o.strip()]
allow_origins = list(DEFAULT_ORIGINS) + _extra_origins

_regex_raw = os.getenv("CORS_ORIGIN_REGEX")
if _regex_raw is None:
    allow_origin_regex = _DEFAULT_VERCEL_REGEX
elif _regex_raw.strip() == "":
    allow_origin_regex = None
else:
    allow_origin_regex = _regex_raw.strip()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)


class QuestionOut(BaseModel):
    id: str
    section: str
    order: int
    text: str
    options: list[dict[str, Any]]


class AssessmentRequest(BaseModel):
    email: EmailStr | None = None
    answers: dict[str, str] = Field(default_factory=dict)
    consent: bool = False
    meta: dict[str, Any] | None = None


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
    submission_id: str | None = None
    email_delivery: str | None = None
    email_delivery_detail: str | None = None


def _validate_answers(body: AssessmentRequest) -> None:
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


def _persist_submission(
    db: Any,
    email: str | None,
    consent: bool,
    answers: dict[str, str],
    report: dict[str, Any],
    meta: dict[str, Any] | None,
) -> str:
    sid = str(uuid.uuid4())
    sub = Submission(
        id=sid,
        email=email,
        consent=consent,
        answers_json=json.dumps(answers),
        report_json=json.dumps(report),
        meta_json=json.dumps(meta) if meta else None,
    )
    db.add(sub)
    db.commit()
    return sid


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
    _validate_answers(body)

    if body.email and not body.consent:
        raise HTTPException(
            status_code=400,
            detail="Consent is required to receive your report by email.",
        )

    report = build_assessment_report(body.answers)
    gaps = [CriticalGap(**g) for g in report["critical_gaps"]]

    from db import SessionLocal

    db = SessionLocal()
    try:
        sid = _persist_submission(
            db,
            str(body.email) if body.email else None,
            body.consent,
            body.answers,
            report,
            body.meta,
        )
    finally:
        db.close()

    email_delivery: str | None = None
    email_delivery_detail: str | None = None
    if body.email and body.consent:
        logger.info("Assessment submission email=%s id=%s", body.email, sid)
        labeled = label_answers(body.answers)
        risk = compute_risk_snapshot(body.answers, report)
        html_body = build_report_html(labeled, report, risk)
        pct = report["percentage"]
        er = send_assessment_report_email(
            str(body.email),
            f"Your IND readiness report — {pct:.0f}%",
            html_body,
        )
        email_delivery = er.status
        email_delivery_detail = er.detail
        if er.status == "failed":
            logger.error("Report email not delivered: %s", er.detail)

    return AssessmentResponse(
        percentage=report["percentage"],
        band=report["band"],
        band_title=report["band_title"],
        band_description=report["band_description"],
        weighted_points=report["weighted_points"],
        max_points=report["max_points"],
        critical_gaps=gaps,
        recommended_steps=report["recommended_steps"],
        calendly_url=report["calendly_url"],
        submission_id=sid,
        email_delivery=email_delivery,
        email_delivery_detail=email_delivery_detail,
    )
