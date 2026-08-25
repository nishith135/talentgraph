from langgraph.graph import StateGraph, END
from agents.state import TalentGraphState
from agents.intake_agent import intake_agent
from agents.retrieval_agent import retrieval_agent
from agents.analysis_agent import analysis_agent
from agents.critique_agent import critique_agent, should_retry


def build_graph():
    """
    Builds and compiles the TalentGraph agent graph.
    Week 3 Day 4: Critique Agent + conditional retry loop added.
    """

    graph = StateGraph(TalentGraphState)

    # Add nodes
    graph.add_node("intake", intake_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("analysis", analysis_agent)
    graph.add_node("critique", critique_agent)

    # Define fixed edges
    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieval")
    graph.add_edge("retrieval", "analysis")
    graph.add_edge("analysis", "critique")

    # Conditional edge — critique decides what happens next
    graph.add_conditional_edges(
        "critique",
        should_retry,
        {
            "retrieval": "retrieval",
            "response": END          # Response Agent goes here on Day 5
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

    print("\n[ RESULT ]")
    print(f"  Critique passed  : {result['critique_passed']}")
    print(f"  Critique feedback: {result['critique_feedback']}")
    print(f"  Retry count      : {result['retry_count']}")
    print(f"  Jobs analyzed    : {result['gap_analysis']['total_jobs_analyzed']}")