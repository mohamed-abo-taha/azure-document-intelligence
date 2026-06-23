"""Runtime settings. Every component has a local default and an Azure backend."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    vector_backend: str = os.getenv("VECTOR_BACKEND", "local")      # local | azure_search
    answer_backend: str = os.getenv("ANSWER_BACKEND", "extractive")  # extractive | azure_openai
    doc_backend: str = os.getenv("DOC_BACKEND", "local")            # local | azure_blob
    feedback_backend: str = os.getenv("FEEDBACK_BACKEND", "local")  # local | cosmos
    top_k: int = int(os.getenv("TOP_K", "4"))

    # Azure AI Search
    search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    search_key: str = os.getenv("AZURE_SEARCH_KEY", "")
    search_index: str = os.getenv("AZURE_SEARCH_INDEX", "documents")

    # Azure OpenAI
    aoai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    aoai_key: str = os.getenv("AZURE_OPENAI_KEY", "")
    aoai_embed_deploy: str = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
    aoai_chat_deploy: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

    # Azure Blob (document store)
    storage_conn: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    blob_container: str = os.getenv("DOC_BLOB_CONTAINER", "documents")
    local_doc_dir: str = os.getenv("LOCAL_DOC_DIR", "artifacts/docs")

    # Azure Cosmos DB (feedback store)
    cosmos_conn: str = os.getenv("COSMOS_CONNECTION_STRING", "")
    cosmos_db: str = os.getenv("COSMOS_DATABASE", "docintel")
    cosmos_container: str = os.getenv("COSMOS_CONTAINER", "feedback")
    local_feedback_path: str = os.getenv("LOCAL_FEEDBACK_PATH", "artifacts/feedback.jsonl")


settings = Settings()
