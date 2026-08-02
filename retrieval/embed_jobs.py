from sentence_transformers import SentenceTransformer
from ingestion.database import supabase
import time

# Load the model once (same model as Day 1)
model = SentenceTransformer('all-MiniLM-L6-v2')

def build_text_for_embedding(job: dict) -> str:
    """
    Combine title + description into one string for embedding.
    If description is missing, fall back to title only.
    """
    title = job.get("title", "")
    description = job.get("description", "")
    return f"{title}. {description}".strip()

def embed_all_jobs():
    print("Fetching jobs without embeddings...")

    # Fetch all jobs where embedding column is NULL
    response = supabase.table("job_postings") \
        .select("id, title, description") \
        .is_("embedding", "null") \
        .execute()

    jobs = response.data

    if not jobs:
        print("No jobs found without embeddings. All up to date!")
        return

    print(f"Found {len(jobs)} jobs to embed.")

    # Build the text for each job
    texts = [build_text_for_embedding(job) for job in jobs]

    # Embed all at once (batch is faster than one by one)
    print("Generating embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)

    print("Saving embeddings to Supabase...")
    success = 0
    errors = 0

    for job, embedding in zip(jobs, embeddings):
        try:
            supabase.table("job_postings") \
                .update({"embedding": embedding.tolist()}) \
                .eq("id", job["id"]) \
                .execute()
            success += 1
        except Exception as e:
            print(f"Error saving embedding for job {job['id']}: {e}")
            errors += 1

    print(f"\nDone. Success: {success}, Errors: {errors}")

if __name__ == "__main__":
    embed_all_jobs()