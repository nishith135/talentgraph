from dotenv import load_dotenv
import os
from supabase import create_client, Client
from extraction.extractor import extract

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch 3 jobs
response = supabase.table("job_postings").select("id, title, company, description").limit(3).execute()
jobs = response.data

for job in jobs:
    print(f"Processing: {job['company']} - {job['title']}")
    
    result = extract(job)
    
    print(f"Seniority: {result.seniority} (confidence: {result.seniority_confidence:.2f})")
    print(f"Skills: {result.skills}")
    print("---")