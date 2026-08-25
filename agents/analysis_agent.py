from collections import Counter
from agents.state import TalentGraphState
from retrieval.gap_analysis import extract_resume_skills, load_resume_text


def analysis_agent(state: TalentGraphState) -> TalentGraphState:
    """
    Reads retrieved_jobs and resume_path from state.
    Runs gap analysis — compares resume skills against job requirements.
    Writes structured gap_analysis dict back to state.
    """

    print("\n[ ANALYSIS AGENT ] Running gap analysis...")

    jobs = state.get("retrieved_jobs") or []
    resume_path = state.get("resume_path", "data/NISHITH_KASHIMALLA_CV.pdf")

    # Handle edge case — no jobs to analyze
    if not jobs:
        print("  No jobs to analyze. Skipping.")
        return {
            **state,
            "gap_analysis": {
                "resume_skills": [],
                "per_job": [],
                "missing_skills_summary": {},
                "total_jobs_analyzed": 0
            }
        }

    # Step 1: Extract resume skills
    resume_text = load_resume_text(resume_path)
    resume_skills = extract_resume_skills(resume_text)
    print(f"  Resume skills  : {sorted(resume_skills)}")

    # Step 2: Per-job gap analysis
    per_job_results = []
    missing_counter = Counter()

    for job in jobs:
        job_skills = set(job.get("extracted_skills") or [])
        matched = resume_skills & job_skills
        missing = job_skills - resume_skills
        similarity = round(1 - job["distance"], 4)

        job_result = {
            "title": job["title"],
            "company": job.get("company", "N/A"),
            "seniority": job.get("extracted_seniority", "N/A"),
            "match_score": similarity,
            "skills_matched": sorted(matched),
            "skills_missing": sorted(missing)
        }

        per_job_results.append(job_result)
        missing_counter.update(missing)

        print(f"  Analyzed: {job['title']} at {job.get('company', 'N/A')}")
        print(f"    Matched : {sorted(matched) if matched else 'none'}")
        print(f"    Missing : {sorted(missing) if missing else 'none'}")

    # Step 3: Build summary of most common missing skills
    missing_skills_summary = dict(missing_counter.most_common(10))

    gap_analysis = {
        "resume_skills": sorted(resume_skills),
        "per_job": per_job_results,
        "missing_skills_summary": missing_skills_summary,
        "total_jobs_analyzed": len(per_job_results)
    }

    print(f"\n  Most common gaps: {missing_skills_summary}")

    return {**state, "gap_analysis": gap_analysis}