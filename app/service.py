from . import db, llm, feedback
from .embeddings import Embedder, JobIndex
from .extract import extract_profile
from .ranking import rank
from .skills import SKILLS


class Matcher:
    def __init__(self):
        self.embedder = Embedder()
        self.index = JobIndex(self.embedder)
        self.jobs: dict[int, dict] = {}
        self.extra_terms: list[str] = []

    def reload(self) -> None:
        jobs = db.all_jobs()
        self.jobs = {j["id"]: j for j in jobs}
        self.extra_terms = sorted({s for j in jobs for s in j["required"] + j["nice"]} - set(SKILLS))
        self.index.build(jobs)

    def profile(self, text: str) -> dict:
        return extract_profile(text, self.extra_terms)

    def match(self, profile: dict, text: str, top_k: int, explain: bool) -> list[dict]:
        vec = self.embedder.embed_resume(text)
        hits = self.index.search(vec, max(top_k * 4, 20))  # retrieve wide, then re-rank
        matches = rank(profile, hits, self.jobs, top_k)
        return llm.explain_all(profile, matches, use_llm=explain)

    def analyze(self, text: str, top_k: int = 5, explain: bool = True) -> dict:
        profile = self.profile(text)
        cid = db.save_candidate(text, profile)
        matches = self.match(profile, text, top_k, explain)
        return {"candidate_id": cid, "profile": profile, "matches": matches,
                "feedback": feedback.build(profile, matches, explain),
                "llm": {"available": llm.available(), "model": llm.config.OLLAMA_MODEL}}


matcher = Matcher()
