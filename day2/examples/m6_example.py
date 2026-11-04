"""
Module 6 example: Sectors functions as tools, and the LLM choosing one.

What it does:
    Defines three Sectors tools as plain functions with docstrings. For each question, the LLM gets
    the tool descriptions and asks for a tool; our code runs that tool and the LLM writes the answer.

How to run (from the project root; about 2 model calls per question):
    python day2/examples/m6_example.py

Expected output:
    ❓ How did NISP close on its last trading day?
    🔧 LLM asks for: get_company_overview {'ticker': 'NISP'}
    💬 NISP closed at IDR 1,185 on 23 October 2026 ...
"""

import os
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
from pydantic_ai import Tool
from pydantic_ai.direct import model_request_sync
from pydantic_ai.messages import ModelRequest, ToolReturnPart
from pydantic_ai.models import ModelRequestParameters
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


TOOLS = [Tool(get_company_overview), Tool(get_daily_prices), Tool(get_top_banks)]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
PARAMS = ModelRequestParameters(function_tools=[t.tool_def for t in TOOLS])   # the tool descriptions


def ask(question):
    """One round: the LLM asks for tools, our code runs them, the LLM answers."""
    messages = [ModelRequest.user_text_prompt(question)]
    response = model_request_sync(model, messages, model_request_parameters=PARAMS)
    messages.append(response)

    returns = []
    for call in response.tool_calls:
        print(f"🔧 LLM asks for: {call.tool_name} {call.args_as_dict()}")
        result = TOOLS_BY_NAME[call.tool_name].function(**call.args_as_dict())     # our code runs the tool
        returns.append(ToolReturnPart(tool_name=call.tool_name, content=result, tool_call_id=call.tool_call_id))
    messages.append(ModelRequest(parts=returns))

    return model_request_sync(model, messages, model_request_parameters=PARAMS).text


if __name__ == "__main__":
    for question in ["How did NISP close on its last trading day?",
                     "Which three banks are the largest by market cap?"]:
        print(f"\n❓ {question}")
        print(f"💬 {ask(question)}")
