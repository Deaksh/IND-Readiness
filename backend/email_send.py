"""Transactional email via Brevo (HTTPS), Resend, or SMTP."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

USER_AGENT = "BeaconIND-Readiness/1.0"


@dataclass
class EmailSendResult:
    status: str  # sent | skipped_no_from | skipped_no_provider | failed
    detail: str | None = None


def send_assessment_report_email(
    to_email: str, subject: str, html_body: str
) -> EmailSendResult:
    settings = get_settings()
    from_addr = settings["email_from"]
    from_name = settings["email_from_name"] or "Beacon"

    if not from_addr:
        logger.warning("EMAIL_FROM not set; skipping send to %s", to_email)
        return EmailSendResult(
            "skipped_no_from",
            "Set EMAIL_FROM in backend/.env to the sender address your provider allows.",
        )

    provider = settings["email_provider"] or "auto"
    brevo_key = settings["brevo_api_key"]
    resend_key = settings["resend_api_key"]
    smtp_ready = bool(
        settings["smtp_host"] and settings["smtp_user"] and settings["smtp_password"]
    )

    def try_brevo() -> None:
        if not brevo_key:
            raise RuntimeError("Brevo API key not configured")
        _send_brevo(brevo_key, from_addr, from_name, to_email, subject, html_body)

    def try_resend() -> None:
        if not resend_key:
            raise RuntimeError("Resend API key not configured")
        _send_resend(resend_key, from_addr, from_name, to_email, subject, html_body)

    def try_smtp() -> None:
        if not smtp_ready:
            raise RuntimeError("SMTP not fully configured")
        _send_smtp(settings, from_addr, to_email, subject, html_body)

    attempts: list[tuple[str, Any]] = []

    if provider == "smtp":
        attempts = [("smtp", try_smtp)]
    elif provider == "brevo":
        attempts = [("brevo", try_brevo)]
    elif provider == "resend":
        attempts = [("resend", try_resend)]
    else:
        # auto: HTTP APIs first (legacy), then SMTP — or SMTP first if you only use SMTP
        # Prefer SMTP when explicitly configured and no API keys, else API-first.
        if smtp_ready and not brevo_key and not resend_key:
            attempts = [("smtp", try_smtp)]
        else:
            if brevo_key:
                attempts.append(("brevo", try_brevo))
            if resend_key:
                attempts.append(("resend", try_resend))
            if smtp_ready:
                attempts.append(("smtp", try_smtp))

    if not attempts:
        logger.warning("No email provider configured; skip send to %s", to_email)
        return EmailSendResult(
            "skipped_no_provider",
            "Configure BREVO_API_KEY, RESEND_API_KEY, or SMTP_* (and EMAIL_FROM), "
            "or set EMAIL_PROVIDER=smtp with full SMTP_*.",
        )

    last_err: str | None = None
    for name, fn in attempts:
        try:
            fn()
            logger.info("Assessment report email sent via %s to %s", name, to_email)
            return EmailSendResult("sent", name)
        except Exception as e:
            last_err = f"{name}: {e}"
            logger.warning("Email via %s failed: %s", name, e)

    return EmailSendResult(
        "failed",
        last_err or "All configured providers failed. Check SMTP_USE_SSL/port 465 vs 587, "
        "firewall, and that EMAIL_FROM matches your mailbox.",
    )


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


def _send_smtp(
    settings: dict[str, Any],
    from_email: str,
    to: str,
    subject: str,
    html: str,
) -> None:
    host = str(settings["smtp_host"])
    port = int(settings["smtp_port"] or "587")
    user = str(settings["smtp_user"])
    password = str(settings["smtp_password"])
    use_ssl = bool(settings.get("smtp_use_ssl")) or port == 465

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to
    msg.set_content(html, subtype="html", charset="utf-8")

    def _login_and_send(sock: smtplib.SMTP | smtplib.SMTP_SSL) -> None:
        try:
            sock.login(user, password)
        except smtplib.SMTPAuthenticationError as e:
            hint = _smtp_auth_hint(host, e)
            raise RuntimeError(hint) from e

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=45) as server:
            _login_and_send(server)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=45) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            _login_and_send(server)
            server.send_message(msg)


def _smtp_auth_hint(host: str, err: smtplib.SMTPAuthenticationError) -> str:
    base = f"SMTP authentication failed: {err!s}."
    h = host.lower()
    if "brevo" in h or "sendinblue" in h:
        return (
            f"{base} For Brevo relay (smtp-relay.brevo.com): SMTP_USER must be the email "
            "you use to log in to Brevo (your Brevo account email), and SMTP_PASSWORD must be "
            "the SMTP key from Brevo → Settings → SMTP & API → generate/copy key — "
            "not your Gmail password. Sender (EMAIL_FROM / SMTP_FROM) must be a domain/email "
            "you have verified under Senders in Brevo."
        )
    return (
        f"{base} Check SMTP_USER / SMTP_PASSWORD, and that the From address is allowed by your provider."
    )
