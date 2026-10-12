from collections import Counter
from agents.state import TalentGraphState
from agents.tracer import get_tracer
from retrieval.gap_analysis import extract_resume_skills, load_resume_text


def analysis_agent(state: TalentGraphState) -> TalentGraphState:
    print("\n[ ANALYSIS AGENT ] Running gap analysis...")

    tracer = get_tracer()
    span = tracer.span(
        trace_id=state.get("trace_id"),
        name="analysis-agent",
        input={"jobs_count": len(state.get("retrieved_jobs") or [])}
    )

    jobs = state.get("retrieved_jobs") or []
    resume_path = state.get("resume_path", "data/NISHITH_KASHIMALLA_CV.pdf")

    if not jobs:
        print("  No jobs to analyze. Skipping.")
        span.end(output={"total_jobs_analyzed": 0})
        return {
            **state,
            "gap_analysis": {
                "resume_skills": [],
                "per_job": [],
                "missing_skills_summary": {},
                "total_jobs_analyzed": 0
            }
        }

    resume_text = load_resume_text(resume_path)
    resume_skills = extract_resume_skills(resume_text)
    print(f"  Resume skills  : {sorted(resume_skills)}")

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

    missing_skills_summary = dict(missing_counter.most_common(10))
    print(f"\n  Most common gaps: {missing_skills_summary}")

    gap_analysis = {
        "resume_skills": sorted(resume_skills),
        "per_job": per_job_results,
        "missing_skills_summary": missing_skills_summary,
        "total_jobs_analyzed": len(per_job_results)
    }

    span.end(output={
        "total_jobs_analyzed": len(per_job_results),
        "missing_skills_summary": missing_skills_summary
    })

    return {**state, "gap_analysis": gap_analysis}