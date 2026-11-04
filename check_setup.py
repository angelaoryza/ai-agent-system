"""
Pre-course check. Run from the project root:  python check_setup.py

Checks the Python version, the packages, the keys in .env (without printing them),
the Sectors API, the OpenAI model, the open-source embedding model and the Sectors MCP server,
and (optional) what the Module 7.5 tools need.
Uses 1 model call and 1 Sectors credit. The first run downloads the embedding model (about 420 MB).
"""

import os
import sys
import asyncio
import warnings

warnings.filterwarnings("ignore")
results = []


def report(name, ok, detail=""):
    results.append(ok)
    print(f"{'✅ PASS' if ok else '❌ FAIL'}  {name}  {detail}")


# ── Python and packages ────────────────────────────────────────────────────────

report("Python 3.11 or newer", sys.version_info >= (3, 11), sys.version.split()[0])

try:
    import requests, bs4, pandas, numpy, dotenv, apscheduler, pydantic_ai, sentence_transformers, fastmcp  # noqa: F401
    import ddgs, langchain_google_community, magic_hour  # noqa: F401
    report("Packages from requirements.txt", True)
except ImportError as e:
    report("Packages from requirements.txt", False, f"missing: {e.name}. Run: pip install -r requirements.txt")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

# ── Keys ───────────────────────────────────────────────────────────────────────

report(".env file in this folder", os.path.exists(".env"), "" if os.path.exists(".env") else "copy .env.example to .env")
for name in ("SECTORS_API_KEY", "OPENAI_API_KEY", "OPENAI_URL"):
    value = os.getenv(name, "")
    report(f"{name} is set", bool(value) and "your-" not in value)

# ── Sectors REST API ───────────────────────────────────────────────────────────

try:
    response = requests.get("https://api.sectors.app/v2/company/report/NISP/",
                            headers={"Authorization": os.getenv("SECTORS_API_KEY")},
                            params={"sections": "overview"}, timeout=30)
    response.raise_for_status()
    overview = response.json()["overview"]
    report("Sectors REST API", True, f"NISP closed at {overview['last_close_price']} on {overview['latest_close_date']}")
except Exception as e:
    report("Sectors REST API", False, str(e)[:150])

# ── OpenAI model and open-source embeddings ────────────────────────────────────

from pydantic_ai import Agent, Embedder
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

try:
    model = OpenAIResponsesModel(
        os.getenv("OPENAI_MODEL", "gpt-6.1-sol"),
        provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_URL")),
    )
    report("OpenAI model", True, Agent(model).run_sync("Reply with the word OK.").output.strip()[:20])
except Exception as e:
    report("OpenAI model", False, str(e)[:150])

try:
    embedder = Embedder("sentence-transformers:all-mpnet-base-v2")
    report("Embedding model", True, f"{len(embedder.embed_query_sync('bank stocks')[0])} numbers per text")
except Exception as e:
    report("Embedding model", False, str(e)[:150])

# ── Sectors MCP server ─────────────────────────────────────────────────────────


async def list_mcp_tools():
    from pydantic_ai.mcp import MCPToolset

    sectors = MCPToolset(
        os.getenv("SECTORS_MCP_URL", "https://sectors-mcp.supertype.ai/mcp"),
        headers={"Authorization": os.getenv("SECTORS_API_KEY")},
    )
    async with sectors:
        return await sectors.list_tools()

try:
    tools = asyncio.run(list_mcp_tools())
    report("Sectors MCP server", len(tools) > 0, f"{len(tools)} tools")
except Exception as e:
    report("Sectors MCP server", False, str(e)[:150])

# ── Module 7.5 tools (optional: without one, only that tool is skipped) ─────────


def optional(name, ok, detail=""):
    print(f"{'✅ PASS' if ok else '⚠️  MISSING'}  {name}  {detail}")


optional("MAGIC_API_KEY is set (image generation)", "your-" not in os.getenv("MAGIC_API_KEY", "your-"))
optional("MY_EMAIL is set (Gmail test)", "@" in os.getenv("MY_EMAIL", "") and "example.com" not in os.getenv("MY_EMAIL", ""))
optional("credentials.json for Gmail", os.path.exists("credentials.json"), "" if os.path.exists("credentials.json") else "ask the trainer")

print("\nAll checks passed. You are ready for class." if all(results)
      else "\nSome checks failed. Fix them, or send this output to the trainer.")
