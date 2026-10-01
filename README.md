# TalentGraph 🎯
### The job application agent that finds roles, tailors your resume, and applies — so you don't have to

---

Job hunting is broken. You spend more time reformatting your resume for each role than actually preparing for interviews. You manually read through dozens of job descriptions trying to figure out which ones are worth applying to. You rewrite your summary for every company. You copy-paste the same details into a hundred different application forms.

TalentGraph is built to fix that.

The end goal: you describe what kind of role you want. TalentGraph finds the best matching live job postings, tailors your resume specifically for each one, and submits the applications — automatically. No manual reformatting. No copy-pasting. No spending three hours applying to ten jobs.

---

## What's the actual novelty here?

Most "resume matchers" are keyword filters with a UI. You paste a job description, they highlight words that match your resume, you do the rest yourself.

TalentGraph is an agent system. It doesn't just tell you what's missing — it acts on it.

The full vision is a pipeline that runs end to end without you touching it:

```
You describe what you want
        ↓
TalentGraph finds live matching jobs from real APIs
        ↓
It reads each job description and your resume together
        ↓
It rewrites your resume summary and bullets to match that specific role
        ↓
It submits the application
        ↓
You get a report of what was applied to and why
```

No generic resume blasted at 50 companies. A tailored application for each role, generated and submitted in minutes.

---

## Where it stands today

The intelligence layer is built. The application layer is in active development.

**What's working right now:** You query the system in plain English. It finds semantically relevant jobs, compares them against your resume, and produces a gap report showing exactly which skills appear most frequently in those roles that you don't have yet.

```
$ python -m agents.cli "find me junior Python developer roles in Bangalore with Django"

#1 — Python Developer at infomaticscorp
     Match score   : 0.655
     You have      : ['flask', 'python', 'rest api', 'sql']
     You're missing: ['django', 'postgresql']

SKILL GAP SUMMARY
  django       ██ (2/2 jobs)
  postgresql   ██ (2/2 jobs)

RECOMMENDATION: Focus on django, postgresql
```

**What's being built next:** The Resume Tailoring Agent rewrites your resume for each matched role. The Application Agent submits it. That's when this stops being a portfolio project and starts being something that actually saves job seekers hours every week.

---

## System architecture

### Layer 1 — Data pipeline

Runs on demand. Fetches live job postings from real APIs, normalizes them into a clean schema, extracts skills and seniority using ML models, embeds each posting as a semantic vector, and stores everything in Supabase Postgres with pgvector.

```
Job APIs (Adzuna + more coming)
    ↓
Normalize + Deduplicate
    ↓
Extract skills    → regex + 100+ skill taxonomy
Extract seniority → zero-shot classification (bart-large-mnli)
    ↓
Embed → sentence-transformers (all-MiniLM-L6-v2)
    ↓
Store in pgvector
```

### Layer 2 — Agent graph (current: intelligence | coming: action)

```
"find me junior Python roles in Bangalore with Django"
                    ↓
        [ Intake Agent ]
        Parses query → structured filters
        seniority: junior | location: Bangalore | skills: [python, django]
                    ↓
        [ Retrieval Agent ]
        Embeds query → pgvector similarity search
        Applies metadata filters → top matching jobs
                    ↓
        [ Analysis Agent ]
        Loads resume PDF → computes skill intersection + gaps per job
                    ↓
        [ Critique Agent ]
        Quality check — too few results or low scores → loosen filters → retry
                    ↑___________________________|
                    ↓ (passed)
        [ Response Agent ]
        Gap report with bar chart + recommendation

        ↓ ↓ ↓ COMING NEXT ↓ ↓ ↓

        [ Resume Tailoring Agent ]
        Rewrites resume summary + bullets to match each specific role
        Different version per application — no generic blasting
                    ↓
        [ Application Agent ]
        Submits via email / Playwright browser automation
                    ↓
        [ Report Agent ]
        Summary of what was applied to, match scores, tailoring decisions
```

The critique loop is what makes the current system a proper multi-agent setup — not just a chain of functions. It self-corrects before showing results. The same principle applies to the application layer: no application gets submitted without passing a quality gate first.

---

## Tech stack

```
Python                   — core language
LangGraph                — multi-agent state machine orchestration
pgvector                 — vector similarity search inside Postgres
sentence-transformers    — semantic embeddings (all-MiniLM-L6-v2)
facebook/bart-large-mnli — zero-shot seniority classification
Supabase                 — Postgres + vector store hosting
Pydantic                 — schema validation on every agent output
pdfplumber               — resume PDF text extraction
Ollama (qwen2:7b)        — local LLM for query parsing and tailoring
Adzuna API               — live job postings (more sources coming)
Playwright               — browser automation for form-based applications (coming)
```

---

## Quickstart

```bash
git clone https://github.com/nishith135/talentgraph
cd talentgraph
pip install -r requirements.txt
```

`.env` file:
```
ADZUNA_APP_ID=your_id
ADZUNA_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

```bash
# Fetch and process jobs
python -m pipeline

# Run a query
python -m agents.cli "find me junior Python developer roles in Bangalore with Django"

# Use your own resume
python -m agents.cli "find me Python roles in Bangalore" myresume.pdf

# Run the eval harness
python -m eval.harness
```

---

## Eval harness

Every change is tested against a 10-case golden dataset before it's trusted. The harness measures filter accuracy, retrieval count, gap detection, and retry behavior per test case.

```
Test cases : 10/10 passed
Checks     : 40/40 passed
Score      : 100%
```

The same eval infrastructure will gate the application layer — no resume gets auto-submitted without passing quality checks first.

---

## Status

### ✅ Built

- Ingestion pipeline — fetch, normalize, deduplicate, Pydantic validation
- ML extraction — zero-shot seniority, regex skill matching (100+ taxonomy)
- pgvector semantic embeddings + hybrid retrieval
- PDF resume parsing — skills extracted from SKILLS section only (no false positives)
- Resume-to-JD semantic matching
- Skill gap analysis — per job and aggregate with frequency ranking
- 5-agent LangGraph graph with self-correcting critique retry loop
- CLI entry point
- Eval harness — 10-case golden dataset, 100% pass rate (40/40 checks)
- Ragas evaluation metrics *(in progress)*
- Langfuse observability *(in progress)*
- GitHub Actions CI gate *(in progress)*

### 🔜 Coming

- **Resume Tailoring Agent** — rewrites resume summary and bullet points per role using the job description as context. No hallucination — only restructures and reframes what's already true on your resume
- **Application Agent** — submits via email for postings with apply@ addresses; Playwright browser automation for form-based applications
- **Multi-source ingestion** — RemoteOK, Jooble APIs alongside Adzuna
- **Application tracking** — log of every submission with match score, tailoring decisions, and outcome
- **React dashboard** — skill gap radar chart, application history, market trend visualization

---

## Project structure

```
talentgraph/
  pipeline.py          ← ingestion entry point
  ingestion/           ← API fetch, normalize, database
  extraction/          ← skill taxonomy, extractor, Pydantic schemas
  retrieval/           ← embeddings, search, resume match, gap analysis
  agents/              ← LangGraph state, 5 agents, graph, CLI
  eval/                ← golden dataset, harness
  data/                ← resume PDF (gitignored)
```

---

*Built by Nishith Kashimalla while job hunting — [@nishithkashimalla](https://substack.com/@nishithkashimalla) on Substack.*
