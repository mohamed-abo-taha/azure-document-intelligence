"""Feedback store (NoSQL): local JSONL or Azure Cosmos DB.

Captures thumbs-up/down on answers so retrieval and prompts can be improved
over time. Cosmos is the production NoSQL backend; a JSONL file is the local one.
"""
from __future__ import annotations

import json
import os
import time
import uuid


class LocalFeedbackStore:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def record(self, item):
        item = dict(item)
        item.setdefault("id", str(uuid.uuid4()))
        item.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item) + "\n")
        return item

    def recent(self, n=20):
        if not os.path.exists(self.path):
            return []
        lines = open(self.path, encoding="utf-8").read().splitlines()[-n:]
        return [json.loads(line) for line in lines]


class CosmosFeedbackStore:
    def __init__(self, settings):
        from azure.cosmos import CosmosClient, PartitionKey

        client = CosmosClient.from_connection_string(settings.cosmos_conn)
        db = client.create_database_if_not_exists(settings.cosmos_db)
        self.container = db.create_container_if_not_exists(
            settings.cosmos_container, PartitionKey(path="/doc_id")
        )

    def record(self, item):
        item = dict(item)
        item.setdefault("id", str(uuid.uuid4()))
        item.setdefault("doc_id", "_")
        item.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
        self.container.upsert_item(item)
        return item

    def recent(self, n=20):
        query = "SELECT TOP @n * FROM c ORDER BY c.ts DESC"
        return list(self.container.query_items(
            query=query, parameters=[{"name": "@n", "value": n}], enable_cross_partition_query=True
        ))


def get_feedbackstore(settings):
    if settings.feedback_backend == "cosmos" and settings.cosmos_conn:
        return CosmosFeedbackStore(settings)
    return LocalFeedbackStore(settings.local_feedback_path)
