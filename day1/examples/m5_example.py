"""
Module 5 example: ask questions about the saved bank news (RAG).

What it does:
    Loads the news saved by Module 2 (data/news/*.json), splits it into chunks, embeds the
    chunks with an open-source model that runs on your laptop (all-mpnet-base-v2), and answers
    a question using only the closest chunks, with sources.

How to run (from the project root; run day1/examples/m2_example.py first):
    python day1/examples/m5_example.py
    python day1/examples/m5_example.py "What did the news say about NISP?"

Expected output:
    📰 40 articles -> 61 chunks
    ❓ Why did Indonesian bank stocks fall sharply in mid October 2026?
    💬 ... MSCI ... [1] ...
    📚 Sources:
    [1] <title> (2026-10-..)
"""

import os
import sys
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


def build_vector_store(chunks):
    vectors = embedder.embed_documents_sync([c["text"] for c in chunks]).embeddings
    return {"chunks": chunks, "vectors": np.array(vectors)}


def similarity_search(vector_store, query, k=4, filter=None):
    query_vector = embedder.embed_query_sync(query)[0]
    scored = [(cosine_similarity(query_vector, v), c) for v, c in zip(vector_store["vectors"], vector_store["chunks"])]
    scored = [(s, c) for s, c in scored if filter is None or filter(c)]
    return [c for s, c in sorted(scored, key=lambda pair: pair[0], reverse=True)[:k]]


def load_news(folder="data/news"):
    docs, seen_titles = [], set()
    for file in sorted(os.listdir(folder)):
        if not file.endswith(".json") or file.startswith("."):
            continue
        with open(os.path.join(folder, file), encoding="utf-8") as f:
            articles = json.load(f)
        for article in articles:
            if article["title"] in seen_titles:
                continue
            seen_titles.add(article["title"])
            docs.append({
                "text": article["title"] + "\n\n" + article["body"],
                "metadata": {"title": article["title"], "date": article["timestamp"][:10],
                             "source": article["source"], "ticker": file.replace(".json", "")},
            })
    return docs


def ask_news(vector_store, question, k=4):
    results = similarity_search(vector_store, question, k=k)
    sources = ""
    for i, doc in enumerate(results, start=1):
        sources += f"[{i}] {doc['metadata']['title']} ({doc['metadata']['date']})\n{doc['text']}\n\n"

    prompt = f"""Answer the question using only the sources below. Cite them as [1], [2], ...
If the sources do not answer the question, say "The saved news does not cover this."
Never give buy or sell advice.

<sources>
{sources}</sources>

Question: {question}"""
    return rag_agent.run_sync(prompt).output, results


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "Why did Indonesian bank stocks fall sharply in mid October 2026?"

    docs = load_news()
    chunks = split_documents(docs)
    print(f"📰 {len(docs)} articles -> {len(chunks)} chunks")

    vector_store = build_vector_store(chunks)
    answer, results = ask_news(vector_store, question)

    print(f"\n❓ {question}\n\n💬 {answer}\n\n📚 Sources:")
    for i, doc in enumerate(results, start=1):
        print(f"[{i}] {doc['metadata']['title']} ({doc['metadata']['date']}) {doc['metadata']['source']}")


if __name__ == "__main__":
    main()
