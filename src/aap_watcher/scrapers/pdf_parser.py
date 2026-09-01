"""PDF text extraction helper (optional dependency).

Many AAPs are distributed as PDF attachments. This module extracts plain text
from PDF bytes so the rest of the pipeline (scrapers, extractors) can treat
them as ordinary :class:`Document` inputs.

Requires the ``pdf`` extra::

    uv pip install "aap-watcher[pdf]"

If ``pypdf`` is missing, ``extract_pdf_text`` raises a clear error rather than
silently returning garbage, and ``pdf_available`` reports availability so
callers can decide how to degrade.
"""

from __future__ import annotations

import io
from typing import Optional

try:
    from pypdf import PdfReader

    PDF_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when pypdf missing
    PdfReader = None
    PDF_AVAILABLE = False


class PDFError(RuntimeError):
    """Raised when a PDF cannot be read or is not actually a PDF."""


def has_pdf_extension(url: Optional[str]) -> bool:
    """True if ``url`` looks like a PDF (case-insensitive ``.pdf`` suffix)."""
    if not url:
        return False
    path = url.split("?", 1)[0].split("#", 1)[0]
    return path.lower().endswith(".pdf")


def is_pdf_bytes(data: bytes) -> bool:
    """Cheap header sniff: PDF files start with ``%PDF``."""
    return data[:5] == b"%PDF-"


def extract_pdf_text(data: bytes) -> str:
    """Extract concatenated text from PDF ``data``.

    Raises:
        PDFError: if the bytes are not a readable PDF, or if ``pypdf`` is not
            installed.
    """
    if not PDF_AVAILABLE:
        raise PDFError(
            "pypdf is not installed. Add the 'pdf' extra: uv pip install 'aap-watcher[pdf]'"
        )
    if not is_pdf_bytes(data):
        raise PDFError("data does not look like a PDF (missing %PDF header)")
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # pragma: no cover - pypdf raises varied parse errors
        raise PDFError(f"could not parse PDF: {exc}") from exc
    pages = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover - page-level extract errors
            raise PDFError(f"could not extract text from PDF page: {exc}") from exc
        pages.append(text)
    return "\n".join(pages).strip()
