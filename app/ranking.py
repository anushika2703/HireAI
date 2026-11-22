"""Re-rank FAISS candidates with skill overlap, semantic relevance and experience fit."""
from . import config


def skill_overlap(cand: set[str], job: dict):
    req, nice = set(job["required"]), set(job["nice"])
    total = 2 * len(req) + len(nice)  # required skills count double
    got = 2 * len(req & cand) + len(nice & cand)
    return (got / total if total else 0.0,
            sorted((req | nice) & cand),
            sorted(req - cand),
            sorted(nice - cand))


def experience_fit(years: float, lo: float, hi: float) -> float:
    if years < lo:
        return max(0.0, 1 - (lo - years) / max(lo, 1))
    if years > hi:
        return max(0.7, 1 - 0.05 * (years - hi))  # mild over-qualification penalty
    return 1.0


def relevance(cosine: float) -> float:
    """MiniLM resume<->JD cosine typically lives in 0.15-0.65; stretch to 0-1."""
    return min(1.0, max(0.0, (cosine - 0.15) / 0.50))


def label(score: float) -> str:
    return ("Excellent" if score >= 80 else "Strong" if score >= 65
            else "Fair" if score >= 50 else "Weak")


def rank(profile: dict, hits: list[tuple[int, float]], jobs: dict[int, dict], top_k: int) -> list[dict]:
    cand, w, results = set(profile["skills"]), config.WEIGHTS, []
    for job_id, cos in hits:
        j = jobs[job_id]
        s, matched, miss_req, miss_nice = skill_overlap(cand, j)
        e = experience_fit(profile["years_experience"], j["min_years"], j["max_years"])
        r = relevance(cos)
        score = 100 * (w["skills"] * s + w["relevance"] * r + w["experience"] * e)
        results.append({
            "job_id": job_id, "title": j["title"], "company": j["company"],
            "location": j["location"], "score": round(score, 1), "label": label(score),
            "breakdown": {"skills": round(100 * s), "experience": round(100 * e),
                          "relevance": round(100 * r)},
            "similarity": round(cos, 3),
            "matched_skills": matched, "missing_required": miss_req, "missing_nice": miss_nice,
            "experience_range": [j["min_years"], j["max_years"]],
        })
    results.sort(key=lambda m: m["score"], reverse=True)
    for i, m in enumerate(results[:top_k], 1):
        m["rank"] = i
    return results[:top_k]
