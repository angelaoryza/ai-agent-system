# OCBC AI Creator Masterclass: Day 1 and Day 2 materials

Build sprint by Algoritma for PT Bank OCBC NISP Tbk. Over two days participants build the
**IDX Market Assistant** on Indonesian stock data from [Sectors](https://sectors.app):
a data script, a scheduled report, an LLM digest, RAG over news, tools, an agent with approval,
MCP tools, and a scheduled agent that explains big price moves.

> Day 1: we tell the LLM what the data is. Day 2: the LLM asks for the data it needs.

Stack for Days 1 and 2: [Pydantic AI](https://ai.pydantic.dev) as the framework, an OpenAI model behind an
OpenAI-compatible endpoint, and an open-source embedding model (`all-mpnet-base-v2`, through sentence-transformers)
that runs on the laptop.

## Setup

1. Python 3.11 or newer, VS Code with the Python and Jupyter extensions, GitHub Copilot.
2. In this folder:

   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in `SECTORS_API_KEY`, `OPENAI_API_KEY` and `OPENAI_URL`.
   For Module 7.5 (optional): `MAGIC_API_KEY`, `MY_EMAIL`, and `credentials.json` from the trainer in this folder.
4. Run `python check_setup.py`. Every line should say ✅ PASS. The first run downloads the embedding model
   (about 420 MB, once); do it before class, on a network that can reach huggingface.co.
5. In VS Code, open a notebook and choose the `.venv` interpreter as the kernel.

Run every script from this folder, for example `python day1/examples/m2_example.py`.

## Pre-course checklist

- [ ] `python --version` shows 3.11 or newer
- [ ] `pip install -r requirements.txt` finished without errors
- [ ] `.env` exists in this folder with the Sectors and OpenAI keys and the OpenAI URL (no quotes, no `Bearer`)
- [ ] `python check_setup.py` shows ✅ for Sectors REST API, OpenAI model, Embedding model and Sectors MCP server
- [ ] A notebook opens in VS Code and runs its first cell
- [ ] On the OCBC network: proxy and certificate settings from IT, if needed (see `.env.example`)
- [ ] Optional, Module 7.5: `check_setup.py` shows ✅ for `MAGIC_API_KEY`, `MY_EMAIL` and `credentials.json`

## Folder map

```
README.md, requirements.txt, .env.example, check_setup.py
data/sample/              saved real Sectors responses (25 Oct 2026), used when Sectors is unreachable
day1/                     Modules 1-5
  Coursebook - Day 1 ... .docx          theory
  Trainer Handbook - Day 1 ... .docx    trainers only
  notebooks/   m2-m5      recap, worked examples, knowledge checks
  examples/    m2-m5      one runnable script per module
  exercises/   m2-m5      exercises with checks at the bottom
  solutions/   m2-m5      trainers only; solutions/notebooks/ has the solved, executed notebooks
day2/                     Modules 6-9 (same layout; no notebook for M9)
```

Every notebook, example and exercise is self-contained: all the functions it uses are written
in the file itself.

Created while you work: `data/news/` (Module 2, used by Modules 5–9), `data/market.db`, `output/`.

## Order of work

Module 2 saves the news that Modules 5–9 use, and Module 3 writes the report that Module 4 reads.
If you start later in the course, run these two first:

```bash
python day1/examples/m2_example.py
python day1/examples/m3_example.py --now
```

## Distributing to participants

Give participants everything except `day1/solutions/`, `day2/solutions/`, both
`Trainer Handbook` files, and any `.env` or `token.json`. Give `credentials.json` (the Gmail OAuth client)
to the class only; each participant's first Gmail run creates their own `token.json`, which stays on their laptop.
