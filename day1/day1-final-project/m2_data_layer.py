"""
Module 2 (starter): the data layer. Four sources into clean, labelled Python objects.

What to build here (about 30 minutes):
    1. get_quarterly_financials(ticker)   the latest quarter from Sectors, or the saved copy when Sectors is down
    2. load_account(path)                 the account CSV, checked and cleaned
    3. read_pdf_text(path)                the text of each page of a PDF
    4. load_call_reports(folder)          every call report, newest first
    5. scrape_news(url, week_end)         this week's articles from the news page

Everything marked "Given" is finished. Replace each `raise NotImplementedError` with your code.
Check your work from this folder (serve the news page first, in a second terminal:
python -m http.server 8000 --directory data/news_site):
    python main.py m2

Copilot is allowed: read every line it writes.
"""

import os
import re
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pypdf import PdfReader
from urllib.parse import urljoin
from datetime import date, timedelta

from config import BASE_URL, HEADERS, ACCOUNT_COLUMNS


# ── Given: Sectors and saved copies ────────────────────────────────────────────

def get_sectors(path, params=None, retries=3):
    """GET one Sectors endpoint. Raises ConnectionError when it cannot be reached after `retries` attempts."""
    for attempt in range(retries):
        try:
            response = requests.get(BASE_URL + path, headers=HEADERS, params=params, timeout=30)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            continue
        response.raise_for_status()
        return response.json()
    raise ConnectionError(f"Sectors unavailable for {path}")


def load_sample(name):
    with open(f"data/sample/{name}.json", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_company_overview(ticker):
    try:
        report, is_cached = get_sectors(f"/company/report/{ticker}/", {"sections": "overview"}), False
    except ConnectionError:
        report, is_cached = load_sample(f"report_{ticker}"), True
    overview = report["overview"]
    return {"name": report["company_name"], "sector": overview["sector"], "market_cap": overview["market_cap"],
            "source": "Sectors", "is_cached": is_cached}


def get_daily_prices(ticker, start, end):
    try:
        return get_sectors(f"/daily/{ticker}/", {"start": start, "end": end})
    except ConnectionError:
        return load_sample(f"daily_{ticker}")


# ── Your work ──────────────────────────────────────────────────────────────────

def get_quarterly_financials(ticker):
    """Return a dict with quarter_end, revenue, earnings, total_debt, total_equity, cash,
    plus source ("Sectors"), fetched_at and is_cached."""
    # 1. get_sectors(f"/financials/quarterly/{ticker}/", {"n_quarters": 1}) returns a list: take [0].
    # 2. On ConnectionError, print a warning and use load_sample(f"quarterly_{ticker}")[0]; is_cached = True.
    # 3. quarter_end is the "date" field and cash is "cash_only".
    raise NotImplementedError("TODO get_quarterly_financials")


def load_account(path):
    """Return (table, notes): the clean rows, and {"bad_rows": n, "duplicates": n}."""
    # 1. pd.read_csv(path, dtype=str). If a column of ACCOUNT_COLUMNS is missing, raise ValueError naming it.
    # 2. Parse "date" with pd.to_datetime and the other columns with pd.to_numeric (errors="coerce").
    # 3. Rows with a value that did not parse are bad: count them, then drop them.
    # 4. Count the duplicate dates, drop them, and sort by date.
    raise NotImplementedError("TODO load_account")


def read_pdf_text(path):
    """Return one dict per page: {"page": 1, "text": ..., "has_text": True}.
    has_text is False when a page has fewer than 50 characters (likely scanned): print a warning."""
    # Use PdfReader(path).pages and page.extract_text().
    raise NotImplementedError("TODO read_pdf_text")


def load_call_reports(folder):
    """Return (reports, skipped). Each report: {"meeting_date", "file", "pages"}, newest first.
    The meeting date comes from the file name (YYYY-MM-DD_call_report.pdf); skip a file without one."""
    # 1. Loop over the .pdf files. date.fromisoformat(file[:10]) raises ValueError when there is no date.
    # 2. pages = read_pdf_text(path)
    # 3. Sort by meeting_date, newest first.
    raise NotImplementedError("TODO load_call_reports")


def scrape_news(url, week_end, days=7):
    """Return {"articles": [...], "source": url, "fetched_at": ..., "is_cached": ...}.
    Each article: title, date, link, text. Keep the articles of the last `days` days up to week_end."""
    # 1. requests.get the page. On requests.exceptions.RequestException, read data/sample/news_ASII.html.
    # 2. Each article is <article class="news-item">: the title and link in h2 > a,
    #    the date in <time datetime="...">, the text in <div class="body">.
    # 3. Make the link absolute with urljoin(url, href).
    raise NotImplementedError("TODO scrape_news")


# ── Given: the account week, saving the news, and all four sources in one call ─

def summarize_account_week(table, week_end):
    """This week (the 7 days to week_end) against the week before: inflow, outflow, average balance, facility usage."""
    end = pd.Timestamp(week_end)
    weeks = {}
    for name, back in (("this_week", 0), ("last_week", 7)):
        rows = table[(table["date"] > end - pd.Timedelta(days=back + 7)) & (table["date"] <= end - pd.Timedelta(days=back))]
        weeks[name] = {"inflow": int(rows["inflow"].sum()), "outflow": int(rows["outflow"].sum()),
                       "avg_balance": int(rows["end_balance"].mean()),
                       "facility_usage": float(round(rows["facility_used"].iloc[-1] / rows["facility_limit"].iloc[-1] * 100, 1))}
    now, before = weeks["this_week"], weeks["last_week"]
    return {**weeks, "inflow_change": round((now["inflow"] / before["inflow"] - 1) * 100, 1),
            "outflow_change": round((now["outflow"] / before["outflow"] - 1) * 100, 1),
            "usage_change_points": round(now["facility_usage"] - before["facility_usage"], 1),
            "source": "account activity", "as_of": str(table[table["date"] <= end]["date"].max().date())}


def save_news_txt(articles, folder="data/news"):
    """One .txt per article (Module 5 reads them). Existing files are kept."""
    os.makedirs(folder, exist_ok=True)
    for article in articles:
        slug = re.sub(r"[^a-z0-9]+", "-", article["title"].lower())[:50].strip("-")
        path = f"{folder}/{article['date']}_{slug}.txt"
        if os.path.exists(path):
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Source: {article['link']}\nDate: {article['date']}\nTitle: {article['title']}\n---\n{article['text']}\n")


def collect_client_data(client, week_end):
    """All four sources for one client. One source failing never stops the others: it is reported in
    data["status"] and data["problems"]."""
    data, status, problems = {"client": client["name"], "week_end": week_end}, {}, []
    end = date.fromisoformat(week_end)
    try:
        data["account"], status["account"] = summarize_account_week(load_account(client["account_file"])[0], week_end), "ok"
    except Exception as e:
        status["account"] = "failed"
        problems.append(f"account: {e}")
    try:
        data["call_reports"], status["call_reports"] = load_call_reports(client["call_report_folder"])[0], "ok"
    except Exception as e:
        status["call_reports"] = "failed"
        problems.append(f"call_reports: {e}")
    try:
        overview, financials = get_company_overview(client["ticker"]), get_quarterly_financials(client["ticker"])
        prices = get_daily_prices(client["ticker"], str(end - timedelta(days=13)), week_end)
        data["market"] = {"overview": overview, "prices": prices, "financials": financials}
        status["market"] = "saved copy" if overview["is_cached"] or financials["is_cached"] else "ok"
    except Exception as e:
        status["market"] = "failed"
        problems.append(f"market: {e}")
    try:
        data["news"] = scrape_news(client["news_url"], week_end)
        save_news_txt(data["news"]["articles"])
        status["news"] = "saved copy" if data["news"]["is_cached"] else "ok"
    except Exception as e:
        status["news"] = "failed"
        problems.append(f"news: {e}")
    for source, state in status.items():
        print(f"{'✅' if state == 'ok' else '⚠️' if state == 'saved copy' else '❌'} {source}: {state}")
    data["status"], data["problems"] = status, problems
    return data
