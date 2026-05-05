"""Admin HTTP API."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from admin_auth import create_admin_token, require_admin, verify_password
from config import get_settings
from db import get_db
from models_db import Submission

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminLoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int = 8


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(body: AdminLoginBody) -> AdminLoginResponse:
    settings = get_settings()
    expected_pw = settings["admin_password"]
    if not expected_pw:
        raise HTTPException(
            status_code=503,
            detail="Admin login is not configured (ADMIN_PASSWORD is unset).",
        )
    admin_em = settings["admin_email"]
    email_norm = body.email.strip().lower()
    if admin_em and email_norm != admin_em.lower():
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not verify_password(body.password.strip(), expected_pw.strip()):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_admin_token(body.email.strip())
    return AdminLoginResponse(access_token=token)


@router.get("/summary")
def admin_summary(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    total = db.query(func.count(Submission.id)).scalar() or 0
    with_email = (
        db.query(func.count(Submission.id)).filter(Submission.email.isnot(None)).scalar() or 0
    )
    without_email = int(total) - int(with_email)
    by_band: dict[str, int] = {}
    rows = db.query(Submission.report_json).all()
    for (rj,) in rows:
        try:
            d = json.loads(rj)
            b = str(d.get("band", "unknown"))
            by_band[b] = by_band.get(b, 0) + 1
        except (json.JSONDecodeError, TypeError):
            by_band["unknown"] = by_band.get("unknown", 0) + 1

    recent_q = (
        db.query(Submission)
        .order_by(Submission.created_at.desc())
        .limit(25)
        .all()
    )
    recent = []
    for s in recent_q:
        band = None
        pct = None
        try:
            d = json.loads(s.report_json)
            band = d.get("band")
            pct = d.get("percentage")
        except (json.JSONDecodeError, TypeError):
            pass
        recent.append(
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "email": s.email,
                "consent": s.consent,
                "band": band,
                "percentage": pct,
            }
        )

    return {
        "total": int(total),
        "with_email": int(with_email),
        "without_email": without_email,
        "by_band": by_band,
        "recent": recent,
    }


@router.get("/submissions")
def admin_submissions(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, Any]:
    q = db.query(Submission).order_by(Submission.created_at.desc())
    total = q.count()
    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).all()
    out = []
    for s in items:
        meta = None
        if s.meta_json:
            try:
                meta = json.loads(s.meta_json)
            except json.JSONDecodeError:
                meta = {"_raw": s.meta_json}
        try:
            report = json.loads(s.report_json)
        except json.JSONDecodeError:
            report = {}
        try:
            answers = json.loads(s.answers_json)
        except json.JSONDecodeError:
            answers = {}
        out.append(
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "email": s.email,
                "consent": s.consent,
                "answers": answers,
                "report": report,
                "meta": meta,
            }
        )
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": out,
    }


@router.get("/submissions/export")
def admin_submissions_export(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
) -> Response:
    rows = db.query(Submission).order_by(Submission.created_at.desc()).all()
    buf = io.StringIO()
    fieldnames = [
        "id",
        "created_at",
        "email",
        "consent",
        "band",
        "percentage",
        "page_url",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "referrer",
        "meta_json",
        "answers_json",
        "report_json",
    ]
    w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for s in rows:
        band = ""
        pct = ""
        try:
            r = json.loads(s.report_json)
            band = r.get("band", "")
            pct = r.get("percentage", "")
        except (json.JSONDecodeError, TypeError):
            pass
        meta_flat: dict[str, Any] = {}
        if s.meta_json:
            try:
                m = json.loads(s.meta_json)
                if isinstance(m, dict):
                    meta_flat["page_url"] = m.get("page_url", "")
                    meta_flat["utm_source"] = m.get("utm_source", "")
                    meta_flat["utm_medium"] = m.get("utm_medium", "")
                    meta_flat["utm_campaign"] = m.get("utm_campaign", "")
                    meta_flat["referrer"] = m.get("referrer", "")
            except json.JSONDecodeError:
                pass
        w.writerow(
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else "",
                "email": s.email or "",
                "consent": s.consent,
                "band": band,
                "percentage": pct,
                "page_url": meta_flat.get("page_url", ""),
                "utm_source": meta_flat.get("utm_source", ""),
                "utm_medium": meta_flat.get("utm_medium", ""),
                "utm_campaign": meta_flat.get("utm_campaign", ""),
                "referrer": meta_flat.get("referrer", ""),
                "meta_json": s.meta_json or "",
                "answers_json": s.answers_json,
                "report_json": s.report_json,
            }
        )
    filename = f"ind_submissions_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
