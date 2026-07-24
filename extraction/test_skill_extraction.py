from dotenv import load_dotenv
import os
from supabase import create_client, Client
from skill_extractor import extract_skills_keyword_matching

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch a few jobs
response = supabase.table("job_postings").select("id, title, company, description").limit(3).execute()
jobs = response.data

for job in jobs:
    description = job["description"]
    title = job["title"]
    company = job["company"]
    
    # Extract skills
    skills_by_category = extract_skills_keyword_matching(description)
    
    print(f"Company: {company}")
    print(f"Job: {title}")
    print(f"Found skills:")
    for category, skills in skills_by_category.items():
        if skills:  # Only print categories with found skills
            print(f"  {category}: {', '.join(skills)}")
    print("---")