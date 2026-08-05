from sentence_transformers import SentenceTransformer
from ingestion.database import supabase

model = SentenceTransformer('all-MiniLM-L6-v2')

def hybrid_search(
    query: str,
    top_k: int = 5,
    seniority: str = None,
    location: str = None,
    required_skills: list = None
):
    """
    Semantic search with optional metadata filters.
    - seniority: 'junior', 'mid-level', or 'senior'
    - location: partial string match e.g. 'Bangalore'
    - required_skills: list of skills that must be present e.g. ['python', 'django']
    """
    print(f"\nSearching for: '{query}'")
    print(f"Filters — Seniority: {seniority}, Location: {location}, Skills: {required_skills}")

    # Step 1: Embed the query
    query_embedding = model.encode(query).tolist()

    # Step 2: Start with semantic search results (fetch more than top_k to allow for filtering)
    response = supabase.rpc("match_jobs", {
        "query_embedding": query_embedding,
        "match_count": 50  # fetch top 50, then filter down
    }).execute()

    results = response.data

    if not results:
        print("No results found.")
        return []

    # Step 3: Apply metadata filters in Python
    filtered = []
    for job in results:
        # Seniority filter
        if seniority and job.get("extracted_seniority") != seniority:
            continue

        # Location filter (partial match)
        if location and location.lower() not in (job.get("location") or "").lower():
            continue

        # Required skills filter
        if required_skills:
            job_skills = [s.lower() for s in (job.get("extracted_skills") or [])]
            if not all(skill.lower() in job_skills for skill in required_skills):
                continue

        filtered.append(job)

        if len(filtered) == top_k:
            break

    if not filtered:
        print("No results matched the filters.")
        return []

    # Step 4: Print results
    for i, job in enumerate(filtered, 1):
        print(f"\n#{i} — {job['title']}")
        print(f"   Company  : {job.get('company', 'N/A')}")
        print(f"   Seniority: {job.get('extracted_seniority', 'N/A')}")
        print(f"   Skills   : {job.get('extracted_skills', [])}")
        print(f"   Similarity: {round(1 - job['distance'], 4)}")
    return filtered

if __name__ == "__main__":
    # Test 1: semantic only, no filters
    hybrid_search("Python backend developer")

    # Test 2: filter by seniority
    hybrid_search("Python backend developer", seniority="junior")

    # Test 3: filter by seniority + required skill
    hybrid_search("Python developer", seniority="junior", required_skills=["django"])