# Reflection — AskMyBook

**Student:** Harshdeep Kaur
**University:** Lovely Professional University, Jalandhar
**Program:** B.Tech CSE — AI & Data Engineering
**Date:** July 2026
**Word count:** 1,074 words

---

## Section 1: What I built (230 words)

I built a system called AskMyBook. The idea is simple — you upload a DBMS textbook PDF, type a question, and it gives you an answer with the exact page number from the book. No guessing, no googling, no scrolling through 600 pages.

The problem it solves is something every student knows. You are studying the night before an exam and you need to find where normalization is explained. You ctrl+F and get 40 results. You don't know which one is the actual explanation. AskMyBook just answers the question directly and tells you the page.

The way it works is — the PDF gets split into small text chunks. Each chunk gets converted into a number vector that represents its meaning. These vectors are stored in a database called ChromaDB. When you ask a question, the system finds the most relevant chunks using two methods — one that understands meaning (dense retrieval) and one that matches exact words (BM25). The top results are sent to an AI model called Llama 3.1 which generates the final answer and is forced to include page citations.

If you ask something that is not in the textbook — like a cricket score or a general knowledge question — the system detects that nothing relevant was found and says "I don't have enough information" instead of making something up. That part is called the guardrail.

---

## Section 2: The hardest technical moment (308 words)

The hardest part for me was getting the guardrail to behave correctly.

The guardrail is the part of the system that decides whether to answer a question or refuse it. If the retrieved chunks have a low similarity score — meaning the question probably isn't in the textbook — the system should say "I don't have enough information" instead of making something up.

The problem was finding the right threshold. There is a variable called MIN_SCORE in retrieve.py. If the best similarity score is below this number, the guardrail fires and the system refuses to answer.

I had set it to 0.25 initially. When I tested it, valid DBMS questions like "What are the ACID properties?" were also getting refused. The guardrail was firing on questions that should have had answers. So I lowered it to 0.20. Then some out-of-scope questions started getting through and the model was making up answers for things not in the book.

I kept going back and forth — 0.25 was too strict, 0.20 was too loose. I tried 0.22, 0.18, different values. The results kept being inconsistent depending on how the question was phrased.

What finally helped was testing properly. I wrote down 5 in-scope questions and 3 out-of-scope questions and tested each value of MIN_SCORE against all 8 of them together instead of just checking one or two. At 0.22 the system passed all 5 in-scope and caught all 3 out-of-scope.

What I learned from this is that you cannot tune a threshold by testing one case at a time. You need a fixed set of test cases and you check every change against all of them at once. This is basically what evaluation means — and I understood it much better after going through this process manually.

---

## Section 3: What surprised me (198 words)

I expected the AI generation part to be the complicated part — calling the LLM, getting a good answer, handling errors. That part was actually straightforward.

What surprised me was how much retrieval matters. If the wrong chunks go into the prompt, the LLM has no chance of giving a correct answer. It will confidently answer from the wrong page. So the quality of retrieval is basically the quality of the whole system.

The second thing that surprised me was BM25. BM25 is a keyword search algorithm from 1994. I expected the modern embedding model to be much better. But for exact DBMS terms like "Boyce-Codd Normal Form" or "two-phase locking," BM25 was actually more reliable. The embedding model would sometimes return pages that were semantically close but not exactly right. BM25 found the exact phrase.

So the best retrieval was not dense-only or BM25-only — it was combining both. That combination is called hybrid retrieval and it genuinely made a difference on the questions I tested. I would not have believed this before building it myself.

---

## Section 4: What I'd do differently (192 words)

The main thing I would do differently is write the evaluation questions first — before writing any code.

I wrote the 21 test questions in Week 3, after the system was already built. That meant I built something and then checked if it worked. If I had written the questions first, I would have known what "working" actually means before I started. It would have also helped me during the MIN_SCORE tuning issue — instead of randomly testing one or two questions, I would have already had a proper test set ready from Day 1.

The second thing is I would start with a smaller PDF. I used a large textbook because it felt more realistic. But a smaller PDF — even 30 pages — is much easier to debug. You can read the chunks yourself and check if retrieval makes sense. With 700+ chunks it is hard to manually verify anything.

In general I rushed toward building and did not spend enough time on testing the foundation first. The MIN_SCORE problem is the best example — it took me much longer than it should have because I had no proper test set to work against.

---

## Section 5: What's next — my 3rd year plan (219 words)

There are three things I want to add to this project before the 3rd year internship.

**First — OCR support.** Right now AskMyBook only works with text-based PDFs. Most older textbooks and handwritten notes are scanned. I want to add OCR support so the system can convert scanned pages into real text. This would make AskMyBook work on any PDF, not just digital ones, which is important because a lot of university material is scanned.

**Second — fine-tuning a smaller model.** Right now I am using Llama 3.1 70B through Groq. It is a general model. I want to fine-tune a smaller model — Llama 3.1 8B — specifically on DBMS question-answer pairs using a method called LoRA. A domain-specific model would understand DBMS terminology better and give more accurate answers. LoRA fine-tuning can be done on free Google Colab GPUs.

**Third — automated evaluation using RAGAS.** Currently I manually score 21 questions. RAGAS is a framework that uses an LLM to automatically score answers on faithfulness and relevance. Automating this means I can test every change quickly instead of manually checking every answer. This is how real ML systems are maintained in production. It would also have helped a lot during the MIN_SCORE tuning — instead of manually checking 8 questions each time, an automated eval would have given me scores instantly.

---

## Resume Bullets

- Built **AskMyBook** — RAG-based Q&A over DBMS textbooks using hybrid retrieval (BM25 + BGE-small + ChromaDB), citation-grounded generation (Groq Llama 3.1 70B), and out-of-corpus guardrails; deployed on Streamlit Cloud

- Evaluated system on 21 Q&A pairs across correctness, citation precision, and guardrail accuracy; tuned retrieval confidence threshold through systematic testing to balance false positives and false negatives

- Implemented multi-document comparison mode for side-by-side answers across two PDFs; built with PyMuPDF, rank-bm25, RRF fusion, ChromaDB, and Groq API