from dotenv import load_dotenv
import os
from supabase import create_client, Client
from extraction.skill_extractor import extract_skills_keyword_matching
from ingestion.database import update_posting_skills

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch all jobs
response = supabase.table("job_postings").select("id, title, company, description").execute()
jobs = response.data

skills_extracted_count = 0
for job in jobs:
    description = job["description"]
    title = job["title"]
    company = job["company"]
    job_id = job["id"]
    
    # Extract skills
    skills_by_category = extract_skills_keyword_matching(description)
    
    # Save to database
    update_posting_skills(job_id, skills_by_category)
    skills_extracted_count += 1
    
    print(f"Company: {company}")
    print(f"Job: {title}")
    print(f"Found skills:")
    for category, skills in skills_by_category.items():
        if skills:
            print(f"  {category}: {', '.join(skills)}")
    print("---")

print(f"Extracted skills for {skills_extracted_count} jobs")