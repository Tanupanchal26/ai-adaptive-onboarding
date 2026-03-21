import json
from pathlib import Path

STANDARD_SKILLS = {
    "Python", "SQL", "Leadership", "Communication", "Java",
    "Excel", "Project Management", "Machine Learning", "Data Analysis",
    "JavaScript", "React", "AWS", "Docker", "Git", "Agile",
    "Tableau", "Power BI", "Marketing", "Sales", "Public Speaking"
}

CATALOG_PATH = Path(__file__).parent / "course_catalog.json"


def load_catalog() -> list:
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


def get_courses_for_gaps(gap_skills: set) -> list:
    """Return courses that cover the missing skills."""
    catalog = load_catalog()
    gap_lower = {s.lower() for s in gap_skills}
    matched = []
    for course in catalog:
        course_skills = {s.lower() for s in course.get("skills", [])}
        if course_skills & gap_lower:
            matched.append(course)
    return matched


def normalize_skills(skills: list) -> set:
    """Normalize skill list to lowercase set, filtered by standard skills."""
    incoming = {s.lower() for s in skills}
    standard_lower = {s.lower(): s for s in STANDARD_SKILLS}
    return {standard_lower[s] for s in incoming if s in standard_lower}
