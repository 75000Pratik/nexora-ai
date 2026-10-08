from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_create_document():
    response = client.post(
        "/documents",
        json={
            "filename": "employee-handbook.pdf",
            "content_type": "application/pdf",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "employee-handbook.pdf"
    assert data["content_type"] == "application/pdf"
    assert data["status"] == "uploaded"
    assert "id" in data

def test_create_document_with_empty_filename():
    response = client.post(
        "/documents",
        json={
            "filename": "",
            "content_type": "application/pdf",
        },
    )

    assert response.status_code == 422    