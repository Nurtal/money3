"""Email notifier (Phase 5).

Sends a digest of monitored changes over SMTP using only the standard library
(``smtplib`` + ``email.mime``). Credentials come from the ``AAP_SMTP_*``
environment variables, following the project's existing ``AAP_*`` config
convention (see ``extraction/llm.py``). No new dependency is required.
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base import ChangeNotice

_DISCLAIMER = (
    "AAP Watcher est un outil d'agrégation et ne constitue pas une source "
    "faisant autorité. Vérifiez toujours éligibilité, montants, délais et "
    "procédure sur la source officielle."
)

_LABELS = {
    "new": "Nouvel appel",
    "modified": "Modifié",
    "deadline_changed": "Date limite modifiée",
    "cancelled": "Annulé",
}


def _html_escape(text: str | None) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _plain(notice: ChangeNotice) -> str:
    lines = [f"[{_LABELS.get(notice.type, notice.type)}] {notice.title or '(sans titre)'}"]
    if notice.organisation:
        lines.append(f"  Organisation : {notice.organisation}")
    if notice.deadline:
        lines.append(f"  Date limite  : {notice.deadline}")
    link = notice.application_url or notice.source_url or notice.key
    if link:
        lines.append(f"  Lien         : {link}")
    return "\n".join(lines)


def _html(notice: ChangeNotice) -> str:
    link = notice.application_url or notice.source_url or notice.key
    href = f'<a href="{_html_escape(link)}">{_html_escape(link)}</a>' if link else ""
    rows = _html_escape(notice.organisation), _html_escape(notice.deadline)
    return (
        f'<li><strong>[{_html_escape(_LABELS.get(notice.type, notice.type))}] '
        f'{_html_escape(notice.title or "(sans titre)")}</strong><br/>'
        f"Organisation : {rows[0]} &nbsp;·&nbsp; Date limite : {rows[1]}<br/>{href}</li>"
    )


def build_digest(notices: list[ChangeNotice]) -> MIMEMultipart:
    """Build a plain-text + HTML MIME entity describing the notices."""
    summary_count = len(notices)
    charset = "utf-8"
    text_parts = [f"AAP Watcher — {summary_count} changement(s) détecté(s).\n"]
    html_parts = [
        f"<html><body><h3>AAP Watcher — {summary_count} changement(s) détecté(s).</h3><ul>"
    ]
    for n in notices:
        text_parts.append(_plain(n))
        html_parts.append(_html(n))
    text_parts.append("")
    text_parts.append(_DISCLAIMER)
    html_parts.append("</ul><p>")
    html_parts.append(_html_escape(_DISCLAIMER))
    html_parts.append("</p></body></html>")

    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText("\n".join(text_parts), "plain", charset))
    msg.attach(MIMEText("".join(html_parts), "html", charset))
    return msg


class EmailNotifier:
    """Deliver change notices by email over SMTP."""

    def __init__(
        self,
        host: str,
        from_addr: str,
        to_addrs: list[str],
        port: int = 587,
        user: str | None = None,
        password: str | None = None,
        starttls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.starttls = starttls

    @classmethod
    def from_env(cls) -> EmailNotifier:
        """Build a notifier from ``AAP_SMTP_*``/``AAP_NOTIFY_TO`` env vars."""
        host = os.environ.get("AAP_SMTP_HOST")
        to = os.environ.get("AAP_NOTIFY_TO")
        if not host or not to:
            raise ValueError(
                "Email notification requires AAP_SMTP_HOST and AAP_NOTIFY_TO "
                "environment variables"
            )
        return cls(
            host=host,
            port=int(os.environ.get("AAP_SMTP_PORT", "587")),
            user=os.environ.get("AAP_SMTP_USER"),
            password=os.environ.get("AAP_SMTP_PASSWORD"),
            from_addr=os.environ.get("AAP_SMTP_FROM", "noreply@aap-watcher.local"),
            to_addrs=[a.strip() for a in to.split(",") if a.strip()],
            starttls=os.environ.get("AAP_SMTP_STARTTLS", "1") not in ("0", "false", "False"),
        )

    def send(self, notices: list[ChangeNotice]) -> None:
        if not notices:
            return
        msg = build_digest(notices)
        msg["Subject"] = f"AAP Watcher — {len(notices)} changement(s)"
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)
        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            if self.starttls:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
            if self.user and self.password:
                smtp.login(self.user, self.password)
            smtp.send_message(msg)
