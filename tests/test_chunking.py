from src.chunking import chunk_text


def test_overlap_and_count():
    text = " ".join(f"w{i}" for i in range(250))
    chunks = chunk_text("d", text, size=120, overlap=30)
    assert len(chunks) >= 2
    assert all(c.doc_id == "d" for c in chunks)
    assert chunks[0].id == "d::0"


def test_empty_text():
    assert chunk_text("d", "") == []
