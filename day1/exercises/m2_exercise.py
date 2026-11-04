"""
Module 2 Exercise: the data layer as a script (about 30 minutes).

Write the data layer that Module 3 will run every morning:
    1. get_sectors(path, params, retries)   one request with a timeout and a retry
    2. get_daily_prices(ticker, start, end) prices, or the saved copy when Sectors is down
    3. get_news(ticker, limit)              news articles
    4. save_news(ticker, articles)          data/news/<TICKER>.json (Module 5 reads it)
    5. store_prices(prices, db_path)        add the rows to SQLite, return the row count

Replace each TODO, then run from the project root:
    python day1/exercises/m2_exercise.py

The checks at the bottom tell you when you are done. Copilot is allowed: read every line it writes.
"""

import os
import json
import time
import sqlite3
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.sectors.app/v2"
HEADERS = {"Authorization": os.getenv("SECTORS_API_KEY")}


def get_sectors(path, params=None, retries=3):
    """GET BASE_URL + path and return the JSON.

    - Timeout, connection error, status 429 or 5xx: wait 2 * attempt seconds and try again.
    - Any other error status (401, 404, ...): raise at once with response.raise_for_status().
    - Still failing after `retries` attempts: raise ConnectionError.
    """
    pass  # TODO


def get_daily_prices(ticker, start, end):
    """Daily prices (list of dicts) from /daily/{ticker}/ with start and end.

    If get_sectors raises ConnectionError, print a warning and return the saved copy
    data/sample/daily_<TICKER>.json instead. Other errors must NOT fall back.
    """
    pass  # TODO


def get_news(ticker, limit=20):
    """The latest articles about one ticker (list of dicts), from /news/."""
    pass  # TODO


def save_news(ticker, articles):
    """Save the articles to data/news/<TICKER>.json (create the folder if needed) and return the path."""
    pass  # TODO


def store_prices(prices, db_path="data/market.db"):
    """Add the price rows to the table daily_prices, without storing a day twice.

    Delete the rows of that symbol first, then append. Return the number of rows
    of that symbol in the table (use pd.read_sql).
    """
    pass  # TODO


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    prices = get_daily_prices("NISP", "2026-10-01", "2026-10-23")
    assert isinstance(prices, list) and len(prices) > 0, "get_daily_prices should return a list of rows"
    assert prices[-1]["date"] == "2026-10-23", "The last row should be 2026-10-23"
    print(f"✅ get_daily_prices: {len(prices)} rows, last close {prices[-1]['close']}")

    try:
        get_sectors("/company/report/XXXX/", retries=1)
        raise AssertionError("A 404 should raise an error")
    except requests.exceptions.HTTPError as e:
        assert e.response.status_code == 404, "A wrong ticker should give 404"
    print("✅ get_sectors: a 404 is raised, not retried")

    real_url, BASE_URL = BASE_URL, "https://api.sectors.app.invalid/v2"     # pretend Sectors is down
    saved = get_daily_prices("NISP", "2026-10-01", "2026-10-23")
    BASE_URL = real_url
    assert isinstance(saved, list) and len(saved) > 0, "When Sectors is down, return the saved copy"
    print(f"✅ fallback: {len(saved)} rows from data/sample/")

    news = get_news("NISP", limit=20)
    assert isinstance(news, list) and len(news) == 20, "get_news should return 20 articles"
    assert "title" in news[0], "Each article should have a title"
    print(f"✅ get_news: {news[0]['title'][:60]}...")

    path = save_news("NISP", news)
    with open(path, encoding="utf-8") as f:
        assert json.load(f) == news, "The saved file should contain the same articles"
    print(f"✅ save_news: {path}")

    first = store_prices(prices)
    again = store_prices(prices)
    assert first == again == len(prices), "Storing the same prices twice must not duplicate rows"
    print(f"✅ store_prices: {again} rows for NISP, no duplicates")

    print("\n🎉 Module 2 exercise done!")
