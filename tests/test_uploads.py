from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app

client = TestClient(app)


def create_test_pdf() -> bytes:
    pdf_stream = BytesIO()

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(pdf_stream)

    return pdf_stream.getvalue()


def test_reject_non_pdf_upload():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "notes.txt",
                b"hello world",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert response.json() == {
        "detail": "Only PDF files are supported."
    }


def test_reject_pdf_without_extractable_text():
    pdf_bytes = create_test_pdf()

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "blank.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "No extractable text was found in the PDF."
    }
