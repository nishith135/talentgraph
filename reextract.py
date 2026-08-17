from ingestion.database import supabase
from extraction.extractor import extract
import json

# Fetch all jobs with NULL extracted_skills
response = supabase.table("job_postings") \
    .select("id, title, description, company") \
    .is_("extracted_skills", "null") \
    .execute()

jobs = response.data
print(f"Found {len(jobs)} jobs to re-extract\n")

success = 0
errors = 0

for job in jobs:
    try:
        result = extract(job)
        supabase.table("job_postings") \
            .update({
                "extracted_skills": result.skills,
                "skills_categories": json.dumps(result.skills_by_category),
                "extracted_seniority": result.seniority,
                "seniority_confidence": result.seniority_confidence
            }) \
            .eq("id", job["id"]) \
            .execute()
        print(f"  Re-extracted: {job.get('company', 'Unknown')} - {job['title']}")
        success += 1
    except Exception as e:
        print(f"  Error on job {job['id']}: {e}")
        errors += 1

print(f"\nDone. Success: {success}, Errors: {errors}")