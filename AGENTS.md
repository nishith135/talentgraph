---
description: TalentGraph project rules — Python/Supabase/LangGraph stack
---

## Role & Workflow
- I (Nishith) direct architecture and review every change. You generate code, but do not treat this as "your" project to redesign — flag architectural concerns before implementing, don't just implement your preferred alternative.
- Always explain what you're about to do and why before touching a file, especially anything under `retrieval/` or `pipeline.py`.

## Code Standards
- Every function must be complete and runnable — no `# TODO`, no `pass` placeholders, no scaffold-only stubs. If something is genuinely out of scope, say so instead of stubbing it.
- Use type hints on all function signatures. Validate external/API data with Pydantic models, not raw dicts.
- All DB access goes through Supabase client calls or the existing `match_jobs` RPC — never raw psycopg2 unless explicitly asked.
- Never hardcode API keys, DB URLs, or the Adzuna credentials. Read from `.env` via existing config pattern only.

## Data & Schema Safety
- Do not modify `skill_list.py` or run bulk re-extraction (`reextract.py`) without explicit confirmation — this has caused false-positive regressions before. Show me the diff of what would change first.
- Never alter the Supabase schema (tables, RPC functions like `match_jobs`) without stating the migration explicitly and waiting for approval.
- Any change to `retrieval/hybrid_search.py` must preserve the existing semantic + metadata hybrid filtering logic unless I ask you to change the retrieval strategy itself.

## LangGraph / Agent Graph
- New agents must follow the existing node pattern (Intake, Retrieval, Analysis, Critique, Response) — same `StateGraph` conventions, same state schema shape, unless a new pattern is discussed first.
- Always wire new nodes into the graph explicitly (edges + conditional routing) — don't leave orphan nodes.
- Local model calls go through `ChatOllama` with the Mistral model already configured — don't swap models without asking.

## Communication
- Be direct. If a request is unclear or the "right" implementation conflicts with what I asked for, say so before writing code — don't silently pick your own interpretation.