from notes_search.adapters.word_chunker import WordChunker


def _chunker(chunk_size=512, overlap=50):
    return WordChunker(chunk_size=chunk_size, chunk_overlap=overlap)


def test_empty_text_returns_no_chunks():
    assert _chunker().chunk("") == []


def test_short_text_fits_in_one_chunk():
    text = " ".join(["word"] * 10)
    chunks = _chunker().chunk(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_text_exactly_chunk_size_produces_tail_chunk():
    # step = chunk_size - overlap = 462, so range(0, 512, 462) = [0, 462]
    # → chunk 0 (512 tokens) + chunk 1 (50-token overlap tail)
    text = " ".join([f"w{i}" for i in range(512)])
    chunks = _chunker().chunk(text)
    assert len(chunks) == 2
    assert len(chunks[1].split()) == 50


def test_long_text_produces_multiple_chunks():
    text = " ".join([f"w{i}" for i in range(1000)])
    chunks = _chunker().chunk(text)
    assert len(chunks) > 1


def test_overlap_means_chunks_share_tokens():
    words = [f"w{i}" for i in range(600)]
    text = " ".join(words)
    chunks = _chunker().chunk(text)
    assert len(chunks) == 2
    first_chunk_words = chunks[0].split()
    second_chunk_words = chunks[1].split()
    assert first_chunk_words[-50:] == second_chunk_words[:50]


def test_each_chunk_has_at_most_chunk_size_tokens():
    text = " ".join([f"w{i}" for i in range(2000)])
    chunks = _chunker().chunk(text)
    for chunk in chunks:
        assert len(chunk.split()) <= 512
