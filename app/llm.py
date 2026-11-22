"""Ollama (via LangChain) explanations, with a deterministic fallback."""
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from . import config

SYSTEM = {
    "explain": (
        "You are a careful recruiting assistant. Use ONLY the facts provided. Never invent skills, "
        "employers, numbers or requirements. Write 2-3 plain sentences addressed to the candidate "
        "as 'you': say why this job fits, then name the biggest gap and how to address it. No lists, no headings."),
    "coach": (
        "You are a concise career coach. Use ONLY the facts provided. Write one short paragraph "
        "(at most 4 sentences) that tells the candidate the most valuable changes to make to their "
        "resume. No lists, no headings."),
}
_state = {"ok": False, "t": 0.0}
_chains: dict = {}


def available() -> bool:
    if not config.USE_LLM:
        return False
    if time.time() - _state["t"] < 30:
        return _state["ok"]
    try:
        with urllib.request.urlopen(config.OLLAMA_BASE_URL.rstrip("/") + "/api/tags", timeout=1.5) as r:
            names = {m["name"].split(":")[0] for m in json.load(r).get("models", [])}
        ok = config.OLLAMA_MODEL.split(":")[0] in names
    except Exception:
        ok = False
    _state.update(ok=ok, t=time.time())
    return ok


def _chain(kind: str):
    if kind not in _chains:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL,
                         temperature=0.2, num_predict=220, client_kwargs={"timeout": 90})
        prompt = ChatPromptTemplate.from_messages([("system", SYSTEM[kind]), ("human", "{facts}")])
        _chains[kind] = prompt | llm | StrOutputParser()
    return _chains[kind]


def _facts(profile: dict, m: dict) -> str:
    lo, hi = m["experience_range"]
    return "\n".join([
        f"Job: {m['title']} at {m['company']} ({m['location']})",
        f"Overall match score: {m['score']}/100 ({m['label']})",
        f"Skills you have that this job wants: {', '.join(m['matched_skills']) or 'none'}",
        f"Required skills missing from your resume: {', '.join(m['missing_required']) or 'none'}",
        f"Nice-to-have skills missing: {', '.join(m['missing_nice']) or 'none'}",
        f"Your experience: {profile['years_experience']} years; the job asks for {lo}-{hi} years",
        f"Resume-to-job-description semantic relevance: {m['breakdown']['relevance']}%",
    ])


def _template(profile: dict, m: dict) -> str:
    lo, hi = m["experience_range"]
    yrs = profile["years_experience"]
    parts = [f"You cover {len(m['matched_skills'])} skills this role looks for"
             + (f", including {', '.join(m['matched_skills'][:4])}." if m["matched_skills"] else ".")]
    if yrs < lo:
        parts.append(f"Your {yrs:g} years is below the {lo:g}-year minimum.")
    elif yrs > hi:
        parts.append(f"Your {yrs:g} years is above the usual {lo:g}–{hi:g} range, so expect a senior-level conversation.")
    else:
        parts.append(f"Your {yrs:g} years fits the {lo:g}–{hi:g} year range.")
    if m["missing_required"]:
        parts.append(f"The main gap is {', '.join(m['missing_required'][:3])}.")
    return " ".join(parts)


def explain_all(profile: dict, matches: list[dict], use_llm: bool = True) -> list[dict]:
    ok = use_llm and available()

    def one(m: dict) -> None:
        if ok:
            try:
                text = _chain("explain").invoke({"facts": _facts(profile, m)}).strip()
                if text:
                    m["explanation"], m["explanation_source"] = text, "llm"
                    return
            except Exception:
                pass
        m["explanation"], m["explanation_source"] = _template(profile, m), "template"

    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(one, matches))
    return matches


def coach_note(profile: dict, tips: list[str], gaps: dict) -> str | None:
    facts = (f"Years of experience: {profile['years_experience']}\n"
             f"Skills detected: {', '.join(profile['skills'])}\n"
             f"Skills missing most often from matching jobs: {gaps or 'none'}\n"
             "Findings:\n- " + "\n- ".join(tips))
    try:
        return _chain("coach").invoke({"facts": facts}).strip() or None
    except Exception:
        return None
