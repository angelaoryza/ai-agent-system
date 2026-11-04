"""
Module 9 example: the scheduler (Day 1) triggers the agent (Day 2).

What it does:
    Every weekday at 16:30 Jakarta time (after the market closes):
      1. our CODE checks the last 10 trading days of each bank for a daily move of 5% or more;
      2. for each move found, the AGENT explains it with the news and the prices;
      3. the explanation is saved to output/alerts/.
    The scheduler decides WHEN, the code decides WHETHER, the agent decides WHAT data to use.

    The banks moved more than 5% on 16 and 20 October 2026 (the MSCI sell-off and the rebound),
    so a run in late October 2026 finds real moves.

How to run (from the project root; 3-4 model calls per alert, max 2 alerts per run):
    python day2/examples/m9_example.py --now    # check once, then stop
    python day2/examples/m9_example.py          # every weekday at 16:30 (Ctrl+C to stop)

Expected output for --now:
    📈 BBRI moved -14.8% on 2026-10-16
    🤖 Asking the agent to explain...
    ✅ Saved output/alerts/BBRI_2026-10-16.md
"""

import os
import sys
import json
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
import numpy as np
from apscheduler.schedulers.blocking import BlockingScheduler
from pydantic_ai import Agent, Embedder
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

BASE_URL = "https://api.sectors.app/v2"
HEADERS = {"Authorization": os.getenv("SECTORS_API_KEY")}
TICKERS = ["BBCA", "BBRI", "BMRI", "NISP"]
THRESHOLD = 0.05      # a daily move of 5% or more
MAX_ALERTS = 2        # at most 2 agent runs per check, to keep the cost small

model = OpenAIResponsesModel(
    os.getenv("OPENAI_MODEL", "gpt-6.1-sol"),
    provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_URL")),
)
embedder = Embedder("sentence-transformers:all-mpnet-base-v2")   # open source, runs on this computer


# ── Step 1: our code checks the condition ──────────────────────────────────────

def get_daily_prices(ticker, days=30):
    end = date.today()
    start = end - timedelta(days=days)
    url = f"{BASE_URL}/daily/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"start": str(start), "end": str(end)}, timeout=30)
    response.raise_for_status()
    return response.json()


def find_big_moves(tickers=TICKERS, threshold=THRESHOLD):
    moves = []
    for ticker in tickers:
        prices = get_daily_prices(ticker)[-11:]          # the last 10 daily changes
        for previous, today in zip(prices, prices[1:]):
            change = today["close"] / previous["close"] - 1
            if abs(change) >= threshold:
                moves.append({"ticker": ticker, "date": today["date"], "close": today["close"], "change": change})
    return sorted(moves, key=lambda m: abs(m["change"]), reverse=True)


# ── Step 2: the agent explains a move ──────────────────────────────────────────

def split_text(text, chunk_size=1500, chunk_overlap=100):
    chunks, start = [], 0
    while True:
        chunks.append(text[start:start + chunk_size])
        if start + chunk_size >= len(text):
            return chunks
        start += chunk_size - chunk_overlap


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def build_news_store():
    chunks = []
    for file in sorted(os.listdir("data/news")):
        if file.endswith(".json") and not file.startswith("."):
            with open(f"data/news/{file}", encoding="utf-8") as f:
                for article in json.load(f):
                    metadata = {"title": article["title"], "date": article["timestamp"][:10]}
                    for piece in split_text(article["title"] + "\n\n" + article["body"]):
                        chunks.append({"text": piece, "metadata": metadata})
    vectors = embedder.embed_documents_sync([c["text"] for c in chunks]).embeddings
    return {"chunks": chunks, "vectors": np.array(vectors)}


def similarity_search(vector_store, query, k=4):
    query_vector = embedder.embed_query_sync(query)[0]
    scored = [(cosine_similarity(query_vector, v), c) for v, c in zip(vector_store["vectors"], vector_store["chunks"])]
    return [c for s, c in sorted(scored, key=lambda pair: pair[0], reverse=True)[:k]]


vector_store = None   # built on the first check


def search_news(query: str) -> str:
    """Search recent Indonesian market news. Use it to find WHY something happened. It does not give prices.

    Args:
        query: what to look for, in plain words.
    """
    results = similarity_search(vector_store, query, k=4)
    return "\n\n".join(f"{c['metadata']['title']} ({c['metadata']['date']})\n{c['text']}" for c in results)


def get_prices_after(ticker: str, start_date: str) -> list:
    """Get the daily closing prices of one IDX company from start_date (YYYY-MM-DD) until today.

    Args:
        ticker: 4-letter IDX code, e.g. BBRI.
        start_date: the first date, YYYY-MM-DD.
    """
    url = f"{BASE_URL}/daily/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"start": start_date, "end": str(date.today())}, timeout=30)
    return [{"date": r["date"], "close": r["close"]} for r in response.json()]


agent = Agent(
    model,
    tools=[search_news, get_prices_after],
    instructions="""You explain big stock moves to relationship managers at a bank in Indonesia.
Use search_news for the reason and get_prices_after for what happened next. Cite article titles and dates.
If the news does not explain the move, say so. At most 6 sentences. Never give buy, sell or hold advice.""",
)


def explain_move(move):
    question = (f"On {move['date']}, {move['ticker']} closed at {move['close']:,} IDR, "
                f"{move['change']:+.1%} versus the day before. Why, and how did it trade afterwards?")
    return agent.run_sync(question).output


# ── Step 3: one scheduled check ────────────────────────────────────────────────

def run_alert_check():
    global vector_store
    moves = find_big_moves()
    if not moves:
        print("No moves of 5% or more. Nothing to explain.")
        return
    if vector_store is None:
        vector_store = build_news_store()

    os.makedirs("output/alerts", exist_ok=True)
    for move in moves[:MAX_ALERTS]:
        path = f"output/alerts/{move['ticker']}_{move['date']}.md"
        if os.path.exists(path):                 # already explained in an earlier run
            continue
        print(f"📈 {move['ticker']} moved {move['change']:+.1%} on {move['date']}")
        print("🤖 Asking the agent to explain...")
        try:
            explanation = explain_move(move)
        except Exception as e:
            explanation = f"(The agent could not explain this move: {e})"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {move['ticker']} moved {move['change']:+.1%} on {move['date']}\n\n{explanation}\n\n"
                    "*Detected by code, explained by an AI agent. Not investment advice.*\n")
        print(f"✅ Saved {path}")


if __name__ == "__main__":
    if "--now" in sys.argv:
        run_alert_check()
        sys.exit()

    scheduler = BlockingScheduler(timezone="Asia/Jakarta")
    scheduler.add_job(run_alert_check, "cron", day_of_week="mon-fri", hour=16, minute=30)
    print("⏰ Alert check every weekday at 16:30 Jakarta time. Ctrl+C to stop.")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Stopped.")
