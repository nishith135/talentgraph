# TalentGraph - Dev Notes

## Day 1: Environment + API Access

### What we built
A script that authenticates with Adzuna's API and pulls live job posting data.

### Core concepts

**1. API keys live in environment variables, never in code.**
Your `.env` file holds secrets (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`). Your Python code reads them at runtime via `os.getenv()` — it never has the actual key values typed into it. If you ever `git push` your code, your `.env` (which is in `.gitignore`) doesn't go with it.

**2. `load_dotenv()` + `os.getenv()` is the standard pattern.**
```python
load_dotenv()  # reads .env, injects values into environment
os.getenv("KEY_NAME")  # retrieves them in your code
```
If it returns `None`, the variable wasn't found — usually a file path, naming, or empty-file issue.

**3. Debugging is about isolating variables, not guessing.**
When you got `None`, we checked in order:
- Does the package exist? (`pip show`)
- Does the file exist? (`Get-ChildItem`)
- Does the file have content? (`.Length`)
- Does the content look right? (`Get-Content`)

**4. PowerShell ≠ Bash.**
`ls -la` is bash/Linux. On Windows PowerShell use `Get-ChildItem -Force`.

**5. The Adzuna API call.**
```python
requests.get(url, params={...})
```
- `params=` as a dict lets `requests` handle URL encoding
- Country code is baked into the URL (`/jobs/in/search/1` = India)
- Always check `response.status_code` before trusting the body

### Done state
- `.env` correctly holds two key-value pairs
- `.gitignore` includes `.env`
- Script successfully returns a `200` status with real job posting JSON

### Mistake log
- Created `.env` but it saved as 0 bytes — file existed, content didn't. Lesson: always verify with `Get-Content` before assuming it worked.

---

## Day 2: Normalizing Raw API Data

### What we built
A `normalize_posting()` function that converts one messy Adzuna job posting into a clean, consistent structure — then ran it across a batch and saved results to disk as JSONL.

### Core concepts

**1. Real APIs are never clean — you need a translation layer.**
Adzuna had: missing fields, inconsistent types (`id` as string or int), nested dicts (`company`, `location`, `category`), and quirks (`salary_min: 0` means "unknown," not ₹0).

**2. `dict.get("key", default)` safely reads data that might not exist.**
```python
raw.get("salary_min")         # None if missing
raw.get("title", "Unknown")   # "Unknown" if missing
```
Using `raw["salary_min"]` directly crashes if the key doesn't exist.

**3. Nested dicts need chained `.get()` calls.**
```python
raw.get("company", {}).get("display_name", "Unknown")
```
Get the outer dict safely first, then the inner value safely.

**4. Sentinel values are a real trap.**
Adzuna uses `0` for "no salary listed," not a true zero. Always inspect real sample data before writing cleaning logic.

**5. Force consistent types.**
`id` came as both string and int — `str(raw.get("id", ""))` avoids downstream bugs.

**6. Loops apply one function to many items.**
```python
for job in raw_jobs:
    cleaned_jobs.append(normalize_posting(job))
```
Write cleaning logic once, apply it to every record.

**7. JSONL format for saving growing datasets.**
One JSON object per line, append-only:
```python
with open("file.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(job) + "\n")
```

### Done state
- `normalize_posting()` handles missing fields, nested dicts, and salary-zero quirk
- 5 real jobs normalized and saved to `data/raw/normalized_postings.jsonl`

### Known limitation
Descriptions from Adzuna are truncated (end in `…`) — will affect skill extraction quality in Day 4-5.

### Mistake log
- Re-running the script creates duplicates since we're only appending — intentional, dedup is Day 3's job.

---

## Day 3: Storage + Dedup Logic

### What we built
A Postgres table in Supabase with a UNIQUE constraint that prevents duplicate job postings. Updated the fetch script to upsert data into the database instead of saving to a file.

### Core concepts

**1. Databases enforce rules, files don't.**
A JSONL file just appends everything. A database table has explicit columns with types (`TEXT`, `INTEGER`) and constraints (`UNIQUE`, `NOT NULL`). Rules are enforced automatically.

**2. The UNIQUE constraint prevents duplicates.**
```sql
UNIQUE(source, external_id)
```
The combination of `source` + `external_id` must never repeat. Adzuna job `5768228434` can only appear once.

**3. Upsert = Update + Insert.**
Instead of writing:
```python
if job_exists:
    update it
else:
    insert it
```
Upsert handles both. In practice with Supabase's Python client, we explicitly try update first, then insert if nothing was updated — more reliable.

**4. Idempotency is production-grade thinking.**
Run your script once or ten times — same result. No duplicates pile up. Critical in real systems where jobs fail and get re-run.

**5. RLS (Row Level Security) is Supabase's permission layer.**
By default, RLS blocks all access. Disabled it for development. In production you'd set up proper security policies.

**6. Pagination gets different results from the same search.**
Adzuna paginates results — page 1 gives top 5, page 2 gives next 5. The page number goes in the URL (`/search/1`, `/search/2`), not as a query param.

**7. `results_per_page` is not a database limit.**
It tells Adzuna how many results to return per request. Has nothing to do with dedup logic.

### Done state
- `job_postings` table created with `UNIQUE(source, external_id)` constraint
- Supabase RLS disabled for development
- Upsert function working (try update, fall back to insert)
- Tested with pagination — page 2 results inserted as new rows without duplicates
- Table has 10 jobs total (5 from page 1, 5 from page 2)

### Key insight
The dedup constraint doesn't limit what gets in — it only prevents exact duplicates. New unique jobs always enter the table regardless of how many times you run the script.

### Mistake log
- `.upsert(posting).execute()` directly on Supabase's Python client doesn't reliably handle conflict resolution. Switched to explicit update-then-insert logic.
- RLS error (`42501`) — Supabase blocks inserts by default. Fixed by disabling RLS on the table for development.

---

## Day 4: First Contact with Hugging Face Pipelines

### What we built
A seniority level classifier using Hugging Face's zero-shot classification model. Feed it a job description, it outputs junior/mid-level/senior + a confidence score. Results saved to database.

### Core concepts

**1. Zero-shot classification.**
Model hasn't been specifically trained on your job descriptions, but understands language well enough to classify things it's never seen before. No training data needed — just use it directly.

**2. Hugging Face = library of pre-trained models.**
Download, use, done. You don't build or train anything yourself.

**3. Transformers library.**
The Python library that runs these models. `pipeline()` is a simple interface — pass text in, get predictions out.

**4. Confidence scores matter.**
Model outputs a score (0.0-1.0) showing how sure it is. High score = more confident. Use this to know when to trust vs when to be skeptical.

**5. Models aren't perfect — you evaluate by hand.**
Tested on real job postings. Most predictions correct, but informaticscorp job said "3-5 years" and model predicted "senior" instead of "mid-level." Model over-predicts seniority on vague descriptions without clear signals.

**6. Manual evaluation is real ML work.**
No way to know if predictions are right without reading actual job descriptions yourself and making your own judgment. This is what data scientists actually do.

### Done state
- Installed `transformers` + `torch`
- Built extraction pipeline that pulls jobs, classifies seniority, saves predictions to database
- Database now has `extracted_seniority` and `seniority_confidence` columns filled
- Manually validated: most predictions correct, model can over-predict on vague descriptions

### Known limitation
Job descriptions from Adzuna are truncated — full descriptions needed for perfect judgment. Model still works reasonably well even on truncated text.

---

## Day 5: Skill Extraction with Hybrid Approach

### What we built
A skill extractor that finds tech skills in job descriptions using keyword matching + word boundaries. Returns skills grouped by category and saves to database.

### Core concepts

**1. Off-the-shelf NER models don't know tech skills.**
They're trained on generic entities (people, places, organizations), not "FastAPI" or "pgvector." Pure ML is the wrong tool here.

**2. Hybrid approach beats pure ML sometimes.**
Keyword matching + word boundaries is simpler, more reliable, and easier to debug than a trained model for this specific problem.

**3. Word boundaries prevent false positives.**
```python
pattern = r'\b' + re.escape(skill) + r'\b'
```
`\b` means "only match this as a standalone word." Stops "go" matching inside "MongoDB" and "c" matching inside "microservices."

**4. Curated taxonomy beats generic models.**
You define what skills matter. Add/remove based on what you actually see in your data. More control, more precision.

**5. Flatten vs. categorize when storing.**
Store both: a flat list of all skills (for simple queries) and a categorized dict (for analysis by category).

**6. Precision vs. recall tradeoff.**
- High recall = catching most skills but some false positives
- High precision = fewer false positives but might miss some skills
- Word boundaries improved precision significantly. Some false positives remain for single-letter skills like "r" and "c."

### Evaluation results (Day 4 pre-fix vs Day 5 post-fix)
| Metric | Before (simple matching) | After (word boundaries) |
|--------|--------------------------|------------------------|
| Hallucinations | High (Go, Gin, R, C) | Reduced significantly |
| Precision | ~25-71% | Improved |
| Recall | ~9-64% | Maintained |

### Done state
- Skill taxonomy with 100+ tech skills across 6+ categories
- Word boundary regex preventing false positives
- All 10 jobs have `extracted_skills` (flat list) and `skills_categories` (categorized dict) in database
- Can now query "which jobs require Docker" or "top skills across all postings"

### Known limitation
Missing skills not in taxonomy (niche frameworks, newer tools). Taxonomy is manually maintained — add skills as you see them in real job data.

### Real world pattern
Production systems use pragmatic hybrid approaches, not always fancy ML. Faster to maintain, easier to debug, more reliable than training a custom NER model on limited data.

### Mistake log
- Simple string matching caused systematic hallucinations (Go, Gin, R, C appearing in almost every job)
- Fixed with `re.search()` + word boundaries instead of `if skill in text_lower`

## Week 1 Review

### What works
- End-to-end pipeline runs with one command
- Dedup logic prevents duplicate jobs
- Seniority extraction works reasonably well on clear descriptions
- Skill extraction catches major tech skills
- Pydantic validation prevents bad data reaching database

### What's janky
- Descriptions are truncated — affects extraction quality
- Skill list has false positives (c, r, go matching incorrectly)
- Confidence scores for seniority sometimes low (0.42, 0.49)
- Skills list has single-letter false positives still

### What I'd fix with more time
- Fetch full job descriptions from Adzuna's detail endpoint
- Remove single-letter skills (c, r) from taxonomy or handle differently
- Add more skills to taxonomy (niche tools, newer frameworks)

### What I learned this week
- i learned a lot of things about how real prodcution grade systems works, also learned not to do silly mistakes like running the files wihtout saving them first.day 6 and 7 have mainly taught me how to unify scripts so that there will be no individual logging to databases, instead we can run two things at a time and save the output to the db. this will reduce the amount of writes to db in the long run. we have created a single pipleline that will run the entire process from fetching jobs to storing them in the database, and then extracting seniority and skills from the stored jobs. we can simply just change the params in pipeline.py's run_pipeline function, if we change the query to some other job role like'data analyst' and the location string to something else like 'hyderabad' the pipeline will adapt and pulls jobs fro data analyst roles which are located in hyderabad, this shows that our pipeline is flexible and not hardcoded 
- 