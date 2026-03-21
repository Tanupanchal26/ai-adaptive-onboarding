import json
import pandas as pd
from pathlib import Path

STANDARD_SKILLS = {
    "Python", "SQL", "Leadership", "Communication", "Java",
    "Excel", "Project Management", "Machine Learning", "Data Analysis",
    "JavaScript", "React", "AWS", "Docker", "Git", "Agile",
    "Tableau", "Power BI", "Marketing", "Sales", "Public Speaking"
}

CATALOG_PATH = Path(__file__).parent / "course_catalog.json"
DIFFICULTY_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}


def load_catalog() -> pd.DataFrame:
    """Load course catalog JSON into a pandas DataFrame."""
    with open(CATALOG_PATH, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["difficulty_rank"] = df["difficulty"].map(DIFFICULTY_ORDER)
    return df


def normalize_skills(skills: list) -> set:
    """Normalize skill list against standard skills (case-insensitive)."""
    incoming = {s.lower() for s in skills}
    standard_lower = {s.lower(): s for s in STANDARD_SKILLS}
    return {standard_lower[s] for s in incoming if s in standard_lower}


def build_learning_path(gap_skills: set) -> list:
    """
    For every gap skill, find matching courses, deduplicate,
    sort beginner → intermediate → advanced.
    Returns ordered list of course dicts with 'why' explanation.
    """
    if not gap_skills:
        return []

    df = load_catalog()
    gap_lower = {s.lower(): s for s in gap_skills}

    matched_ids = set()
    results = []

    # Sort gaps so beginner courses come first
    df_sorted = df.sort_values("difficulty_rank")

    for _, course in df_sorted.iterrows():
        course_skills_lower = {s.lower() for s in course["skills"]}
        covering = [gap_lower[s] for s in course_skills_lower if s in gap_lower]

        if covering and course["id"] not in matched_ids:
            matched_ids.add(course["id"])
            results.append({
                "id":         course["id"],
                "title":      course["title"],
                "duration":   course["duration"],
                "difficulty": course["difficulty"],
                "skills":     course["skills"],
                "why":        f"Covers your gap: {', '.join(covering)}"
            })

    return results


def get_courses_for_gaps(gap_skills: set) -> list:
    """Alias kept for backward compatibility."""
    return build_learning_path(gap_skills)
