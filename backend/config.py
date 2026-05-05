"""Application settings loaded from environment (.env via load_dotenv in main)."""

from __future__ import annotations

import os
from functools import lru_cache


@lru_cache
def get_settings() -> dict[str, str | None]:
    """Return settings dict; values may be None if unset."""
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./submissions.db"),
        "admin_api_key": (os.getenv("ADMIN_API_KEY") or "").strip() or None,
        "admin_password": (os.getenv("ADMIN_PASSWORD") or "").strip() or None,
        "admin_email": (os.getenv("ADMIN_EMAIL") or "").strip() or None,
        "admin_jwt_secret": (os.getenv("ADMIN_JWT_SECRET") or "").strip() or None,
        # Email — Brevo (HTTPS API)
        "brevo_api_key": (os.getenv("BREVO_API_KEY") or os.getenv("SENDINBLUE_API_KEY") or "").strip() or None,
        "email_from": (os.getenv("EMAIL_FROM") or "").strip() or None,
        "email_from_name": (os.getenv("EMAIL_FROM_NAME") or "Beacon IND Readiness").strip(),
        # Resend alternative
        "resend_api_key": (os.getenv("RESEND_API_KEY") or "").strip() or None,
        # SMTP fallback (optional)
        "smtp_host": (os.getenv("SMTP_HOST") or "").strip() or None,
        "smtp_port": os.getenv("SMTP_PORT", "587"),
        "smtp_user": (os.getenv("SMTP_USER") or "").strip() or None,
        "smtp_password": (os.getenv("SMTP_PASSWORD") or "").strip() or None,
    }


def admin_jwt_signing_secret() -> str:
    s = get_settings()
    j = s["admin_jwt_secret"]
    if j:
        return j
    k = s["admin_api_key"]
    if k:
        return k
    return "dev-insecure-change-me"
