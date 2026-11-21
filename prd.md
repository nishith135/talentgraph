# TalentGraph — PRD

## What it is
A multi-agent job-application assistant. The user describes the role they want. TalentGraph finds live matching jobs, compares them to the user's resume, **tailors the resume per job**, and (stretch) submits applications. The gap analysis is only the intelligence layer; the tailoring and applying are the actual product.

Primary user: the author, job hunting for Python / backend / data / AI roles, mainly in Hyderabad.

## Current state (done, do not rebuild)
- **Ingestion:** Adzuna API, normalize, dedupe, Pydantic validation, Supabase Postgres. Entry: `python -m pipeline`.
- **Extraction:** zero-shot seniority (bart-large-mnli), regex skill matching over a taxonomy in `extraction/skill_list.py`.
- **Retrieval:** pgvector embeddings (all-MiniLM-L6-v2), `match_jobs` SQL function, hybrid search, PDF resume parsing, gap analysis.
- **Agents (LangGraph):** Intake (Ollama qwen2:7b) → Retrieval → Analysis → Critique (retry loop, max 2) → Response. Entry: `python -m agents.cli "<query>" [resume.pdf]`.
- **Eval:** `eval/golden_dataset.py` (10 cases) + `eval/harness.py`. Currently **10/10, 40/40 checks**.
- **Observability:** Langfuse tracing via `agents/tracer.py`, one trace per run, one span per agent.
- **CI:** `.github/workflows/eval.yml` runs the eval harness on every push to main. Currently green.
- **Skipped:** Ragas (dependency conflicts with the LangGraph stack). Do not attempt to reinstall it.

## Remaining work (strict priority order, do not add anything else)
1. **Resume Tailoring Agent.** New node after Analysis and Critique, before Response. Inputs: base resume text, a job's description, and that job's matched/missing skills. Output: a tailored summary and reordered/reworded bullets per job. Rule: only reframe what is already true on the resume. Never invent skills or experience. Store the result in state (e.g. `tailored_resumes`) and show it in the Response output.
2. **Fresh job data.** Add a scheduled GitHub Actions workflow (cron, daily) that runs `python -m pipeline` so the DB stays current. Retrieval keeps querying the pre-embedded DB; do not fetch and embed live on every query.
3. **Eval for the new agent.** Add 2–3 golden cases that check the tailoring output does not contain skills absent from the base resume. Harness must stay at full pass.
4. **README update.** Reflect the real state and the tailoring agent. Keep the built vs planned split.
5. **Stretch, only if everything above is done:** Application Agent (email-based apply first; Playwright only if time remains).

## Hard constraints
- `python -m eval.harness` must stay at **40/40** (plus any new cases). Run it after every change.
- Do not change pinned dependency versions in `requirements.txt`. There is a known LangChain / LangGraph / Langfuse version conflict. The tracer code uses the older Langfuse API (`tracer.span`); do not upgrade Langfuse.
- Intake Agent uses local Ollama (qwen2:7b). The Gemini free tier is rate-limited (20 requests/day), so do not route agents through it.
- `requirements.txt` must stay Linux-compatible (no `pywin32`, `pywinpty`, etc.) and UTF-8 without BOM.
- Never commit `.env` or the resume PDF.
- No new features, refactors, or frameworks beyond the list above.

## Known limitations (do not "fix" unless asked)
- Adzuna descriptions are truncated.
- Seniority classifier over-predicts "senior" on vague JDs.
- Skill taxonomy gaps (e.g. noise like `unity`, `monday`).
- Response Agent says "strong match" when zero jobs are found (cosmetic bug, fix only if trivial).
- Dataset is small (~41–47 jobs).

## Working agreement for the AI agent
1. Scan the codebase first. Report what exists, anything broken or inconsistent, and your plan for task 1. **Wait for approval before editing.**
2. Work on a branch, one task at a time, in the priority order above.
3. After each task: run the eval harness, show the output, then stop for review.
4. Keep changes minimal. If something isn't required by the task, skip it.

## Definition of done
- Tailoring agent produces a per-job tailored resume with no invented skills.
- Eval harness fully passing locally and in CI.
- Scheduled ingestion workflow running.
- README matches reality.