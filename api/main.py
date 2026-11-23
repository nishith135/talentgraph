import os
import tempfile
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.graph import build_graph
from agents.tracer import get_tracer

app = FastAPI(
    title="TalentGraph API",
    description="Multi-agent job-application assistant backend",
    version="1.0.0"
)

# Enable CORS for localhost (development and UI integration)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile graph once for performance across requests
graph_app = build_graph()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
async def run(
    query: str = Form(..., description="Job search query in plain English"),
    resume: Optional[UploadFile] = File(None, description="Candidate resume PDF file")
):
    temp_resume_path = None
    try:
        if resume and resume.filename:
            # Save uploaded resume PDF to a temporary file for parsing
            suffix = os.path.splitext(resume.filename)[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                content = await resume.read()
                temp_file.write(content)
                temp_resume_path = temp_file.name
            resume_path = temp_resume_path
        else:
            # Fallback to default candidate resume in repo
            resume_path = "data/NISHITH_KASHIMALLA_CV.pdf"

        # Trace via Langfuse if available
        tracer = get_tracer()
        trace = tracer.trace(
            name="talentgraph-api-run",
            input={"query": query, "resume": resume_path},
            metadata={"source": "api"}
        ) if (tracer and hasattr(tracer, "trace")) else None

        initial_state = {
            "user_query": query,
            "resume_path": resume_path,
            "filters": None,
            "original_filters": None,
            "retrieved_jobs": None,
            "gap_analysis": None,
            "critique_passed": None,
            "critique_feedback": None,
            "retry_count": 0,
            "tailored_resumes": None,
            "final_output": None,
            "trace_id": trace.id if trace else None
        }

        result = graph_app.invoke(initial_state)

        # Update trace
        if trace:
            trace.update(
                output={"final_output": result.get("final_output")},
                metadata={
                    "retry_count": result.get("retry_count"),
                    "critique_feedback": result.get("critique_feedback"),
                    "jobs_analyzed": result.get("gap_analysis", {}).get("total_jobs_analyzed")
                }
            )
            if hasattr(tracer, "flush"):
                tracer.flush()

        gap_analysis = result.get("gap_analysis") or {}
        return {
            "status": "success",
            "filters": result.get("filters"),
            "original_filters": result.get("original_filters"),
            "matches": gap_analysis.get("per_job", []),
            "skill_gaps": gap_analysis.get("missing_skills_summary", {}),
            "tailored_resumes": result.get("tailored_resumes") or [],
            "retry_count": result.get("retry_count", 0),
            "critique_passed": result.get("critique_passed", False),
            "critique_feedback": result.get("critique_feedback", ""),
            "final_output": result.get("final_output", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_resume_path and os.path.exists(temp_resume_path):
            try:
                os.remove(temp_resume_path)
            except OSError:
                pass

