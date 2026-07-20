# Design Document — AskMyBook

**Student:** Harshdeep Kaur
**University:** Lovely Professional University, Jalandhar
**Program:** B.Tech CSE — AI & Data Engineering
**Date:** June 2026
**Problem:** I2 — Document Q&A
**Segment:** 3 — Foundations of Applied Machine Learning

---

## 1. The Problem

Every DBMS student has a 600 page textbook. Before exams, finding a specific concept means either ctrl+F with vague keywords and getting 40 results, or randomly flipping pages hoping to land on the right section.

I wanted to build something where you just ask the question in plain English and it tells you the answer and the page number. That is it. Simple problem, but actually useful.

---

## 2. What I Am Building

A RAG (Retrieval-Augmented Generation) based Q&A system called AskMyBook.

The user uploads a DBMS textbook PDF. They type a question. The system finds the most relevant parts of the textbook and uses an AI model to generate a direct answer — with page citations from the actual book.

If the question has nothing to do with the textbook (like a cricket score or a general knowledge question), the system refuses to answer instead of making something up.

There is also a mini-extension — a "Compare Two Documents" mode where you can upload two different PDFs and ask the same question to both. The app shows answers side by side.

---

## 3. Architecture

```
DBMS PDF
    │
    ▼
PyMuPDF (extract text page by page)
    │
    ▼
Chunking (300 tokens, 50 token overlap)
    │
    ▼
BGE-small-en-v1.5 (convert chunks to vectors)
    │
    ▼
ChromaDB (store vectors on disk)
    │
    ─────────────────────────────────────
    │                                   │
    ▼                                   ▼
Dense Retrieval                     BM25 Retrieval
(semantic meaning)              (exact keyword match)
    │                                   │
    └──────────── RRF Fusion ───────────┘
                      │
                  Top 5 chunks
                      │
                      ▼
            Groq — Llama 3.1 70B
          (generate answer with citations)
                      │
                      ▼
                Streamlit UI
          (chat interface with page refs)
```

---

## 4. Tech Stack

| Component | Tool | Why I chose it |
|-----------|------|----------------|
| PDF parsing | PyMuPDF | Fast, free, handles most textbook PDFs well |
| Embeddings | BGE-small-en-v1.5 | Runs locally, no API cost, good quality |
| Vector database | ChromaDB | No server setup needed, saves to disk, free |
| Keyword retrieval | BM25 via rank-bm25 | Catches exact DBMS terms that dense search misses |
| Retrieval fusion | Reciprocal Rank Fusion | Combines BM25 and dense scores without needing to tune weights |
| LLM | Groq + Llama 3.1 70B | Completely free, fast, follows citation instructions well |
| UI | Streamlit | Simple to build, easy to deploy for free |

---

## 5. Chunking Strategy

I split each page into chunks of 300 tokens with 50 token overlap.

**Why 300 tokens:** Small enough that one chunk covers one concept. Large enough that the chunk has enough context to be meaningful on its own.

**Why 50 token overlap:** If a sentence falls at the boundary between two chunks, it will appear in both. This means retrieval can find it from either side.

**Why token-based and not character-based:** LLMs have token limits, not character limits. Counting tokens is more accurate for staying within context windows.

---

## 6. Retrieval Strategy

I use hybrid retrieval — combining dense retrieval and BM25.

**Dense retrieval** uses BGE-small embeddings to find chunks that are semantically similar to the question. Good for paraphrased or conceptual questions like "what ensures data reliability in transactions" — it will find ACID properties even without those exact words.

**BM25** is keyword based. Good for exact DBMS terminology like "Boyce-Codd Normal Form" or "two-phase locking protocol" where the precise term matters.

**RRF fusion** combines the ranked results from both. Instead of averaging scores (which does not work because BM25 and cosine similarity are on different scales), RRF uses ranks. Each document gets a score based on its position in each list. This is more robust.

---

## 7. Guardrail

If the best dense similarity score is below 0.22, the system does not call the LLM. It returns a fixed message: "I couldn't find relevant information in the document to answer this."

This prevents the model from making up answers for questions that are not in the textbook.

I tuned the threshold by testing 5 in-scope and 3 out-of-scope questions at different values (0.25, 0.22, 0.20). At 0.22 all in-scope questions passed and all out-of-scope were refused.

---

## 8. Mini-Extension — Compare Two Documents

The user can upload two PDFs. Asking any question runs retrieval separately on each document and generates two answers side by side.

**Implementation:** Each PDF gets its own ChromaDB collection with a doc_name metadata field. At query time, I filter by doc_name to retrieve from each separately, then call the LLM twice with different context.

**Use case:** Compare how two different DBMS textbooks explain the same concept — for example Ramakrishnan vs Silberschatz on normalization.

---

## 9. What I Am Not Building

- No user login or accounts
- No persistent chat history across sessions
- No fine-tuned model
- No automated CI/CD pipeline
- No OCR for scanned PDFs

These are things I want to add in 3rd year. For now the goal is a working, deployed, documented system.

---

## 10. Success Criteria

- [ ] User uploads DBMS PDF and asks 10 questions — all get answers with page citations
- [ ] Guardrail fires correctly on 3 out-of-scope questions
- [ ] App deployed at a public Streamlit URL
- [ ] 21 question eval set manually scored
- [ ] Compare Two Documents mode working with two PDFs