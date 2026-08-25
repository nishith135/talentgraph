from agents.state import TalentGraphState

# Minimum thresholds for acceptable results
MIN_JOBS_REQUIRED = 2
MIN_MATCH_SCORE = 0.45
MAX_RETRIES = 2


def critique_agent(state: TalentGraphState) -> TalentGraphState:
    """
    Reads gap_analysis from state.
    Decides whether results are good enough to pass forward.
    If not, writes critique_feedback and routes back to retrieval.
    If yes, sets critique_passed = True and routes to response.
    """

    print("\n[ CRITIQUE AGENT ] Evaluating results...")

    gap_analysis = state.get("gap_analysis") or {}
    retry_count = state.get("retry_count") or 0
    per_job = gap_analysis.get("per_job") or []
    total_jobs = gap_analysis.get("total_jobs_analyzed") or 0

    # If we've already retried too many times, pass forward regardless
    if retry_count >= MAX_RETRIES:
        print(f"  Max retries ({MAX_RETRIES}) reached. Passing forward with current results.")
        return {
            **state,
            "critique_passed": True,
            "critique_feedback": "Max retries reached. Results may be limited."
        }

    # Check 1: Were enough jobs retrieved?
    if total_jobs < MIN_JOBS_REQUIRED:
        feedback = (
            f"Only {total_jobs} job(s) retrieved — not enough for a meaningful analysis. "
            f"Loosening filters and retrying."
        )
        print(f"  Failed: {feedback}")
        return {
            **state,
            "critique_passed": False,
            "critique_feedback": feedback,
            "retry_count": retry_count + 1,
            "filters": _loosen_filters(state.get("filters") or {})
        }

    # Check 2: Are match scores high enough?
    scores = [job["match_score"] for job in per_job]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0

    if avg_score < MIN_MATCH_SCORE:
        feedback = (
            f"Average match score {avg_score} is below threshold {MIN_MATCH_SCORE}. "
            f"Loosening filters and retrying."
        )
        print(f"  Failed: {feedback}")
        return {
            **state,
            "critique_passed": False,
            "critique_feedback": feedback,
            "retry_count": retry_count + 1,
            "filters": _loosen_filters(state.get("filters") or {})
        }

    # All checks passed
    print(f"  Passed: {total_jobs} jobs retrieved, average match score {avg_score}")
    return {
        **state,
        "critique_passed": True,
        "critique_feedback": f"{total_jobs} jobs retrieved, average match score {avg_score}."
    }


def _loosen_filters(filters: dict) -> dict:
    """
    Returns a relaxed version of the current filters.
    Called when critique fails — gives retrieval a better chance
    of finding results on the next pass.

    Loosening strategy:
    - Drop required_skills first (most restrictive filter)
    - Then drop seniority
    - Location is kept — user almost always wants a specific city
    """
    loosened = filters.copy()

    if loosened.get("required_skills"):
        print("  Loosening: dropping required_skills filter")
        loosened["required_skills"] = []

    elif loosened.get("seniority"):
        print("  Loosening: dropping seniority filter")
        loosened["seniority"] = None

    return loosened


def should_retry(state: TalentGraphState) -> str:
    """
    Conditional edge function for LangGraph.
    Returns the name of the next node based on critique result.
    """
    if state.get("critique_passed"):
        return "response"
    return "retrieval"