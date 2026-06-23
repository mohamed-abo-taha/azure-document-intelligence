from src.chunking import Chunk
from src.vectorstore import LocalVectorStore


def test_search_ranks_relevant_chunk_first():
    vs = LocalVectorStore()
    vs.add([
        Chunk("a::0", "a", "cats and dogs are common household pets"),
        Chunk("b::0", "b", "azure container apps can scale to zero replicas"),
    ])
    hits = vs.search("how do container apps scale", k=2)
    assert hits
    assert hits[0].chunk.doc_id == "b"


def test_empty_store_returns_nothing():
    assert LocalVectorStore().search("anything") == []
