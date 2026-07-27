from transformers import pipeline
from extraction.skill_extractor import extract_skills_keyword_matching
from extraction.Schemas import JobExtraction

# Load classifier once at module level
# (loading it inside the function would reload it on every call — very slow)
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

SENIORITY_LABELS = ["junior", "mid-level", "senior"]


def extract(posting: dict) -> JobExtraction:
    """
    Takes one cleaned job posting dictionary.
    Returns a validated JobExtraction object.
    Raises ValueError if extraction output doesn't match schema.
    """

    posting_id = posting["id"]
    description = posting.get("description", "")

    # Step 1: Seniority extraction
    try:
        seniority_result = classifier(description, SENIORITY_LABELS)
        seniority = seniority_result["labels"][0]
        confidence = seniority_result["scores"][0]
    except Exception as e:
        print(f"Seniority extraction failed for posting {posting_id}: {e}")
        seniority = "unknown"
        confidence = 0.0

    # Step 2: Skill extraction
    try:
        skills_by_category = extract_skills_keyword_matching(description)
        all_skills = []
        for skill_list in skills_by_category.values():
            all_skills.extend(skill_list)
        all_skills = list(set(all_skills))

    except Exception as e:
        print(f"Skill extraction failed for posting {posting_id}: {e}")
        skills_by_category = {}
        all_skills = []

    # Step 3: Validate output against schema
    extraction = JobExtraction(
        posting_id=posting_id,
        seniority=seniority,
        seniority_confidence=confidence,
        skills=all_skills,
        skills_by_category=skills_by_category
    )

    return extraction