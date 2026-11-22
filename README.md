# Resume → Job Matcher

Upload a resume, get ranked jobs with an explanation of each match and concrete advice for improving the profile.

```
Resume (PDF/DOCX/TXT)
  → extract.py     skills (taxonomy + regex), experience (date ranges), education, quality signals
  → embeddings.py  sentence-transformers (all-MiniLM-L6-v2); resume = mean of chunk embeddings
  → FAISS          IndexFlatIP over job embeddings (cosine), retrieves top 4×k
  → ranking.py     score = 0.50 skill overlap + 0.35 semantic relevance + 0.15 experience fit
  → llm.py         Ollama via LangChain explains each match from the structured facts only
  → feedback.py    rule-based tips (+ optional LLM coach note)
  → FastAPI REST + static web UI;  SQLite stores jobs and candidates
```

## Run with Docker
```bash
docker compose up --build        # first start pulls the llama3.2 model (~2 GB)
open http://localhost:8000       # API docs at /docs
```
The app works without Ollama: explanations fall back to a template and the UI says so.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2             # optional
uvicorn app.main:app --reload
```
Settings are environment variables: `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `EMBED_MODEL`, `USE_LLM=0`, `DATA_DIR`.

## API
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/analyze` | multipart `file` or form `text`; optional `top_k`, `explain` → profile, matches, feedback |
| GET | `/api/candidates/{id}/matches` | re-match a stored resume |
| GET / POST | `/api/jobs` | list jobs / add one (the FAISS index is rebuilt) |
| GET | `/api/health` | job count, Ollama status |

```bash
curl -F file=@resume.pdf -F top_k=5 http://localhost:8000/api/analyze
curl -X POST localhost:8000/api/jobs -H 'content-type: application/json' -d \
 '{"title":"Go Engineer","description":"Build services in Go.","required":["Go","Docker"],"min_years":3,"max_years":8}'
```

## Design notes
- **Why not embeddings alone?** Embeddings capture role similarity but blur exact tools. Skill overlap (required skills count double) makes the score explainable, and the three components are returned so the UI can show them.
- **LLM grounding:** the prompt contains only extracted facts and tells the model not to invent any. The LLM explains the ranking; it never decides it.
- **Tests:** `python -m pytest` covers extraction, scoring and ranking without loading any model.

## Known limits
- Skills outside `app/skills.py` are only found if a job lists them (they are scanned for automatically). Extend the taxonomy for better coverage.
- Experience comes from date ranges and “N years of experience” lines; unusual date formats are missed. Education date ranges are skipped on purpose.
- Scanned PDFs need OCR (not included). The relevance rescaling in `ranking.relevance` is tuned for MiniLM; retune it if you change the embedding model.
- Seed jobs are fictional. Replace `seed/jobs.json` or POST your own.
