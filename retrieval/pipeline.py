from sentence_transformers import SentenceTransformer
from ingestion.database import supabase
from retrieval.resume_match import load_resume
from retrieval.gap_analysis import extract_resume_skills, run_gap_analysis
from retrieval.hybrid_search import hybrid_search
import sys

model = SentenceTransformer('all-MiniLM-L6-v2')


def run_retrieval_pipeline(
    resume_path: str = "data/NISHITH_KASHIMALLA_CV.pdf",
    top_k: int = 10,
    seniority: str = None,
    required_skills: list = None
):
    """
    Full Week 2 retrieval pipeline:
    1. Load resume
    2. Semantic job matching
    3. Optional hybrid filtering
    4. Gap analysis report
    """

    print("\n" + "=" * 60)
    print("TALENTGRAPH — RETRIEVAL PIPELINE")
    print("=" * 60)

    # -------------------------
    # STEP 1: Load Resume
    # -------------------------
    print("\n[ STEP 1 ] Loading resume...")
    resume_text = load_resume(resume_path)
    resume_skills = extract_resume_skills(resume_text)
    print(f"Resume skills detected: {sorted(resume_skills)}")

    # -------------------------
    # STEP 2: Semantic Matching
    # -------------------------
    print("\n[ STEP 2 ] Finding top matching jobs...")
    resume_embedding = model.encode(resume_text).tolist()

    response = supabase.rpc("match_jobs", {
        "query_embedding": resume_embedding,
        "match_count": 50
    }).execute()

    all_results = response.data

    if not all_results:
        print("No jobs found in database.")
        return

    # -------------------------
    # STEP 3: Optional Filtering
    # -------------------------
    if seniority or required_skills:
        print(f"\n[ STEP 3 ] Applying filters...")
        print(f"  Seniority    : {seniority or 'any'}")
        print(f"  Must have    : {required_skills or 'none'}")

        filtered = []
        for job in all_results:
            if seniority and job.get("extracted_seniority") != seniority:
                continue
            if required_skills:
                job_skills = [s.lower() for s in (job.get("extracted_skills") or [])]
                if not all(skill.lower() in job_skills for skill in required_skills):
                    continue
            filtered.append(job)
            if len(filtered) == top_k:
                break

        jobs = filtered
    else:
        print("\n[ STEP 3 ] No filters applied.")
        jobs = all_results[:top_k]

    if not jobs:
        print("No jobs matched the filters.")
        return

    # -------------------------
    # STEP 4: Gap Analysis
    # -------------------------
    print(f"\n[ STEP 4 ] Running gap analysis on top {len(jobs)} jobs...")
    print("=" * 60)

    from collections import Counter
    missing_counter = Counter()

    for i, job in enumerate(jobs, 1):
        job_skills = set(job.get("extracted_skills") or [])
        matched = resume_skills & job_skills
        missing = job_skills - resume_skills
        similarity = round(1 - job["distance"], 4)

        print(f"\n#{i} — {job['title']} at {job.get('company', 'N/A')}")
        print(f"   Match Score  : {similarity}")
        print(f"   Seniority    : {job.get('extracted_seniority', 'N/A')}")
        print(f"   You have     : {sorted(matched) if matched else 'none matched'}")
        print(f"   You're missing: {sorted(missing) if missing else 'none — full match!'}")

        missing_counter.update(missing)

    # -------------------------
    # STEP 5: Summary Report
    # -------------------------
    print("\n" + "=" * 60)
    print("SKILL GAP SUMMARY")
    print("=" * 60)

    if missing_counter:
        for skill, count in missing_counter.most_common(10):
            bar = "█" * count
            print(f"   {skill:<25} {bar} ({count}/{len(jobs)} jobs)")
    else:
        print("No skill gaps found — strong match!")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Default: no filters
    # Example with filters:
    # run_retrieval_pipeline(seniority="junior", required_skills=["python"])

    pdf = f"data/{sys.argv[1]}" if len(sys.argv) > 1 else "data/NISHITH_KASHIMALLA_CV.pdf"
    run_retrieval_pipeline(resume_path=pdf)