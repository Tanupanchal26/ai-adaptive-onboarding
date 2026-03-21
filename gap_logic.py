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
    Map raw skill list to standard taxonomy via semantic similarity.
    Single call into semantic_engine — no duplicate model instance.
    """
    from semantic_engine import normalize_to_taxonomy
    return normalize_to_taxonomy(list(skills), STANDARD_SKILLS)


def compute_gaps(candidate_skills: set, jd_skills: set, threshold: float = 0.65) -> dict:
    """
    Semantic skill gap analysis.
    Returns matched, gaps, scores, best_match, coverage_pct, and extra.
    """
    from semantic_engine import semantic_skill_match
    result = semantic_skill_match(
        list(candidate_skills), list(jd_skills), threshold=threshold
    )
    return {
        "gaps":         set(result.gaps),
        "matched":      set(result.matched),
        "scores":       result.scores,        # jd_skill → cosine score
        "best_match":   result.best_match,    # jd_skill → best candidate skill
        "extra":        candidate_skills - jd_skills,
        "coverage_pct": result.coverage_pct,
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
