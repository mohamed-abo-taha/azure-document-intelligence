"""Vector stores: a local TF-IDF store and an Azure AI Search store.

The local store keeps the repo runnable with no Azure account; the Azure AI
Search store is the production path (dense vectors embedded by Azure OpenAI).
Both expose the same add/search interface.
"""
from __future__ import annotations

from dataclasses import dataclass

from .chunking import Chunk


@dataclass
class Hit:
    chunk: Chunk
    score: float


class VectorStore:
    def add(self, chunks): raise NotImplementedError
    def search(self, query, k=4): raise NotImplementedError
    def count(self): raise NotImplementedError


class LocalVectorStore(VectorStore):
    """TF-IDF + cosine similarity. Re-fits on add (fine for modest corpora)."""

    def __init__(self):
        self._chunks: list[Chunk] = []
        self._matrix = None
        self._vec = None

    def add(self, chunks):
        self._chunks.extend(chunks)
        self._refit()

    def _refit(self):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        self._matrix = self._vec.fit_transform([c.text for c in self._chunks])

    def search(self, query, k=4):
        if not self._chunks:
            return []
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        sims = cosine_similarity(self._vec.transform([query]), self._matrix)[0]
        order = np.argsort(sims)[::-1][:k]
        return [Hit(self._chunks[i], float(sims[i])) for i in order if sims[i] > 0]

    def count(self):
        return len(self._chunks)


class AzureAISearchStore(VectorStore):
    """Azure AI Search with a vector field; embeds via Azure OpenAI."""

    def __init__(self, settings, embedder):
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient

        self.embedder = embedder
        self.client = SearchClient(
            settings.search_endpoint, settings.search_index, AzureKeyCredential(settings.search_key)
        )

    def add(self, chunks):
        vectors = self.embedder.embed([c.text for c in chunks])
        docs = [
            {"id": c.id.replace("::", "__"), "doc_id": c.doc_id, "text": c.text, "vector": v}
            for c, v in zip(chunks, vectors)
        ]
        self.client.upload_documents(docs)

    def search(self, query, k=4):
        from azure.search.documents.models import VectorizedQuery

        qv = self.embedder.embed([query])[0]
        vq = VectorizedQuery(vector=qv, k_nearest_neighbors=k, fields="vector")
        results = self.client.search(search_text=None, vector_queries=[vq], top=k)
        return [
            Hit(Chunk(id=r["id"], doc_id=r.get("doc_id", ""), text=r["text"]),
                float(r.get("@search.score", 0.0)))
            for r in results
        ]

    def count(self):
        return self.client.get_document_count()


def get_vectorstore(settings, embedder=None):
    if settings.vector_backend == "azure_search" and settings.search_endpoint:
        from .embeddings import AzureOpenAIEmbedder

        return AzureAISearchStore(settings, embedder or AzureOpenAIEmbedder(settings))
    return LocalVectorStore()
