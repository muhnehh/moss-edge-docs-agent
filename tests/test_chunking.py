from moss_integration.moss_indexer import ChunkConfig, chunk_text


def test_chunk_text_splits_long_content() -> None:
    text = (
        "Sentence one about Moss retrieval performance. "
        "Sentence two about local indexing and updates. "
        "Sentence three about low-latency voice experiences. "
        "Sentence four about reranking for better context precision. "
    )

    chunks = chunk_text(text, ChunkConfig(max_chars=90, min_chars=20))

    assert len(chunks) >= 2
    assert all(len(chunk) >= 20 for chunk in chunks)


def test_chunk_text_filters_short_noise() -> None:
    text = "Tiny. Small. Mini."
    chunks = chunk_text(text, ChunkConfig(max_chars=80, min_chars=30))
    assert chunks == []
