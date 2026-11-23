from pathlib import Path
import re
import json
import pdfplumber
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from agents.state import TalentGraphState
from agents.tracer import get_tracer

TAILORING_PROMPT = ChatPromptTemplate.from_template("""You are a resume tailoring agent.
Tailor the candidate's resume for the target job(s).

CRITICAL RULES (NON-NEGOTIABLE):
1. ONLY reframe and emphasize skills that ALREADY EXIST in the candidate's base resume: {resume_skills}.
2. NEVER mention, invent, or add any missing skills in the summary or bullets.
3. The following skills are strict GAPS that the candidate DOES NOT have: {missing_skills_list}.
   DO NOT mention them anywhere in the tailored summary or bullets (do NOT say "looking to learn", "interested in", etc.).
4. Report missing skills strictly under "skill_gaps".

Target Jobs to Tailor:
{jobs_block}

Return ONLY a JSON array with one object per target job, matching this exact schema:
[
  {{
    "job_title": "<job title>",
    "company": "<company>",
    "tailored_summary": "<2-3 sentence summary emphasizing ONLY existing matched skills: {resume_skills}>",
    "tailored_bullets": [
      "<achievement bullet emphasizing matched skills>",
      "<achievement bullet emphasizing matched skills>"
    ],
    "skill_gaps": ["<gap 1>", "<gap 2>"]
  }}
]

Return only valid JSON. No markdown formatting, no explanations.
""")


def _load_resume_text_safe(path: str) -> str:
    resume_path = Path(path)
    if not resume_path.exists():
        return ""
    text_parts = []
    try:
        with pdfplumber.open(resume_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    except Exception:
        return ""
    return "\n".join(text_parts).strip()


def _sanitize_text(text: str, forbidden_skills: list) -> str:
    """Removes or cleans sentences containing forbidden (missing) skills."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    cleaned_sentences = []
    for s in sentences:
        has_forbidden = False
        for skill in forbidden_skills:
            if re.search(rf"\b{re.escape(skill)}\b", s, flags=re.IGNORECASE):
                has_forbidden = True
                break
        if not has_forbidden:
            cleaned_sentences.append(s)
    return " ".join(cleaned_sentences).strip()


def tailoring_agent(state: TalentGraphState) -> TalentGraphState:
    print("\n[ TAILORING AGENT ] Tailoring resumes for top jobs...")

    tracer = get_tracer()
    jobs = state.get("retrieved_jobs") or []
    gap_analysis = state.get("gap_analysis") or {}
    per_job_analysis = gap_analysis.get("per_job") or []
    resume_skills = gap_analysis.get("resume_skills") or []

    # Limit to top 3 jobs per run to keep runtime sane
    jobs_to_process = jobs[:3]

    span = tracer.span(
        trace_id=state.get("trace_id"),
        name="tailoring-agent",
        input={"jobs_to_tailor": len(jobs_to_process)}
    ) if (tracer and hasattr(tracer, "span")) else None

    if not jobs_to_process:
        print("  No jobs to tailor. Skipping.")
        if span:
            span.end(output={"tailored_count": 0, "tailored_resumes": []})
        return {**state, "tailored_resumes": []}

    resume_path = state.get("resume_path", "data/NISHITH_KASHIMALLA_CV.pdf")
    resume_text = _load_resume_text_safe(resume_path)

    # Build target jobs block and collect all missing skills
    jobs_metadata = []
    jobs_lines = []
    all_missing_set = set()

    for i, job in enumerate(jobs_to_process):
        analysis = per_job_analysis[i] if i < len(per_job_analysis) else {}
        matched = analysis.get("skills_matched", [])
        missing = analysis.get("skills_missing", [])
        title = job.get("title", "Software Engineer")
        company = job.get("company", "N/A")
        desc = (job.get("description") or "")[:300]

        all_missing_set.update(missing)
        jobs_metadata.append({
            "title": title,
            "company": company,
            "matched": matched,
            "missing": missing
        })

        jobs_lines.append(
            f"Job {i+1}: {title} at {company}\n"
            f"  Matched Skills: {', '.join(matched) if matched else 'none'}\n"
            f"  Gaps (strictly DO NOT mention): {', '.join(missing) if missing else 'none'}\n"
            f"  Description excerpt: {desc}\n"
        )

    jobs_block = "\n".join(jobs_lines)

    # Local Ollama qwen2:7b only with compact context and prediction limits for production speed
    llm = ChatOllama(model="qwen2:7b", temperature=0.1, num_ctx=1024, num_predict=350)
    chain = TAILORING_PROMPT | llm

    tailored_resumes = []
    try:
        response = chain.invoke({
            "resume_skills": ", ".join(resume_skills[:15]),
            "missing_skills_list": ", ".join(sorted(all_missing_set)) if all_missing_set else "none",
            "jobs_block": jobs_block
        })
        raw = response.content.strip()
        clean = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        match = re.search(r"\[.*\]", clean, re.DOTALL)
        parsed_list = json.loads(match.group(0) if match else clean)

        if not isinstance(parsed_list, list):
            parsed_list = [parsed_list]

        for i, meta in enumerate(jobs_metadata):
            missing_skills = meta["missing"]
            matched_skills = meta["matched"]
            entry = parsed_list[i] if i < len(parsed_list) and isinstance(parsed_list[i], dict) else {}

            raw_summary = entry.get("tailored_summary") or f"Targeted profile for {meta['title']} emphasizing {', '.join(matched_skills)}."
            sanitized_summary = _sanitize_text(raw_summary, missing_skills)
            if not sanitized_summary:
                sanitized_summary = f"Targeted profile for {meta['title']} emphasizing {', '.join(matched_skills)}."

            raw_bullets = entry.get("tailored_bullets") or [
                f"Applied {skill} in software development and production systems." for skill in matched_skills[:3]
            ]

            sanitized_bullets = []
            for b in raw_bullets:
                clean_b = _sanitize_text(str(b), missing_skills)
                if clean_b:
                    sanitized_bullets.append(clean_b)

            if not sanitized_bullets:
                sanitized_bullets = [
                    f"Applied {skill} in engineering systems." for skill in matched_skills[:2]
                ] if matched_skills else ["Experienced software developer with proven background."]

            tailored_resumes.append({
                "job_title": meta["title"],
                "company": meta["company"],
                "tailored_summary": sanitized_summary,
                "tailored_bullets": sanitized_bullets,
                "skill_gaps": missing_skills
            })

        print(f"  ✓ Tailored {len(tailored_resumes)} resume(s) successfully.")
    except Exception as e:
        print(f"  Warning: Tailoring batch error: {e}. Falling back to structured generation.")
        for meta in jobs_metadata:
            tailored_resumes.append({
                "job_title": meta["title"],
                "company": meta["company"],
                "tailored_summary": f"Targeted profile for {meta['title']} emphasizing {', '.join(meta['matched'])}.",
                "tailored_bullets": [
                    f"Applied {skill} in software development." for skill in meta["matched"][:3]
                ] if meta["matched"] else ["Experienced software developer with proven background."],
                "skill_gaps": meta["missing"]
            })

    if span:
        span.end(output={"tailored_count": len(tailored_resumes)})

    return {**state, "tailored_resumes": tailored_resumes}
