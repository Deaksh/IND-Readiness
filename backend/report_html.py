"""HTML email report — table layout, inline styles for clients."""

from __future__ import annotations

import html
from typing import Any

Band = str


def band_email_theme(band: Band) -> dict[str, str]:
    themes = {
        "green": {
            "hero_bg": "#ecfdf5",
            "hero_border": "#10b981",
            "pill_bg": "#059669",
            "pill_color": "#ffffff",
            "bar_from": "#10b981",
            "bar_to": "#34d399",
            "accent_text": "#065f46",
        },
        "yellow": {
            "hero_bg": "#fffbeb",
            "hero_border": "#f59e0b",
            "pill_bg": "#d97706",
            "pill_color": "#ffffff",
            "bar_from": "#f59e0b",
            "bar_to": "#fbbf24",
            "accent_text": "#92400e",
        },
        "orange": {
            "hero_bg": "#fff7ed",
            "hero_border": "#ea580c",
            "pill_bg": "#c2410c",
            "pill_color": "#ffffff",
            "bar_from": "#ea580c",
            "bar_to": "#fb923c",
            "accent_text": "#9a3412",
        },
        "red": {
            "hero_bg": "#fff1f2",
            "hero_border": "#e11d48",
            "pill_bg": "#be123c",
            "pill_color": "#ffffff",
            "bar_from": "#e11d48",
            "bar_to": "#fb7185",
            "accent_text": "#9f1239",
        },
    }
    return themes.get(band, themes["orange"])


def build_report_html(
    answers_labeled: list[dict[str, str]],
    report: dict[str, Any],
    risk_snapshot: dict[str, Any],
) -> str:
    """
    answers_labeled: rows with question, answer_label, section, order, ...
    report: scored payload (band, percentage, band_title, band_description, gaps, steps, ...)
    risk_snapshot: deadline_summary, approx_days_in_window, estimated_remediation_hours, gap_count
    """
    pct = float(report.get("percentage", 0))
    band = str(report.get("band", "orange"))
    t = band_email_theme(band)
    band_title = html.escape(str(report.get("band_title", "")))
    band_desc = html.escape(str(report.get("band_description", "")))
    band_label = html.escape(f"{pct:.0f}% — {report.get('band_title', '')}")
    pill_text = band_title
    score_line = html.escape(
        f"Model score: {report.get('weighted_points', 0)} / {report.get('max_points', 15)} weighted points "
        f"({pct:.1f}% normalized)"
    )

    gaps: list[dict[str, str]] = report.get("critical_gaps") or []
    gaps_rows = ""
    if not gaps:
        gaps_rows = (
            '<tr><td style="padding:8px 0;font-size:14px;color:#64748b;">'
            "No automated critical gaps from your answers.</td></tr>"
        )
    else:
        for g in gaps:
            gaps_rows += (
                f'<tr><td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">'
                f'<div style="font-size:14px;font-weight:600;color:#9f1239;">✕ {html.escape(g.get("message", ""))}</div>'
                f'<div style="font-size:12px;color:#7f1d1d;margin-top:4px;">{html.escape(g.get("risk_note", ""))}</div>'
                f"</td></tr>"
            )

    steps: list[str] = report.get("recommended_steps") or []
    steps_html = ""
    for i, s in enumerate(steps, 1):
        steps_html += (
            f'<tr><td style="padding:6px 0;font-size:14px;color:#0f172a;">'
            f'<strong style="color:#64748b;">{i}.</strong> {html.escape(s)}</td></tr>'
        )

    qa_rows = ""
    for row in sorted(answers_labeled, key=lambda r: int(r.get("order", "0"))):
        q = html.escape(row.get("question", ""))
        a = html.escape(row.get("answer_label", ""))
        sec = html.escape(row.get("section", ""))
        qa_rows += (
            f'<tr>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;font-size:13px;color:#64748b;width:28%;">{sec}</td>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;font-size:13px;color:#0f172a;">{q}</td>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;font-size:13px;font-weight:600;color:#1d4ed8;">{a}</td>'
            f"</tr>"
        )

    days = risk_snapshot.get("approx_days_in_window")
    days_str = (
        f"~{int(days)} days (mid-window heuristic)"
        if days is not None
        else "Not applicable (18+ mo / unspecified)"
    )
    deadline = html.escape(str(risk_snapshot.get("deadline_summary", "—")))
    hours = risk_snapshot.get("estimated_remediation_hours", "—")

    # Gradient bar using table + inner td width
    bar_w = max(0, min(100, int(round(pct))))

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width" /></head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f1f5f9;padding:24px 12px;">
<tr><td align="center">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">

<!-- Hero -->
<tr><td style="background-color:{t["hero_bg"]};border-left:4px solid {t["hero_border"]};padding:24px 28px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr>
<td style="vertical-align:middle;">
<div style="font-size:12px;font-weight:600;letter-spacing:0.08em;color:{t["accent_text"]};text-transform:uppercase;">Your IND readiness</div>
<div style="font-size:36px;font-weight:700;color:#0f172a;line-height:1.1;margin-top:6px;">{pct:.0f}%</div>
<div style="font-size:13px;color:#64748b;margin-top:4px;">{band_label}</div>
</td>
<td align="right" style="vertical-align:middle;">
<span style="display:inline-block;background:{t["pill_bg"]};color:{t["pill_color"]};font-size:12px;font-weight:700;padding:8px 14px;border-radius:999px;">{pill_text}</span>
</td>
</tr></table>
<p style="margin:16px 0 0;font-size:15px;line-height:1.5;color:{t["accent_text"]};">{band_desc}</p>
<!-- Progress bar -->
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:18px;">
<tr><td style="height:10px;background:#e2e8f0;border-radius:6px;overflow:hidden;">
<table role="presentation" width="{bar_w}%" cellspacing="0" cellpadding="0"><tr>
<td style="height:10px;background:linear-gradient(90deg,{t["bar_from"]},{t["bar_to"]});border-radius:6px;font-size:0;line-height:0;">&nbsp;</td>
</tr></table></td></tr></table>
<p style="margin:12px 0 0;font-size:12px;color:#64748b;">{score_line}</p>
</td></tr>

<!-- Two columns: gaps | risk -->
<tr><td style="padding:20px 24px 8px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr>
<td width="50%" valign="top" style="padding-right:12px;">
<div style="font-size:11px;font-weight:700;letter-spacing:0.06em;color:#64748b;text-transform:uppercase;">Critical gaps</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:8px;">{gaps_rows}</table>
</td>
<td width="50%" valign="top" style="padding-left:12px;border-left:1px solid #e2e8f0;">
<div style="font-size:11px;font-weight:700;letter-spacing:0.06em;color:#64748b;text-transform:uppercase;">Risk snapshot</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:8px;">
<tr><td style="padding:6px 0;font-size:13px;color:#64748b;">Deadline / window</td></tr>
<tr><td style="padding:0 0 10px;font-size:14px;font-weight:600;color:#0f172a;">{deadline}</td></tr>
<tr><td style="padding:6px 0;font-size:13px;color:#64748b;">Days (heuristic)</td></tr>
<tr><td style="padding:0 0 10px;font-size:14px;font-weight:600;color:#0f172a;">{html.escape(days_str)}</td></tr>
<tr><td style="padding:6px 0;font-size:13px;color:#64748b;">Est. remediation effort</td></tr>
<tr><td style="padding:0;font-size:14px;font-weight:600;color:#0f172a;">{html.escape(str(hours))} hours (rough order of magnitude)</td></tr>
</table>
</td>
</tr></table>
</td></tr>

<!-- Next steps -->
<tr><td style="padding:8px 24px 20px;">
<div style="font-size:11px;font-weight:700;letter-spacing:0.06em;color:#64748b;text-transform:uppercase;">Recommended next steps</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:8px;">{steps_html}</table>
</td></tr>

<!-- Q&A -->
<tr><td style="padding:8px 24px 28px;">
<div style="font-size:11px;font-weight:700;letter-spacing:0.06em;color:#64748b;text-transform:uppercase;">Your responses</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:8px;border-collapse:collapse;">
<tr style="background:#f8fafc;">
<th align="left" style="padding:8px;font-size:11px;color:#64748b;text-transform:uppercase;">Section</th>
<th align="left" style="padding:8px;font-size:11px;color:#64748b;text-transform:uppercase;">Question</th>
<th align="left" style="padding:8px;font-size:11px;color:#64748b;text-transform:uppercase;">Answer</th>
</tr>
{qa_rows}
</table>
</td></tr>

<tr><td style="padding:16px 24px 24px;font-size:11px;color:#94a3b8;text-align:center;border-top:1px solid #e2e8f0;">
Beacon IND Readiness Assessment · Planning aid only, not legal or regulatory advice.
</td></tr>
</table>
</td></tr></table>
</body></html>"""
