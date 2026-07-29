"""
Thin wrapper around ChromaDB so the rest of the app talks to a simple
add()/query() interface instead of the Chroma client directly.
"""
from functools import lru_cache

import chromadb
from chromadb.config import Settings

from . import config
from .chunking import Chunk
from .embeddings import get_embedding_provider


@lru_cache(maxsize=1)
def get_client() -> chromadb.ClientAPI:
    # anonymized_telemetry=False avoids a known posthog capture() signature
    # mismatch in this chromadb version that otherwise logs an error (and
    # wastes a network call) on every single query/ingest.
    return chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection():
    client = get_client()
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(chunks: list[Chunk]) -> int:
    """Embed and upsert a batch of chunks into Chroma. Returns count stored."""
    if not chunks:
        return 0

    provider = get_embedding_provider()
    texts = [c.text for c in chunks]
    vectors = provider.embed(texts)

    collection = get_collection()
    ids = [f"{c.source_path}::{i}::{hash(c.text) & 0xffffffff}" for i, c in enumerate(chunks)]
    metadatas = [
        {
            "source_path": c.source_path,
            "chunk_type": c.chunk_type,
            "symbol": c.symbol or "",
            "start_line": c.start_line or -1,
        }
        for c in chunks
    ]

    collection.upsert(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)
    return len(chunks)


def query(question: str, top_k: int | None = None) -> list[dict]:
    """Return the top-k most relevant chunks for a natural-language question."""
    provider = get_embedding_provider()
    query_vector = provider.embed_one(question)

    collection = get_collection()
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k or config.TOP_K,
    )

    hits = []
    for doc, meta, dist in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({"text": doc, "metadata": meta, "distance": dist})
    return hits


def collection_stats() -> dict:
    collection = get_collection()
    return {"collection": config.COLLECTION_NAME, "count": collection.count()}
