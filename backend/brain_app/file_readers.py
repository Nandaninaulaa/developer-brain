"""
Reads raw text out of a file on disk, regardless of type.
PDF extraction uses pypdf; everything else is read as plain text.
"""
from pathlib import Path


def read_file_text(path: Path) -> str:
    if path.suffix == ".pdf":
        return _read_pdf(path)
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ImportError("pypdf is required to ingest PDFs — pip install pypdf") from e

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages)
