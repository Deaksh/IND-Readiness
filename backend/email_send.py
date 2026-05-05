"""Transactional email via Brevo (HTTPS), Resend, or SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

USER_AGENT = "BeaconIND-Readiness/1.0"


def send_assessment_report_email(to_email: str, subject: str, html_body: str) -> None:
    settings = get_settings()
    from_addr = settings["email_from"]
    from_name = settings["email_from_name"] or "Beacon"

    if not from_addr:
        logger.warning("EMAIL_FROM not set; skipping send to %s", to_email)
        return

    if settings["brevo_api_key"]:
        _send_brevo(settings["brevo_api_key"], from_addr, from_name, to_email, subject, html_body)
        return
    if settings["resend_api_key"]:
        _send_resend(
            settings["resend_api_key"], from_addr, from_name, to_email, subject, html_body
        )
        return
    if settings["smtp_host"] and settings["smtp_user"] and settings["smtp_password"]:
        _send_smtp(settings, from_addr, to_email, subject, html_body)
        return

    logger.warning("No email provider configured (BREVO_API_KEY, RESEND_API_KEY, or SMTP_*); skip send")


def _send_brevo(
    api_key: str,
    from_email: str,
    from_name: str,
    to: str,
    subject: str,
    html: str,
) -> None:
    payload: dict[str, Any] = {
        "sender": {"email": from_email, "name": from_name},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "User-Agent": USER_AGENT,
            },
            json=payload,
        )
        r.raise_for_status()
    logger.info("Brevo email sent to %s", to)


def _send_resend(
    api_key: str,
    from_email: str,
    from_name: str,
    to: str,
    subject: str,
    html: str,
) -> None:
    payload = {
        "from": f"{from_name} <{from_email}>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": USER_AGENT,
            },
            json=payload,
        )
        r.raise_for_status()
    logger.info("Resend email sent to %s", to)


def _send_smtp(
    settings: dict[str, str | None],
    from_email: str,
    to: str,
    subject: str,
    html: str,
) -> None:
    host = settings["smtp_host"]
    port = int(settings["smtp_port"] or "587")
    user = settings["smtp_user"]
    password = settings["smtp_password"]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(str(user), str(password))
        server.sendmail(from_email, [to], msg.as_string())
    logger.info("SMTP email sent to %s", to)
