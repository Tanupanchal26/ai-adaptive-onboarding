import json
import logging
import pandas as pd
from pathlib import Path

# [Improvement] module-level model cache — loaded once, reused across all calls
_MODEL_CACHE: dict = {}   # key: model name → SentenceTransformer instance

log = logging.getLogger(__name__)


def _get_model(name: str = "all-MiniLM-L6-v2"):
    """Return a cached SentenceTransformer, loading it only on first call."""
    if name not in _MODEL_CACHE:
        from sentence_transformers import SentenceTransformer
        _MODEL_CACHE[name] = SentenceTransformer(name)
    return _MODEL_CACHE[name]

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


# [Improvement] extensible proficiency thresholds — change in one place
_PROFICIENCY_BANDS = [
    (0.92, "Expert"),
    (0.80, "Advanced"),
    (0.65, "Intermediate"),
    (0.0,  "Beginner"),
]


def _proficiency_level(score: float) -> str:
    """Map a cosine similarity score to a human-readable proficiency label."""
    for threshold, label in _PROFICIENCY_BANDS:
        if score >= threshold:
            return label
    return "Beginner"


def _build_proficiency(scores: dict) -> dict:
    """Build proficiency map for every scored skill."""
    return {s: {"level": _proficiency_level(v), "score": v} for s, v in scores.items()}


def _prioritize_gaps(gaps: list, scores: dict) -> list:
    # [Improvement] gap prioritization — lowest similarity = highest urgency
    return sorted(gaps, key=lambda s: scores.get(s, 0.0))


def _adaptive_confidence(matched: set, scores: dict, coverage_pct: int) -> float:
    # [Improvement] smarter confidence — blends similarity quality with coverage breadth
    if not matched:
        return 0.0
    avg_sim  = sum(scores[s] for s in matched) / len(matched)
    coverage = coverage_pct / 100
    # weighted blend: 60% similarity quality, 40% coverage breadth
    return round(0.6 * avg_sim + 0.4 * coverage, 4)


def _semantic_match(
    candidate_skills: set, jd_skills: set, threshold: float
) -> tuple:
    """Cosine similarity match — returns (matched, gaps, scores, best_match)."""
    import numpy as np
    model     = _get_model()
    cand_list = list(candidate_skills)
    jd_list   = list(jd_skills)
    cand_emb  = model.encode(cand_list, convert_to_numpy=True, normalize_embeddings=True)
    jd_emb    = model.encode(jd_list,   convert_to_numpy=True, normalize_embeddings=True)
    sim       = jd_emb @ cand_emb.T   # (J, C)
    matched, gaps, scores, best_match = [], [], {}, {}
    for j, skill in enumerate(jd_list):
        best_c     = int(sim[j].argmax()) if cand_list else 0
        best_score = float(sim[j, best_c]) if cand_list else 0.0
        scores[skill]     = round(best_score, 4)
        best_match[skill] = cand_list[best_c] if cand_list else ""
        (matched if best_score >= threshold else gaps).append(skill)
    return matched, gaps, scores, best_match


def _setdiff_match(candidate_skills: set, jd_skills: set) -> tuple:
    """Exact set-difference fallback — no external dependencies."""
    cand_lower = {s.lower(): s for s in candidate_skills}
    matched    = [s for s in jd_skills if s.lower() in cand_lower]
    gaps       = [s for s in jd_skills if s.lower() not in cand_lower]
    scores     = {s: (1.0 if s in matched else 0.0) for s in jd_skills}
    best_match = {s: cand_lower.get(s.lower(), "") for s in jd_skills}
    return matched, gaps, scores, best_match


def compute_gaps(candidate_skills: set, jd_skills: set, threshold: float = 0.65) -> dict:
    """
    Semantic skill-gap analysis.
    Returns matched, gaps, scores, best_match, coverage_pct, confidence,
    proficiency, prioritized_gaps, and critical_gaps.
    Falls back to exact set-difference if sentence-transformers is unavailable.
    Signature unchanged — fully backward compatible.
    """
    # [Improvement] safe type coercion — accept list/tuple/set from any caller
    candidate_skills = set(candidate_skills) if candidate_skills else set()
    jd_skills        = set(jd_skills)        if jd_skills        else set()

    if not jd_skills:
        return {
            "gaps": set(), "matched": candidate_skills, "scores": {}, "best_match": {},
            "extra": set(), "coverage_pct": 100, "confidence": 1.0,
            "proficiency": {}, "prioritized_gaps": [], "critical_gaps": [],
        }

    try:
        matched, gaps, scores, best_match = _semantic_match(
            candidate_skills, jd_skills, threshold
        )
    except Exception as exc:
        log.warning("semantic encoding failed (%s) — using set-difference fallback", exc)
        matched, gaps, scores, best_match = _setdiff_match(candidate_skills, jd_skills)

    matched_set  = set(matched)
    coverage_pct = round(len(matched_set) / max(len(jd_skills), 1) * 100)
    prioritized  = _prioritize_gaps(gaps, scores)

    return {
        "gaps":             set(gaps),
        "matched":          matched_set,
        "scores":           scores,
        "best_match":       best_match,
        "extra":            candidate_skills - jd_skills,
        "coverage_pct":     coverage_pct,
        "confidence":       _adaptive_confidence(matched_set, scores, coverage_pct),
        "proficiency":      _build_proficiency(scores),
        # [Improvement] new keys — additive only, no existing key removed
        "prioritized_gaps": prioritized,
        "critical_gaps":    prioritized[:3],
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
