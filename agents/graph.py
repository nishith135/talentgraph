from langgraph.graph import StateGraph, END
from agents.state import TalentGraphState
from agents.intake_agent import intake_agent
from agents.retrieval_agent import retrieval_agent
from agents.analysis_agent import analysis_agent
from agents.critique_agent import critique_agent, should_retry
from agents.response_agent import response_agent
from agents.tracer import get_tracer
import sys


def build_graph():
    """
    Builds and compiles the TalentGraph agent graph.
    Complete 5-agent graph with critique retry loop.
    """

    graph = StateGraph(TalentGraphState)

    graph.add_node("intake", intake_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("analysis", analysis_agent)
    graph.add_node("critique", critique_agent)
    graph.add_node("response", response_agent)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieval")
    graph.add_edge("retrieval", "analysis")
    graph.add_edge("analysis", "critique")
    graph.add_edge("response", END)

    graph.add_conditional_edges(
        "critique",
        should_retry,
        {
            "retrieval": "retrieval",
            "response": "response"
        }
    )

    return graph.compile()


if __name__ == "__main__":
    query = " ".join(sys.argv[1:-1]) if len(sys.argv) > 2 else \
            sys.argv[1] if len(sys.argv) == 2 else \
            "find me Python developer roles"

    resume_file = sys.argv[-1] if len(sys.argv) > 2 and sys.argv[-1].endswith(".pdf") \
                  else "NISHITH_KASHIMALLA_CV.pdf"

    resume_path = f"data/{resume_file}"

    # Create one Langfuse trace for this entire run
    tracer = get_tracer()
    trace = tracer.trace(
        name="talentgraph-run",
        input={"query": query, "resume": resume_path},
        metadata={"source": "cli"}
    ) if (tracer and hasattr(tracer, "trace")) else None

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
        "trace_id": trace.id if trace else None   # pass trace ID into state
    }

    print(f"\nQuery      : '{query}'")
    print(f"Resume     : {resume_path}")
    if trace:
        print(f"Trace ID   : {trace.id}")
    print("Running TalentGraph...\n")

    result = app.invoke(initial_state)

    # Update the trace with the final output
    if trace:
        trace.update(
            output={"final_output": result.get("final_output")},
            metadata={
                "retry_count": result.get("retry_count"),
                "critique_feedback": result.get("critique_feedback"),
                "jobs_analyzed": result.get("gap_analysis", {}).get("total_jobs_analyzed")
            }
        )

    # Flush ensures all data is sent before the script exits
    if tracer and hasattr(tracer, "flush"):
        tracer.flush()

    print(f"\nRetry count: {result['retry_count']}")
    print(f"Critique   : {result['critique_feedback']}")
    if trace:
        print(f"Trace logged to Langfuse: {trace.id}")