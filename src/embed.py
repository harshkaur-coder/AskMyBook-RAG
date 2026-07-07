"""
embed.py  —  Step 2: Embed chunks and store in ChromaDB
"""

import chromadb
from chromadb.utils import embedding_functions
from loguru import logger
from tqdm import tqdm

from src.ingest import Chunk


COLLECTION  = "askmybook"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"   # free, runs locally, no API key needed
BATCH_SIZE  = 64


# ── DB connection ────────────────────────────────────────────────────────────

def get_collection(db_path: str):
    """Get (or create) the ChromaDB collection with BGE-small as embedder."""
    client   = chromadb.PersistentClient(path=db_path)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    return client.get_or_create_collection(
        name             = COLLECTION,
        embedding_function = embed_fn,
        metadata         = {"hnsw:space": "cosine"},
    )


# ── Store ────────────────────────────────────────────────────────────────────

def embed_and_store(chunks: list[Chunk], db_path: str) -> None:
    """Embed all chunks and persist to ChromaDB. Safe to call multiple times."""
    col      = get_collection(db_path)
    existing = set(col.get()["ids"])
    new      = [c for c in chunks if c.chunk_id not in existing]

    if not new:
        logger.info("All chunks already in DB — nothing to do.")
        return

    logger.info(f"Embedding {len(new)} new chunks …")
    for i in tqdm(range(0, len(new), BATCH_SIZE), desc="Embedding"):
        batch = new[i : i + BATCH_SIZE]
        col.add(
            ids       = [c.chunk_id for c in batch],
            documents = [c.text     for c in batch],
            metadatas = [{"doc_name": c.doc_name, "page_num": c.page_num}
                         for c in batch],
        )
    logger.success(f"DB now has {col.count()} chunks total.")


# ── Dense retrieval ──────────────────────────────────────────────────────────

def dense_retrieve(query: str, db_path: str,
                   top_k: int = 5, doc_filter: str | None = None) -> list[dict]:
    """Semantic similarity search. Returns top_k chunks with scores."""
    col   = get_collection(db_path)
    where = {"doc_name": doc_filter} if doc_filter else None
    res   = col.query(
        query_texts = [query],
        n_results   = top_k,
        where       = where,
        include     = ["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, dist in zip(res["documents"][0],
                                 res["metadatas"][0],
                                 res["distances"][0]):
        hits.append({
            "text":     text,
            "doc_name": meta["doc_name"],
            "page_num": meta["page_num"],
            "score":    round(1 - dist, 4),
        })
    return hits


def get_all_chunks(db_path: str) -> list[dict]:
    """Fetch every stored chunk — used to build the BM25 index."""
    col = get_collection(db_path)
    res = col.get(include=["documents", "metadatas"])
    chunks = []
    for text, meta in zip(res["documents"], res["metadatas"]):
        chunks.append({
            "text":     text,
            "doc_name": meta["doc_name"],
            "page_num": meta["page_num"],
        })
    return chunks


# ── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from src.ingest import ingest_pdf

    pdf    = sys.argv[1] if len(sys.argv) > 1 else "data/raw/textbook.pdf"
    db     = "data/processed/chroma_db"
    chunks = ingest_pdf(pdf)
    embed_and_store(chunks, db)

    print("\n🔍 Test retrieval: 'what is virtual memory?'")
    hits = dense_retrieve("what is virtual memory?", db)
    for h in hits:
        print(f"  Page {h['page_num']}  score={h['score']}  →  {h['text'][:80]}...")
