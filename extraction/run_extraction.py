from dotenv import load_dotenv
import os
from supabase import create_client, Client
from extraction.extractor import extract
from ingestion.database import save_extraction

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch all jobs
response = supabase.table("job_postings").select(
    "id, title, company, description"
).execute()
jobs = response.data

success_count = 0
error_count = 0

for job in jobs:
    try:
        print(f"Extracting: {job['company']} - {job['title']}")
        
        result = extract(job)
        save_extraction(result)
        
        success_count += 1
        print(f"  Seniority: {result.seniority} ({result.seniority_confidence:.2f})")
        print(f"  Skills: {result.skills[:5]}...")  # Show first 5 skills
        
    except ValueError as e:
        error_count += 1
        print(f"  Validation error: {e}")
    except Exception as e:
        error_count += 1
        print(f"  Unexpected error: {e}")

print(f"\nDone. Success: {success_count}, Errors: {error_count}")