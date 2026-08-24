from langgraph.graph import StateGraph, END
from agents.state import TalentGraphState
from agents.intake_agent import intake_agent
from agents.retrieval_agent import retrieval_agent


def build_graph():
    """
    Builds and compiles the TalentGraph agent graph.
    Week 3 Day 2: Intake + Retrieval wired in.
    """

    graph = StateGraph(TalentGraphState)

    # Add nodes
    graph.add_node("intake", intake_agent)
    graph.add_node("retrieval", retrieval_agent)

    # Define edges
    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieval")
    graph.add_edge("retrieval", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    initial_state = {
        "user_query": "find me junior Python developer roles in Bangalore with Django",
        "resume_path": "data/NISHITH_KASHIMALLA_CV.pdf",
        "filters": None,
        "retrieved_jobs": None,
        "gap_analysis": None,
        "critique_passed": None,
        "critique_feedback": None,
        "retry_count": 0,
        "final_output": None
    }

    print("\nRunning TalentGraph agent graph...")
    result = app.invoke(initial_state)

    print("\n[ RESULT ]")
    print(f"  Filters: {result['filters']}")
    print(f"  Jobs retrieved: {len(result['retrieved_jobs'] or [])} jobs")

    for i, job in enumerate(result["retrieved_jobs"] or [], 1):
        print(f"\n  #{i} — {job['title']} at {job.get('company', 'N/A')}")
        print(f"       Seniority : {job.get('extracted_seniority', 'N/A')}")
        print(f"       Match     : {round(1 - job['distance'], 4)}")