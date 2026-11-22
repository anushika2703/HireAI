"""Resume text -> structured profile (skills, experience, education, quality signals)."""
import io
import re
from datetime import date
from functools import lru_cache

from .skills import CASE_SENSITIVE, SKILLS


def read_resume(filename: str | None, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
    if name.endswith(".docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="ignore")


# ---------- skills ----------
@lru_cache(maxsize=1024)
def _pattern(terms: tuple[str, ...]) -> re.Pattern:
    alts = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alts})(?!\w)", re.I)


def find_skills(text: str, extra: list[str] | None = None) -> list[str]:
    found = []
    for c, aliases in SKILLS.items():
        hit = _pattern(tuple({c.lower(), *aliases})).search(text)
        if not hit and c in CASE_SENSITIVE:
            hit = re.search(rf"(?<!\w)(?:{'|'.join(map(re.escape, CASE_SENSITIVE[c]))})(?!\w)", text)
        if hit:
            found.append(c)
    for term in extra or []:  # job-specific skills outside the taxonomy
        if term not in SKILLS and term not in found and _pattern((term.lower(),)).search(text):
            found.append(term)
    return found


# ---------- experience ----------
_MON = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
_MONTHS = _MON.split("|")
_DATE = rf"(?:(?:{_MON})[a-z]*\.?,?\s+)?(?:19|20)\d{{2}}"
_RANGE = re.compile(
    rf"({_DATE})\s*(?:-|–|—|to)\s*({_DATE}|present|current|now|till date|ongoing)", re.I)
_EDU_LINE = re.compile(
    r"universit|college|institute|school|b\.?tech|m\.?tech|bachelor|master|b\.?sc|m\.?sc"
    r"|ph\.?d|mba|degree|cgpa|gpa", re.I)
_EXPLICIT = re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)\b", re.I)


def _month_index(s: str, is_end: bool) -> int:
    s = s.strip().lower()
    if re.match(r"(present|current|now|till|ongoing)", s):
        t = date.today()
        return t.year * 12 + t.month - 1
    year = int(re.search(r"(?:19|20)\d{2}", s).group())
    m = re.match(r"([a-z]{3})", s)
    month = _MONTHS.index(m.group(1)) + 1 if m and m.group(1) in _MONTHS else (12 if is_end else 1)
    return year * 12 + month - 1


def estimate_years(text: str) -> float:
    spans, explicit = [], 0.0
    for line in text.splitlines():
        if re.search(r"experience|\bexp\b", line, re.I):
            for m in _EXPLICIT.finditer(line):
                explicit = max(explicit, min(float(m.group(1)), 45))
        if _EDU_LINE.search(line):  # education date ranges are not work experience
            continue
        for m in _RANGE.finditer(line):
            try:
                a, b = _month_index(m.group(1), False), _month_index(m.group(2), True)
            except (AttributeError, ValueError):
                continue
            if b >= a and (b - a) < 45 * 12:
                spans.append((a, b + 1))
    merged: list[list[int]] = []
    for a, b in sorted(spans):  # merge overlaps so parallel roles aren't double counted
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    computed = sum(b - a for a, b in merged) / 12
    return round(max(computed, explicit), 1)


# ---------- education ----------
_LEVELS = [
    ("PhD", 3, re.compile(r"\b(?:ph\.?d|doctorate)\b", re.I)),
    ("Master's", 2, re.compile(r"\b(?:m\.?tech|m\.?sc|mba|master(?:'?s)?)\b", re.I)),
    ("Bachelor's", 1, re.compile(r"\b(?:b\.?tech|b\.?sc|bachelor(?:'?s)?)\b|\bb\.e\.", re.I)),
]


def find_education(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        for label, rank, rx in _LEVELS:
            if rx.search(line):
                out.append({"level": label, "rank": rank, "detail": line.strip()[:120]})
                break
    return out


# ---------- profile ----------
_METRIC = re.compile(r"\d+\s?%|[$₹€]\s?\d|\b\d+(?:\.\d+)?\s?(?:k|m|x|ms|rps)\b|\b\d{2,}\b\s+(?:users|requests|customers)", re.I)


def _guess_name(text: str) -> str:
    for line in text.splitlines()[:5]:
        line = line.strip()
        if 1 < len(line.split()) <= 4 and re.fullmatch(r"[A-Za-z.\-' ]+", line):
            return line
    return ""


def extract_profile(text: str, extra_skills: list[str] | None = None) -> dict:
    edu = find_education(text)
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    return {
        "name": _guess_name(text),
        "email": email.group() if email else "",
        "skills": find_skills(text, extra_skills),
        "years_experience": estimate_years(text),
        "education": [{"level": e["level"], "detail": e["detail"]} for e in edu],
        "highest_education": max(edu, key=lambda e: e["rank"])["level"] if edu else None,
        "word_count": len(text.split()),
        "signals": {
            "has_summary": bool(re.search(r"^\s*(summary|profile|objective|about)\b", text, re.I | re.M)),
            "has_projects": bool(re.search(r"^\s*(projects?|portfolio)\b", text, re.I | re.M)),
            "metric_count": len(_METRIC.findall(text)),
        },
    }
