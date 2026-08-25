from langgraph.graph import StateGraph, END
from agents.state import TalentGraphState
from agents.intake_agent import intake_agent
from agents.retrieval_agent import retrieval_agent
from agents.analysis_agent import analysis_agent


def build_graph():
    """
    Builds and compiles the TalentGraph agent graph.
    Week 3 Day 3: Intake + Retrieval + Analysis wired in.
    """

    graph = StateGraph(TalentGraphState)

    # Add nodes
    graph.add_node("intake", intake_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("analysis", analysis_agent)

    # Define edges
    graph.set_entry_point("intake")
    graph.add_edge("intake", "retrieval")
    graph.add_edge("retrieval", "analysis")
    graph.add_edge("analysis", END)

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
    print(f"  Jobs analyzed  : {result['gap_analysis']['total_jobs_analyzed']}")
    print(f"  Missing skills : {result['gap_analysis']['missing_skills_summary']}")
    print(f"\n  Per job breakdown:")

    for job in result["gap_analysis"]["per_job"]:
        print(f"\n  — {job['title']} at {job['company']}")
        print(f"    Match score : {job['match_score']}")
        print(f"    You have    : {job['skills_matched'] or 'none matched'}")
        print(f"    You're missing: {job['skills_missing'] or 'none'}")