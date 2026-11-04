"""
Module 7 Exercise: build the agent with Pydantic AI, and approve actions before they run.

Write two things:
    1. agent           Agent with the tools, the system prompt, approval for save_note,
                       and output_type=[str, DeferredToolRequests]
    2. ask(...)        ask a question; when the agent pauses, approve or reject, then resume

Run from the project root:
    python day2/exercises/m7_exercise.py

Copilot is allowed. The checks use about 6 model calls.
"""

import os
import requests
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


# ── Given: the tools from Module 6 ─────────────────────────────────────────────

def get_company_overview(ticker: str) -> dict:
    """Get the profile and latest closing price of one company on the Indonesia Stock Exchange.
    Use it for questions about a single company, e.g. "How did NISP close?".

    Args:
        ticker: 4-letter IDX code, e.g. BBCA, BBRI, BMRI, NISP.
    """
    url = f"{BASE_URL}/company/report/{ticker}/"
    response = requests.get(url, headers=HEADERS, params={"sections": "overview"}, timeout=30)
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


SYSTEM_PROMPT = """You are the IDX Market Assistant for relationship managers at a bank in Indonesia.
Use the tools to get data; never guess a number. Say the date of every price you quote.
Never give buy, sell or hold advice. Only save a note when the user asks."""


# ── Your work ──────────────────────────────────────────────────────────────────

# TODO 1: create the agent with Agent(model, tools=[..., Tool(save_note, requires_approval=True)],
#         instructions=..., output_type=[str, DeferredToolRequests])
agent = None  # TODO


def ask(question, approve):
    """Ask the agent a question, in a new conversation. If it pauses for approval, decide each
    waiting call: True when approve is True, else ToolDenied("..."). Return the final result."""
    # 1. result = agent.run_sync(question)
    # 2. while isinstance(result.output, DeferredToolRequests):
    #        decisions = {call.tool_call_id: ... for call in result.output.approvals}
    # 3.     resume with agent.run_sync(message_history=result.all_messages(),
    #                                   deferred_tool_results=DeferredToolResults(approvals=decisions))
    pass  # TODO


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    assert agent is not None, "Create the agent (TODO 1)"

    result = ask("Which bank has the highest return on equity, and what was its last close?", approve=True)
    used = [p.tool_name for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)]
    assert "get_top_banks" in used, f"The agent should use the ranking tool. It used {used}"
    print("✅ ranking question:", result.output[:120].replace("\n", " "), "...")

    for f in ("rejected.txt", "approved.txt"):
        if os.path.exists(f"output/notes/{f}"):
            os.remove(f"output/notes/{f}")

    ask("Save a note called rejected.txt that says: test", approve=False)
    assert not os.path.exists("output/notes/rejected.txt"), "A rejected save must not write the file"
    print("✅ rejected: no file written")

    ask("Save a note called approved.txt that says: test", approve=True)
    assert os.path.exists("output/notes/approved.txt"), "An approved save should write the file"
    print("✅ approved: file written")

    print("\n🎉 Module 7 exercise done!")
