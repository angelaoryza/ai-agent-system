"""
Module 3 example: the daily bank report, run once or on a schedule.

What it does:
    For each bank it combines the company overview with the last 10 trading days into one
    Markdown report (output/reports/report_<date>.md). A bank that fails is listed in the
    report and in output/run_log.txt; the others still run.

How to run (from the project root):
    python day1/examples/m3_example.py --now        # one run, then stop
    python day1/examples/m3_example.py --every 20   # every 20 seconds (Ctrl+C to stop)
    python day1/examples/m3_example.py              # every weekday at 07:30 Jakarta time

Expected output for --now:
    ✅ BBCA
    ✅ BBRI
    ✅ BMRI
    ✅ NISP
    📄 Report saved: output/reports/report_<date>.md
"""

import os
import sys
import time
import requests
import pandas as pd
from datetime import date, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.sectors.app/v2"
HEADERS = {"Authorization": os.getenv("SECTORS_API_KEY")}
TICKERS = ["BBCA", "BBRI", "BMRI", "NISP"]


# ── Data (from Module 2) ───────────────────────────────────────────────────────

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


# ── Report ─────────────────────────────────────────────────────────────────────

def build_company_report(ticker):
    report = get_company_report(ticker)
    prices = get_daily_prices(ticker).tail(10)
    return {
        "ticker": ticker,
        "company_name": report["company_name"],
        "market_cap": report["overview"]["market_cap"],
        "last_date": prices["date"].iloc[-1],
        "last_close": int(prices["close"].iloc[-1]),
        "daily_change": prices["close"].iloc[-1] / prices["close"].iloc[-2] - 1,
        "period_change": prices["close"].iloc[-1] / prices["close"].iloc[0] - 1,
        "last_volume": int(prices["volume"].iloc[-1]),
        "avg_volume": float(prices["volume"].mean()),
    }


def write_report(rows, failed):
    lines = [f"# IDX Bank Report, {date.today()}", "",
             "| Ticker | Company | Last close | 1-day | 10-day | Volume vs avg |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['ticker']} | {r['company_name']} | {r['last_close']:,} | "
                     f"{r['daily_change']:+.2%} | {r['period_change']:+.2%} | {r['last_volume'] / r['avg_volume']:.2f}x |")
    if failed:
        lines += ["", "**Not included:** " + ", ".join(failed)]
    lines += ["", "*Data: Sectors. Prices as of the last trading day shown. Not investment advice.*"]
    return "\n".join(lines)


def run_daily_report(tickers=TICKERS):
    rows, failed = [], []
    for ticker in tickers:
        try:
            rows.append(build_company_report(ticker))
            print(f"✅ {ticker}")
        except Exception as e:
            print(f"❌ {ticker}: {e}")
            failed.append(ticker)

    os.makedirs("output/reports", exist_ok=True)
    path = f"output/reports/report_{date.today()}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(write_report(rows, failed))
    with open("output/run_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')} report: {len(rows)} ok, failed: {failed}\n")
    print(f"📄 Report saved: {path}")
    return path


# ── Schedule ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--now" in sys.argv:
        run_daily_report()
        sys.exit()

    scheduler = BlockingScheduler(timezone="Asia/Jakarta")
    if "--every" in sys.argv:
        seconds = int(sys.argv[sys.argv.index("--every") + 1])
        scheduler.add_job(run_daily_report, "interval", seconds=seconds)
        print(f"⏰ Report every {seconds} seconds. Ctrl+C to stop.")
    else:
        scheduler.add_job(run_daily_report, "cron", day_of_week="mon-fri", hour=7, minute=30)
        print("⏰ Report every weekday at 07:30 Jakarta time. Ctrl+C to stop.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Stopped.")
