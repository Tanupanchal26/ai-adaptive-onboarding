"""
semantic_engine.py — SkillBridge Adaptive Engine v2.0
──────────────────────────────────────────────────────
Single source of truth for all embedding and similarity operations.

Design principles
-----------------
- One SentenceTransformer instance shared across the entire pipeline.
- LRU-cached embeddings: the same string is never encoded twice per session.
- All matching is semantic (cosine similarity), never exact string comparison.
- Every public function is pure and stateless from the caller's perspective.

Public API
----------
    semantic_skill_match(candidate_skills, jd_skills, threshold) -> MatchResult
    normalize_to_taxonomy(raw_skills, taxonomy, threshold)        -> set[str]
    optimize_courses(course_catalog, gaps, threshold)             -> list[dict]
    SEMANTIC_AVAILABLE                                            -> bool
"""

from __future__ import annotations

import numpy as np
from functools import lru_cache
from dataclasses import dataclass, field

# ── Model bootstrap ───────────────────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    SEMANTIC_AVAILABLE = True
except ImportError:
    _MODEL = None
    SEMANTIC_AVAILABLE = False


# ── Embedding cache ───────────────────────────────────────────────────────────
@lru_cache(maxsize=2048)
def _embed(text: str) -> np.ndarray:
    """
    Encode a single string and cache the result.
    Using per-string caching (vs batch) keeps the cache hit rate high
    across calls with overlapping skill sets.
    """
    return _MODEL.encode(text, convert_to_numpy=True, normalize_embeddings=True)


def _embed_many(texts: list[str]) -> np.ndarray:
    """Return a (N, D) matrix — uses cache for each string individually."""
    return np.vstack([_embed(t) for t in texts])


# ── Core similarity ───────────────────────────────────────────────────────────
def _cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity matrix between rows of a and rows of b.
    Embeddings from _embed() are already L2-normalised, so this reduces
    to a plain dot product — O(N·M·D) with no extra norm passes.
    """
    return a @ b.T


# ── Result type ───────────────────────────────────────────────────────────────
@dataclass
class MatchResult:
    """
    Structured output of semantic_skill_match.

    Attributes
    ----------
    matched       : JD skills the candidate already satisfies
    gaps          : JD skills the candidate is missing
    scores        : similarity score for every JD skill (index-aligned with
                    matched + gaps combined in original jd_skills order)
    best_match    : for each JD skill, the candidate skill that scored highest
    coverage_pct  : int — percentage of JD skills matched
    """
    matched:      list[str]
    gaps:         list[str]
    scores:       dict[str, float]        # jd_skill → best cosine score
    best_match:   dict[str, str]          # jd_skill → best candidate skill
    coverage_pct: int


# ── Public: semantic skill matching ──────────────────────────────────────────
def semantic_skill_match(
    candidate_skills: list[str],
    jd_skills:        list[str],
    threshold:        float = 0.65,
) -> MatchResult:
    """
    Compare every JD skill against every candidate skill via cosine similarity.

    For each JD skill, the best-matching candidate skill is found.
    If that best score >= threshold, the JD skill is considered *matched*.
    Otherwise it is a *gap*.

    Falls back to exact lowercase matching when sentence-transformers is
    unavailable (e.g. minimal deployment without the package).

    Parameters
    ----------
    candidate_skills : skills extracted from the resume
    jd_skills        : skills required by the job description
    threshold        : cosine similarity cutoff (default 0.65)

    Returns
    -------
    MatchResult with matched, gaps, per-skill scores, best_match, coverage_pct
    """
    if not candidate_skills or not jd_skills:
        return MatchResult(
            matched=[], gaps=list(jd_skills),
            scores={s: 0.0 for s in jd_skills},
            best_match={s: "" for s in jd_skills},
            coverage_pct=0,
        )

    # ── Semantic path ─────────────────────────────────────────────────────────
    if SEMANTIC_AVAILABLE:
        cand_emb = _embed_many(candidate_skills)   # (C, D) — normalised
        jd_emb   = _embed_many(jd_skills)          # (J, D) — normalised

        # sim[j, c] = cosine similarity between jd_skills[j] and candidate_skills[c]
        sim = _cosine_matrix(jd_emb, cand_emb)     # (J, C)

        matched, gaps   = [], []
        scores, best_match = {}, {}

        for j, jd_skill in enumerate(jd_skills):
            best_c     = int(sim[j].argmax())
            best_score = float(sim[j, best_c])
            scores[jd_skill]     = round(best_score, 4)
            best_match[jd_skill] = candidate_skills[best_c]
            if best_score >= threshold:
                matched.append(jd_skill)
            else:
                gaps.append(jd_skill)

    # ── Exact fallback ────────────────────────────────────────────────────────
    else:
        cand_lower = {s.lower(): s for s in candidate_skills}
        matched, gaps   = [], []
        scores, best_match = {}, {}
        for jd_skill in jd_skills:
            hit = cand_lower.get(jd_skill.lower())
            if hit:
                matched.append(jd_skill)
                scores[jd_skill]     = 1.0
                best_match[jd_skill] = hit
            else:
                gaps.append(jd_skill)
                scores[jd_skill]     = 0.0
                best_match[jd_skill] = ""

    coverage_pct = round(len(matched) / max(len(jd_skills), 1) * 100)
    return MatchResult(
        matched=matched, gaps=gaps,
        scores=scores, best_match=best_match,
        coverage_pct=coverage_pct,
    )


# ── Public: taxonomy normalisation ───────────────────────────────────────────
def normalize_to_taxonomy(
    raw_skills: list[str],
    taxonomy:   set[str],
    threshold:  float = 0.65,
) -> set[str]:
    """
    Map a list of raw skill strings onto the standard taxonomy.

    Each raw skill is compared against every taxonomy entry; the best-matching
    taxonomy term is kept if its score >= threshold.  This handles:
      - abbreviations  : "ML"  → "Machine Learning"
      - synonyms       : "People Management" → "Leadership"
      - casing/spacing : "machine learning" → "Machine Learning"

    Falls back to exact lowercase lookup when sentence-transformers unavailable.
    """
    if not raw_skills:
        return set()

    taxonomy_list = list(taxonomy)

    if not SEMANTIC_AVAILABLE:
        std_lower = {s.lower(): s for s in taxonomy_list}
        return {std_lower[s.lower()] for s in raw_skills if s.lower() in std_lower}

    raw_emb  = _embed_many(raw_skills)       # (R, D)
    tax_emb  = _embed_many(taxonomy_list)    # (T, D)
    sim      = _cosine_matrix(raw_emb, tax_emb)  # (R, T)

    normalised = set()
    for r in range(len(raw_skills)):
        best_t     = int(sim[r].argmax())
        best_score = float(sim[r, best_t])
        if best_score >= threshold:
            normalised.add(taxonomy_list[best_t])
    return normalised


# ── Public: efficiency-ranked course optimisation ────────────────────────────
def optimize_courses(
    course_catalog: list[dict],
    gaps:           list[str],
    threshold:      float = 0.60,
) -> list[dict]:
    """
    Score every course by efficiency = semantically_covered_gaps / duration.

    Course skills are matched to gaps semantically (not by exact string),
    so a course covering "Machine Learning" will match a gap of "ML" or
    "Deep Learning Basics" if similarity >= threshold.

    Parameters
    ----------
    course_catalog : list of course dicts (must have 'skills' and 'duration')
    gaps           : list of gap skill strings
    threshold      : cosine similarity for course-skill → gap matching (0.60)

    Returns
    -------
    List of scored course dicts, sorted by score DESC.
    Each dict has: name, skills, duration, score, covers (semantically matched gaps).
    """
    if not gaps or not course_catalog:
        return []

    # Pre-encode gaps once
    if SEMANTIC_AVAILABLE:
        gap_emb = _embed_many(gaps)   # (G, D)

    scored = []
    for course in course_catalog:
        course_skills = course.get("skills", [])
        if not course_skills:
            continue

        if SEMANTIC_AVAILABLE:
            cs_emb  = _embed_many(course_skills)          # (S, D)
            sim     = _cosine_matrix(cs_emb, gap_emb)     # (S, G)
            # A gap is "covered" if any course skill scores >= threshold against it
            covered_gaps = [
                gaps[g]
                for g in range(len(gaps))
                if sim[:, g].max() >= threshold
            ]
        else:
            gaps_lower   = {g.lower() for g in gaps}
            covered_gaps = [
                s for s in course_skills if s.lower() in gaps_lower
            ]

        if not covered_gaps:
            continue

        duration = max(course.get("duration", 1), 1)
        score    = round(len(covered_gaps) / duration, 4)
        scored.append({
            "name":     course.get("title", course.get("name", "")),
            "skills":   course_skills,
            "duration": course.get("duration", 0),
            "score":    score,
            "covers":   covered_gaps,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
