from langgraph.graph import StateGraph, END
from agents.state import TalentGraphState
from agents.intake_agent import intake_agent
from agents.retrieval_agent import retrieval_agent
from agents.analysis_agent import analysis_agent
from agents.critique_agent import critique_agent, should_retry
from agents.response_agent import response_agent


def build_graph():
    """
    Complete TalentGraph agent graph.
    Week 3 Day 5: All 5 agents wired in with critique loop.

    Flow:
    intake → retrieval → analysis → critique → response
                  ↑______________|  (if critique fails)
    """

    graph = StateGraph(TalentGraphState)

    # Add all nodes
    graph.add_node("intake", intake_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("analysis", analysis_agent)
    graph.add_node("critique", critique_agent)
    graph.add_node("response", response_agent)

    # Fixed edges
    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieval")
    graph.add_edge("retrieval", "analysis")
    graph.add_edge("analysis", "critique")
    graph.add_edge("response", END)

    # Conditional edge — critique routes to response or loops to retrieval
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