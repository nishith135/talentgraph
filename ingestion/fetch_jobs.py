from dotenv import load_dotenv
import os
import requests
from normalize import normalize_posting

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

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

for job in cleaned_jobs:
    print(job)
    print("---")


import json
import os

os.makedirs("data/raw", exist_ok=True)
with open("data/raw/normalized_postings.jsonl", "a", encoding="utf-8") as f:
    for job in cleaned_jobs:
        f.write(json.dumps(job) + "\n")

print(f"Saved {len(cleaned_jobs)} jobs to data/raw/normalized_postings.jsonl")