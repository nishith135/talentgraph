from sentence_transformers import SentenceTransformer
from ingestion.database import supabase
from agents.state import TalentGraphState

model = SentenceTransformer('all-MiniLM-L6-v2')


def retrieval_agent(state: TalentGraphState) -> TalentGraphState:
    """
    Reads filters from state.
    Runs hybrid semantic search against the database.
    Writes retrieved_jobs back to state.
    """

    print("\n[ RETRIEVAL AGENT ] Fetching matching jobs...")

    filters = state.get("filters") or {}
    seniority = filters.get("seniority")
    location = filters.get("location")
    required_skills = filters.get("required_skills") or []

    print(f"  Seniority      : {seniority or 'any'}")
    print(f"  Location       : {location or 'any'}")
    print(f"  Required skills: {required_skills or 'none'}")

    # Step 1: Embed the user query as the search vector
    # We reconstruct a search string from the filters
    # so the semantic search is grounded in what the user wants
    search_text = _build_search_text(filters)
    print(f"  Search text    : '{search_text}'")

    query_embedding = model.encode(search_text).tolist()

    # Step 2: Fetch top 50 semantically similar jobs from pgvector
    response = supabase.rpc("match_jobs", {
        "query_embedding": query_embedding,
        "match_count": 50
    }).execute()

    all_jobs = response.data or []

    # Step 3: Apply metadata filters
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

    return {**state, "retrieved_jobs": filtered_jobs}


def _build_search_text(filters: dict) -> str:
    """
    Reconstruct a readable search string from filters.
    This is what gets embedded as the query vector.

    Example:
      filters = {"seniority": "junior", "location": "Bangalore", "required_skills": ["python"]}
      output  = "junior Python developer Bangalore"
    """
    parts = []

    if filters.get("seniority"):
        parts.append(filters["seniority"])

    if filters.get("required_skills"):
        parts.extend(filters["required_skills"])
        parts.append("developer")

    if filters.get("location"):
        parts.append(filters["location"])

    # Fallback if filters are all empty
    return " ".join(parts) if parts else "software developer"


def _apply_filters(
    jobs: list,
    seniority: str,
    location: str,
    required_skills: list,
    top_k: int
) -> list:
    """
    Apply seniority, location, and skill filters to the
    semantically retrieved job list.

    Separated into its own function to keep retrieval_agent() readable.
    """
    filtered = []

    for job in jobs:
        # Seniority filter — exact match
        if seniority and job.get("extracted_seniority") != seniority:
            continue

        # Location filter — partial string match
        job_location = (job.get("location") or "").lower()
        if location and location.lower() not in job_location:
            continue

        # Skills filter — all required skills must be present
        if required_skills:
            job_skills = [s.lower() for s in (job.get("extracted_skills") or [])]
            if not all(skill.lower() in job_skills for skill in required_skills):
                continue

        filtered.append(job)

        if len(filtered) == top_k:
            break

    return filtered