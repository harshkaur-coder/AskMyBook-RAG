"""
app.py  —  Streamlit UI for AskMyBook

Run with:  streamlit run app.py
"""

import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from src.pipeline import AskMyBook

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title = "AskMyBook",
    page_icon  = "📚",
    layout     = "wide",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📚 AskMyBook")
    st.caption("RAG-based Q&A over your textbooks")
    st.divider()

    mode = st.radio(
        "Mode",
        ["Ask One Document", "Compare Two Documents"],
        index=0,
    )

    st.divider()
    st.markdown("**Upload your PDF(s)**")
    pdf1 = st.file_uploader("Primary document", type=["pdf"], key="pdf1")

    pdf2 = None
    if mode == "Compare Two Documents":
        pdf2 = st.file_uploader("Second document", type=["pdf"], key="pdf2")

    st.divider()
    st.markdown("**About**")
    st.caption(
        "Built with PyMuPDF · BGE-small · ChromaDB · BM25 · Groq (Llama 3.1) · Streamlit\n\n"
        "Segment 3 — Applied ML · Problem I2 · LPU B.Tech CSE-AIDE"
    )


# ── Session state ─────────────────────────────────────────────────────────────

if "bot" not in st.session_state:
    st.session_state.bot       = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "loaded_files" not in st.session_state:
    st.session_state.loaded_files = []


# ── Helper: save uploaded file to temp path ───────────────────────────────────

def save_upload(uploaded_file) -> str:
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


# ── Load documents into pipeline ──────────────────────────────────────────────

def load_docs():
    if pdf1 is None:
        return

    loaded = [pdf1.name] + ([pdf2.name] if pdf2 else [])
    if loaded == st.session_state.loaded_files:
        return   # already loaded, skip

    with st.spinner("Reading and indexing PDF(s) — first time takes ~1 min …"):
        path1 = save_upload(pdf1)
        bot   = AskMyBook(pdf_path=path1)

        if pdf2 is not None:
            path2 = save_upload(pdf2)
            bot.add_document(path2)

        st.session_state.bot          = bot
        st.session_state.loaded_files = loaded
        st.session_state.chat_history = []


load_docs()


# ── Main area ─────────────────────────────────────────────────────────────────

if st.session_state.bot is None:
    st.title("📚 AskMyBook")
    st.info("👈 Upload a PDF in the sidebar to get started.")
    st.stop()

bot = st.session_state.bot

st.title("📚 AskMyBook")
st.caption(f"Loaded: {', '.join(st.session_state.loaded_files)}")

# ── Chat history ──────────────────────────────────────────────────────────────

for item in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        if item["out_of_scope"]:
            st.warning(item["answer"])
        else:
            st.write(item["answer"])
        if item.get("citations"):
            with st.expander(f"📌 Sources ({len(item['citations'])} chunks used)"):
                for cite in item["citations"]:
                    st.markdown(f"**Page {cite['page_num']}** — {cite['snippet']}")


# ── Input ─────────────────────────────────────────────────────────────────────

query = st.chat_input("Ask a question about your document …")

if query:
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        with st.spinner("Searching and generating …"):

            if mode == "Ask One Document":
                result = bot.ask(query)

                if result["out_of_scope"]:
                    st.warning(result["answer"])
                else:
                    st.write(result["answer"])
                    with st.expander(f"📌 Sources ({len(result['citations'])} chunks used)"):
                        for cite in result["citations"]:
                            st.markdown(f"**Page {cite['page_num']}** — {cite['snippet']}")

                st.session_state.chat_history.append({
                    "question":    query,
                    "answer":      result["answer"],
                    "citations":   result["citations"],
                    "out_of_scope": result["out_of_scope"],
                })

            else:
                # Compare Two Documents mode
                if len(bot.doc_names) < 2:
                    st.error("Please upload a second document in the sidebar first.")
                else:
                    doc_a, doc_b = bot.doc_names[0], bot.doc_names[1]
                    comp         = bot.compare(query, doc_a, doc_b)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**📄 {doc_a}**")
                        st.write(comp["answer_a"])
                        with st.expander("Sources"):
                            for c in comp["cites_a"]:
                                st.caption(f"Page {c['page_num']}: {c['snippet']}")
                    with col2:
                        st.markdown(f"**📄 {doc_b}**")
                        st.write(comp["answer_b"])
                        with st.expander("Sources"):
                            for c in comp["cites_b"]:
                                st.caption(f"Page {c['page_num']}: {c['snippet']}")

                    st.session_state.chat_history.append({
                        "question":    query,
                        "answer":      f"**{doc_a}**: {comp['answer_a']}\n\n**{doc_b}**: {comp['answer_b']}",
                        "citations":   comp["cites_a"] + comp["cites_b"],
                        "out_of_scope": False,
                    })
