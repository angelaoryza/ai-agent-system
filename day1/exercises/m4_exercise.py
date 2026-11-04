"""
Module 4 Exercise: put the report in the prompt and get a digest back.

Write three things:
    1. build_prompt(report)    the prompt: the report between tags + the task
    2. write_digest(report)    one call to the LLM, returns the text
    3. BankDigest              a Pydantic model, used for structured output

Run  python day1/examples/m3_example.py --now  first (it writes today's report), then:
    python day1/exercises/m4_exercise.py

Copilot is allowed. The checks use 2 model calls.
"""

import os
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

load_dotenv()

model = OpenAIResponsesModel(
    os.getenv("OPENAI_MODEL", "gpt-6.1-sol"),
    provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_URL")),
)

SYSTEM_PROMPT = """You write a short morning digest of Indonesian bank stocks for relationship managers.
Use only the facts in the report. Quote numbers exactly, with their dates.
Never give buy, sell or hold advice, price targets or predictions."""

digest_agent = Agent(model, instructions=SYSTEM_PROMPT)  # the rules live in the agent


def build_prompt(report):
    """Return the prompt: the report between <report> tags, then the task."""
    pass  # TODO


def write_digest(report):
    """Run digest_agent with build_prompt(report) and return the reply text."""
    # Use digest_agent.run_sync(...) and read the text with .output
    pass  # TODO


# Define BankDigest with: ticker (str), last_close (int),
# trend (only "up", "down" or "flat"), summary (str)
class BankDigest(BaseModel):
    pass  # TODO


class MorningDigest(BaseModel):
    headline: str
    banks: list[BankDigest]


# ── Check your work (do not edit) ──────────────────────────────────────────────

if __name__ == "__main__":
    with open(f"output/reports/report_{date.today()}.md", encoding="utf-8") as f:
        report = f.read()

    prompt = build_prompt(report)
    assert isinstance(prompt, str), "build_prompt should return the prompt as a string"
    assert "<report>" in prompt and report in prompt, "Put the report between <report> tags"
    print("✅ build_prompt")

    digest = write_digest(report)
    assert isinstance(digest, str) and len(digest) > 50, "write_digest should return the reply text"
    print("✅ write_digest:", digest[:120].replace("\n", " "), "...")

    assert set(BankDigest.model_fields) == {"ticker", "last_close", "trend", "summary"}, "BankDigest fields"
    result = digest_agent.run_sync(prompt, output_type=MorningDigest).output
    assert result.banks and all(b.trend in ("up", "down", "flat") for b in result.banks)
    print("✅ BankDigest:", [(b.ticker, b.trend) for b in result.banks])

    print("\n🎉 Module 4 exercise done!")
