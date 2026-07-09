# AskMyBook-RAG
AI-powered PDF Question Answering System using RAG, ChromaDB, LangChain and Streamlit.
# AskMyBook 📚

> RAG-based Q&A system — ask questions about your DBMS textbook, get answers with exact page citations.

**Student:** Harshdeep Kaur | **LPU B.Tech CSE-AIDE** | **Segment 3 — Applied ML** | **Problem I2**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](YOUR_STREAMLIT_URL_HERE)
[![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-ff4b4b)](https://streamlit.io)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)

---

## Demo

🎬 [Watch 3-min Loom walkthrough](YOUR_LOOM_URL_HERE)

🌐 [Try the live app](YOUR_STREAMLIT_URL_HERE)

---

## What this does

Upload your DBMS textbook PDF. Ask questions in plain English. Get:

- ✅ Accurate answers grounded strictly in the textbook
- ✅ Inline page citations (`[Page 42]`) for every fact stated
- ✅ "I don't know" response for out-of-scope questions (guardrail)
- ✅ Side-by-side answer comparison across two documents (mini-extension)

**Example questions it can answer:**
- *"What is normalization and what are its different forms?"*
- *"Explain the difference between DDL and DML."*
- *"What is a foreign key and how is it different from a primary key?"*
- *"Describe the ACID properties of a transaction."*
- *"What is a deadlock in DBMS and how is it handled?"*

---

## Architecture

```
DBMS PDF ──► PyMuPDF ──► 300-token chunks ──► BGE-small ──► ChromaDB
                                                                 │
User question ──► BM25 + Dense retrieval ──► RRF Fusion ─────────┘
                                                    │
                                                Top-5 chunks
                                                    │
                                        Groq (Llama 3.1 70B) + citation prompt
                                                    │
                                         Answer + [Page X] Citations
                                                    │
                                              Streamlit UI
```

**Hybrid retrieval explained:**
- **Dense (BGE-small)** catches semantic/conceptual matches — e.g. "data integrity" finds chunks about constraints even if those exact words aren't there
- **BM25** catches exact DBMS terminology — e.g. "Boyce-Codd Normal Form", "serializability", "B+ tree" — where the precise term matters
- **RRF fusion** combines both ranked lists without needing to tune score weights

---

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| PDF parsing | PyMuPDF 1.24.5 | Fast, handles complex textbook layouts with tables and figures |
| Embeddings | BGE-small-en-v1.5 | Free, runs locally, no API cost for indexing |
| Vector store | ChromaDB 0.5.3 | No server needed, persistent on disk, free |
| Keyword retrieval | BM25 (rank-bm25) | Catches exact DBMS terms dense search misses |
| Retrieval fusion | Reciprocal Rank Fusion | Robust merge — no score-scale tuning needed |
| LLM | Groq + Llama 3.1 70B | 100% free tier, fast, follows citation instructions reliably |
| UI | Streamlit 1.36.0 | Chat interface, one-command deploy |

---

## Quickstart

### Prerequisites
- Python 3.11+
- Free Groq API key → [console.groq.com](https://console.groq.com)

### Install

```bash
git clone https://github.com/harshdeepkaur/askmybook.git
cd askmybook

python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

> ⚠️ First install takes 5–15 min. `sentence-transformers` downloads the BGE model (~90MB).

### Configure

```bash
cp .env.example .env
# Open .env and paste your Groq API key
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501), upload your DBMS PDF, and start asking.

### Run tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
askmybook/
├── app.py                  # Streamlit UI — main entry point
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py           # PDF parsing + token-aware chunking
│   ├── embed.py            # BGE-small embedding + ChromaDB storage
│   ├── retrieve.py         # BM25 index + RRF hybrid fusion
│   ├── generate.py         # Groq LLM call + citation prompt + guardrail
│   └── pipeline.py         # AskMyBook class — connects all modules
├── tests/
│   └── test_pipeline.py    # 9 unit tests (no PDF or API key needed)
├── docs/
│   ├── design_doc.md
│   ├── eval_report.md      # 21 Q&A pairs manually scored
│   ├── reflection.md       # 1000–1500 word reflection piece
│   └── adr/
│       ├── ADR-001-vector-db-choice.md
│       ├── ADR-002-llm-choice.md
│       └── ADR-003-chunking-strategy.md
└── data/
    ├── raw/                # Put your DBMS PDF here (git-ignored)
    └── processed/          # ChromaDB files (git-ignored)
```

---

## Evaluation Results

Tested on **DBMS textbook** (chapters 1–10), 21 questions — 18 in-scope + 3 guardrail.

| Metric | Score |
|--------|-------|
| Correct answers | — / 18 |
| Citations present | — / 18 |
| Guardrail correct | — / 3 |


## Status
- [x] PDF ingestion and chunking (ingest.py)
- [x] BGE-small embeddings stored in ChromaDB (embed.py)
- [x] BM25 + dense hybrid retrieval with RRF (retrieve.py)
- [x] Groq Llama 3.1 generation with citations (generate.py)
- [x] Out-of-corpus guardrail working
- [x] Streamlit chat UI with Compare Two Docs mode
- [ ] Unit tests (Week 3)
- [ ] 21-question eval (Week 3)
- [ ] Deployed live URL (Week 3)

Full details → [docs/eval_report.md](docs/eval_report.md)

---

## Mini-Extension: Compare Two Documents

Toggle **"Compare Two Documents"** in the sidebar. Upload two PDFs (e.g. two different DBMS textbooks or DBMS + SQL reference). Ask any question — the app retrieves from both and shows side-by-side answers with page citations from each source.

**Example use:** *"How does Ramakrishnan explain 3NF vs how does Silberschatz explain it?"*

---

## Architecture Decision Records

- [ADR-001 — Vector DB: Why ChromaDB over Pinecone/FAISS](docs/adr/ADR-001-vector-db-choice.md)
- [ADR-002 — LLM: Why Groq + Llama 3.1 over GPT-4o-mini](docs/adr/ADR-002-llm-choice.md)
- [ADR-003 — Chunking: Why 300 tokens with 50-token overlap](docs/adr/ADR-003-chunking-strategy.md)

---

## Known Limitations

- Scanned PDFs (image-only pages) return no text — OCR support is a future addition
- Groq free tier: 30 requests/min — not suitable for high traffic
- ChromaDB resets if the deployment container restarts — PDF must be re-uploaded
- No persistent chat history across sessions

---

## 3rd Year Roadmap

This project is the foundation. Extensions planned for 3rd year internship:

1. **OCR support** — handle scanned DBMS textbooks using Tesseract or Surya
2. **Fine-tune Llama 3.1 8B** on DBMS-specific Q&A pairs using LoRA — better accuracy on technical terms
3. **Agentic routing** — auto-detect which document a question belongs to without user selecting
4. **Automated eval pipeline** — LLM-as-judge scoring using RAGAS framework
5. **Persistent vector store** — user accounts, saved document collections

---

## Resume Bullets

```
• Built AskMyBook — RAG-based Q&A over DBMS textbooks using hybrid retrieval
  (BM25 + BGE-small + ChromaDB), citation-grounded generation (Groq Llama 3.1 70B),
  and out-of-corpus guardrails; deployed on Streamlit Cloud

• Evaluated over 21 Q&A pairs scoring correctness, citation precision, and guardrail
  accuracy; iterated on chunking strategy and retrieval threshold based on failure analysis

• Implemented multi-document comparison mode enabling side-by-side answers from two PDFs;
  built with PyMuPDF, rank-bm25, ChromaDB, RRF fusion, and Groq API
```

---

## License

MIT — free to use, learn from, and extend.

---

*Built during LPU B.Tech CSE-AIDE Internship · Segment 3 Applied ML · June–July 2026*

