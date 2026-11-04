"""
Module 2 example: the data retrieval layer, end to end.

What it does:
    For BBCA, BBRI, BMRI and NISP it pulls the company report, the last 30 days of prices
    and the latest news from Sectors, plus the list of Indonesian banks from Wikipedia.
    It saves JSON, CSV, Markdown, TXT and SQLite. If Sectors cannot be reached, it uses
    the saved copy in data/sample/.

How to run (from the project root):
    python day1/examples/m2_example.py

Expected output:
    ✅ BBCA: report, 20 price rows, 20 articles      (about 20 trading days in 30 calendar days)
    ✅ BBRI: ...
    ✅ Wikipedia: 7 state-owned banks
    ✅ Done. See output/ and data/
"""

import os
import json
import time
import sqlite3
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.sectors.app/v2"
HEADERS = {"Authorization": os.getenv("SECTORS_API_KEY")}
TICKERS = ["BBCA", "BBRI", "BMRI", "NISP"]


# ── Sectors API ────────────────────────────────────────────────────────────────

def get_sectors(path, params=None, retries=3):
    """GET one Sectors endpoint. Try again when the server is slow or busy."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(BASE_URL + path, headers=HEADERS, params=params, timeout=30)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"Attempt {attempt} for {path}: {e}")
            time.sleep(2 * attempt)
            continue
        if response.status_code == 429 or response.status_code >= 500:
            print(f"Attempt {attempt} for {path}: server answered {response.status_code}")
            time.sleep(2 * attempt)
            continue
        response.raise_for_status()   # 401, 404, ...: trying again will not help
        return response.json()
    raise ConnectionError(f"Sectors unavailable for {path}")


def load_sample(name):
    with open(f"data/sample/{name}.json", encoding="utf-8") as f:
        return json.load(f)


def get_company_report(ticker):
    try:
        return get_sectors(f"/company/report/{ticker}/", {"sections": "overview"})
    except ConnectionError:
        print(f"⚠️ Using the saved report for {ticker}")
        return load_sample(f"report_{ticker}")


def get_daily_prices(ticker, start, end):
    try:
        return get_sectors(f"/daily/{ticker}/", {"start": start, "end": end})
    except ConnectionError:
        print(f"⚠️ Using the saved prices for {ticker}")
        return load_sample(f"daily_{ticker}")


def get_news(ticker, limit=20):
    try:
        return get_sectors("/news/", {"symbols": ticker, "limit": limit})["results"]
    except ConnectionError:
        print(f"⚠️ Using the saved news for {ticker}")
        return load_sample(f"news_{ticker}")


# ── Public web page ────────────────────────────────────────────────────────────

def get_state_owned_banks():
    url = "https://en.wikipedia.org/wiki/List_of_banks_in_Indonesia"
    html = requests.get(url, headers={"User-Agent": "OCBC-AI-Masterclass/1.0"}, timeout=30).text
    first_table = BeautifulSoup(html, "html.parser").find("table", class_="wikitable")
    rows = []
    for tr in first_table.find_all("tr")[1:]:
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) >= 2:                             # skip sub-heading rows
            owner = cells[2] if len(cells) > 2 else ""  # some rows share the owner cell above
            rows.append([cells[0], cells[1], owner])
    return pd.DataFrame(rows, columns=["name", "founded", "majority_owner"])


# ── Saving ─────────────────────────────────────────────────────────────────────

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    os.makedirs("data/news", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    end = date.today()
    start = end - timedelta(days=30)
    conn = sqlite3.connect("data/market.db")
    profiles = []

    for ticker in TICKERS:
        try:
            report = get_company_report(ticker)
            prices = pd.DataFrame(get_daily_prices(ticker, str(start), str(end)))
            news = get_news(ticker)

            save_json(report, f"output/report_{ticker}.json")
            prices.to_csv(f"output/prices_{ticker}.csv", index=False)
            prices.to_sql("daily_prices", conn, if_exists="append", index=False)
            save_json(news, f"data/news/{ticker}.json")      # Module 5 reads this

            overview = report["overview"]
            profiles.append(f"## {report['company_name']} ({ticker})\n"
                            f"- Last close: {overview['last_close_price']} on {overview['latest_close_date']}\n")
            print(f"✅ {ticker}: report, {len(prices)} price rows, {len(news)} articles")
        except Exception as e:
            print(f"❌ {ticker}: {e}")

    try:
        banks = get_state_owned_banks()
        banks.to_csv("output/state_owned_banks.csv", index=False)
        print(f"✅ Wikipedia: {len(banks)} state-owned banks")
    except Exception as e:
        print(f"❌ Wikipedia: {e}")

    with open("output/bank_profiles.md", "w", encoding="utf-8") as f:
        f.write("# Bank profiles\n\n" + "\n".join(profiles))
    with open("output/run_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{date.today()}: {len(profiles)} of {len(TICKERS)} banks pulled\n")
    print("✅ Done. See output/ and data/")


if __name__ == "__main__":
    main()
