"""PDF text extraction helpers for Agent A."""
from __future__ import annotations

from pathlib import Path
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract visible text from a PDF using PyMuPDF.

    Raises a clear error if the file is missing or unreadable instead of failing
    later with an obscure stack trace.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"SRS PDF not found: {path}. Put your PDF in data/uploaded_srs.pdf or pass the PDF path to the CLI.")

    try:
        with fitz.open(str(path)) as doc:
            return "\n".join(page.get_text("text") for page in doc)
    except Exception as exc:  # pragma: no cover - defensive message only
        raise RuntimeError(f"Unable to read PDF {path}: {exc}") from exc
