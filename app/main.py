from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, db, feedback, llm
from .extract import read_resume
from .service import matcher


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    matcher.reload()
    yield


app = FastAPI(title="Resume → Job Matcher", version="1.0", lifespan=lifespan)


class JobIn(BaseModel):
    title: str
    company: str = ""
    location: str = ""
    description: str
    required: list[str] = Field(min_length=1)
    nice: list[str] = []
    min_years: float = 0
    max_years: float = 99


@app.get("/api/health")
def health():
    return {"status": "ok", "jobs": len(matcher.jobs), "llm_available": llm.available(),
            "model": config.OLLAMA_MODEL, "embedding_model": config.EMBED_MODEL}


@app.get("/api/sample")
def sample():
    return {"text": (config.SEED_DIR / "sample_resume.txt").read_text()}


@app.post("/api/analyze")
def analyze(file: UploadFile | None = File(None), text: str | None = Form(None),
            top_k: int = Form(5), explain: bool = Form(True)):
    """Resume (PDF/DOCX/TXT upload or pasted text) -> profile, ranked jobs, explanations, feedback."""
    if file is not None and file.filename:
        data = file.file.read(config.MAX_UPLOAD_BYTES + 1)
        if len(data) > config.MAX_UPLOAD_BYTES:
            raise HTTPException(413, "File is larger than 5 MB.")
        try:
            text = read_resume(file.filename, data)
        except Exception:
            raise HTTPException(422, "Couldn’t read that file. Upload a PDF, DOCX or TXT resume.")
    if not text or len(text.strip()) < 50:
        raise HTTPException(422, "No resume text found. Scanned PDFs need OCR, which isn’t supported yet; "
                                 "paste the text instead.")
    return matcher.analyze(text, top_k=max(1, min(top_k, 10)), explain=explain)


@app.get("/api/candidates/{cid}/matches")
def rematch(cid: int, top_k: int = 5, explain: bool = False):
    """Re-run matching for a stored resume, e.g. after new jobs were added."""
    c = db.get_candidate(cid)
    if not c:
        raise HTTPException(404, "Candidate not found.")
    profile = matcher.profile(c["resume_text"])
    matches = matcher.match(profile, c["resume_text"], max(1, min(top_k, 10)), explain)
    return {"candidate_id": cid, "profile": profile, "matches": matches,
            "feedback": feedback.build(profile, matches, explain)}


@app.get("/api/jobs")
def list_jobs():
    return list(matcher.jobs.values())


@app.post("/api/jobs", status_code=201)
def add_job(job: JobIn):
    job_id = db.add_job(job.model_dump())
    matcher.reload()  # re-embed and rebuild the FAISS index
    return {"id": job_id}


app.mount("/", StaticFiles(directory=config.BASE / "app" / "static", html=True), name="ui")
