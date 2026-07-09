"""
pipeline.py  —  The single entry point that connects all modules

Usage:
    from src.pipeline import AskMyBook
    bot = AskMyBook(pdf_path="data/raw/textbook.pdf")
    result = bot.ask("What is virtual memory?")
    print(result["answer"])
"""

import os
from dotenv import load_dotenv
from loguru import logger

from src.ingest   import ingest_pdf
from src.embed    import embed_and_store, dense_retrieve, get_all_chunks
from src.retrieve import BM25Index, hybrid_retrieve
from src.generate import generate_answer

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/processed/chroma_db")


class AskMyBook:
    """
    One object that wraps the full RAG pipeline.
    Call .ask(question) to get an answer with citations.
    Call .ask(question, compare_doc="other_doc_name") to compare two docs.
    """

    def __init__(self, pdf_path: str, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ingest_and_index(pdf_path)

    def _ingest_and_index(self, pdf_path: str) -> None:
        logger.info("Pipeline starting …")

        # Step 1 + 2: parse PDF → embed → store
        chunks = ingest_pdf(pdf_path)
        embed_and_store(chunks, self.db_path)

        # Step 3: build BM25 index from stored chunks
        all_chunks      = get_all_chunks(self.db_path)
        self.bm25_index = BM25Index(all_chunks)
        self.doc_names  = list({c["doc_name"] for c in all_chunks})

        logger.success("Pipeline ready.")

    def add_document(self, pdf_path: str) -> None:
        """Add a second PDF (used by Compare Two Docs feature in Week 3)."""
        chunks = ingest_pdf(pdf_path)
        embed_and_store(chunks, self.db_path)
        # Rebuild BM25 index to include new doc
        all_chunks      = get_all_chunks(self.db_path)
        self.bm25_index = BM25Index(all_chunks)
        self.doc_names  = list({c["doc_name"] for c in all_chunks})
        logger.success(f"Added document. DB now has docs: {self.doc_names}")

    def ask(self, query: str, doc_filter: str | None = None) -> dict:
        """
        Ask a question.
        Returns: {answer, citations, out_of_scope, chunks_used}
        """
        chunks, has_evidence = hybrid_retrieve(
            query      = query,
            db_path    = self.db_path,
            bm25_index = self.bm25_index,
            top_k      = 5,
            doc_filter = doc_filter,
        )
        result               = generate_answer(query, chunks, has_evidence)
        result["chunks_used"] = chunks
        return result

    def compare(self, query: str, doc_a: str, doc_b: str) -> dict:
        """
        Ask the same question against two documents and compare answers.
        Returns: {answer_a, answer_b, doc_a, doc_b}
        """
        result_a = self.ask(query, doc_filter=doc_a)
        result_b = self.ask(query, doc_filter=doc_b)
        return {
            "query":    query,
            "doc_a":    doc_a,
            "answer_a": result_a["answer"],
            "cites_a":  result_a["citations"],
            "doc_b":    doc_b,
            "answer_b": result_b["answer"],
            "cites_b":  result_b["citations"],
        }


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else "data/raw/textbook.pdf"
    bot = AskMyBook(pdf_path=pdf)

    questions = [
        "What is virtual memory?",
        "Explain page replacement algorithms.",
        "What is the capital of Mars?",   # should trigger guardrail
    ]

    for q in questions:
        print(f"\n❓ {q}")
        res = bot.ask(q)
        print(f"{'⚠️ OUT OF SCOPE' if res['out_of_scope'] else '✅'} {res['answer'][:200]}")
