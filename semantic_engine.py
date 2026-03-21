"""
semantic_engine.py
──────────────────
Semantic skill matching using sentence-transformers (all-MiniLM-L6-v2).
Replaces naive set-difference with cosine similarity so synonyms like
"ML" ↔ "Machine Learning" are correctly matched.

Integration:
    from semantic_engine import semantic_skill_match
    matched, gaps = semantic_skill_match(candidate_skills, jd_skills)
"""
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    SEMANTIC_AVAILABLE = True
except ImportError:
    _model = None
    SEMANTIC_AVAILABLE = False


def _cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between every row of a and every row of b."""
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a_norm @ b_norm.T


def semantic_skill_match(
    candidate_skills: list,
    jd_skills: list,
    threshold: float = 0.65,
) -> tuple[list, list]:
    """
    Compare each JD skill against all candidate skills via cosine similarity.

    Parameters
    ----------
    candidate_skills : list of str  — skills from the resume
    jd_skills        : list of str  — skills required by the job description
    threshold        : float        — similarity cutoff (default 0.65)

    Returns
    -------
    matched : list  — JD skills the candidate already has
    gaps    : list  — JD skills the candidate is missing
    """
    if not SEMANTIC_AVAILABLE or not candidate_skills or not jd_skills:
        cand_lower = {s.lower() for s in candidate_skills}
        matched = [s for s in jd_skills if s.lower() in cand_lower]
        gaps    = [s for s in jd_skills if s.lower() not in cand_lower]
        return matched, gaps

    # Batch-encode both lists in two calls (fast)
    cand_emb = _model.encode(candidate_skills, convert_to_numpy=True)
    jd_emb   = _model.encode(jd_skills,        convert_to_numpy=True)

    # sim[i, j] = similarity between jd_skills[i] and candidate_skills[j]
    sim = _cosine_similarity_matrix(jd_emb, cand_emb)

    matched, gaps = [], []
    for i, jd_skill in enumerate(jd_skills):
        if sim[i].max() >= threshold:
            matched.append(jd_skill)
        else:
            gaps.append(jd_skill)

    return matched, gaps


def optimize_courses(course_catalog: list, gaps: list) -> list:
    """
    Score every course by: score = gaps_covered / duration
    Higher score = more efficient (covers more gaps per hour).

    Returns courses sorted by score DESC with 'covers' and 'score' fields.
    """
    gaps_lower = {g.lower() for g in gaps}
    scored = []

    for course in course_catalog:
        covered = [s for s in course.get("skills", []) if s.lower() in gaps_lower]
        if not covered:
            continue
        score = round(len(covered) / max(course.get("duration", 1), 1), 2)
        scored.append({
            "name":     course.get("title", course.get("name", "")),
            "skills":   course.get("skills", []),
            "duration": course.get("duration", 0),
            "score":    score,
            "covers":   covered,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
