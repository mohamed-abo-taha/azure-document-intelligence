from src.answer import ExtractiveAnswerer
from src.docstore import LocalDocStore
from src.feedback import LocalFeedbackStore
from src.rag import RagService
from src.vectorstore import LocalVectorStore


def _service(tmp_path):
    return RagService(
        LocalVectorStore(),
        ExtractiveAnswerer(),
        LocalDocStore(str(tmp_path / "docs")),
        LocalFeedbackStore(str(tmp_path / "fb.jsonl")),
        top_k=3,
    )


def test_ingest_and_ask_is_grounded(tmp_path):
    svc = _service(tmp_path)
    svc.ingest("d1", "Azure Container Apps can scale to zero when there is no traffic. KEDA provides the scaling rules.")
    svc.ingest("d2", "Transformers use self-attention to weigh tokens in a sequence.")
    out = svc.ask("What scales to zero when there is no traffic?")
    assert out["answer"]
    assert any(c["doc_id"] == "d1" for c in out["citations"])
    assert out["retrieved"][0]["doc_id"] == "d1"


def test_feedback_roundtrip(tmp_path):
    svc = _service(tmp_path)
    rec = svc.record_feedback({"query": "q", "answer": "a", "rating": 1, "doc_id": "d1"})
    assert rec["id"]
    assert svc.fb.recent(5)
