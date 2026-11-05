"""
Module 4 (starter): the first LLM calls. Give the model the right data, get a form back, check it in code.

What to build here (about 30 minutes):
    1. build_brief_prompt(sections)        the messages: rules (system) + the code sections (human)
    2. CallReportPoints                    a Pydantic model: the form for one call report
    3. check_call_report(points, text)     code checks the form: every evidence phrase is in the report

The other forms, the news summary, the weekly brief and `add_llm_sections` (which puts it all together
and keeps the Module 3 text whenever a check fails) are Given.
Run  python main.py m3  first (it saves this week's sections), then:
    python main.py m4

Copilot is allowed. The checks use about 4 model calls.
"""

import re
import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from config import CLIENT, llm


# ── Given: the rules, the forms and the checks ─────────────────────────────────

RULES = """You write for a relationship manager (RM) at a bank in Indonesia, who reads it before talking to the client.
Use only the data between the tags. Quote numbers exactly as they appear; never calculate a new number.
If something is missing, say that it is missing. Never judge the client's creditworthiness and never
recommend a credit decision: that is for people, not for this report."""

JUDGEMENT_WORDS = ["creditworth", "credit risk", "risky", "approve the", "reject the", "recommend", "should lend"]


class Point(BaseModel):
    point: str = Field(description="One plan or request, in a short sentence")
    evidence: str = Field(description="A short phrase copied word for word from the call report")


class FollowUp(BaseModel):
    action: str
    owner: str
    due_date: str = Field(description="As written in the call report, e.g. 15 Nov 2026")


class NewsItem(BaseModel):
    link: str = Field(description="The link of the article, exactly as given")
    one_line: str = Field(description="What the article says, in one sentence")
    about_client: bool = Field(description="True only if the article is mainly about the client")


class NewsItems(BaseModel):
    items: list[NewsItem]


class Observation(BaseModel):
    text: str = Field(description="One observation for the RM, with numbers quoted exactly")
    sources: list[Literal["account", "market", "call_report", "news"]]


class WeeklyBrief(BaseModel):
    headline: str
    observations: list[Observation] = Field(description="2 to 4 observations")


CALL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RULES),
    ("human", "<call_report>\n{report}\n</call_report>\n\nFill in the form from this call report only. "
              "Copy each evidence phrase word for word."),
])

NEWS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RULES),
    ("human", "The client is {client}.\n<articles>\n{articles}\n</articles>\n\n"
              "Fill in one item per article, in the same order, with the link exactly as given."),
])


def sections_text(sections):
    return "\n\n".join(f"[{key}] {s['title']} ({s['status']})\n{s['text']}" for key, s in sections.items())


def flat(text):
    return " ".join(text.split()).lower()


# ── Your work ──────────────────────────────────────────────────────────────────

def build_brief_prompt(sections):
    """Return [("system", RULES), ("human", <sections_text(sections) between <sections> tags + the task>)].
    The task: one headline, then 2 to 4 observations, each naming its sources."""
    raise NotImplementedError("TODO build_brief_prompt")


# Define CallReportPoints with: meeting_date (str, YYYY-MM-DD), client_plans (list of Point),
# client_requests (list of Point), follow_ups (list of FollowUp)
class CallReportPoints(BaseModel):
    pass  # TODO: add the four fields


def check_call_report(points, text):
    """Return a list of problems (empty when the form passes):
    - each evidence phrase of the plans and requests must appear in the text (compare with flat(), which
      ignores line breaks, extra spaces and capitals)
    - each follow-up must have a due date"""
    raise NotImplementedError("TODO check_call_report")


# ── Given: the jobs that use your work, and their checks ───────────────────────

def call_with_form(form, messages):
    """Ask for a filled-in form. Try once more if the reply does not fit. Return (form, problem)."""
    problem = None
    for attempt in (1, 2):
        try:
            return llm.with_structured_output(form).invoke(messages), None
        except Exception as e:
            problem = f"{form.__name__} not filled in: {type(e).__name__}"
    return None, problem


def read_call_report(latest):
    text = "\n".join(page["text"] for page in latest["pages"])
    return call_with_form(CallReportPoints, CALL_PROMPT.invoke({"report": text}))


def summarize_news(articles):
    if not articles:
        return [], None                                       # no articles, no model call
    numbered = "\n\n".join(f"[{i}] {a['title']} ({a['date']})\nLink: {a['link']}\n{a['text']}" for i, a in enumerate(articles, 1))
    form, problem = call_with_form(NewsItems, NEWS_PROMPT.invoke({"client": CLIENT["name"], "articles": numbered}))
    return (form.items if form else None), problem


def write_weekly_brief(sections):
    """Only checked material goes in: the code sections, and the summaries that passed their checks."""
    return call_with_form(WeeklyBrief, build_brief_prompt(sections))


def check_news(items, articles):
    sent, got = [a["link"] for a in articles], [item.link for item in items]
    return [f"unknown link: {link}" for link in got if link not in sent] + [f"article skipped: {link}" for link in sent if link not in got]


def check_brief(brief, sections):
    problems, given = [], flat(sections_text(sections))
    if not 2 <= len(brief.observations) <= 4:
        problems.append(f"{len(brief.observations)} observations, expected 2 to 4")
    for observation in brief.observations:
        for number in re.findall(r"\d+(?:[.,]\d+)*", observation.text):
            if number not in given:
                problems.append(f"number not in the sections: {number}")
        for source in observation.sources:
            key = "call_reports" if source == "call_report" else source
            if sections.get(key, {}).get("status") == "missing":
                problems.append(f"cites a missing source: {source}")
        problems += [f"judgement language: {w}" for w in JUDGEMENT_WORDS if w in flat(observation.text)]
    return problems


def add_llm_sections(sections, data):
    """Run the three jobs and their checks. A failed check keeps the Module 3 version and says so."""
    if data.get("call_reports"):
        latest = data["call_reports"][0]
        points, problem = read_call_report(latest)
        problems = check_call_report(points, "\n".join(p["text"] for p in latest["pages"])) if points else [problem]
        if problems:
            sections["call_reports"]["text"] += f"\n\n*Not summarised: {problems[0]}.*"
        else:
            lines = [f"Meeting on {points.meeting_date} (`{os.path.basename(latest['file'])}`)."]
            lines += [f"- Plan: {p.point} (\"{p.evidence}\")" for p in points.client_plans]
            lines += [f"- Request: {p.point} (\"{p.evidence}\")" for p in points.client_requests]
            lines += [f"- Follow-up: {f.action.rstrip('.')}. Owner: {f.owner}. Due: {f.due_date}." for f in points.follow_ups]
            sections["call_reports"].update(text="\n".join(lines), data=points.model_dump())
        print(f"{'✅' if not problems else '⚠️'} call report: {'checked' if not problems else problems[0]}")

    articles = (data.get("news") or {}).get("articles") or []
    if articles:
        items, problem = summarize_news(articles)
        problems = check_news(items, articles) if items is not None else [problem]
        if problems:
            sections["news"]["text"] += f"\n\n*Not summarised: {problems[0]}.*"
        else:
            sections["news"]["text"] = "\n".join(f"- [{a['date']}]({a['link']}) {item.one_line}"
                                                 f"{'' if item.about_client else ' (mentions the client in passing)'}"
                                                 for a, item in zip(articles, items))
        print(f"{'✅' if not problems else '⚠️'} news: {'checked' if not problems else problems[0]}")

    brief, problem = write_weekly_brief(sections)
    problems = check_brief(brief, sections) if brief else [problem]
    if problems:
        text = f"Not written this week: {problems[0]}. The sections below are complete."
    else:
        text = (f"**{brief.headline}**\n\n" + "\n".join(f"- {o.text} ({', '.join(o.sources)})" for o in brief.observations)
                + "\n\n*Written by an AI model from the sections below; every number checked by code.*")
    print(f"{'✅' if not problems else '⚠️'} brief: {'checked' if not problems else problems[0]}")
    return {"brief": {"title": "This week", "status": "ok" if not problems else "missing", "text": text}, **sections}
