# TalentGraph 🎯
### A multi-agent job intelligence system that tells you exactly what skills you're missing

---

Most resume matchers are keyword filters dressed up in a UI. TalentGraph is different — it's a proper data + agent system that ingests live job postings, understands them semantically, and gives you an honest gap report against your actual resume.

Built over 4 weeks as a real portfolio project while job hunting. The system found my own skill gaps. I'm fixing them.

---

## The problem it solves

You're applying for Python Developer roles. You read 20 job descriptions. You notice "Django" keeps coming up. You wonder if it's everywhere or just in a few postings. You have no systematic way to know.

TalentGraph answers that question automatically.

```
$ python -m agents.cli "find me junior Python developer roles in Bangalore"

SKILL GAP SUMMARY
  django         ████ (4/10 jobs)
  postgresql     ██   (2/10 jobs)
  azure          ██   (2/10 jobs)

RECOMMENDATION: Focus on django, postgresql, azure
```

---

## How it works

### Layer 1 — Data pipeline

Runs on demand. Fetches live job postings from Adzuna API, normalizes them into a clean schema, deduplicates, extracts skills and seniority using ML models, embeds each posting as a 384-dimensional vector, and stores everything in Supabase Postgres with pgvector.

```
Adzuna API
    ↓
Normalize + Deduplicate
    ↓
Extract skills (regex + 100+ skill taxonomy)
Extract seniority (zero-shot classification)
    ↓
Embed with sentence-transformers (all-MiniLM-L6-v2)
    ↓
Store in pgvector
```

### Layer 2 — 5-agent LangGraph pipeline

Runs on every query. Takes your plain English question, parses it into filters, retrieves semantically relevant jobs, compares them against your resume, checks its own output quality, and formats a final report.

```
"find me junior Python roles in Bangalore with Django"
                        ↓
              [ Intake Agent ]
         Parses query → extracts filters
         seniority: junior | location: Bangalore | skills: [python, django]
                        ↓
            [ Retrieval Agent ]
         Embeds query → pgvector similarity search
         Applies metadata filters → returns top 10 jobs
                        ↓
            [ Analysis Agent ]
         Loads your resume PDF
         Computes skill intersection + gap per job
                        ↓
            [ Critique Agent ]
         Are results good enough?
         Too few jobs or low match scores → loosen filters → retry
                        ↑___________________________|
                        ↓ (if passed)
            [ Response Agent ]
         Formats final gap report with bar chart
```

The critique loop is what makes this a proper multi-agent system — not just a chain of functions. The system self-corrects before showing you results.

---

## Tech stack

```
Python              — core language
LangGraph           — multi-agent state machine orchestration
pgvector            — vector similarity search inside Postgres
sentence-transformers — semantic embeddings (all-MiniLM-L6-v2)
facebook/bart-large-mnli — zero-shot seniority classification
Supabase            — Postgres + vector store hosting
Pydantic            — schema validation on every extraction
pdfplumber          — resume PDF text extraction
Ollama (qwen2:7b)   — local LLM for the Intake Agent
Adzuna API          — live job postings source
```

---

## Quickstart

```powershell
git clone https://github.com/nishith135/talentgraph
cd talentgraph
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Add your credentials to `.env`:
```
ADZUNA_APP_ID=your_id
ADZUNA_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

Fetch and process jobs:
```powershell
python -m pipeline
```

Run a query:
```powershell
python -m agents.cli "find me junior Python developer roles in Bangalore with Django"
```

Use your own resume:
```powershell
python -m agents.cli "find me junior Python roles in Bangalore" myresume.pdf
```

Run the eval harness:
```powershell
python -m eval.harness
```

---

## Eval harness

Every change to the system is tested against a 10-case golden dataset before it's trusted. The harness measures four things per test case: filter accuracy, job count, gap detection, and retry behavior.

```
======================================================================
EVAL SUMMARY
======================================================================
  Test cases passed : 10/10
  Checks passed     : 40/40
  Overall score     : 100.0%

  All test cases passed!
```

Cases cover: happy path queries, impossible filters (no matching jobs), low match score scenarios, vague queries, multi-skill filters, and cross-category role matching.

---

## Status

### ✅ Done

- Adzuna API ingestion — normalization, dedup, Pydantic validation
- Seniority classification — zero-shot with facebook/bart-large-mnli
- Skill extraction — regex keyword matching against 100+ skill taxonomy
- pgvector setup — semantic embeddings, hybrid retrieval, custom SQL match function
- PDF resume parsing — skill extraction from resume's SKILLS section only
- Resume-to-JD semantic matching
- Skill gap analysis — per-job and aggregate missing skills
- 5-agent LangGraph graph with critique retry loop
- CLI entry point
- Eval harness — 10-case golden dataset, 100% pass rate

### 🔜 In progress / planned

- Ragas metrics — faithfulness, context precision, context recall
- Langfuse observability — per-agent tracing, cost and latency dashboards
- GitHub Actions CI — blocks deploy on eval regression
- Multi-source ingestion — RemoteOK, Jooble APIs
- Seniority filter in gap analysis
- React frontend — skill gap radar chart, market trend visualization

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

*Built by Nishith Kashimalla — [@nishithkashimalla](https://substack.com/@nishithkashimalla) on Substack where I write about building this in public.*
