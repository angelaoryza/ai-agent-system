"""
Module 5 Exercise: RAG over the news saved in Module 2.

Write three functions:
    1. load_news()                     data/news/*.json -> a list of documents (dicts)
    2. build_vector_store(docs)        split into chunks, embed, store
    3. ask_news(vector_store, question) retrieve the closest chunks and answer from them

Run  python day1/examples/m2_example.py  first (it saves the news), then:
    python day1/exercises/m5_exercise.py

Copilot is allowed. The checks use 1 model call and embed the news once.
"""

import os
import json
import numpy as np
from dotenv import load_dotenv
from pydantic_ai import Agent, Embedder
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

model = OpenAIResponsesModel(
    os.getenv("OPENAI_MODEL", "gpt-6.1-sol"),
    provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_URL")),
)
rag_agent = Agent(model)
embedder = Embedder("sentence-transformers:all-mpnet-base-v2")   # open source, runs on your laptop


# ── Given: splitting and searching ─────────────────────────────────────────────

def split_text(text, chunk_size=1500, chunk_overlap=100):
    """Cut a text into pieces of chunk_size characters; each piece repeats the last chunk_overlap characters of the one before."""
    chunks, start = [], 0
    while True:
        chunks.append(text[start:start + chunk_size])
        if start + chunk_size >= len(text):
            return chunks
        start += chunk_size - chunk_overlap


def split_documents(docs, chunk_size=1500, chunk_overlap=100):
    return [{"text": piece, "metadata": doc["metadata"]}
            for doc in docs for piece in split_text(doc["text"], chunk_size, chunk_overlap)]


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def similarity_search(vector_store, query, k=4, filter=None):
    """The k chunks closest in meaning to the query (filter: a function that gets a chunk and returns True to keep it)."""
    query_vector = embedder.embed_query_sync(query)[0]
    scored = [(cosine_similarity(query_vector, v), c) for v, c in zip(vector_store["vectors"], vector_store["chunks"])]
    scored = [(s, c) for s, c in scored if filter is None or filter(c)]
    return [c for s, c in sorted(scored, key=lambda pair: pair[0], reverse=True)[:k]]


# ── Your work ──────────────────────────────────────────────────────────────────

def load_news(folder="data/news"):
    """One document per article, from every .json file in the folder.
    A document is a dict {"text": ..., "metadata": {...}}
    text = title + blank line + body
    metadata = {"title", "date" (first 10 characters of timestamp), "source", "ticker" (the file name)}"""
    # Skip files that do not end with .json, and hidden files starting with "."
    pass  # TODO


def build_vector_store(docs):
    """Split the docs (chunk_size=1500, chunk_overlap=100), embed the chunks, and return
    the vector store: {"chunks": chunks, "vectors": np.array(<one vector per chunk>)}."""
    # Use split_documents(docs)
    # and embedder.embed_documents_sync([...the chunk texts...]).embeddings
    pass  # TODO


def ask_news(vector_store, question, k=4):
    """Find the k closest chunks, put them in the prompt as numbered sources, and return the answer text."""
    # 1. results = similarity_search(vector_store, question, k=k)
    # 2. Build a text with one block per source: "[1] title (date)\n<text>"
    # 3. Prompt: answer only from the sources, cite [1], [2], say so if the sources do not cover it
    # 4. Return rag_agent.run_sync(prompt).output
    pass  # TODO


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    docs = load_news()
    assert docs and isinstance(docs[0], dict), "load_news should return a list of dicts"
    assert set(docs[0]["metadata"]) == {"title", "date", "source", "ticker"}, "Check the metadata keys"
    print(f"✅ load_news: {len(docs)} articles")

    vector_store = build_vector_store(docs)
    closest = similarity_search(vector_store, "acquisition", k=1)
    assert closest, "build_vector_store should return a vector store with the chunks"
    print(f"✅ build_vector_store: closest to 'acquisition' -> {closest[0]['metadata']['title'][:60]}")

    answer = ask_news(vector_store, "Why did bank stocks fall in mid October 2026?")
    assert isinstance(answer, str) and "[" in answer, "ask_news should return the answer, with [n] citations"
    print("✅ ask_news:", answer[:150].replace("\n", " "), "...")

    print("\n🎉 Module 5 exercise done!")
