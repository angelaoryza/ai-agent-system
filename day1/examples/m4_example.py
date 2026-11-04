"""
Module 4 example: from the daily report to an AI-written digest.

What it does:
    Reads today's report from Module 3 (run  python day1/examples/m3_example.py --now  first),
    fills a prompt template with it, and asks the model for a morning digest twice:
    as text (for people) and as structured output (for code). Saves both in output/digests/.

How to run (from the project root; 2 model calls):
    python day1/examples/m4_example.py

Expected output:
    📝 Digest:
    Indonesian bank stocks ... BBCA closed at 5,025 on 2026-10-23 ...
    📦 Structured:
    BBCA 5025 down | ...
    ✅ Saved output/digests/digest_<date>.md and .json
"""

import os
import json
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


class BankDigest(BaseModel):
    ticker: str
    last_close: int
    trend: Literal["up", "down", "flat"] = Field(description="Direction of the 10-day change")
    summary: str = Field(description="One factual sentence from the report")


class MorningDigest(BaseModel):
    headline: str
    banks: list[BankDigest]


# One template, filled with a new report every morning
DIGEST_TEMPLATE = ("<report>\n{report}\n</report>\n\n"
                   "Write the digest: one headline sentence, then one short sentence per bank.")


def main():
    report_path = f"output/reports/report_{date.today()}.md"
    if not os.path.exists(report_path):
        print("❌ No report for today. Run  python day1/examples/m3_example.py --now  first.")
        return
    with open(report_path, encoding="utf-8") as f:
        report = f.read()

    prompt = DIGEST_TEMPLATE.format(report=report)
    digest = digest_agent.run_sync(prompt).output
    print("📝 Digest:\n" + digest)

    result = digest_agent.run_sync(prompt, output_type=MorningDigest).output
    print("\n📦 Structured:")
    for bank in result.banks:
        print(bank.ticker, bank.last_close, bank.trend, "|", bank.summary)

    os.makedirs("output/digests", exist_ok=True)
    with open(f"output/digests/digest_{date.today()}.md", "w", encoding="utf-8") as f:
        f.write(digest + "\n\n*AI-generated from Sectors data. Not investment advice.*\n")
    with open(f"output/digests/digest_{date.today()}.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"\n✅ Saved output/digests/digest_{date.today()}.md and .json")


if __name__ == "__main__":
    main()
