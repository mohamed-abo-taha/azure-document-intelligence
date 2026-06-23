"""Retrieval evaluation: hit-rate@k and MRR over a small labeled set."""
from __future__ import annotations


def evaluate_retrieval(rag, qrels, k=4) -> dict:
    """qrels: list of {"query": ..., "doc_id": ...}.

    A query is a hit if its gold document appears in the top-k retrieved chunks.
    """
    hits, reciprocal_rank = 0, 0.0
    for q in qrels:
        docs = [r["doc_id"] for r in rag.search(q["query"], k)]
        if q["doc_id"] in docs:
            hits += 1
            reciprocal_rank += 1.0 / (docs.index(q["doc_id"]) + 1)
    n = len(qrels) or 1
    return {
        "n": len(qrels),
        f"hit_rate@{k}": round(hits / n, 4),
        "mrr": round(reciprocal_rank / n, 4),
    }
