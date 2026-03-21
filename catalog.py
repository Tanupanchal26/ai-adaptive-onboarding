import json
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "course_catalog.json"


def load_catalog() -> dict:
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


def get_courses_for_domain(domain: str, level: str = None) -> list:
    """Return courses filtered by domain and optional level."""
    catalog = load_catalog()
    courses = [c for c in catalog["courses"] if c["domain"] == domain]
    if level:
        courses = [c for c in courses if c["level"] == level]
    return courses


def get_role_requirements(role: str) -> dict:
    """Return required skill scores for a given target role."""
    catalog = load_catalog()
    return catalog["role_requirements"].get(role, {})


def get_all_roles() -> list:
    catalog = load_catalog()
    return list(catalog["role_requirements"].keys())


def recommend_courses(skill_gaps: list, max_per_domain: int = 2) -> list:
    """
    Given a list of skill gap dicts {skill, current, required},
    return recommended courses sorted by gap severity.
    """
    catalog = load_catalog()
    all_courses = catalog["courses"]
    recommended = []

    gaps_sorted = sorted(skill_gaps, key=lambda x: x["required"] - x["current"], reverse=True)

    domain_counts = {}
    for gap in gaps_sorted:
        domain = gap["skill"]
        if domain_counts.get(domain, 0) >= max_per_domain:
            continue
        gap_size = gap["required"] - gap["current"]
        if gap_size <= 0:
            continue
        level = "beginner" if gap["current"] < 40 else "intermediate" if gap["current"] < 70 else "advanced"
        matches = [c for c in all_courses if c["domain"] == domain and c["level"] == level]
        if not matches:
            matches = [c for c in all_courses if c["domain"] == domain]
        for course in matches[:max_per_domain]:
            if course not in recommended:
                recommended.append(course)
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

    return recommended
