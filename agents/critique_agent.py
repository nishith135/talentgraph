from agents.state import TalentGraphState
from agents.tracer import get_tracer

MIN_JOBS_REQUIRED = 2
MIN_MATCH_SCORE = 0.45
MAX_RETRIES = 2


def critique_agent(state: TalentGraphState) -> TalentGraphState:
    print("\n[ CRITIQUE AGENT ] Evaluating results...")

    tracer = get_tracer()
    span = tracer.span(
        trace_id=state.get("trace_id"),
        name="critique-agent",
        input={
            "total_jobs": state.get("gap_analysis", {}).get("total_jobs_analyzed"),
            "retry_count": state.get("retry_count")
        }
    )

    gap_analysis = state.get("gap_analysis") or {}
    retry_count = state.get("retry_count") or 0
    per_job = gap_analysis.get("per_job") or []
    total_jobs = gap_analysis.get("total_jobs_analyzed") or 0

    if retry_count >= MAX_RETRIES:
        print(f"  Max retries ({MAX_RETRIES}) reached. Passing forward.")
        span.end(output={"passed": True, "reason": "max_retries_reached"})
        return {
            **state,
            "critique_passed": True,
            "critique_feedback": "Max retries reached. Results may be limited."
        }

    if total_jobs < MIN_JOBS_REQUIRED:
        feedback = f"Only {total_jobs} job(s) retrieved. Loosening filters and retrying."
        print(f"  Failed: {feedback}")
        span.end(output={"passed": False, "reason": "insufficient_jobs"})
        return {
            **state,
            "critique_passed": False,
            "critique_feedback": feedback,
            "retry_count": retry_count + 1,
            "filters": _loosen_filters(state.get("filters") or {})
        }

    scores = [job["match_score"] for job in per_job]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0

    if avg_score < MIN_MATCH_SCORE:
        feedback = f"Average match score {avg_score} below threshold. Retrying."
        print(f"  Failed: {feedback}")
        span.end(output={"passed": False, "reason": "low_match_scores", "avg_score": avg_score})
        return {
            **state,
            "critique_passed": False,
            "critique_feedback": feedback,
            "retry_count": retry_count + 1,
            "filters": _loosen_filters(state.get("filters") or {})
        }

    print(f"  Passed: {total_jobs} jobs retrieved, average match score {avg_score}")
    span.end(output={"passed": True, "avg_score": avg_score, "total_jobs": total_jobs})
    return {
        **state,
        "critique_passed": True,
        "critique_feedback": f"{total_jobs} jobs retrieved, average match score {avg_score}."
    }


def _loosen_filters(filters: dict) -> dict:
    loosened = filters.copy()
    if loosened.get("required_skills"):
        print("  Loosening: dropping required_skills filter")
        loosened["required_skills"] = []
    elif loosened.get("seniority"):
        print("  Loosening: dropping seniority filter")
        loosened["seniority"] = None
    return loosened


def should_retry(state: TalentGraphState) -> str:
    if state.get("critique_passed"):
        return "response"
    return "retrieval"