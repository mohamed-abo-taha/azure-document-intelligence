"""Split documents into overlapping word-window chunks."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    id: str
    doc_id: str
    text: str
    metadata: dict = field(default_factory=dict)


def chunk_text(doc_id: str, text: str, size: int = 120, overlap: int = 30) -> list[Chunk]:
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks = []
    i = n = 0
    while i < len(words):
        piece = " ".join(words[i : i + size])
        chunks.append(Chunk(id=f"{doc_id}::{n}", doc_id=doc_id, text=piece, metadata={"start": i}))
        i += step
        n += 1
    return chunks
