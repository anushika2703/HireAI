"""Rule-based profile feedback (always on) + optional LLM coach note."""
from collections import Counter

from . import llm


def build(profile: dict, matches: list[dict], use_llm: bool = True) -> dict:
    tips: list[dict] = []
    add = lambda p, t: tips.append({"priority": p, "tip": t})

    gaps = Counter(s for m in matches for s in m["missing_required"])
    for skill, n in gaps.most_common(3):
        add("high", f"{skill} is required by {n} of your top {len(matches)} matches but isn’t on your "
                    f"resume. If you’ve used it, name it in a bullet; if not, a small project would close the gap.")

    sig = profile["signals"]
    if sig["metric_count"] < 3:
        add("high", "Add numbers to your achievements (latency cut by 30%, 2M requests a day, team of 4). "
                    "Few measurable results were found.")
    if not sig["has_summary"]:
        add("medium", "Open with a 2–3 line summary that names your target role, years of experience and strongest stack.")
    if len(profile["skills"]) < 6:
        add("medium", "Few skills were detected. Add a Skills section that lists tools by their standard names.")
    if not profile["education"]:
        add("medium", "No degree or qualification was detected. Add an Education section, even if brief.")
    if profile["years_experience"] == 0:
        add("medium", "Experience dates weren’t recognised. Use a format like “Jan 2021 – Present” on each role.")
    if not sig["has_projects"] and profile["years_experience"] < 3:
        add("low", "With under three years of experience, a Projects section with links helps you stand out.")
    if profile["word_count"] < 200:
        add("low", "The resume looks thin. Add detail on what you built and the impact it had.")
    elif profile["word_count"] > 1000:
        add("low", "The resume is long. Trim older roles to one or two lines so recent work stands out.")

    note = None
    if use_llm and llm.available():
        note = llm.coach_note(profile, [t["tip"] for t in tips], dict(gaps))
    return {"tips": tips, "coach_note": note}
