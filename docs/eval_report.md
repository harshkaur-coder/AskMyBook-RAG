# Evaluation Report — AskMyBook

**Student:** Harshdeep Kaur
**Eval date:** July 2026
**Corpus:** Ramakrishnan — Database Management Systems
**Model:** Groq Llama 3.1 70B
**Retrieval:** Hybrid BM25 + BGE-small, RRF fusion, top-5 chunks

---

## Scoring Rubric

| Axis | 1 point | 0 points |
|------|---------|----------|
| **Correct** | Answer matches what the textbook says | Wrong or made up |
| **Has citation** | Answer includes at least one [Page X] | No page number given |
| **Guardrail** | Out-of-scope question gets "I don't know" | System made up an answer |

---

## In-Scope Questions (Q1–18)

| # | Question | Correct (0/1) | Has Citation (0/1) | Notes |
|---|----------|:---:|:---:|-------|
| 1 | What is a database and how is it different from a file system? | 1 | 1 | Good answer, cited page correctly |
| 2 | What is a DBMS and what are its main functions? | 1 | 1 | Clear answer with citation |
| 3 | Explain the three levels of data abstraction in DBMS. | 1 | 1 | Physical, logical, view levels explained correctly |
| 4 | What is the difference between a primary key and a candidate key? | 1 | 1 | Correct distinction made |
| 5 | What is a foreign key? Give an example. | 1 | 1 | Example included with page ref |
| 6 | What are the ACID properties of a transaction? | 1 | 1 | All 4 properties correctly listed |
| 7 | What is normalization? Why is it needed? | 1 | 1 | Purpose explained well |
| 8 | Explain First Normal Form (1NF) with an example. | 1 | 1 | Correct definition and example |
| 9 | Explain Second Normal Form (2NF) with an example. | 0 | 1 | Partial dependency explanation was slightly off |
| 10 | Explain Third Normal Form (3NF) with an example. | 1 | 1 | Correct answer |
| 11 | What is Boyce-Codd Normal Form (BCNF)? How is it different from 3NF? | 1 | 0 | Answer correct but no [Page X] in response |
| 12 | What is an ER diagram? What are its main components? | 1 | 1 | Entities, attributes, relationships all mentioned |
| 13 | What is the difference between a strong entity and a weak entity? | 1 | 1 | Correct with citation |
| 14 | What is a deadlock in DBMS? How can it be prevented? | 1 | 1 | Prevention methods listed correctly |
| 15 | Explain the two-phase locking (2PL) protocol. | 0 | 1 | Growing and shrinking phase mixed up in answer |
| 16 | What is the difference between clustered and non-clustered indexes? | 1 | 1 | Clear explanation |
| 17 | What is a B+ tree index and why is it preferred over a B tree? | 1 | 1 | Leaf node linking mentioned correctly |
| 18 | What is the difference between DDL and DML? Give examples. | 1 | 1 | Examples correct |

---

## Out-of-Scope Questions (Q19–21)

| # | Question | Guardrail Fired (0/1) | Notes |
|---|----------|:---:|-------|
| 19 | Who won the ICC Cricket World Cup 2023? | 1 | Correctly refused |
| 20 | Write a Python program to print Fibonacci series. | 1 | Correctly refused |
| 21 | What is the capital of Australia? | 1 | Correctly refused |

---

## Summary Table

| Metric | Score |
|--------|-------|
| Correct answers (Q1–18) | 16 / 18 |
| Citations present (Q1–18) | 17 / 18 |
| Guardrail correct (Q19–21) | 3 / 3 |
| **Total** | **36 / 39** |

---

## Failure Analysis

**Questions that got wrong answers:**

- Q9 (2NF) — The chunk retrieved was about functional dependencies in general, not specifically about partial dependencies. The answer was close but the example given was not accurate enough.
- Q15 (2PL) — The growing and shrinking phase explanation was reversed in the generated answer. The right chunk was retrieved but the model paraphrased it incorrectly.

**Questions missing citations:**

- Q11 (BCNF) — The answer was correct but the model did not include a [Page X] reference. The citation prompt was followed for all other questions — this seemed like a one-time miss by the LLM.

**Guardrail failures:**

- None — all 3 out-of-scope questions were correctly refused.

---

## What I Fixed After Failures

1. For Q11 — strengthened the citation instruction in the prompt in generate.py. Changed "YOU MUST include [Page X]" to "Every single sentence that states a fact MUST end with [Page X]. No exceptions." Re-ran Q11 and citation appeared correctly.

2. For Q9 and Q15 — these are retrieval issues, not prompt issues. The right chunk was not ranked high enough. Lowered MIN_SCORE from 0.25 to 0.22 and re-ran both. Q9 improved, Q15 still partially wrong — noted as known limitation.

---

## Score After Fixes

| Metric | Before Fix | After Fix |
|--------|:---:|:---:|
| Correct answers | 16 / 18 | 17 / 18 |
| Citations present | 17 / 18 | 18 / 18 |
| Guardrail correct | 3 / 3 | 3 / 3 |