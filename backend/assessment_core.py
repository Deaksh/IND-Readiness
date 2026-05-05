"""Pure assessment scoring → report dict (API + persistence + email)."""

from __future__ import annotations

import os
from typing import Any

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

DEFAULT_CALENDLY = "https://calendly.com/beaconone-org/30min"


def label_answers(answers: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for q in QUESTIONS:
        oid = answers.get(q.id, "")
        lab = ""
        for o in q.options:
            if o.id == oid:
                lab = o.label
                break
        rows.append(
            {
                "id": q.id,
                "section": q.section,
                "order": str(q.order),
                "question": q.text,
                "answer_id": oid,
                "answer_label": lab,
            }
        )
    return rows


def build_assessment_report(answers: dict[str, str]) -> dict[str, Any]:
    required_ids = {q.id for q in QUESTIONS}
    weighted = sum(points_for_answer(qid, answers[qid]) for qid in required_ids)
    pct = compute_percentage(answers)
    band = band_from_percentage(pct)
    title, desc = band_copy(band)
    gaps_raw = derive_gaps(answers)
    gaps = [{"message": g["message"], "risk_note": g["risk_note"]} for g in gaps_raw]
    calendly = os.getenv("CALENDLY_URL") or DEFAULT_CALENDLY
    return {
        "percentage": pct,
        "band": band,
        "band_title": title,
        "band_description": desc,
        "weighted_points": round(weighted, 2),
        "max_points": MAX_POINTS,
        "critical_gaps": gaps,
        "recommended_steps": recommended_steps(gaps_raw),
        "calendly_url": calendly,
    }
