from sentence_transformers import SentenceTransformer
from ingestion.database import supabase

model = SentenceTransformer('all-MiniLM-L6-v2')

def semantic_search(query: str, top_k: int = 5):
    """
    Given a plain English query, return the top_k most semantically
    similar job postings from the database.
    """
    print(f"\nSearching for: '{query}'")

    # Step 1: Embed the query
    query_embedding = model.encode(query).tolist()

    # Step 2: Call Supabase's pgvector similarity search
    response = supabase.rpc("match_jobs", {
        "query_embedding": query_embedding,
        "match_count": top_k
    }).execute()

    results = response.data

    if not results:
        print("No results found.")
        return []

    # Step 3: Print results
    for i, job in enumerate(results, 1):
        print(f"\n#{i} — {job['title']}")
        print(f"   Company : {job['company']}")
        print(f"   Location: {job.get('location_display', 'N/A')}")
        print(f"   Seniority: {job.get('extracted_seniority', 'N/A')}")
        print(f"   Skills  : {job.get('extracted_skills', [])}")
        print(f"   Similarity: {round(1 - job['distance'], 4)}")

    return results

if __name__ == "__main__":
    semantic_search("Python backend developer with Django experience")
    semantic_search("machine learning engineer deep learning")
    semantic_search("frontend React developer")