from sentence_transformers import SentenceTransformer
from ingestion.database import supabase
from agents.state import TalentGraphState
from agents.tracer import get_tracer

model = SentenceTransformer('all-MiniLM-L6-v2')


def retrieval_agent(state: TalentGraphState) -> TalentGraphState:
    print("\n[ RETRIEVAL AGENT ] Fetching matching jobs...")

    tracer = get_tracer()
    span = tracer.span(
        trace_id=state.get("trace_id"),
        name="retrieval-agent",
        input={"filters": state.get("filters")}
    )

    filters = state.get("filters") or {}
    seniority = filters.get("seniority")
    location = filters.get("location")
    required_skills = filters.get("required_skills") or []

    print(f"  Seniority      : {seniority or 'any'}")
    print(f"  Location       : {location or 'any'}")
    print(f"  Required skills: {required_skills or 'none'}")

    search_text = _build_search_text(filters)
    print(f"  Search text    : '{search_text}'")

    query_embedding = model.encode(search_text).tolist()

    response = supabase.rpc("match_jobs", {
        "query_embedding": query_embedding,
        "match_count": 50
    }).execute()

    all_jobs = response.data or []
    filtered_jobs = _apply_filters(
        jobs=all_jobs,
        seniority=seniority,
        location=location,
        required_skills=required_skills,
        top_k=10
    )

    print(f"  Jobs retrieved : {len(filtered_jobs)} (after filtering from {len(all_jobs)})")

    if not filtered_jobs:
        print("  Warning: No jobs matched the filters.")

    span.end(output={
        "jobs_retrieved": len(filtered_jobs),
        "total_searched": len(all_jobs),
        "search_text": search_text
    })

    return {**state, "retrieved_jobs": filtered_jobs}


def _build_search_text(filters: dict) -> str:
    parts = []
    if filters.get("seniority"):
        parts.append(filters["seniority"])
    if filters.get("required_skills"):
        parts.extend(filters["required_skills"])
        parts.append("developer")
    if filters.get("location"):
        parts.append(filters["location"])
    return " ".join(parts) if parts else "software developer"


def _apply_filters(jobs, seniority, location, required_skills, top_k):
    filtered = []
    for job in jobs:
        if seniority and job.get("extracted_seniority") != seniority:
            continue
        job_location = (job.get("location") or "").lower()
        if location and location.lower() not in job_location:
            continue
        if required_skills:
            job_skills = [s.lower() for s in (job.get("extracted_skills") or [])]
            if not all(skill.lower() in job_skills for skill in required_skills):
                continue
        filtered.append(job)
        if len(filtered) == top_k:
            break
    return filtered