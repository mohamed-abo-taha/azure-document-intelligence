"""Ingest the bundled sample documents and run a small retrieval evaluation."""
from __future__ import annotations

import json
import os

from src.config import settings
from src.eval import evaluate_retrieval
from src.serve import build_service

SAMPLE_DIR = "data/sample_docs"
QRELS = "data/qrels.json"


def main():
    svc = build_service()
    for name in sorted(os.listdir(SAMPLE_DIR)):
        if name.endswith(".txt"):
            with open(os.path.join(SAMPLE_DIR, name), encoding="utf-8") as f:
                svc.ingest(name[:-4], f.read())
    print("indexed chunks:", svc.vs.count())

    qrels = json.load(open(QRELS, encoding="utf-8"))
    result = evaluate_retrieval(svc, qrels, k=settings.top_k)
    os.makedirs("results", exist_ok=True)
    json.dump(result, open("results/eval.json", "w"), indent=2)
    print("retrieval eval:", result)

    demo = qrels[0]["query"]
    print("\nQ:", demo)
    print("A:", svc.ask(demo)["answer"])


if __name__ == "__main__":
    main()
