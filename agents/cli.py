"""
TalentGraph CLI — Week 3 entry point.

Usage:
    python -m agents.cli
    python -m agents.cli "find me junior Python roles in Bangalore"
    python -m agents.cli "find me junior Python roles in Bangalore" myresume.pdf
"""

import sys
from agents.graph import build_graph


def main():
    # Parse arguments
    query = " ".join(sys.argv[1:-1]) if len(sys.argv) > 2 else \
            sys.argv[1] if len(sys.argv) == 2 else \
            "find me Python developer roles"

    resume_file = sys.argv[-1] if len(sys.argv) > 2 and sys.argv[-1].endswith(".pdf") \
                  else "NISHITH_KASHIMALLA_CV.pdf"

    resume_path = f"data/{resume_file}"

    # Build and run the graph
    app = build_graph()

    initial_state = {
        "user_query": query,
        "resume_path": resume_path,
        "filters": None,
        "retrieved_jobs": None,
        "gap_analysis": None,
        "critique_passed": None,
        "critique_feedback": None,
        "retry_count": 0,
        "final_output": None
    }

    print(f"\nQuery      : '{query}'")
    print(f"Resume     : {resume_path}")
    print("Running TalentGraph...\n")

    result = app.invoke(initial_state)

    # Summary line at the end
    print(f"\nRetry count: {result['retry_count']}")
    print(f"Critique   : {result['critique_feedback']}")


if __name__ == "__main__":
    main()