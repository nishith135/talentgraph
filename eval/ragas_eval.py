"""
TalentGraph Ragas Evaluation — Week 4 Day 3

Measures RAG quality across four dimensions:
  - Faithfulness      : is the gap report grounded in retrieved job content?
  - Answer Relevance  : does the response match what was asked?
  - Context Precision : were the retrieved jobs actually relevant?
  - Context Recall    : did we find all the relevant jobs?
"""

from dotenv import load_dotenv
import os
import json
from agents.graph import build_graph
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from ragas.embeddings import HuggingFaceEmbeddings

load_dotenv()

def get_ragas_llm():
    model_name = os.getenv("GOOGLE_MODEL", "gemini-3.8-flash")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set. Please add your key to talentgraph/.env")
    return LangchainLLMWrapper(
        ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0
        )
    )

eval_embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")

# Test cases for Ragas — simpler than the golden dataset
# Each needs: question, ground_truth, and we'll fill answer + contexts from the pipeline
RAGAS_TEST_CASES = [
    {
        "question": "find me junior Python developer roles in Bangalore with Django",
        "ground_truth": "Junior Python developer roles in Bangalore requiring Django and related backend skills like PostgreSQL and Flask"
    },
    {
        "question": "find me Python developer roles",
        "ground_truth": "Python developer roles requiring skills like Django, Flask, REST APIs and database experience"
    },
    {
        "question": "find me data analyst roles in Hyderabad",
        "ground_truth": "Data analyst roles in Hyderabad requiring SQL, data visualization and analytical skills"
    },
    {
        "question": "find me mid-level Python developer roles",
        "ground_truth": "Mid-level Python developer roles requiring Python frameworks and some cloud or database experience"
    },
    {
        "question": "find me full stack developer roles with React and Python",
        "ground_truth": "Full stack roles requiring both React for frontend and Python for backend development"
    }
]


def run_pipeline_for_ragas(app, query: str) -> tuple[str, list[str]]:
    """
    Runs one query through the pipeline.
    Returns (answer, contexts) where:
      - answer   = the final gap report as a string
      - contexts = list of job description strings used as context
    """
    initial_state = {
        "user_query": query,
        "resume_path": "data/NISHITH_KASHIMALLA_CV.pdf",
        "filters": None,
        "original_filters": None,
        "retrieved_jobs": None,
        "gap_analysis": None,
        "critique_passed": None,
        "critique_feedback": None,
        "retry_count": 0,
        "final_output": None
    }

    result = app.invoke(initial_state)

    # The answer is the final formatted output
    answer = result.get("final_output") or "No results found."

    # The contexts are the job descriptions of retrieved jobs
    # This is what Ragas checks the answer against for faithfulness
    retrieved_jobs = result.get("retrieved_jobs") or []
    contexts = []
    for job in retrieved_jobs:
        job_text = f"{job.get('title', '')} at {job.get('company', '')}. {job.get('description', '')}"
        contexts.append(job_text.strip())

    # Ragas needs at least one context — fallback if empty
    if not contexts:
        contexts = ["No relevant jobs found in database."]

    return answer, contexts


def run_ragas_eval():
    print("\n" + "=" * 60)
    print("TALENTGRAPH — RAGAS EVALUATION")
    print("=" * 60)
    print(f"Running {len(RAGAS_TEST_CASES)} test cases...\n")

    app = build_graph()

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    # Run each test case through the pipeline
    for i, tc in enumerate(RAGAS_TEST_CASES, 1):
        print(f"[{i}/{len(RAGAS_TEST_CASES)}] Running: '{tc['question']}'")
        answer, context = run_pipeline_for_ragas(app, tc["question"])

        questions.append(tc["question"])
        answers.append(answer)
        contexts.append(context)
        ground_truths.append(tc["ground_truth"])

        print(f"  Retrieved {len(context)} job context(s)")
        print(f"  Answer length: {len(answer)} chars\n")

    # Build the Ragas dataset
    ragas_dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    # Run Ragas evaluation
    print("Running Ragas scoring (this uses an LLM — may take a minute)...")
    print("Note: Adzuna descriptions are truncated which may lower recall scores.\n")

    gemini_llm = get_ragas_llm()

    results = evaluate(
        ragas_dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm = gemini_llm,
        embeddings = eval_embeddings  
    )

    def _mean_score(val):
        if isinstance(val, (list, tuple)):
            clean_vals = [v for v in val if v is not None and not (isinstance(v, float) and v != v)]
            return round(sum(clean_vals) / len(clean_vals), 4) if clean_vals else 0.0
        elif isinstance(val, (int, float)):
            return round(val, 4)
        return val

    # Print results
    print("\n" + "=" * 60)
    print("RAGAS SCORES")
    print("=" * 60)
    print(f"  Faithfulness     : {_mean_score(results.get('faithfulness'))}")
    print(f"  Answer Relevance : {_mean_score(results.get('answer_relevancy'))}")
    print(f"  Context Precision: {_mean_score(results.get('context_precision'))}")
    print(f"  Context Recall   : {_mean_score(results.get('context_recall'))}")
    print("=" * 60)
    print("\nScore guide: 0 = worst, 1 = best")
    print("Expected low recall due to truncated Adzuna descriptions.")
    print("=" * 60 + "\n")

    return results


if __name__ == "__main__":
    run_ragas_eval()