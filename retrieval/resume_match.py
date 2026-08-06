from sentence_transformers import SentenceTransformer
from ingestion.database import supabase
from pathlib import Path
import pdfplumber 
import sys 

model = SentenceTransformer('all-MiniLM-L6-v2')

def load_resume(path: str = "data/NISHITH_KASHIMALLA_CV.pdf") -> str:
    """
    Extract text from a PDF resume.
    """
    resume_path = Path(path)
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume not found at {path}. Add your resume PDF to the data/ folder.")
    
    text = ""
    with pdfplumber.open(resume_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    text = text.strip()
    print(f"Resume loaded — {len(text.split())} words extracted from PDF")
    return text

def match_resume_to_jobs(top_k: int = 10, resume_path: str = "data/NISHITH_KASHIMALLA_CV.pdf"):
    """
    Embed the resume and find the most similar job postings.
    """
    # Step 1: Load and embed resume
    resume_text = load_resume(resume_path)
    print("Generating resume embedding...")
    resume_embedding = model.encode(resume_text).tolist()

    # Step 2: Search against all job postings
    response = supabase.rpc("match_jobs", {
        "query_embedding": resume_embedding,
        "match_count": top_k
    }).execute()

    results = response.data

    if not results:
        print("No results found.")
        return []

    # Step 3: Print results
    print(f"\nTop {top_k} jobs matching your resume:\n")
    print("=" * 60)
    
    for i, job in enumerate(results, 1):
        similarity = round(1 - job['distance'], 4)
        print(f"#{i} — {job['title']}")
        print(f"   Company  : {job.get('company', 'N/A')}")
        print(f"   Seniority: {job.get('extracted_seniority', 'N/A')}")
        print(f"   Skills   : {job.get('extracted_skills', [])}")
        print(f"   Match    : {similarity}")
        print()

    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use filename passed as argument
        pdf_path = f"data/{sys.argv[1]}"
        match_resume_to_jobs(top_k=10, resume_path=pdf_path)
    else:
        # Default: use NISHITH_KASHIMALLA_CV.pdf
        match_resume_to_jobs(top_k=10)