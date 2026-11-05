"""
Module 3 (starter): automation. Turn the data layer into a report that runs by itself, with no LLM.

What to build here (about 30 minutes):
    1. build_account_section(account)        the account section: this week against last week, all numbers in code
    2. run_weekly_report(client, week_end)   collect, build, render, save and log; never raises
    3. start_scheduler()                     run the report every Monday at 07:00 Jakarta time

The market, call report and news sections, the rendering, the saving and the log are Given.
Check your work (serve the news page first, as in Module 2):
    python main.py m3

Copilot is allowed.
"""

import os
import time
from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from config import CLIENT, WEEK_END
from m2_data_layer import collect_client_data, save_json


# ── Given: the other sections, the report and the log ──────────────────────────

def weekly_price_change(prices):
    """Last close of this week against the last close a week earlier."""
    if len(prices) < 2:
        return {"change": None, "reason": "fewer than two trading days of prices"}
    last = prices[-1]
    week_ago = str(date.fromisoformat(last["date"]) - timedelta(days=7))
    earlier = [p for p in prices if p["date"] <= week_ago]
    if not earlier:
        return {"change": None, "reason": f"no price on or before {week_ago}"}
    return {"close": last["close"], "date": last["date"], "previous_close": earlier[-1]["close"],
            "previous_date": earlier[-1]["date"], "change": round((last["close"] / earlier[-1]["close"] - 1) * 100, 1)}


def build_market_section(market):
    """Company overview and transaction (price) data in one section, plus the latest quarter."""
    if not market:
        return {"title": "Market (Sectors)", "status": "missing", "text": "Not available this week: Sectors could not be reached and there is no saved copy."}
    overview, price, q = market["overview"], weekly_price_change(market["prices"]), market["financials"]
    price_line = (f"Share price IDR {price['close']:,} on {price['date']}, {price['change']:+.1f}% against IDR "
                  f"{price['previous_close']:,} on {price['previous_date']}." if price["change"] is not None
                  else f"Weekly price change not available: {price['reason']}.")
    text = "\n".join([f"{overview['name']}, {overview['sector']}. Market cap IDR {overview['market_cap'] / 1e12:,.1f}T.", "",
                      price_line, "",
                      f"Quarter to {q['quarter_end']}: revenue IDR {q['revenue'] / 1e12:,.1f}T, earnings IDR {q['earnings'] / 1e12:,.1f}T, "
                      f"total debt IDR {q['total_debt'] / 1e12:,.1f}T, equity IDR {q['total_equity'] / 1e12:,.1f}T, cash IDR {q['cash'] / 1e12:,.1f}T."])
    cached = overview["is_cached"] or q["is_cached"]
    return {"title": "Market (Sectors)", "status": "saved copy" if cached else "ok", "text": text,
            "data": {"price": price}, "source": "Sectors API"}


def build_call_report_section(call_reports):
    if not call_reports:
        return {"title": "From our last meeting", "status": "missing", "text": "No call report could be read."}
    latest = call_reports[0]
    text = (f"Latest meeting: {latest['meeting_date']} (`{os.path.basename(latest['file'])}`, {len(latest['pages'])} pages). "
            f"{len(call_reports)} call reports on file. Not summarised yet.")
    return {"title": "From our last meeting", "status": "ok", "text": text, "source": "call reports"}


def build_news_section(news):
    if news is None:
        return {"title": "News this week", "status": "missing", "text": "Not available: the news page could not be read."}
    if not news["articles"]:
        return {"title": "News this week", "status": "ok", "text": "No news about the client this week."}
    text = "\n".join(f"- {a['date']}: [{a['title']}]({a['link']})" for a in news["articles"])
    return {"title": "News this week", "status": "saved copy" if news["is_cached"] else "ok", "text": text, "source": news["source"]}


def render_report(client, week_end, sections, problems):
    lines = [f"# Weekly Client Report: {client['name']} ({client['ticker']})", "",
             f"Week ending {week_end}. For the relationship manager; not for the client.", ""]
    for section in sections.values():
        mark = {"ok": "", "saved copy": " (saved copy)", "missing": " (missing)"}[section["status"]]
        lines += [f"## {section['title']}{mark}", "", section["text"], ""]
    sources = ", ".join(s["source"] for s in sections.values() if s.get("source"))
    status = "complete" if all(s["status"] == "ok" for s in sections.values()) else "partial"
    lines += ["---", f"*Sources: {sources}. Generated {time.strftime('%Y-%m-%d %H:%M')}. Status: {status}.*"]
    if problems:
        lines += ["", "*Problems: " + "; ".join(problems) + "*"]
    return "\n".join(lines)


def save_report(markdown, client, week_end):
    os.makedirs("output/reports", exist_ok=True)
    path = f"output/reports/{client['ticker']}_{week_end}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path


def write_run_log(status, details):
    os.makedirs("output", exist_ok=True)
    with open("output/run_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')} {status}: {details}\n")


# ── Your work ──────────────────────────────────────────────────────────────────

def build_account_section(account):
    """Return {"title": "Account activity", "status", "text", "data", "source"}.
    If account is None, return status "missing" and a text that starts with "Not available".
    Otherwise status "ok" and a Markdown table: inflow, outflow, average balance and facility usage,
    this week, last week and the change (% for money, points for facility usage)."""
    # 1. account["this_week"] and account["last_week"] hold the numbers; the changes are already computed,
    #    except the average balance change: (this / last - 1) * 100.
    # 2. Show money in billions with one decimal: f"IDR {value / 1e9:,.1f}B".
    raise NotImplementedError("TODO build_account_section")


def run_weekly_report(client=CLIENT, week_end=WEEK_END):
    """Collect the data, build the four sections, render and save the report, and write one log line
    ("ok" when every section is ok, else "partial"). Return the report path.
    Never raise: on any error, write a "failed" log line and return None."""
    # 1. data = collect_client_data(client, week_end)
    # 2. sections = {"account": build_account_section(data.get("account")), "market": ..., "call_reports": ..., "news": ...}
    # 3. save_report(render_report(...), client, week_end), then save_json({"data": data, "sections": sections}, ...)
    #    next to it (Module 4 reads it), then write_run_log(status, details).
    raise NotImplementedError("TODO run_weekly_report")


def start_scheduler():
    """Create a BackgroundScheduler in Jakarta time, add run_weekly_report every Monday at 07:00,
    start it, and return (scheduler, job)."""
    # Use: scheduler.add_job(run_weekly_report, "cron", day_of_week=..., hour=..., minute=...)
    raise NotImplementedError("TODO start_scheduler")
