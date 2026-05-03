"""Beacon IND Readiness Assessment — question bank, scoring, and gap analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Band = Literal["green", "yellow", "orange", "red"]


@dataclass(frozen=True)
class Option:
    id: str
    label: str
    points: float  # 0, 0.5, or 1.0 toward max 15


@dataclass(frozen=True)
class Question:
    id: str
    section: str
    order: int
    text: str
    options: tuple[Option, ...]


QUESTIONS: tuple[Question, ...] = (
    Question(
        id="q1",
        section="Analytical Data",
        order=1,
        text="Do you have HPLC purity data for your drug substance?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("in_progress", "In Progress", 0.5),
            Option("no", "No", 0.0),
        ),
    ),
    Question(
        id="q2",
        section="Analytical Data",
        order=2,
        text="Is your analytical data stored in a tamper-proof system?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
            Option("dont_know", "Don't Know", 0.0),
        ),
    ),
    Question(
        id="q3",
        section="Analytical Data",
        order=3,
        text="Have you validated your analytical methods per ICH Q2(R2)?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("partial", "Partial", 0.5),
            Option("no", "No", 0.0),
        ),
    ),
    Question(
        id="q4",
        section="Analytical Data",
        order=4,
        text="Do you have complete audit trails for data transformations?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
            Option("dont_know", "Don't Know", 0.0),
        ),
    ),
    Question(
        id="q5",
        section="Analytical Data",
        order=5,
        text="Can you generate an audit package in under 1 hour?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
        ),
    ),
    Question(
        id="q6",
        section="CMC Documentation",
        order=6,
        text="Have you drafted ICH M4Q Section 3.2.S (Drug Substance)?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("partial", "Partial", 0.5),
            Option("no", "No", 0.0),
        ),
    ),
    Question(
        id="q7",
        section="CMC Documentation",
        order=7,
        text="Are your CMC sections version-controlled?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
        ),
    ),
    Question(
        id="q8",
        section="CMC Documentation",
        order=8,
        text="Have you linked analytical data to CMC sections?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
            Option("dont_know", "Don't Know", 0.0),
        ),
    ),
    Question(
        id="q9",
        section="CMC Documentation",
        order=9,
        text="Is your CMC documentation eCTD-ready?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
            Option("dont_know", "Don't Know", 0.0),
        ),
    ),
    Question(
        id="q10",
        section="CMC Documentation",
        order=10,
        text="Have you had a pre-IND meeting with FDA?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
            Option("scheduled", "Scheduled", 0.5),
        ),
    ),
    Question(
        id="q11",
        section="Regulatory Strategy",
        order=11,
        text="Have you mapped your therapeutic to ICH/FDA requirements?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("partial", "Partial", 0.5),
            Option("no", "No", 0.0),
        ),
    ),
    Question(
        id="q12",
        section="Regulatory Strategy",
        order=12,
        text="Do you have a regulatory consultant or in-house RA team?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
        ),
    ),
    Question(
        id="q13",
        section="Regulatory Strategy",
        order=13,
        text="How many months until IND submission?",
        options=(
            Option("0_6", "0–6", 1.0),
            Option("6_12", "6–12", 1.0),
            Option("12_18", "12–18", 0.5),
            Option("18_plus", "18+", 0.0),
        ),
    ),
    Question(
        id="q14",
        section="Regulatory Strategy",
        order=14,
        text="Have you identified all missing evidence?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
            Option("dont_know", "Don't Know", 0.0),
        ),
    ),
    Question(
        id="q15",
        section="Regulatory Strategy",
        order=15,
        text="Do you have a risk mitigation plan for regulatory blockers?",
        options=(
            Option("yes", "Yes", 1.0),
            Option("no", "No", 0.0),
        ),
    ),
)

QUESTION_BY_ID = {q.id: q for q in QUESTIONS}
MAX_POINTS = float(len(QUESTIONS))


def points_for_answer(question_id: str, option_id: str) -> float:
    q = QUESTION_BY_ID.get(question_id)
    if not q:
        return 0.0
    for opt in q.options:
        if opt.id == option_id:
            return opt.points
    return 0.0


def compute_percentage(answers: dict[str, str]) -> float:
    total = sum(points_for_answer(qid, answers.get(qid, "")) for qid in QUESTION_BY_ID)
    return round(100.0 * total / MAX_POINTS, 1)


def band_from_percentage(pct: float) -> Band:
    if pct >= 90:
        return "green"
    if pct >= 70:
        return "yellow"
    if pct >= 50:
        return "orange"
    return "red"


def band_copy(band: Band) -> tuple[str, str]:
    labels = {
        "green": ("Ready to submit", "90%+ readiness — strong IND foundation."),
        "yellow": ("Close but gaps remain", "70–90% readiness — address gaps before filing."),
        "orange": ("Significant work needed", "50–70% readiness — prioritize critical path items."),
        "red": ("High risk of clinical hold", "<50% readiness — remediate before IND submission."),
    }
    return labels[band]


@dataclass(frozen=True)
class GapRule:
    question_id: str
    trigger_options: frozenset[str]
    message: str
    risk_note: str


GAP_RULES: tuple[GapRule, ...] = (
    GapRule(
        "q2",
        frozenset({"no", "dont_know"}),
        "Analytical data not in a tamper-proof system",
        "21 CFR Part 11 / ALCOA+ risk",
    ),
    GapRule(
        "q4",
        frozenset({"no", "dont_know"}),
        "No audit trail for data transformations",
        "Data integrity concern",
    ),
    GapRule(
        "q5",
        frozenset({"no"}),
        "Cannot produce an audit package quickly",
        "Inspection readiness gap",
    ),
    GapRule(
        "q7",
        frozenset({"no"}),
        "CMC sections not version-controlled",
        "FDA will ask about change history",
    ),
    GapRule(
        "q8",
        frozenset({"no", "dont_know"}),
        "Analytical data not linked to CMC narratives",
        "Traceability gap for reviewers",
    ),
    GapRule(
        "q9",
        frozenset({"no", "dont_know"}),
        "CMC documentation not eCTD-ready",
        "Submission formatting / structure risk",
    ),
    GapRule(
        "q10",
        frozenset({"no"}),
        "No pre-IND meeting with FDA",
        "Alignment risk with agency expectations",
    ),
    GapRule(
        "q14",
        frozenset({"no", "dont_know"}),
        "Missing evidence not fully identified",
        "Undefined filing risk",
    ),
    GapRule(
        "q15",
        frozenset({"no"}),
        "No risk mitigation plan for regulatory blockers",
        "Program-level regulatory risk",
    ),
)


def derive_gaps(answers: dict[str, str]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    seen_msg: set[str] = set()
    for rule in GAP_RULES:
        choice = answers.get(rule.question_id, "")
        if choice in rule.trigger_options:
            if rule.message not in seen_msg:
                seen_msg.add(rule.message)
                gaps.append(
                    {
                        "message": rule.message,
                        "risk_note": rule.risk_note,
                    }
                )
    return gaps


# Recommended steps keyed by gap message substring or generic order
STEP_LIBRARY: tuple[str, ...] = (
    "Implement content-addressed storage and controlled access for analytical raw data",
    "Stand up CMC version control (change logs, approval workflow, baselines for IND)",
    "Create an audit package template tied to study phases and data transformations",
    "Map remaining CMC gaps to ICH M4Q 3.2.S / 3.2.P and assign owners and dates",
    "Schedule a pre-IND or written response path to align on CMC and clinical pharmacology",
)


def recommended_steps(gaps: list[dict[str, str]]) -> list[str]:
    steps: list[str] = []
    blob = " ".join(g["message"].lower() for g in gaps)
    if "tamper-proof" in blob:
        steps.append(STEP_LIBRARY[0])
    if "version-controlled" in blob or "version control" in blob:
        steps.append(STEP_LIBRARY[1])
    if "audit trail" in blob or "audit package" in blob:
        steps.append(STEP_LIBRARY[2])
    if "ectd-ready" in blob or "linked analytical" in blob:
        steps.append(STEP_LIBRARY[3])
    if "pre-ind meeting" in blob:
        steps.append(STEP_LIBRARY[4])
    for s in STEP_LIBRARY:
        if s not in steps:
            steps.append(s)
        if len(steps) >= 5:
            break
    return steps[:5]
