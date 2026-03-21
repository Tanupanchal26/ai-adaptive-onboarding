import json
import pandas as pd
from pathlib import Path

STANDARD_SKILLS = {
    "Python", "SQL", "Leadership", "Communication", "Java",
    "Excel", "Project Management", "Machine Learning", "Data Analysis",
    "JavaScript", "React", "AWS", "Docker", "Git", "Agile",
    "Tableau", "Power BI", "Marketing", "Sales", "Public Speaking",
    "TypeScript", "Next.js", "Testing", "Jest", "Cypress",
    "DSA", "Problem Solving", "Node.js", "REST API", "Backend",
    "MongoDB", "Database", "Kubernetes", "Cloud", "DevOps",
    "HTML", "CSS", "System Design", "Architecture", "Deep Learning"
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


def compute_gaps(candidate_skills: set, jd_skills: set, threshold: float = 0.70) -> dict:
    """
    Semantic skill gap analysis using cosine similarity.
    Falls back to set-difference if sentence-transformers unavailable.
    """
    from parser import FUZZY_AVAILABLE, _embedder
    if not FUZZY_AVAILABLE or not candidate_skills or not jd_skills:
        matched = jd_skills & candidate_skills
        gaps    = jd_skills - candidate_skills
    else:
        from sentence_transformers import util
        cand_list = list(candidate_skills)
        jd_list   = list(jd_skills)
        cand_emb  = _embedder.encode(cand_list, convert_to_tensor=True)
        jd_emb    = _embedder.encode(jd_list,   convert_to_tensor=True)
        matched, gaps = set(), set()
        for i, jd_skill in enumerate(jd_list):
            scores = util.cos_sim(jd_emb[i], cand_emb)[0]
            if float(scores.max()) >= threshold:
                matched.add(jd_skill)
            else:
                gaps.add(jd_skill)
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
