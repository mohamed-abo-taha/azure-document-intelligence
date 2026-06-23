"""Raw document storage: local filesystem or Azure Blob (Azurite-compatible)."""
from __future__ import annotations

import os


class LocalDocStore:
    def __init__(self, root):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def put(self, doc_id, text):
        with open(os.path.join(self.root, doc_id + ".txt"), "w", encoding="utf-8") as f:
            f.write(text)

    def get(self, doc_id):
        with open(os.path.join(self.root, doc_id + ".txt"), encoding="utf-8") as f:
            return f.read()

    def list(self):
        return sorted(f[:-4] for f in os.listdir(self.root) if f.endswith(".txt"))


class AzureBlobDocStore:
    def __init__(self, connection_string, container):
        from azure.storage.blob import BlobServiceClient

        self.service = BlobServiceClient.from_connection_string(connection_string)
        self.container = container
        try:
            self.service.create_container(container)
        except Exception:
            pass

    def _client(self):
        return self.service.get_container_client(self.container)

    def put(self, doc_id, text):
        self._client().upload_blob(name=doc_id + ".txt", data=text.encode("utf-8"), overwrite=True)

    def get(self, doc_id):
        return self._client().download_blob(doc_id + ".txt").readall().decode("utf-8")

    def list(self):
        return sorted(b.name[:-4] for b in self._client().list_blobs() if b.name.endswith(".txt"))


def get_docstore(settings):
    if settings.doc_backend == "azure_blob" and settings.storage_conn:
        return AzureBlobDocStore(settings.storage_conn, settings.blob_container)
    return LocalDocStore(settings.local_doc_dir)
