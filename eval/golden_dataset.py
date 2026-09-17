"""
TalentGraph Golden Dataset — Week 4 Day 1

Each test case defines:
- query: the plain English input
- expected_min_jobs: minimum acceptable jobs returned
- expected_critique_pass: should critique pass?
- expected_gaps: skills that MUST appear in missing skills summary
- expected_filters: what the Intake Agent should extract
- notes: human-readable description of what this test covers
"""

GOLDEN_DATASET = [

    # -------------------------
    # HAPPY PATH CASES
    # -------------------------
    {
        "id": "TC001",
        "notes": "Standard junior Python + Django query — should find 2 jobs cleanly",
        "query": "find me junior Python developer roles in Bangalore with Django",
        "expected_filters": {
            "seniority": "junior",
            "location": "Bangalore",
            "required_skills": ["python", "django"]
        },
        "expected_min_jobs": 2,
        "expected_critique_pass": True,
        "expected_gaps": ["django", "postgresql"],
        "expected_retry_count": 0
    },
    {
        "id": "TC002",
        "notes": "Broad Python query — no filters, should return 10 jobs easily",
        "query": "find me Python developer roles",
        "expected_filters": {
            "seniority": None,
            "location": None,
            "required_skills": ["python"]
        },
        "expected_min_jobs": 5,
        "expected_critique_pass": True,
        "expected_gaps": ["django"],
        "expected_retry_count": 0
    },
    {
        "id": "TC003",
        "notes": "Data analyst query — low match scores expected, dataset is mostly Python roles",
        "query": "find me data analyst roles in Hyderabad",
        "expected_filters": {
            "seniority": None,
            "location": "Hyderabad",
            "required_skills": []
        },
        "expected_min_jobs": 2,
        "expected_critique_pass": True,
        "expected_gaps": [],
        "expected_retry_count": -1   # -1 means skip retry check for this case
    },
    {
        "id": "TC004",
        "notes": "Senior Python query — should return senior roles only",
        "query": "find me senior Python developer roles in Bangalore",
        "expected_filters": {
            "seniority": "senior",
            "location": "Bangalore",
            "required_skills": ["python"]
        },
        "expected_min_jobs": 2,
        "expected_critique_pass": True,
        "expected_gaps": [],
        "expected_retry_count": 0
    },

    # -------------------------
    # RETRY LOOP CASES
    # -------------------------
    {
        "id": "TC005",
        "notes": "Impossible filters — Chennai Rust roles don't exist, should retry and fail gracefully",
        "query": "find me junior Rust developer roles in Chennai with Kubernetes",
        "expected_filters": {
            "seniority": "junior",
            "location": "Chennai",
            "required_skills": ["rust", "kubernetes"]
        },
        "expected_min_jobs": 0,
        "expected_critique_pass": True,   # passes after max retries
        "expected_gaps": [],
        "expected_retry_count": 2
    },
    {
        "id": "TC006",
        "notes": "ML roles — don't exist in dataset, should retry and fall back",
        "query": "find me machine learning engineer roles with PyTorch",
        "expected_filters": {
            "seniority": None,
            "location": None,
            "required_skills": ["pytorch"]
        },
        "expected_min_jobs": 0,
        "expected_critique_pass": True,
        "expected_gaps": [],
        "expected_retry_count": 1
    },

    # -------------------------
    # EDGE CASES
    # -------------------------
    {
        "id": "TC007",
        "notes": "Very vague query — no filters extracted, should still return results",
        "query": "show me jobs",
        "expected_filters": {
            "seniority": None,
            "location": None,
            "required_skills": []
        },
        "expected_min_jobs": 1,
        "expected_critique_pass": True,
        "expected_gaps": [],
        "expected_retry_count": 0
    },
    {
        "id": "TC008",
        "notes": "Mid-level query — should filter correctly on seniority",
        "query": "find me mid-level Python developer roles",
        "expected_filters": {
            "seniority": "mid-level",
            "location": None,
            "required_skills": ["python"]
        },
        "expected_min_jobs": 2,
        "expected_critique_pass": True,
        "expected_gaps": [],
        "expected_retry_count": 0
    },
    {
        "id": "TC009",
        "notes": "Multiple required skills — strict filter, may need retry",
        "query": "find me Python developer roles with Django and PostgreSQL and Redis",
        "expected_filters": {
            "seniority": None,
            "location": None,
            "required_skills": ["python", "django", "postgresql", "redis"]
        },
        "expected_min_jobs": 0,
        "expected_critique_pass": True,
        "expected_gaps": [],
        "expected_retry_count": 1
    },
    {
        "id": "TC010",
        "notes": "Full stack query — tests cross-category skill matching",
        "query": "find me full stack developer roles with React and Python",
        "expected_filters": {
            "seniority": None,
            "location": None,
            "required_skills": ["react", "python"]
        },
        "expected_min_jobs": 1,
        "expected_critique_pass": True,
        "expected_gaps": [],
        "expected_retry_count": 1
    }
]