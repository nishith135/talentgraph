from extraction.skill_list import SKILL_TAXONOMY

def extract_skills_keyword_matching(text: str) -> dict:
    """
    Find skills in text by simple keyword matching.
    Returns skills grouped by category.
    """
    text_lower = text.lower()
    found_skills = {}
    
    for category, skills in SKILL_TAXONOMY.items():
        found_skills[category] = []
        
        for skill in skills:
            if skill in text_lower:
                found_skills[category].append(skill)
    
    return found_skills