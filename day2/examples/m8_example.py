"""
Module 8 example: an agent with tools from the Sectors MCP server.

What it does:
    Connects to the Sectors MCP server (our code is the MCP client), lists its tools,
    keeps three of them, and gives them to a Pydantic AI agent.

How to run (from the project root; about 4 model calls):
    python day2/examples/m8_example.py

Expected output:
    🔌 Sectors MCP server: 66 tools, using 3
    ❓ Which bank stocks gained most over the last 7 days?
    🔧 Tools used: ['fetch-companies-top-changes']
    💬 ...
"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from pydantic_ai import Agent
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

SYSTEM_PROMPT = f"""You are the IDX Market Assistant for relationship managers at a bank in Indonesia.
Today is {date.today()}. The MCP tools take explicit dates: work them out from today.
Use the tools to get data; never guess a number. Say the date of every price you quote.
Never give buy, sell or hold advice."""

QUESTIONS = [
    "Which bank stocks gained most over the last 7 days?",
    "How did NISP trade between 14 and 23 October 2026?",
]


async def main():
    sectors = MCPToolset(
        os.getenv("SECTORS_MCP_URL", "https://sectors-mcp.supertype.ai/mcp"),
        headers={"Authorization": os.getenv("SECTORS_API_KEY")},
    )

    async with sectors:
        tools = await sectors.list_tools()
        mcp_tools = sectors.filtered(lambda ctx, tool_def: tool_def.name in SELECTED)
        print(f"🔌 Sectors MCP server: {len(tools)} tools, using {len(SELECTED)}")

        agent = Agent(model, toolsets=[mcp_tools], instructions=SYSTEM_PROMPT)

        for question in QUESTIONS:
            result = await agent.run(question)
            used = [p.tool_name for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)]
            print(f"\n❓ {question}\n🔧 Tools used: {used}\n💬 {result.output}")


if __name__ == "__main__":
    asyncio.run(main())
