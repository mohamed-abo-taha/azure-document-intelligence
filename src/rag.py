"""RAG orchestration: ingest documents, retrieve, answer, capture feedback."""
from __future__ import annotations

from .chunking import chunk_text


class RagService:
    def __init__(self, vectorstore, answerer, docstore, feedback, top_k=4):
        self.vs = vectorstore
        self.answerer = answerer
        self.docs = docstore
        self.fb = feedback
        self.top_k = top_k

    def ingest(self, doc_id, text):
        self.docs.put(doc_id, text)
        chunks = chunk_text(doc_id, text)
        self.vs.add(chunks)
        return {"doc_id": doc_id, "chunks": len(chunks)}

    def search(self, query, k=None):
        hits = self.vs.search(query, k or self.top_k)
        return [
            {"doc_id": h.chunk.doc_id, "chunk_id": h.chunk.id,
             "score": round(h.score, 4), "text": h.chunk.text}
            for h in hits
        ]

    def ask(self, query, k=None):
        hits = self.vs.search(query, k or self.top_k)
        out = self.answerer.answer(query, hits)
        out["retrieved"] = [
            {"doc_id": h.chunk.doc_id, "chunk_id": h.chunk.id, "score": round(h.score, 4)}
            for h in hits
        ]
        return out

    def record_feedback(self, item):
        return self.fb.record(item)
