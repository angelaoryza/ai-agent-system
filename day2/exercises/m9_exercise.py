"""
Module 9 Exercise: the scheduler triggers the agent.

Write three things:
    1. find_big_moves()      CODE checks the condition: daily moves of 5% or more
    2. run_alert_check()     for each move, the AGENT explains it; save the explanation
    3. the scheduler         run the check every weekday at 16:30 Jakarta time

The agent and explain_move() are given (from Module 7). Run from the project root:
    python day2/exercises/m9_exercise.py

Copilot is allowed. The checks use about 3 model calls.
"""

import os
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

BASE_URL = "https://api.sectors.app/v2"
HEADERS = {"Authorization": os.getenv("SECTORS_API_KEY")}
TICKERS = ["BBCA", "BBRI", "BMRI", "NISP"]

model = OpenAIResponsesModel(
    os.getenv("OPENAI_MODEL", "gpt-6.1-sol"),
    provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_URL")),
)


def get_daily_prices(ticker, days=30):
    end = date.today()
    start = end - timedelta(days=days)
    url = f"{BASE_URL}/daily/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"start": str(start), "end": str(end)}, timeout=30)
    response.raise_for_status()
    return response.json()


# ── Given: the agent that explains a move ──────────────────────────────────────

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
    tools=[get_prices_after],
    instructions="You explain big stock moves to relationship managers. Use the price tool. "
                  "At most 4 sentences. Never give buy, sell or hold advice.",
)


def explain_move(move):
    question = (f"On {move['date']}, {move['ticker']} closed at {move['close']:,} IDR, "
                f"{move['change']:+.1%} versus the day before. How did it trade afterwards?")
    return agent.run_sync(question).output


# ── Your work ──────────────────────────────────────────────────────────────────

def find_big_moves(tickers=TICKERS, threshold=0.05):
    """For each ticker, look at the last 11 daily prices (= 10 daily changes).
    Return a list of {"ticker", "date", "close", "change"} for every day where
    abs(close / previous close - 1) >= threshold, largest move first."""
    pass  # TODO


def run_alert_check(max_alerts=1):
    """Find the big moves. For the first `max_alerts` moves, ask explain_move(move) and save
    the text to output/alerts/<TICKER>_<DATE>.md. Skip a move whose file already exists.
    Return the list of files written."""
    pass  # TODO


def start_scheduler():
    """Create a BackgroundScheduler in Jakarta time, add run_alert_check every weekday
    at 16:30, start it, and return (scheduler, job)."""
    pass  # TODO


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    moves = find_big_moves()
    print(f"Found {len(moves)} moves of 5% or more")
    if moves:
        assert all(abs(m["change"]) >= 0.05 for m in moves), "Only moves of 5% or more"
        assert abs(moves[0]["change"]) >= abs(moves[-1]["change"]), "Sort the largest move first"
        print(f"✅ find_big_moves: largest {moves[0]['ticker']} {moves[0]['change']:+.1%} on {moves[0]['date']}")

        written = run_alert_check()
        again = run_alert_check()
        assert again == [], "A move that already has a file must be skipped"
        print(f"✅ run_alert_check: wrote {written or 'nothing new'}, and skipped it the second time")
    else:
        print("   (no moves in the last 10 trading days, so run_alert_check has nothing to explain)")

    scheduler, job = start_scheduler()
    nxt = job.next_run_time
    scheduler.shutdown()
    assert (nxt.hour, nxt.minute) == (16, 30) and nxt.weekday() < 5, f"Next run should be a weekday at 16:30, got {nxt}"
    print(f"✅ start_scheduler: next run {nxt}")

    print("\n🎉 Module 9 exercise done!")
