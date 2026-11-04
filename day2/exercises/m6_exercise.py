"""
Module 6 Exercise: two new Sectors tools, and the round trip as a function.

Write:
    1. get_top_movers(period, n)   tool: the banks that rose and fell most (/companies/top-changes/)
    2. get_valuation(ticker)       tool: the valuation section of a company report
    3. ask(question, tools)        one round trip: the LLM asks, our code runs the tools, the LLM answers

A tool is a plain function. The docstring is what the LLM reads: say what the tool returns, when to
use it, and what each argument means (under "Args:", after a blank line). Then run from the project root:
    python day2/exercises/m6_exercise.py

Copilot is allowed. The checks use about 4 model calls.
"""

import os
import requests
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


def get_company_overview(ticker: str) -> dict:
    """Get the profile and latest closing price of one company on the Indonesia Stock Exchange.
    Use it for questions about a single company, e.g. "How did NISP close?".

    Args:
        ticker: 4-letter IDX code, e.g. BBCA, BBRI, BMRI, NISP.
    """
    response = requests.get(f"{BASE_URL}/company/report/{ticker}/", headers=HEADERS,
                            params={"sections": "overview"}, timeout=30)
    return response.json()


# TODO 1: the tool get_top_movers(period: str = "1d", n: int = 5) -> dict
# Endpoint: f"{BASE_URL}/companies/top-changes/" with params
#   {"sub_sector": "banks", "periods": period, "classifications": "top_gainers,top_losers", "n_stock": n}
# Allowed periods: 1d, 7d, 14d, 30d, 365d. Say so in the docstring.
def get_top_movers(period: str = "1d", n: int = 5) -> dict:
    pass  # TODO


# TODO 2: the tool get_valuation(ticker: str) -> dict
# Endpoint: f"{BASE_URL}/company/report/{ticker}/" with params {"sections": "valuation"}
def get_valuation(ticker: str) -> dict:
    pass  # TODO


def ask(question, tools):
    """One round trip. `tools` is a list of plain functions. Return (answer_text, names_of_the_tools_called).

    1. Wrap each function in Tool(...), put their tool_def in ModelRequestParameters(function_tools=[...]),
       and send [ModelRequest.user_text_prompt(question)] with model_request_sync.
    2. For each tool call: run the tool with call.args_as_dict(), and collect a
       ToolReturnPart(tool_name=call.tool_name, content=result, tool_call_id=call.tool_call_id).
    3. Add the response and ModelRequest(parts=[...the returns...]), send the messages again,
       and return the final text and the tool names.
    """
    pass  # TODO


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    for t in (get_top_movers, get_valuation):
        description = Tool(t).tool_def.description or ""
        assert len(description) > 60, f"Write a full docstring for {t.__name__}: the LLM reads it"

    movers = get_top_movers(period="7d", n=3)
    assert "top_gainers" in movers and "top_losers" in movers, "get_top_movers should return gainers and losers"
    print("✅ get_top_movers:", [m["symbol"] for m in movers["top_gainers"]["7d"]])

    valuation = get_valuation("BBCA")
    assert "valuation" in valuation, "get_valuation should ask for the valuation section"
    print("✅ get_valuation:", list(valuation["valuation"])[:3])

    tools = [get_company_overview, get_top_movers, get_valuation]
    answer, used = ask("Which banks fell the most over the last 7 days?", tools)
    assert "get_top_movers" in used, f"The LLM used {used}. Improve the get_top_movers docstring."
    assert isinstance(answer, str) and answer, "ask should return the final answer text"
    print("✅ ask (movers):", answer[:120].replace("\n", " "), "...")

    answer, used = ask("What is the forward P/E of BBCA?", tools)
    assert "get_valuation" in used, f"The LLM used {used}. Improve the get_valuation docstring."
    print("✅ ask (valuation):", answer[:120].replace("\n", " "), "...")

    print("\n🎉 Module 6 exercise done!")
