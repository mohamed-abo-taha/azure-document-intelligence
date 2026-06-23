"""Answer generation: a local extractive answerer and an Azure OpenAI answerer."""
from __future__ import annotations

import re


class ExtractiveAnswerer:
    """Pick the sentences from retrieved chunks that overlap the query, with
    citations. No LLM — a transparent baseline grounded strictly in the sources.
    """

    def answer(self, query, hits):
        if not hits:
            return {"answer": "No relevant information was found in the indexed documents.", "citations": []}
        q_terms = set(re.findall(r"[a-z]{3,}", query.lower()))
        scored = []
        for h in hits:
            for sentence in re.split(r"(?<=[.!?])\s+", h.chunk.text):
                terms = set(re.findall(r"[a-z]{3,}", sentence.lower()))
                overlap = len(q_terms & terms)
                if overlap:
                    scored.append((overlap, sentence.strip(), h.chunk))
        scored.sort(key=lambda x: -x[0])
        top = scored[:3] if scored else [(0, hits[0].chunk.text[:300], hits[0].chunk)]
        answer = " ".join(s for _, s, _ in top)
        seen, citations = set(), []
        for _, _, c in top:
            key = (c.doc_id, c.id)
            if key not in seen:
                seen.add(key)
                citations.append({"doc_id": c.doc_id, "chunk_id": c.id})
        return {"answer": answer, "citations": citations}


class AzureOpenAIAnswerer:
    """Grounded RAG answer via Azure OpenAI chat completions."""

    def __init__(self, settings):
        from openai import AzureOpenAI

        self.client = AzureOpenAI(
            azure_endpoint=settings.aoai_endpoint, api_key=settings.aoai_key, api_version="2024-06-01"
        )
        self.deployment = settings.aoai_chat_deploy

    def answer(self, query, hits):
        context = "\n\n".join(f"[{i + 1}] {h.chunk.text}" for i, h in enumerate(hits))
        messages = [
            {"role": "system", "content": "Answer using ONLY the numbered sources. Cite them as [n]. "
                                           "If the answer is not in the sources, say so."},
            {"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {query}"},
        ]
        resp = self.client.chat.completions.create(model=self.deployment, messages=messages, temperature=0)
        return {
            "answer": resp.choices[0].message.content,
            "citations": [{"doc_id": h.chunk.doc_id, "chunk_id": h.chunk.id} for h in hits],
        }


def get_answerer(settings):
    if settings.answer_backend == "azure_openai" and settings.aoai_endpoint:
        return AzureOpenAIAnswerer(settings)
    return ExtractiveAnswerer()
