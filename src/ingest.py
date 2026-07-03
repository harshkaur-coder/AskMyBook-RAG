"""
ingest.py  —  Step 1: Read PDF, split into chunks
"""

import re
from pathlib import Path
from dataclasses import dataclass
import fitz          # PyMuPDF
import tiktoken
from loguru import logger
from tqdm import tqdm


# ── Data model ──────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    chunk_id:    str
    doc_name:    str
    page_num:    int
    text:        str
    token_count: int = 0


# ── Settings ────────────────────────────────────────────────────────────────

CHUNK_SIZE = 300   # tokens per chunk
OVERLAP    = 50    # tokens shared between consecutive chunks


# ── Helpers ─────────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    text = re.sub(r"-\n", "", text)           # fix hyphenated line-breaks
    text = re.sub(r"\n{3,}", "\n\n", text)    # collapse blank lines
    text = re.sub(r" {2,}", " ", text)        # collapse spaces
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)  # lone page numbers
    return text.strip()


# ── Core ────────────────────────────────────────────────────────────────────

def extract_pages(pdf_path: str) -> list[dict]:
    """Return list of {page_num, text} for every page that has text."""
    doc   = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        text = _clean(page.get_text("text"))
        if len(text) > 50:
            pages.append({"page_num": i + 1, "text": text})
    doc.close()
    logger.info(f"Extracted {len(pages)} pages from {Path(pdf_path).name}")
    return pages


def chunk_pages(pages: list[dict], doc_name: str) -> list[Chunk]:
    """Split page text into overlapping token-sized chunks."""
    enc    = tiktoken.get_encoding("cl100k_base")
    step   = CHUNK_SIZE - OVERLAP
    chunks = []

    for page in pages:
        tokens   = enc.encode(page["text"])
        page_num = page["page_num"]

        if len(tokens) <= CHUNK_SIZE:
            chunks.append(Chunk(
                chunk_id    = f"{doc_name}_p{page_num}_c0",
                doc_name    = doc_name,
                page_num    = page_num,
                text        = enc.decode(tokens),
                token_count = len(tokens),
            ))
            continue

        for idx, start in enumerate(range(0, len(tokens), step)):
            window = tokens[start : start + CHUNK_SIZE]
            if len(window) < 30:
                break
            chunks.append(Chunk(
                chunk_id    = f"{doc_name}_p{page_num}_c{idx}",
                doc_name    = doc_name,
                page_num    = page_num,
                text        = enc.decode(window),
                token_count = len(window),
            ))

    logger.info(f"Created {len(chunks)} chunks from {doc_name}")
    return chunks


def ingest_pdf(pdf_path: str) -> list[Chunk]:
    """Full pipeline: PDF path → list of Chunk objects."""
    doc_name = Path(pdf_path).stem.replace(" ", "_").lower()
    pages    = extract_pages(pdf_path)
    return chunk_pages(pages, doc_name)


# ── Quick test (run: python src/ingest.py) ──────────────────────────────────

if __name__ == "__main__":
    import sys
    path   = sys.argv[1] if len(sys.argv) > 1 else "data/raw/textbook.pdf"
    chunks = ingest_pdf(path)
    print(f"\n✅ Total chunks : {len(chunks)}")
    print(f"   First chunk  : page {chunks[0].page_num}, {chunks[0].token_count} tokens")
    print(f"   Preview      : {chunks[0].text[:150]}...")
