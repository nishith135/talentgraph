import sys
from agents.graph import build_graph
from agents.tracer import get_tracer


def main():
    query = " ".join(sys.argv[1:-1]) if len(sys.argv) > 2 else \
            sys.argv[1] if len(sys.argv) == 2 else \
            "find me Python developer roles"

    resume_file = sys.argv[-1] if len(sys.argv) > 2 and sys.argv[-1].endswith(".pdf") \
                  else "NISHITH_KASHIMALLA_CV.pdf"

    resume_path = f"data/{resume_file}"

    # Create Langfuse trace
    tracer = get_tracer()
    trace = tracer.trace(
        name="talentgraph-run",
        input={"query": query, "resume": resume_path},
        metadata={"source": "cli"}
    )

    app = build_graph()

    initial_state = {
        "user_query": query,
        "resume_path": resume_path,
        "filters": None,
        "original_filters": None,
        "retrieved_jobs": None,
        "gap_analysis": None,
        "critique_passed": None,
        "critique_feedback": None,
        "retry_count": 0,
        "final_output": None,
        "trace_id": trace.id
    }

    print(f"\nQuery      : '{query}'")
    print(f"Resume     : {resume_path}")
    print(f"Trace ID   : {trace.id}")
    print("Running TalentGraph...\n")

    result = app.invoke(initial_state)

    # Update trace with final results
    trace.update(
        output={"final_output": result.get("final_output")},
        metadata={
            "retry_count": result.get("retry_count"),
            "jobs_analyzed": result.get("gap_analysis", {}).get("total_jobs_analyzed")
        }
    )

    tracer.flush()

    print(f"\nRetry count: {result['retry_count']}")
    print(f"Critique   : {result['critique_feedback']}")
    print(f"Trace logged: {trace.id}")


if __name__ == "__main__":
    main()