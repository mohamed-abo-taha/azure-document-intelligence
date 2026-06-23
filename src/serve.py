"""FastAPI service for document Q&A.

Each component (retrieval, answering, document store, feedback) is selected by
config, so the same app runs fully locally or fully on Azure.
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .answer import get_answerer
from .config import settings
from .docstore import get_docstore
from .feedback import get_feedbackstore
from .rag import RagService
from .vectorstore import get_vectorstore


def build_service() -> RagService:
    return RagService(
        get_vectorstore(settings),
        get_answerer(settings),
        get_docstore(settings),
        get_feedbackstore(settings),
        settings.top_k,
    )


app = FastAPI(title="Document intelligence (RAG)", version="1.0")
_svc = None


def svc() -> RagService:
    global _svc
    if _svc is None:
        _svc = build_service()
    return _svc


class IngestRequest(BaseModel):
    doc_id: str
    text: str


class QueryRequest(BaseModel):
    query: str
    k: int | None = None


class FeedbackRequest(BaseModel):
    query: str
    answer: str
    rating: int
    doc_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "indexed_chunks": svc().vs.count(),
            "backends": {"vector": settings.vector_backend, "answer": settings.answer_backend,
                         "docs": settings.doc_backend, "feedback": settings.feedback_backend}}


@app.post("/ingest")
def ingest(req: IngestRequest):
    return svc().ingest(req.doc_id, req.text)


@app.post("/search")
def search(req: QueryRequest):
    return {"results": svc().search(req.query, req.k)}


@app.post("/ask")
def ask(req: QueryRequest):
    return svc().ask(req.query, req.k)


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    return svc().record_feedback(req.model_dump())
