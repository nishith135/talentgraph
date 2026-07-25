import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_posting(posting: dict) -> dict:
    """
    Takes one cleaned posting and inserts or updates it in the database.
    If source + external_id already exists, it updates that row.
    If it's new, it inserts a new row.
    """
    
    try:
        # Try to update first
        response = supabase.table("job_postings").update(posting).eq("source", posting["source"]).eq("external_id", posting["external_id"]).execute()
        
        # If no rows were updated, insert instead
        if not response.data:
            response = supabase.table("job_postings").insert(posting).execute()
        
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error upserting posting {posting.get('external_id')}: {e}")
        return None

def update_posting_seniority(posting_id: int, seniority: str, confidence: float) -> dict:
    """
    Updates a posting with its extracted seniority level.
    """
    response = supabase.table("job_postings").update({
        "extracted_seniority": seniority,
        "seniority_confidence": confidence
    }).eq("id", posting_id).execute()
    
    return response.data[0] if response.data else None
    
def update_posting_skills(posting_id: int, skills: dict) -> dict:
    """
    Updates a posting with extracted skills.
    skills is a dict like {"backend": ["python", "django"], "devops": ["docker"]}
    """
    # Flatten all skills into one list
    all_skills = []
    for category, skill_list in skills.items():
        all_skills.extend(skill_list)
    
    response = supabase.table("job_postings").update({
        "extracted_skills": all_skills,
        "skills_categories": str(skills)  # Save as JSON string
    }).eq("id", posting_id).execute()
    
    return response.data[0] if response.data else None