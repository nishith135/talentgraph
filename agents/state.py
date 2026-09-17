from typing import TypedDict, Optional

class TalentGraphState(TypedDict):
    """
    Shared state passed between all agents in the graph.
    Every agent reads from this and writes back to it.
    """

    # Set by the user before the graph runs
    user_query: str
    resume_path: str

    # Set by the Intake Agent
    # original_filters is never modified after intake — safe to check in evals
    filters: Optional[dict]
    original_filters: Optional[dict]

    # Set by the Retrieval Agent
    retrieved_jobs: Optional[list]

    # Set by the Analysis Agent
    gap_analysis: Optional[dict]

    # Set by the Critique Agent
    critique_passed: Optional[bool]
    critique_feedback: Optional[str]
    retry_count: Optional[int]

    # Set by the Response Agent
    final_output: Optional[str]