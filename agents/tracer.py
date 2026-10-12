"""
TalentGraph — Langfuse tracer utility.

This file creates one shared Langfuse client that all agents import.
Think of it as the single recorder that every agent reports to.
"""

from langfuse import Langfuse
from dotenv import load_dotenv
import os

load_dotenv()

# One shared client — created once, used by all agents
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)


def get_tracer():
    """Returns the shared Langfuse client."""
    return langfuse