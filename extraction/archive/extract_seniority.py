
from ingestion.database import update_posting_seniority
from transformers import pipeline
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load classifier
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

labels = ["junior", "mid-level", "senior"]

# Fetch jobs from database
response = supabase.table("job_postings").select("id, title,company, description").limit(5).execute()
jobs = response.data

for job in jobs:
    description = job["description"]
    title = job["title"]
    company = job["company"]
    job_id = job["id"]
    
    # Run classifier
    result = classifier(description, labels)
    predicted_seniority = result["labels"][0]  # top label
    confidence = result["scores"][0]  # top score

    # Save to database
    update_posting_seniority(job_id, predicted_seniority, confidence)

    print(f"company:{company}")
    print(f"Job: {title}")
    print(f"Predicted seniority: {predicted_seniority} (confidence: {confidence:.2f})")
    print("---")