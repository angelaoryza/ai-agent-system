"""
Module 3 Exercise: turn the data layer into a scheduled report.

Write three functions:
    1. build_company_report(ticker)   overview + last 10 trading days in one dict
    2. run_daily_report(tickers)      all banks; one failing bank must not stop the run
    3. start_scheduler()              run the report every weekday at 07:30 Jakarta time

Replace each TODO, then run from the project root:
    python day1/exercises/m3_exercise.py

Copilot is allowed.
"""

import os
import requests
import pandas as pd
from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.sectors.app/v2"
HEADERS = {"Authorization": os.getenv("SECTORS_API_KEY")}
TICKERS = ["BBCA", "BBRI", "BMRI", "NISP"]


# ── Given: the data functions from Module 2 ────────────────────────────────────

def get_company_report(ticker):
    url = f"{BASE_URL}/company/report/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"sections": "overview"}, timeout=30)
    response.raise_for_status()
    return response.json()


def get_daily_prices(ticker, days=30):
    end = date.today()
    start = end - timedelta(days=days)
    url = f"{BASE_URL}/daily/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"start": str(start), "end": str(end)}, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json())


# ── Your work ──────────────────────────────────────────────────────────────────

def build_company_report(ticker):
    """Return a dict with: ticker, company_name, market_cap, last_date, last_close,
    daily_change (last / previous - 1) and period_change (last / first - 1) over the
    last 10 trading days."""
    # 1. report = get_company_report(ticker)
    # 2. prices = get_daily_prices(ticker).tail(10)
    # 3. Build the dict. The overview is in report["overview"].
    pass  # TODO


def run_daily_report(tickers=TICKERS):
    """Build the report for every ticker. A failing ticker is skipped, not fatal.
    Save one Markdown line per bank to output/reports/report_<date>.md and return
    (rows, failed): the list of dicts that worked and the list of tickers that failed."""
    # 1. Loop over the tickers with try/except around build_company_report(ticker).
    # 2. Write the file: a title, one line per bank, and a line listing the failed tickers.
    pass  # TODO


def start_scheduler():
    """Create a BackgroundScheduler in Jakarta time, add run_daily_report every
    weekday at 07:30, start it, and return (scheduler, job)."""
    # Use: scheduler.add_job(run_daily_report, "cron", day_of_week=..., hour=..., minute=...)
    pass  # TODO


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    nisp = build_company_report("NISP")
    assert nisp["company_name"] == "PT Bank OCBC NISP Tbk", "company_name comes from the report"
    assert set(nisp) >= {"last_close", "daily_change", "period_change"}, "Missing keys in the dict"
    print(f"✅ build_company_report: NISP {nisp['last_close']} ({nisp['daily_change']:+.2%})")

    rows, failed = run_daily_report(["BBCA", "XXXX", "NISP"])
    assert [r["ticker"] for r in rows] == ["BBCA", "NISP"], "BBCA and NISP should work"
    assert failed == ["XXXX"], "XXXX should be in failed, and the run should go on"
    assert os.path.exists(f"output/reports/report_{date.today()}.md"), "Save the report file"
    print("✅ run_daily_report: one bad ticker did not stop the run")

    scheduler, job = start_scheduler()
    nxt = job.next_run_time
    scheduler.shutdown()
    assert (nxt.hour, nxt.minute) == (7, 30) and nxt.weekday() < 5, f"Next run should be a weekday at 07:30, got {nxt}"
    print(f"✅ start_scheduler: next run {nxt}")

    print("\n🎉 Module 3 exercise done!")
