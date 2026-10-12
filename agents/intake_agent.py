from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from agents.state import TalentGraphState
from agents.tracer import get_tracer
import json
import re

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
    print("\n[ INTAKE AGENT ] Parsing user query...")
    print(f"  Query: {state['user_query']}")

    # Start a Langfuse span for this agent
    tracer = get_tracer()
    span = tracer.span(
        trace_id=state.get("trace_id"),
        name="intake-agent",
        input={"query": state["user_query"]}
    )

    llm = ChatOllama(model="qwen2:7b")
    chain = INTAKE_PROMPT | llm

    response = chain.invoke({"query": state["user_query"]})
    raw = response.content.strip()

    try:
        clean = re.sub(r"```json|```", "", raw).strip()
        filters = json.loads(clean)
    except json.JSONDecodeError:
        print(f"  Warning: Could not parse filters. Raw: {raw}")
        filters = {"seniority": None, "location": None, "required_skills": []}

    print(f"  Filters extracted: {filters}")

    # End the span with output
    span.end(output={"filters": filters})

    return {**state, "filters": filters, "original_filters": filters}