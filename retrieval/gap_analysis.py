from sentence_transformers import SentenceTransformer
from ingestion.database import supabase
from extraction.skill_extractor import extract_skills_keyword_matching
import pdfplumber
from pathlib import Path
from collections import Counter
import sys

model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_skills_section(resume_text: str) -> str:
    """
    Pull out only the SKILLS section from the resume text.
    Falls back to full text if section not found.
    """
    lines = resume_text.split('\n')
    skills_lines = []
    in_skills_section = False

    for line in lines:
        # Detect start of SKILLS section
        if line.strip().upper() in ('SKILLS', 'TECHNICAL SKILLS', 'SKILLS & TOOLS'):
            in_skills_section = True
            continue
        
        # Detect start of next section — stop collecting
        if in_skills_section and line.strip().upper() in (
            'EXPERIENCE', 'EDUCATION', 'PROJECTS', 
            'CERTIFICATIONS', 'LANGUAGES', 'SUMMARY'
        ):
            break
        
        if in_skills_section:
            skills_lines.append(line)

    if not skills_lines:
        print("Warning: SKILLS section not found, falling back to full resume text.")
        return resume_text

    skills_text = '\n'.join(skills_lines)
    print(f"Skills section extracted:\n{skills_text}\n")
    return skills_text


def extract_resume_skills(resume_text: str) -> set:
    """
    Extract skills from the SKILLS section only.
    """
    skills_section = extract_skills_section(resume_text)
    skills_dict = extract_skills_keyword_matching(skills_section)
    all_skills = set()
    for category_skills in skills_dict.values():
        all_skills.update(category_skills)
    return all_skills

def load_resume_text(path: str) -> str:
    resume_path = Path(path)
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume not found at {path}")
    
    text = ""
    with pdfplumber.open(resume_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def run_gap_analysis(resume_path: str = "data/NISHITH_KASHIMALLA_CV.pdf", top_k: int = 10):
    """
    Compare resume skills against top matching job requirements.
    """
    # Step 1: Load resume + extract skills
    print("Loading resume...")
    resume_text = load_resume_text(resume_path)
    resume_skills = extract_resume_skills(resume_text)
    print(f"Skills found in resume: {sorted(resume_skills)}\n")

    # Step 2: Embed resume + fetch top matching jobs
    print("Fetching top matching jobs...")
    resume_embedding = model.encode(resume_text).tolist()
    response = supabase.rpc("match_jobs", {
        "query_embedding": resume_embedding,
        "match_count": top_k
    }).execute()

    jobs = response.data
    if not jobs:
        print("No jobs found.")
        return

    # Step 3: Gap analysis per job
    missing_skills_counter = Counter()

    print(f"\n{'='*60}")
    print("PER JOB GAP ANALYSIS")
    print(f"{'='*60}\n")

    for i, job in enumerate(jobs, 1):
        job_skills = set(job.get("extracted_skills") or [])
        matched = resume_skills & job_skills        # skills you have
        missing = job_skills - resume_skills        # skills you don't have

        similarity = round(1 - job["distance"], 4)

        print(f"#{i} — {job['title']} at {job.get('company', 'N/A')}")
        print(f"   Match Score : {similarity}")
        print(f"   Seniority   : {job.get('extracted_seniority', 'N/A')}")
        print(f"   You have    : {sorted(matched) if matched else 'none matched'}")
        print(f"   You're missing: {sorted(missing) if missing else 'none — full match!'}")
        print()

        # Count how often each missing skill appears across jobs
        missing_skills_counter.update(missing)

    # Step 4: Aggregate — which missing skills come up most often
    print(f"{'='*60}")
    print("MOST COMMON MISSING SKILLS ACROSS TOP JOBS")
    print(f"{'='*60}\n")

    if missing_skills_counter:
        for skill, count in missing_skills_counter.most_common(10):
            print(f"   {skill}: missing in {count}/{top_k} jobs")
    else:
        print("No skill gaps found — strong match!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_gap_analysis(resume_path=f"data/{sys.argv[1]}")
    else:
        run_gap_analysis()