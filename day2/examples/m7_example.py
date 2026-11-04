"""
Module 7 example: the IDX Market Assistant agent, with approval before actions.

What it does:
    Builds an agent with Pydantic AI's Agent: 3 Sectors tools to read data and 1 action tool
    (save_note) that needs your approval. Asks a company question, a ranking question,
    and a request to save a note; you approve or reject the save in the terminal.

How to run (from the project root; about 6-10 model calls):
    python day2/examples/m7_example.py

Expected output:
    ❓ How did NISP trade over the last week?
    🔧 Tools used: ['get_daily_prices']
    💬 ...
    ⏸️ The agent wants to run save_note with {'filename': 'roe_leaders.txt', 'text': '...'}
    Approve? (y/n):
"""

import os
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
from pydantic_ai import Agent, Tool, DeferredToolRequests, DeferredToolResults, ToolDenied
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

BASE_URL = "https://api.sectors.app/v2"
HEADERS = {"Authorization": os.getenv("SECTORS_API_KEY")}

model = OpenAIResponsesModel(
    os.getenv("OPENAI_MODEL", "gpt-6.1-sol"),
    provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_URL")),
)


# ── Tools ──────────────────────────────────────────────────────────────────────

def get_company_overview(ticker: str) -> dict:
    """Get the profile and latest closing price of one company on the Indonesia Stock Exchange.
    Use it for questions about a single company, e.g. "How did NISP close?".

    Args:
        ticker: 4-letter IDX code, e.g. BBCA, BBRI, BMRI, NISP.
    """
    url = f"{BASE_URL}/company/report/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"sections": "overview"}, timeout=30)
    return response.json()


def get_daily_prices(ticker: str, days: int = 10) -> list:
    """Get the daily closing prices and volumes of one IDX company for the last `days` calendar days.
    Use it for questions about how a stock moved recently, e.g. "How did BMRI do this week?".

    Args:
        ticker: 4-letter IDX code, e.g. BMRI.
        days: how many calendar days back to look (a week is 7).
    """
    end = date.today()
    start = end - timedelta(days=days)
    url = f"{BASE_URL}/daily/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"start": str(start), "end": str(end)}, timeout=30)
    return response.json()


def get_top_banks(metric: str = "market_cap", n: int = 5) -> dict:
    """Rank Indonesian listed banks by a metric, highest first.
    Use it for ranking questions such as "Which banks are the largest?" or "Which bank has the highest ROE?".

    Args:
        metric: one of market_cap, roe_ttm (return on equity), pe_ttm (price/earnings), pb_mrq (price/book), yield_ttm (dividend yield).
        n: how many banks to return.
    """
    params = {"where": "sub_sector='banks'", "order_by": f"-{metric}", "limit": n, "include_query_values": "true"}
    response = requests.get(f"{BASE_URL}/companies/", headers=HEADERS, params=params, timeout=30)
    return response.json()


def save_note(filename: str, text: str) -> str:
    """Save a short note to a text file in the output folder. Use it only when the user asks to save something."""
    os.makedirs("output/notes", exist_ok=True)
    with open(f"output/notes/{filename}", "w", encoding="utf-8") as f:
        f.write(text)
    return f"Note saved to output/notes/{filename}"


# ── Agent ──────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the IDX Market Assistant for relationship managers at a bank in Indonesia.
Use the tools to get data; never guess a number. Say the date of every price you quote.
Never give buy, sell or hold advice. Only save a note when the user asks."""

agent = Agent(
    model,
    tools=[get_company_overview, get_daily_prices, get_top_banks, Tool(save_note, requires_approval=True)],
    instructions=SYSTEM_PROMPT,
    output_type=[str, DeferredToolRequests],
)


def ask(question):
    result = agent.run_sync(question)

    while isinstance(result.output, DeferredToolRequests):     # the agent paused for approval
        decisions = {}
        for call in result.output.approvals:
            print(f"⏸️ The agent wants to run {call.tool_name} with {call.args_as_dict()}")
            if input("Approve? (y/n): ").strip().lower() == "y":
                decisions[call.tool_call_id] = True
            else:
                decisions[call.tool_call_id] = ToolDenied("The reviewer rejected this.")
        result = agent.run_sync(message_history=result.all_messages(),
                                deferred_tool_results=DeferredToolResults(approvals=decisions))

    used = [p.tool_name for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)]
    print(f"🔧 Tools used: {used}")
    print(f"💬 {result.output}")


if __name__ == "__main__":
    questions = ["How did NISP trade over the last week?",
                 "Which three banks have the highest return on equity? Save the ranking in a note called roe_leaders.txt"]
    for question in questions:
        print(f"\n❓ {question}")
        ask(question)
