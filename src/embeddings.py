"""Azure OpenAI embeddings (used by the Azure AI Search backend).

Imported lazily so local runs never need the openai package or any credentials.
"""
from __future__ import annotations


class AzureOpenAIEmbedder:
    def __init__(self, settings):
        from openai import AzureOpenAI

        self.client = AzureOpenAI(
            azure_endpoint=settings.aoai_endpoint,
            api_key=settings.aoai_key,
            api_version="2024-06-01",
        )
        self.deployment = settings.aoai_embed_deploy

    def embed(self, texts):
        resp = self.client.embeddings.create(model=self.deployment, input=list(texts))
        return [d.embedding for d in resp.data]
