import json
import pandas as pd
from pathlib import Path

STANDARD_SKILLS = {
    # ── Technical ──────────────────────────────────────────────────────────────
    "Python", "SQL", "Java", "JavaScript", "React", "TypeScript", "Next.js",
    "Node.js", "REST API", "Backend", "HTML", "CSS",
    "AWS", "Docker", "Kubernetes", "Cloud", "DevOps", "Git", "Agile",
    "Machine Learning", "Deep Learning", "Data Analysis", "Statistics",
    "Tableau", "Power BI", "Database", "MongoDB", "System Design", "Architecture",
    "Testing", "Jest", "Cypress", "DSA", "Problem Solving",
    "Linux", "Networking", "Security", "Cybersecurity",
    # ── Business / Non-technical ───────────────────────────────────────────────
    "Leadership", "Communication", "Public Speaking", "Project Management",
    "Excel", "Marketing", "Sales", "Negotiation",
    "CRM", "Salesforce", "SEO", "Content Marketing", "Social Media",
    "Brand Management", "Market Research", "Customer Success",
    "Financial Analysis", "Budgeting", "Business Development",
    "HR", "Recruitment", "Training", "Coaching",
    "Strategy", "Operations", "Supply Chain", "Logistics",
    "Product Management", "UX Design", "Figma",
}

CATALOG_PATH = Path(__file__).parent / "course_catalog.json"
DIFFICULTY_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}


def normalize_skills(skills: list) -> set:
    """
    Map raw skill list to standard taxonomy.
    Uses fuzzy cosine matching (sentence-transformers) if available,
    otherwise falls back to exact lowercase set match.
    """
    from parser import fuzzy_match_skills
    return fuzzy_match_skills(skills, STANDARD_SKILLS)


def compute_gaps(candidate_skills: set, jd_skills: set, threshold: float = 0.65) -> dict:
    """
    Semantic skill gap analysis — delegates to semantic_engine.semantic_skill_match.
    Falls back to set-difference if sentence-transformers unavailable.
    """
    from semantic_engine import semantic_skill_match
    matched_list, gaps_list = semantic_skill_match(
        list(candidate_skills), list(jd_skills), threshold=threshold
    )
    matched = set(matched_list)
    gaps    = set(gaps_list)
    return {
        "gaps":         gaps,
        "matched":      matched,
        "extra":        candidate_skills - jd_skills,
        "coverage_pct": round(len(matched) / max(len(jd_skills), 1) * 100)
    }


def load_catalog() -> pd.DataFrame:
    with open(CATALOG_PATH, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["difficulty_rank"] = df["difficulty"].map(DIFFICULTY_ORDER)
    # normalize field name — support both formats
    if "skills_covered" in df.columns and "skills" not in df.columns:
        df["skills"] = df["skills_covered"]
    if "duration_hrs" in df.columns and "duration" not in df.columns:
        df["duration"] = df["duration_hrs"]
    return df
