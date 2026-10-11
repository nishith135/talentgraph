from dotenv import load_dotenv
import os
import json
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from agents.state import TalentGraphState

load_dotenv()

# Prompt template for parsing user query
INTAKE_PROMPT = ChatPromptTemplate.from_template("""
You are a job search assistant. Extract structured filters from the user's query.

User query: {query}

Return ONLY a JSON object with these fields:
- seniority: "junior", "mid-level", "senior", or null
- location: city name as a string, or null
- required_skills: list of skill strings, or empty list

Example output:
{{"seniority": "junior", "location": "Bangalore", "required_skills": ["python", "django"]}}

Return only the JSON. No explanation. No markdown.
""")


def intake_agent(state: TalentGraphState) -> TalentGraphState:
    """
    Reads user_query from state.
    Parses intent and extracts filters.
    Writes filters back to state.
    """
    print("\n[ INTAKE AGENT ] Parsing user query...")
    print(f"  Query: {state['user_query']}")

    # Initialize the LLM dynamically from environment
    model_name = os.getenv("OLLAMA_MODEL", "qwen2:7b")

    llm = ChatOllama(
        model=model_name,
        temperature=0
    )
    chain = INTAKE_PROMPT | llm

    # Run the chain
    response = chain.invoke({"query": state["user_query"]})
    if isinstance(response.content, list):
        raw = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in response.content
        ).strip()
    else:
        raw = str(response.content).strip()

    # Parse JSON safely
    try:
        # Strip markdown code fences if present
        clean = re.sub(r"```json|```", "", raw).strip()
        filters = json.loads(clean)
    except json.JSONDecodeError:
        print(f"  Warning: Could not parse filters, using empty defaults. Raw: {raw}")
        filters = {
            "seniority": None,
            "location": None,
            "required_skills": []
        }

    print(f"  Filters extracted: {filters}")

    # Write to both filters (mutable) and original_filters (permanent snapshot)
    return {**state, "filters": filters, "original_filters": filters}