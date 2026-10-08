from pathlib import Path 

from pypdf import PdfReader

def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))

    pages_text: list[str] = [] 

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text)

    return "\n".join(pages_text).strip()                          