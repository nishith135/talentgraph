from datetime import datetime, timezone


def normalize_posting(raw):
    """
    Takes one messy job posting (a dictionary) from Adzuna
    and returns a clean, consistent version of it.
    """

    # Company name is nested inside a "company" dictionary
    company = raw.get("company", {}).get("display_name", "Unknown")

    # Location is also nested - grab both the display text and the area list
    location = raw.get("location", {})
    location_display = location.get("display_name", "Unknown")
    location_area = location.get("area", [])

    # Category is nested too
    category = raw.get("category", {}).get("label", "Unknown")

    # Salary handling: Adzuna sometimes uses 0 to mean "unknown"
    salary_min = raw.get("salary_min")
    salary_min = None if not salary_min else salary_min

    salary_max = raw.get("salary_max")
    salary_max = None if not salary_max else salary_max

    # Force id to always be text, since Adzuna sends it inconsistently
    external_id = str(raw.get("id", ""))

    # Adzuna sends this as text '0' or '1' - convert to a real True/False
    salary_is_predicted = raw.get("salary_is_predicted") == "1"

    # Record the exact moment we processed this posting
    fetched_at = datetime.now(timezone.utc).isoformat()

    return {
        "external_id": external_id,
        "source": "adzuna",
        "title": raw.get("title", "Unknown"),
        "company": company,
        "location_display": location_display,
        "location_area": location_area,
        "description": raw.get("description", ""),
        "category": category,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_is_predicted": salary_is_predicted,
        "contract_type": raw.get("contract_type"),
        "contract_time": raw.get("contract_time"),
        "created": raw.get("created"),
        "redirect_url": raw.get("redirect_url"),
        "fetched_at": fetched_at,
    }