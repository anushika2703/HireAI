import json
from pathlib import Path

from app.extract import extract_profile, estimate_years
from app.ranking import experience_fit, rank, skill_overlap
from app.skills import SKILLS

ROOT = Path(__file__).resolve().parent.parent
RESUME = (ROOT / "seed" / "sample_resume.txt").read_text()
JOBS = json.loads((ROOT / "seed" / "jobs.json").read_text())


def test_skill_extraction():
    p = extract_profile(RESUME)
    for s in ["Python", "FastAPI", "Kafka", "AWS", "Docker", "PostgreSQL", "Redis", "Node.js", "CI/CD", "Testing"]:
        assert s in p["skills"], s
    assert "Java" not in p["skills"] and "JavaScript" not in p["skills"]


def test_no_false_positives_from_substrings():
    skills = extract_profile("I use PostgreSQL and NoSQL; the rest of the team uses JavaScript.")["skills"]
    assert set(skills) == {"PostgreSQL", "JavaScript"}  # no SQL (inside PostgreSQL/NoSQL), no REST APIs


def test_experience_merges_overlap_and_skips_education():
    assert 6 <= extract_profile(RESUME)["years_experience"] < 8
    assert estimate_years("Dev, Jan 2020 - Dec 2021\nLead, Jun 2021 - Dec 2021") == 2.0
    assert estimate_years("B.Tech, Some University, 2016 - 2020") == 0


def test_education_and_signals():
    p = extract_profile(RESUME)
    assert p["highest_education"] == "Bachelor's"
    assert p["signals"]["has_summary"] and p["signals"]["metric_count"] >= 3


def test_seed_job_skills_exist_in_taxonomy():
    for j in JOBS:
        assert set(j["required"] + j["nice"]) <= set(SKILLS), j["title"]


def test_scoring_helpers():
    job = {"required": ["Python", "AWS"], "nice": ["Kafka"]}
    score, matched, miss_req, miss_nice = skill_overlap({"Python", "Kafka"}, job)
    assert matched == ["Kafka", "Python"] and miss_req == ["AWS"] and miss_nice == []
    assert round(score, 2) == 0.6  # (2 + 1) / (4 + 1)
    assert experience_fit(6, 5, 9) == 1.0 and experience_fit(2, 4, 8) == 0.5


def test_rank_orders_by_score():
    profile = extract_profile(RESUME)
    jobs = {i: {**j, "id": i} for i, j in enumerate(JOBS, 1)}
    hits = [(i, 0.45) for i in jobs]  # same semantic score; skills + experience decide
    top = rank(profile, hits, jobs, 3)
    assert top[0]["title"] == "Senior Backend Engineer"
    assert [m["rank"] for m in top] == [1, 2, 3] and top[0]["score"] >= top[1]["score"]
