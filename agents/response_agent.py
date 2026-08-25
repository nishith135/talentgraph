from agents.state import TalentGraphState


def response_agent(state: TalentGraphState) -> TalentGraphState:
    """
    Reads gap_analysis, filters, and critique_feedback from state.
    Formats everything into a clean, human-readable final report.
    Writes final_output back to state.
    """

    print("\n[ RESPONSE AGENT ] Formatting final output...")

    gap_analysis = state.get("gap_analysis") or {}
    filters = state.get("filters") or {}
    critique_feedback = state.get("critique_feedback", "")
    per_job = gap_analysis.get("per_job") or []
    missing_summary = gap_analysis.get("missing_skills_summary") or {}
    total_jobs = gap_analysis.get("total_jobs_analyzed") or 0

    lines = []

    # -------------------------
    # Header
    # -------------------------
    lines.append("=" * 60)
    lines.append("TALENTGRAPH — RESULTS")
    lines.append("=" * 60)

    # -------------------------
    # Search summary
    # -------------------------
    lines.append("\nSEARCH FILTERS")
    lines.append(f"  Seniority      : {filters.get('seniority') or 'any'}")
    lines.append(f"  Location       : {filters.get('location') or 'any'}")
    lines.append(f"  Required skills: {filters.get('required_skills') or 'none'}")
    lines.append(f"  Jobs analyzed  : {total_jobs}")
    lines.append(f"  Critique       : {critique_feedback}")

    # -------------------------
    # Per job breakdown
    # -------------------------
    lines.append("\nJOB MATCHES")
    lines.append("-" * 60)

    if not per_job:
        lines.append("  No jobs found matching your filters.")
    else:
        for i, job in enumerate(per_job, 1):
            lines.append(f"\n  #{i} — {job['title']} at {job['company']}")
            lines.append(f"       Match score : {job['match_score']}")
            lines.append(f"       Seniority   : {job['seniority']}")
            lines.append(
                f"       You have    : {job['skills_matched'] if job['skills_matched'] else 'none matched'}"
            )
            lines.append(
                f"       You're missing: {job['skills_missing'] if job['skills_missing'] else 'none — full match!'}"
            )

    # -------------------------
    # Skill gap summary
    # -------------------------
    lines.append("\nSKILL GAP SUMMARY")
    lines.append("-" * 60)

    if missing_summary:
        for skill, count in missing_summary.items():
            bar = "█" * count
            lines.append(f"  {skill:<25} {bar} ({count}/{total_jobs} jobs)")
    else:
        lines.append("  No skill gaps found — strong match!")

    # -------------------------
    # Actionable recommendation
    # -------------------------
    lines.append("\nRECOMMENDATION")
    lines.append("-" * 60)

    if missing_summary:
        top_gaps = list(missing_summary.keys())[:3]
        lines.append(
            f"  Focus on: {', '.join(top_gaps)}"
        )
        lines.append(
            "  These skills appear most frequently across your top matched jobs."
        )
    else:
        lines.append("  Your resume is a strong match for these roles.")

    lines.append("\n" + "=" * 60)

    # Join all lines into final output string
    final_output = "\n".join(lines)

    # Print it
    print(final_output)

    return {**state, "final_output": final_output}