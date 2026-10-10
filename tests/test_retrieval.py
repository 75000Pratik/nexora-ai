from app.schemas.retrieval import RetrievalResult

def test_retrieval_result_schema():
    result = RetrievalResult(
        document_id="123e4567-e89b-12d3-a456-426614174000",
        chunk_index=2,
        text="AWS experience with EC2 and S3.",
        score=0.75,
        start_char=100,
        end_char=130,
    )

    assert result.document_id == "123e4567-e89b-12d3-a456-426614174000"
    assert result.chunk_index == 2
    assert result.text == "AWS experience with EC2 and S3."
    assert result.score == 0.75
    assert result.start_char == 100
    assert result.end_char == 130