from pathlib import Path

from pypdf import PdfReader


MAX_PDF_PAGES = 100


class PDFPageLimitExceededError(ValueError):
    """Raised when a PDF exceeds the allowed page count."""


def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))

    if len(reader.pages) > MAX_PDF_PAGES:
        raise PDFPageLimitExceededError(
            f"PDF cannot contain more than {MAX_PDF_PAGES} pages."
        )

    pages_text: list[str] = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text)

    return "\n".join(pages_text).strip()
