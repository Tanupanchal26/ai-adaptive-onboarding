from gap_logic import load_catalog


def build_learning_path(gaps: set) -> list:
    """
    For each gap skill, find matching courses from catalog.
    Deduplicate, sort beginner → intermediate → advanced.
    Returns ordered list with 'why' explanation per course.
    """
    if not gaps:
        return []

    df = load_catalog().sort_values("difficulty_rank")
    gap_lower = {s.lower(): s for s in gaps}
    seen_ids = set()
    pathway = []

    for _, course in df.iterrows():
        course_skills_lower = {s.lower() for s in course["skills"]}
        covering = [gap_lower[s] for s in course_skills_lower if s in gap_lower]

        if covering and course["id"] not in seen_ids:
            seen_ids.add(course["id"])
            pathway.append({
                "id":         course["id"],
                "title":      course["title"],
                "duration":   course["duration"],
                "difficulty": course["difficulty"],
                "skills":     course["skills"],
                "why":        f"Covers your gap: {', '.join(covering)}"
            })

    return pathway


def estimate_time(pathway: list) -> dict:
    """Return total, static baseline, saved hours, and efficiency %."""
    total        = sum(c["duration"] for c in pathway)
    static       = round(total * 1.67)
    saved        = static - total
    efficiency   = round((saved / static) * 100) if static else 0
    return {"total": total, "static": static, "saved": saved, "efficiency": efficiency}
