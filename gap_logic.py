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


def normalize_skills(skills: list) -> set:
    """Map raw skill list to standard taxonomy (case-insensitive)."""
    standard_lower = {s.lower(): s for s in STANDARD_SKILLS}
    return {standard_lower[s.lower()] for s in skills if s.lower() in standard_lower}


def compute_gaps(candidate_skills: set, jd_skills: set) -> dict:
    """Return gaps, matched, and coverage stats."""
    return {
        "gaps":    jd_skills - candidate_skills,
        "matched": jd_skills & candidate_skills,
        "extra":   candidate_skills - jd_skills,
        "coverage_pct": round(len(jd_skills & candidate_skills) / max(len(jd_skills), 1) * 100)
    }


def load_catalog() -> pd.DataFrame:
    with open(CATALOG_PATH, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["difficulty_rank"] = df["difficulty"].map(DIFFICULTY_ORDER)
    return df
