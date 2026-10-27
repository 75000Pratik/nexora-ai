import pytest

from app.services.chunking_service import chunk_text
from app.services.text_service import normalize_text


def test_normalize_text():
    text = "Hello    world\r\n\r\n\r\nThis    is Nexora."

    result = normalize_text(text)

    assert result == "Hello world\n\nThis is Nexora."


def test_chunk_text_without_overlap():
    text = "abcdefghij"

    chunks = chunk_text(
        text,
        chunk_size=5,
        overlap=0,
    )

    assert len(chunks) == 2

    assert chunks[0].text == "abcde"
    assert chunks[1].text == "fghij"


def test_chunk_with_overlap():
    text = "abcdefghij"

    chunks = chunk_text(
        text,
        chunk_size=6,
        overlap=2,
    )

    assert len(chunks) == 2

    assert chunks[0].text == "abcdef"
    assert chunks[1].text == "efghij"

    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 6

    assert chunks[1].start_char == 4
    assert chunks[1].end_char == 10


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            "hello world",
            chunk_size=5,
            overlap=5,
        )


def test_chunk_text_prefers_paragraph_boundary():
    text = "First paragraph.\n\nSecond paragraph."

    chunks = chunk_text(
        text,
        chunk_size=20,
        overlap=0,
    )

    assert chunks[0].text == "First paragraph."
    assert chunks[1].text == "Second paragraph."
