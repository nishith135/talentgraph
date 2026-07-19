from dotenv import load_dotenv
import os
import requests
from normalize import normalize_posting
from database import upsert_posting

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

page = 2
url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"

params = {
    "app_id": APP_ID,
    "app_key": APP_KEY,
    "results_per_page": 5,
    "what": "python developer",
    "where": "bangalore"
}

response = requests.get(url, params=params)
data = response.json()

raw_jobs = data["results"]

cleaned_jobs = []
for job in raw_jobs:
    cleaned = normalize_posting(job)
    cleaned_jobs.append(cleaned)

upserted_count = 0
for job in cleaned_jobs:
    result = upsert_posting(job)
    if result:
        upserted_count += 1

print(f"Upserted {upserted_count} jobs to database")