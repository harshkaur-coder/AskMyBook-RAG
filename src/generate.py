"""
generate.py  —  Step 4: Build prompt, call Groq, return answer + citations

Key design decisions:
  1. Citations are forced in the prompt — model must say [Page X] inline
  2. Guardrail: if has_evidence=False we return a canned "I don't know" message
     without calling the API at all (saves money, avoids hallucination)
  3. System prompt instructs model to ONLY use provided context — no internet knowledge
"""

import os
from groq import Groq
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

MODEL = "llama-3.3-70b-versatile"   # free on Groq, very capable


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Formats the retrieved chunks into a context block and appends the question.
    Each chunk is tagged with its page number so the model can cite it.
    """
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1} — Page {chunk['page_num']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    return f"""You are an expert assistant that answers questions ONLY using the provided textbook excerpts.

RULES:
1. Answer ONLY from the context below. Do not use outside knowledge.
2. Every fact you state MUST include a citation in the format [Page X].
3. If the context does not contain enough information, say exactly: "The document does not contain enough information to answer this question."
4. Be concise and clear. Use bullet points when listing multiple items.

CONTEXT:
{context}

QUESTION: {query}

ANSWER (with [Page X] citations):"""


# ── Main generate function ────────────────────────────────────────────────────

def generate_answer(
    query:        str,
    chunks:       list[dict],
    has_evidence: bool,
) -> dict:
    """
    Returns a dict with:
      answer      : str  — the LLM answer with inline citations
      citations   : list — [{page_num, text_snippet}]
      out_of_scope: bool — True if guardrail fired
    """

    # Guardrail: don't call LLM if retrieval found nothing useful
    if not has_evidence:
        logger.info("Guardrail fired — returning out-of-scope message.")
        return {
            "answer":       "I couldn't find relevant information in the document to answer this question. Please try rephrasing, or ask something related to the document's content.",
            "citations":    [],
            "out_of_scope": True,
        }

    # Build prompt and call Groq
    prompt = build_prompt(query, chunks)
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    logger.info(f"Calling Groq ({MODEL}) for: '{query[:50]}'")
    response = client.chat.completions.create(
        model    = MODEL,
        messages = [{"role": "user", "content": prompt}],
        temperature = 0.1,    # low temp = more factual, less creative
        max_tokens  = 512,
    )

    answer = response.choices[0].message.content.strip()

    # Build citations list from the chunks we passed
    citations = [
        {"page_num": c["page_num"], "snippet": c["text"][:120] + "…"}
        for c in chunks
    ]

    return {
        "answer":       answer,
        "citations":    citations,
        "out_of_scope": False,
    }


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Fake chunks to test the prompt builder without a real PDF
    fake_chunks = [
        {"page_num": 12, "text": "Virtual memory is a memory management technique that gives each process the illusion of having its own large, contiguous address space."},
        {"page_num": 15, "text": "Page replacement algorithms like LRU, FIFO and Optimal are used to decide which page to evict when physical memory is full."},
    ]
    result = generate_answer("What is virtual memory?", fake_chunks, has_evidence=True)
    print("\n📝 Answer:\n", result["answer"])
    print("\n📌 Citations:")
    for c in result["citations"]:
        print(f"   Page {c['page_num']}: {c['snippet']}")
