"""
Module 5 (starter): RAG over the call reports and the news, with citations.

What to build here (about 30 minutes):
    1. load_call_report_docs(reports)            one Document per page with text, with type, date, page, file
    2. retrieve(question, k, only_type)          the closest chunks, filtered by type, newest first
    3. ask_documents(question, only_type)        retrieve, then answer from the numbered sources

Loading the news, splitting, building the index (`refresh_store`) and the answer form are Given.
Run  python main.py m2  first (it saves the news), then:
    python main.py m5

Copilot is allowed. The checks use 1 model call and embed the documents once.
"""

import os
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CLIENT, llm, embeddings
from m2_data_layer import load_call_reports


# ── Given ──────────────────────────────────────────────────────────────────────

def load_news_docs(folder="data/news"):
    docs, seen_titles = [], set()
    if not os.path.isdir(folder):                    # Module 2 has not saved any news yet
        print(f"⚠️ {folder} not found: no news in the index. Run `python main.py m2` first.")
        return docs
    for file in sorted(os.listdir(folder)):
        if not file.endswith(".txt") or file.startswith("."):
            continue
        with open(os.path.join(folder, file), encoding="utf-8") as f:
            header, text = f.read().split("\n---\n", 1)
        meta = dict(line.split(": ", 1) for line in header.splitlines())     # Source, Date, Title
        if meta["Title"] in seen_titles:
            continue
        seen_titles.add(meta["Title"])
        docs.append(Document(page_content=meta["Title"] + "\n\n" + text,
                             metadata={"type": "news", "date": meta["Date"], "title": meta["Title"],
                                       "link": meta["Source"], "file": file}))
    return docs


def split_docs(docs):
    return RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100).split_documents(docs)


def label(doc):
    where = f"page {doc.metadata['page']}" if doc.metadata["type"] == "call_report" else doc.metadata["title"]
    return f"{doc.metadata['type']} {doc.metadata['date']} ({doc.metadata['file']}, {where})"


ASK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You answer a relationship manager's questions about the client {client}.
Use only the numbered sources. Cite them as [1], [2], ... after each statement.
Each source is either a call report (what the client told us) or news (what the press reports): say which.
If the sources do not answer the question, say so and set covered to false. Never guess.
Never judge the client's creditworthiness."""),
    ("human", "<sources>\n{sources}</sources>\n\nQuestion: {question}"),
])


class Answer(BaseModel):
    answer: str = Field(description="The answer, with [n] citations")
    cited: list[int] = Field(description="The numbers of the sources the answer uses")
    covered: bool = Field(description="False if the sources do not answer the question")


vector_store = None          # the index; refresh_store() builds it, retrieve() reads it


# ── Your work ──────────────────────────────────────────────────────────────────

def load_call_report_docs(reports):
    """One Document per page that has text. page_content: the page text.
    metadata: {"type": "call_report", "date": <meeting_date>, "page": <page number>, "file": <file name only>}"""
    raise NotImplementedError("TODO load_call_report_docs")


def retrieve(question, k=4, only_type=None):
    """The k chunks of vector_store closest to the question, sorted newest first (metadata["date"]).
    With only_type ("news" or "call_report"), keep only chunks of that type."""
    # vector_store.similarity_search(question, k=k, filter=...) takes a function: Document -> True/False
    raise NotImplementedError("TODO retrieve")


def ask_documents(question, only_type=None):
    """Return (answer, results): the Answer form from the model, and the chunks it was given.
    Number the sources "[1] <label(doc)>\\n<text>" and fill ASK_PROMPT with client, sources and question."""
    raise NotImplementedError("TODO ask_documents")


# ── Given: build the index from every file (the weekly run calls it; Day 2 too) ─

def refresh_store():
    """Rebuild the index from every saved news file and call report page."""
    global vector_store
    docs = load_news_docs() + load_call_report_docs(load_call_reports(CLIENT["call_report_folder"])[0])
    chunks = split_docs(docs)
    vector_store = InMemoryVectorStore.from_documents(chunks, embeddings)
    news = sum(d.metadata["type"] == "news" for d in docs)
    print(f"📚 {news} news articles + {len(docs) - news} call report pages -> {len(chunks)} chunks")
    return vector_store
