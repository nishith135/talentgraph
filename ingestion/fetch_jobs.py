from dotenv import load_dotenv
import os
import requests
from ingestion.normalize import normalize_posting
from ingestion.database import upsert_posting

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


def fetch_and_store_jobs(query: str, location: str, pages: int = 2) -> list:
    """
    Fetches job postings from Adzuna and stores them in database.
    Returns list of inserted job IDs.
    """
    inserted_ids = []

    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"

        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": 10,
            "what": query,
            "where": location
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"Failed to fetch page {page}: {response.status_code}")
            continue

        data = response.json()
        raw_jobs = data.get("results", [])

        for job in raw_jobs:
            cleaned = normalize_posting(job)
            result = upsert_posting(cleaned)
            if result:
                inserted_ids.append(result["id"])

        print(f"  Page {page}: fetched {len(raw_jobs)} jobs")

    return inserted_ids