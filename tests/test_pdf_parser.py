import io
import zlib

import pytest

from aap_watcher.scrapers.pdf_parser import (
    extract_pdf_text,
    has_pdf_extension,
    is_pdf_bytes,
    PDFError,
)


def _make_pdf_bytes(text: str) -> bytes:
    """Build a minimal single-page PDF embedding the given text (Helvetica).

    A stripped-down but valid PDF 1.4 document: one page, a content stream
    that draws the text, and a /Type1 Helvetica font resource so pypdf's
    extract_text can map glyphs back to characters.
    """
    escaped = text.encode("latin-1", errors="replace").decode("latin-1").replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    content = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
    stream = zlib.compress(content)
    objects = []
    objects.append(
        b"<< /Type /Catalog /Pages 2 0 R >>"
    )
    objects.append(
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    )
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> "
        b"/Contents 5 0 R >>"
    )
    objects.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    )
    objects.append(
        b"<< /Length " + str(len(stream)).encode() + b" /Filter /FlateDecode >>\nstream\n" + stream + b"\nendstream"
    )
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode()
        out += body + b"\n"
        out += b"endobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += b"trailer\n<< /Size " + str(len(objects) + 1).encode() + b" /Root 1 0 R >>\n"
    out += b"startxref\n" + str(xref_pos).encode() + b"\n%%EOF"
    return bytes(out)


def test_extract_pdf_text_roundtrip():
    data = _make_pdf_bytes("Date limite : 15 octobre 2026")
    out = extract_pdf_text(data)
    assert "2026" in out
    assert "octobre" in out


def test_extract_pdf_returns_string():
    data = _make_pdf_bytes("Page une")
    out = extract_pdf_text(data)
    assert isinstance(out, str)
    assert "Page une" in out


def test_is_pdf_bytes_sniff():
    assert is_pdf_bytes(b"%PDF-1.4")
    assert not is_pdf_bytes(b"<!DOCTYPE html>")


def test_has_pdf_extension():
    assert has_pdf_extension("https://example.org/aap.pdf")
    assert has_pdf_extension("https://example.org/aap.PDF?download=1")
    assert has_pdf_extension("https://example.org/aap.pdf#page=2")
    assert not has_pdf_extension("https://example.org/aap.html")
    assert not has_pdf_extension(None)


def test_extract_pdf_rejects_non_pdf():
    with pytest.raises(PDFError):
        extract_pdf_text(b"<html>not a pdf</html>")


def test_extract_pdf_missing_dependency_clean_error(monkeypatch):
    import aap_watcher.scrapers.pdf_parser as pdf_parser

    monkeypatch.setattr(pdf_parser, "PDF_AVAILABLE", False)
    monkeypatch.setattr(pdf_parser, "PdfReader", None)
    with pytest.raises(PDFError):
        extract_pdf_text(b"%PDF-1.4")
