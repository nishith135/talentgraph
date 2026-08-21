from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from agents.state import TalentGraphState
import json
import re

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

    # Initialize the LLM
    llm = ChatOllama(model="qwen2:7b")
    chain = INTAKE_PROMPT | llm

    # Run the chain
    response = chain.invoke({"query": state["user_query"]})
    raw = response.content.strip()

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

    # Write back to state
    return {**state, "filters": filters}