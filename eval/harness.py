"""
TalentGraph Eval Harness — Week 4 Day 2

Runs every test case in the golden dataset against the live pipeline
and scores the results across four dimensions:
  1. Filter accuracy  — did Intake extract the right filters?
  2. Job count        — did Retrieval return enough jobs?
  3. Gap accuracy     — did expected skills appear in the gap summary?
  4. Retry count      — did the critique loop retry the right number of times?
"""

from agents.graph import build_graph
from eval.golden_dataset import GOLDEN_DATASET


def run_single_test(app, test_case: dict) -> dict:
    """
    Runs one test case through the live pipeline.
    Returns a result dict with pass/fail for each check.
    """

    # Build the initial state from the test case
    initial_state = {
        "user_query": test_case["query"],
        "resume_path": "data/NISHITH_KASHIMALLA_CV.pdf",
        "filters": None,
        "retrieved_jobs": None,
        "gap_analysis": None,
        "critique_passed": None,
        "critique_feedback": None,
        "retry_count": 0,
        "final_output": None
    }

    # Run the full pipeline
    result = app.invoke(initial_state)
    print(f"  DEBUG original_filters: {result.get('original_filters')}")
    print(f"  DEBUG filters: {result.get('filters')}")

    # Pull out what we need to check
    actual_filters = result.get("original_filters") or {}
    actual_jobs = result.get("gap_analysis", {}).get("total_jobs_analyzed") or 0
    actual_gaps = result.get("gap_analysis", {}).get("missing_skills_summary") or {}
    actual_retry = result.get("retry_count") or 0

    # -------------------------
    # Check 1: Filter accuracy
    # -------------------------
    expected_filters = test_case["expected_filters"]
    filter_checks = []

    # Seniority must match exactly
    filter_checks.append(
        actual_filters.get("seniority") == expected_filters.get("seniority")
    )

    # Location — case insensitive, partial match
    expected_location = (expected_filters.get("location") or "").lower()
    actual_location = (actual_filters.get("location") or "").lower()
    location_match = expected_location == "" or expected_location in actual_location
    filter_checks.append(location_match)
    
    # Required skills — case insensitive subset check
    expected_skills = set(s.lower() for s in expected_filters.get("required_skills") or [])
    actual_skills = set(s.lower() for s in actual_filters.get("required_skills") or [])
    filter_checks.append(expected_skills.issubset(actual_skills))

    filter_passed = all(filter_checks)

    # -------------------------
    # Check 2: Job count
    # -------------------------
    job_count_passed = actual_jobs >= test_case["expected_min_jobs"]

    # -------------------------
    # Check 3: Gap accuracy
    # -------------------------
    # Every expected gap skill must appear in the actual missing skills summary
    expected_gap_skills = set(s.lower() for s in test_case["expected_gaps"])
    actual_gap_skills = set(s.lower() for s in actual_gaps.keys())

    if not expected_gap_skills:
        # No gaps expected — auto pass
        gap_passed = True
    else:
        gap_passed = expected_gap_skills.issubset(actual_gap_skills)
    
    print(f"  DEBUG retry: actual={actual_retry}, expected={test_case['expected_retry_count']}")
    # -------------------------
    # Check 4: Retry count (-1 means skip this check)
    # -------------------------
    if test_case["expected_retry_count"] == -1:
        retry_passed = True
    else:
        retry_passed = actual_retry == test_case["expected_retry_count"]

    # -------------------------
    # Compile result
    # -------------------------
    checks_passed = sum([filter_passed, job_count_passed, gap_passed, retry_passed])

    return {
        "id": test_case["id"],
        "notes": test_case["notes"],
        "query": test_case["query"],
        "filter_passed": filter_passed,
        "job_count_passed": job_count_passed,
        "gap_passed": gap_passed,
        "retry_passed": retry_passed,
        "checks_passed": checks_passed,
        "total_checks": 4,
        "actual_jobs": actual_jobs,
        "actual_retry": actual_retry,
        "actual_gaps": list(actual_gap_skills),
        "actual_filters": actual_filters
    }


def run_eval_harness():
    """
    Runs all test cases and prints a full report.
    """

    print("\n" + "=" * 70)
    print("TALENTGRAPH EVAL HARNESS")
    print("=" * 70)
    print(f"Running {len(GOLDEN_DATASET)} test cases...\n")

    # Build the graph once — reuse across all test cases
    app = build_graph()

    results = []
    for i, test_case in enumerate(GOLDEN_DATASET, 1):
        print(f"[{i}/{len(GOLDEN_DATASET)}] Running {test_case['id']}...")
        result = run_single_test(app, test_case)
        results.append(result)

        # Show pass/fail per check inline
        checks = [
            ("Filters", result["filter_passed"]),
            ("Job count", result["job_count_passed"]),
            ("Gaps", result["gap_passed"]),
            ("Retries", result["retry_passed"])
        ]
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"    {status} {name}")
        print()

    # -------------------------
    # Summary report
    # -------------------------
    total_checks = sum(r["total_checks"] for r in results)
    passed_checks = sum(r["checks_passed"] for r in results)
    passed_cases = sum(1 for r in results if r["checks_passed"] == r["total_checks"])

    print("=" * 70)
    print("EVAL SUMMARY")
    print("=" * 70)
    print(f"  Test cases passed : {passed_cases}/{len(results)}")
    print(f"  Checks passed     : {passed_checks}/{total_checks}")
    print(f"  Overall score     : {round(passed_checks / total_checks * 100, 1)}%")

    # Show failed cases
    failed = [r for r in results if r["checks_passed"] < r["total_checks"]]
    if failed:
        print(f"\n  Failed cases:")
        for r in failed:
            failed_checks = []
            if not r["filter_passed"]:
                failed_checks.append("Filters")
            if not r["job_count_passed"]:
                failed_checks.append("Job count")
            if not r["gap_passed"]:
                failed_checks.append("Gaps")
            if not r["retry_passed"]:
                failed_checks.append("Retries")
            print(f"    {r['id']} — failed: {', '.join(failed_checks)}")
            print(f"    Query: {r['query']}")
            print(f"    Actual jobs: {r['actual_jobs']}, retries: {r['actual_retry']}")
            print(f"    Actual gaps: {r['actual_gaps']}")
            print()
    else:
        print("\n  All test cases passed!")

    print("=" * 70 + "\n")

    return results


if __name__ == "__main__":
    run_eval_harness()
