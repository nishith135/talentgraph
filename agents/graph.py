from langgraph.graph import StateGraph, END
from agents.state import TalentGraphState
from agents.intake_agent import intake_agent


def build_graph():
    """
    Builds and compiles the TalentGraph agent graph.
    Currently only has the Intake Agent wired in.
    More agents will be added Day by Day.
    """

    graph = StateGraph(TalentGraphState)

    # Add nodes
    graph.add_node("intake", intake_agent)

    # Set entry point
    graph.set_entry_point("intake")

    # For now, intake goes straight to END
    graph.add_edge("intake", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    # Test run
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