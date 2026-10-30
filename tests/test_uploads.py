from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app
from app.schemas.chunk import DocumentChunk

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


def test_upload_document_with_project_id(monkeypatch):
    stored_data = {}

    def fake_extract_text(file_path):
        return "This is test document content."

    def fake_process_document_text(extracted_text):
        chunks = [
            DocumentChunk(
                chunk_index=0,
                text=extracted_text,
                start_char=0,
                end_char=len(extracted_text),
            )
        ]
        embeddings = [[0.1] * 384]

        return chunks, embeddings

    def fake_store_document_chunks(
        document_id,
        chunks,
        embeddings,
        project_id=None,
    ):
        stored_data["document_id"] = document_id
        stored_data["project_id"] = project_id
        stored_data["chunks"] = chunks

    monkeypatch.setattr(
        "app.api.documents.extract_text_from_pdf",
        fake_extract_text,
    )
    monkeypatch.setattr(
        "app.api.documents.process_document_text",
        fake_process_document_text,
    )
    monkeypatch.setattr(
        "app.api.documents.vector_store.store_document_chunks",
        fake_store_document_chunks,
    )

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "test.pdf",
                create_test_pdf(),
                "application/pdf",
            )
        },
        data={
            "project_id": "project-a",
        },
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "test.pdf"
    assert stored_data["project_id"] == "project-a"
    assert len(stored_data["chunks"]) == 1
