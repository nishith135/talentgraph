from dotenv import load_dotenv
import os
from supabase import create_client, Client
from ingestion.fetch_jobs import fetch_and_store_jobs
from extraction.extractor import extract
from ingestion.database import save_extraction

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def run_pipeline(query: str, location: str, pages: int = 2):
    """
    Full pipeline:
    1. Fetch jobs from Adzuna
    2. Normalize and store in database
    3. Extract seniority + skills from newly fetched jobs only
    4. Save extractions back to database
    """

    print(f"\n--- STEP 1: Fetching jobs for '{query}' in '{location}' ---")
    inserted_ids = fetch_and_store_jobs(query, location, pages)
    total_fetched = len(inserted_ids)
    print(f"Fetched and stored {total_fetched} jobs")

    if not inserted_ids:
        print("No new jobs fetched — nothing to extract.")
        return

    print(f"\n--- STEP 2: Running extraction on {total_fetched} newly fetched jobs ---")
    response = supabase.table("job_postings").select(
        "id, title, company, description"
    ).in_("id", inserted_ids).execute()
    jobs = response.data

    success_count = 0
    error_count = 0

    for job in jobs:
        try:
            result = extract(job)
            save_extraction(result)
            success_count += 1
            print(f"  Extracted: {job['company']} - {job['title']} | {result.seniority} ({result.seniority_confidence:.2f})")
        except ValueError as e:
            error_count += 1
            print(f"  Validation error for {job['company']}: {e}")
        except Exception as e:
            error_count += 1
            print(f"  Error for {job['company']}: {e}")

    print(f"\n--- PIPELINE COMPLETE ---")
    print(f"Jobs fetched: {total_fetched}")
    print(f"Extractions successful: {success_count}")
    print(f"Extractions failed: {error_count}")


if __name__ == "__main__":
    run_pipeline(
        query="data analyst",
        location="hyderabad",
        pages=2
    )
    