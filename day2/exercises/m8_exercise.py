"""
Module 8 Exercise: an agent with Sectors MCP tools and a tool of our own.

Write:
    1. get_watchlist()          a local tool: the RM desk's watchlist (our data, not the provider's)
    2. get_mcp_answer(question) connect to the Sectors MCP server, keep the SELECTED tools,
                                add get_watchlist, build the agent, and return await agent.run(...)

Run from the project root:
    python day2/exercises/m8_exercise.py

Copilot is allowed. The checks use about 6 model calls.
"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from pydantic_ai import Agent, Tool
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

model = OpenAIResponsesModel(
    os.getenv("OPENAI_MODEL", "gpt-6.1-sol"),
    provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_URL")),
)

SELECTED = ["fetch-company-report", "fetch-daily-price", "fetch-companies-top-changes"]
WATCHLIST = ["BBCA", "BBRI", "BMRI", "NISP"]

SYSTEM_PROMPT = f"""You are the IDX Market Assistant for relationship managers at a bank in Indonesia.
Today is {date.today()}. The MCP tools take explicit dates: work them out from today.
Use the tools to get data; never guess a number. Say the date of every price you quote.
Never give buy, sell or hold advice."""


# TODO 1: a local tool get_watchlist() -> list that returns WATCHLIST.
# The docstring must say when to use it: questions about "my banks", "the watchlist", "our banks".
def get_watchlist() -> list:
    pass  # TODO


async def get_mcp_answer(question):
    """Answer with an agent that has the SELECTED Sectors MCP tools plus get_watchlist. Return the result."""
    # 1. sectors = MCPToolset(os.getenv("SECTORS_MCP_URL", ...), headers={"Authorization": ...})
    # 2. async with sectors:
    #        keep the SELECTED tools with sectors.filtered(lambda ctx, tool_def: ...)
    #        create the agent with toolsets=[...] and tools=[get_watchlist], and return await agent.run(question)
    pass  # TODO


def tools_used(result):
    return [p.tool_name for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)]


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    assert Tool(get_watchlist).tool_def.description, "Write a docstring for get_watchlist: it is the tool's description"
    assert get_watchlist() == WATCHLIST, "get_watchlist should return WATCHLIST"
    print("✅ get_watchlist:", get_watchlist())

    result = asyncio.run(get_mcp_answer("How did NISP close on 23 October 2026?"))
    assert result is not None, "get_mcp_answer should return the result of agent.run"
    used = tools_used(result)
    assert used and all(name in SELECTED for name in used), f"Only SELECTED MCP tools are needed here, the agent used {used}"
    assert "1,185" in result.output or "1185" in result.output, "NISP closed at 1,185"
    print("✅ MCP only:", used)

    result = asyncio.run(get_mcp_answer("Which of my watchlist banks closed highest on its last trading day?"))
    used = tools_used(result)
    assert "get_watchlist" in used, f"The agent should look up the watchlist first, it used {used}"
    assert any(name in SELECTED for name in used), f"The agent should then use an MCP tool, it used {used}"
    print("✅ Mixed:", used)
    print("✅ Answer:", result.output[:150].replace("\n", " "))
    print("\n🎉 Module 8 exercise done!")
