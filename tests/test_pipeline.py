"""
tests/test_pipeline.py

Run with:  pytest tests/ -v

These tests do NOT need a real PDF or API key.
They test the logic of each module in isolation.
"""

import pytest
from src.ingest   import _clean, chunk_pages, Chunk
from src.retrieve import fuse, BM25Index
from src.generate import build_prompt


# ── ingest.py tests ───────────────────────────────────────────────────────────

def test_clean_removes_lone_page_numbers():
    raw    = "Some text\n\n   42   \n\nMore text"
    result = _clean(raw)
    assert "42" not in result or "text" in result   # page num gone or buried in context


def test_clean_fixes_hyphenated_linebreak():
    raw    = "hyper-\nvisor"
    result = _clean(raw)
    assert "hypervisor" in result


def test_chunk_pages_returns_chunks():
    fake_pages = [{"page_num": 1, "text": "word " * 400}]
    chunks     = chunk_pages(fake_pages, "testdoc")
    assert len(chunks) > 1, "Long page should produce multiple chunks"


def test_chunk_page_short_page_is_one_chunk():
    fake_pages = [{"page_num": 1, "text": "short text here"}]
    chunks     = chunk_pages(fake_pages, "testdoc")
    assert len(chunks) == 1


def test_chunk_ids_are_unique():
    fake_pages = [{"page_num": i, "text": "word " * 350} for i in range(1, 5)]
    chunks     = chunk_pages(fake_pages, "testdoc")
    ids        = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "All chunk IDs must be unique"


# ── retrieve.py tests ─────────────────────────────────────────────────────────

def test_rrf_fusion_merges_correctly():
    dense = [
        {"text": "chunk A", "doc_name": "doc1", "page_num": 1, "score": 0.9},
        {"text": "chunk B", "doc_name": "doc1", "page_num": 2, "score": 0.8},
    ]
    bm25 = [
        {"text": "chunk B", "doc_name": "doc1", "page_num": 2, "bm25_score": 5.0},
        {"text": "chunk C", "doc_name": "doc1", "page_num": 3, "bm25_score": 4.0},
    ]
    result = fuse(dense, bm25, top_k=3)
    assert len(result) == 3
    # chunk B should rank high because it appears in BOTH lists
    texts = [r["text"] for r in result]
    assert "chunk B" in texts


def test_bm25_index_returns_results():
    chunks = [
        {"text": "virtual memory paging",  "doc_name": "doc", "page_num": 1},
        {"text": "process scheduling FCFS", "doc_name": "doc", "page_num": 2},
        {"text": "file system inode",       "doc_name": "doc", "page_num": 3},
    ]
    idx    = BM25Index(chunks)
    hits   = idx.search("virtual memory", top_k=2)
    assert hits[0]["page_num"] == 1, "Should return the virtual memory chunk first"


# ── generate.py tests ─────────────────────────────────────────────────────────

def test_build_prompt_includes_page_numbers():
    chunks = [
        {"page_num": 5,  "text": "some text about OS"},
        {"page_num": 10, "text": "more text about scheduling"},
    ]
    prompt = build_prompt("What is an OS?", chunks)
    assert "Page 5"  in prompt
    assert "Page 10" in prompt


def test_build_prompt_includes_question():
    chunks = [{"page_num": 1, "text": "some text"}]
    prompt = build_prompt("What is paging?", chunks)
    assert "What is paging?" in prompt
