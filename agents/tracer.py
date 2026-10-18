"""
TalentGraph — Langfuse tracer utility.

This file creates one shared Langfuse client that all agents import.
Think of it as the single recorder that every agent reports to.
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from langfuse import Langfuse
    langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )
    LANGFUSE_AVAILABLE = True
except Exception:
    langfuse = None
    LANGFUSE_AVAILABLE = False


def get_tracer():
    return langfuse