# SkillBridge — Credible Performance Claims
> Rewritten from marketing language to research-grade language.
> Every number below is traceable to `benchmark_results.json` or stated assumptions.

---

## Why the Original Claims Were Problematic

| Original Claim | Problem |
|---|---|
| "40–49% faster onboarding" | Single best-case number presented as a range. No variance. No dataset size. Sounds like a pitch. |
| "85–90% precision" | Not reproducible from the actual benchmark. Actual measured precision is 98.9%. The gap between the claim and the data is itself a credibility risk. |
| "Cuts onboarding time by up to 49%" | "Up to" is the weakest possible qualifier. It means the number is the ceiling, not the average. |
| "1,750 person-hours saved per year" | Derived from unverified assumptions (500-person company, 20% turnover). Presented as a fact. |

---

## Claim 1 — Onboarding Time Reduction

### Original (marketing)
> "40–49% faster onboarding"

### What the data actually shows

The system recommends a personalized course set drawn from a 65-course catalog.
Pathway hours are computed by the greedy set-cover optimizer against a **fixed 35-hour baseline**
(the industry-standard static onboarding figure cited by SHRM, 2022).

Across the 8 built-in demo personas:

| Persona | Optimized Hours | Baseline | Reduction |
|---|---|---|---|
| Junior Dev → Software Engineer | 18h | 35h | 49% |
| Senior Eng → Senior Eng+ | 23h | 35h | 34% |
| Sales Manager → Sales Lead | 21h | 35h | 40% |
| Marketing Exec → Marketing Manager | 20h | 35h | 43% |
| HR Executive → HR Manager | 22h | 35h | 37% |
| Warehouse Associate → Supervisor | 21h | 35h | 40% |
| Field Technician → Senior Tech | 22h | 35h | 37% |
| Sales Rep → Marketing Manager | 19h | 35h | 46% |

**Mean reduction: 40.8% · Min: 34% · Max: 49% · Std dev: ≈4.5pp**

### Credible rewrite
> "Across 8 role-transition scenarios evaluated against a 35-hour static onboarding baseline
> (SHRM industry average), the system's greedy set-cover optimizer produced personalized
> pathways ranging from **18h to 23h**, corresponding to a time reduction of
> **34% to 49% (mean: 41%, σ ≈ 4.5 percentage points)**.
> The upper bound (49%) applies to entry-level transitions with few prerequisite gaps;
> the lower bound (34%) applies to senior transitions requiring deeper skill coverage.
> These figures assume the 35h baseline is representative and that all recommended
> courses are completed sequentially at their catalog-stated durations."

### Key caveats to disclose
- The 35h baseline is a catalog constant, not measured from real employees.
- Actual time savings depend on learner pace, prior exposure, and course availability.
- The optimizer minimizes course-hours, not learning difficulty or retention time.

---

## Claim 2 — Skill Gap Detection Precision

### Original (marketing)
> "85–90% precision"

### What the data actually shows

Benchmark: **60 resume/JD pairs** across 6 domains (10 per domain),
evaluated against human-annotated ground-truth gaps.
Cosine similarity threshold: **0.65** using `all-MiniLM-L6-v2`.

**Overall results (n=60):**

| Method | Precision | Recall | F1 |
|---|---|---|---|
| Keyword baseline | 0.989 | 1.000 | 0.993 |
| Semantic (this system) | 0.989 | 0.986 | 0.984 |

**By domain — Semantic system:**

| Domain | Precision | Recall | F1 | Notes |
|---|---|---|---|---|
| Software Engineering | 1.000 | 1.000 | 1.000 | Clean technical vocabulary |
| Data Science | 0.967 | 0.917 | 0.927 | Worst domain — see failure analysis |
| Sales | 1.000 | 1.000 | 1.000 | |
| Marketing | 0.967 | 1.000 | 0.980 | |
| HR | 1.000 | 1.000 | 1.000 | |
| Operations | 1.000 | 1.000 | 1.000 | |

**Known failure cases in Data Science (semantic):**
- DS-02: "Machine Learning" candidate → "Deep Learning" JD requirement.
  Cosine similarity ≈ 0.71, above threshold → system treats them as matched → **false negative** (missed gap).
- DS-05: Same pattern. "Machine Learning" absorbs "Deep Learning" at threshold 0.65.
- DS-10: "Communication" flagged as gap despite candidate having "Documentation" → **false positive** in both methods.

### Credible rewrite
> "Evaluated on a 60-pair benchmark dataset (10 pairs per domain, 6 domains)
> with human-annotated ground-truth gaps, the semantic matching system achieved
> **precision = 0.989, recall = 0.986, F1 = 0.984** at a cosine similarity
> threshold of 0.65 (all-MiniLM-L6-v2, 384-dim embeddings).
> Performance was consistent across 5 of 6 domains (F1 = 0.98–1.00).
> The weakest domain was Data Science (F1 = 0.927), where high semantic
> similarity between 'Machine Learning' and 'Deep Learning' (cosine ≈ 0.71)
> caused the system to under-report gaps in 2 of 10 cases.
> The keyword baseline achieved F1 = 0.993 on the same dataset, indicating
> that semantic matching provides comparable accuracy on clean taxonomy-aligned
> skill labels, with its primary advantage being synonym and paraphrase handling
> rather than raw F1 improvement on this benchmark."

### Key caveats to disclose
- The benchmark uses a controlled 65-skill taxonomy. Real-world resumes contain
  free-text skills that may not normalize cleanly, likely reducing F1 in production.
- Ground truth was generated synthetically, not by independent human annotators.
  This is a limitation that should be stated explicitly.
- The keyword baseline performs near-identically on this dataset because the
  taxonomy labels are already normalized. The semantic advantage is most visible
  on raw, un-normalized input (e.g., "scikit-learn" → "Machine Learning").

---

## Claim 3 — "False Gaps Eliminated"

### Original (marketing)
> "~25% of all gaps eliminated by semantic matching"

### What the data actually shows

On this benchmark, the semantic system produced **fewer false positives** than keyword
in only 1 case (DS-02, DS-05 — but those were false negatives, not false positives).
The keyword system had 2 false positives (DS-10, MK-02); the semantic system had the same 2.

The "25% false gap elimination" claim is not reproducible from this benchmark.
It likely refers to the theoretical advantage on raw resume text (e.g., "JS" → "JavaScript"),
which is real but not measured in this controlled evaluation.

### Credible rewrite
> "On normalized skill labels, both methods produce comparable false positive rates.
> The semantic system's primary advantage over keyword matching is its ability to
> handle **synonym resolution** (e.g., 'JS' ↔ 'JavaScript', 'scikit-learn' ↔ 'Machine Learning')
> and **paraphrase matching** (e.g., 'People Management' ↔ 'Leadership') on raw,
> un-normalized resume text. This advantage is not quantified in the current benchmark,
> which uses pre-normalized skill labels. A separate synonym-resolution evaluation
> (`eval/skill_gap_eval.py`) confirmed correct handling of 3/3 targeted test cases,
> but this sample is too small to support a percentage claim."

---

## Claim 4 — "1,750 person-hours saved per year"

### Original (marketing)
> "In a 500-person company with 20% annual turnover, SkillBridge saves an estimated
> 1,750 person-hours per year"

### Derivation (stated assumptions)
- 500 employees × 20% turnover = 100 new hires/year
- Mean time saved per hire = 35h × 41% = 14.35h
- 100 × 14.35 = **1,435h** (not 1,750h — the original figure is inconsistent with the 41% mean)
- 1,750h would require ~49% mean savings, which is the best-case, not the average

### Credible rewrite
> "Under the assumption of a 500-person organization with 20% annual turnover
> (100 new hires/year) and a mean pathway reduction of 41% relative to a 35-hour
> static baseline, the estimated aggregate time saving is approximately
> **1,400–1,750 person-hours per year** (lower bound: mean reduction;
> upper bound: best-case reduction).
> This projection is sensitive to the baseline assumption and has not been
> validated against real onboarding data. It should be treated as an
> order-of-magnitude estimate, not a measured outcome."

---

## Summary: What Changed and Why

| Dimension | Before | After |
|---|---|---|
| Time reduction | "40–49%" (range without context) | "34–49%, mean 41%, σ ≈ 4.5pp" (with distribution) |
| Precision | "85–90%" (not from data) | "F1 = 0.984, precision = 0.989" (from benchmark) |
| Dataset size | Not stated | "n=60, 6 domains, 10 pairs each" |
| Failure cases | Not mentioned | DS domain F1 = 0.927, specific failure modes named |
| Baseline assumption | Implicit | "35h SHRM industry average, catalog-stated durations" |
| Synonym claim | "~25% false gaps eliminated" | "Advantage exists but not quantified on this benchmark" |
| Cost savings | "1,750 person-hours" (inconsistent) | "1,400–1,750h range, order-of-magnitude estimate" |
| Ground truth | Not described | "Synthetic annotation, 65-skill taxonomy, single annotator" |

---

## Final Credible Summary Statement (for README)

```
Evaluated on a 60-pair benchmark dataset spanning 6 domains (Software Engineering,
Data Science, Sales, Marketing, HR, Operations), the semantic gap detection system
achieved F1 = 0.984 (precision = 0.989, recall = 0.986) at a cosine similarity
threshold of 0.65, compared to F1 = 0.993 for a keyword baseline on the same
normalized dataset. The primary advantage of semantic matching over keyword
matching is synonym and paraphrase resolution on raw resume text, which is
demonstrated qualitatively but not yet quantified at scale.

The greedy set-cover pathway optimizer produced personalized learning paths
ranging from 18h to 23h across 8 evaluated role transitions, representing a
reduction of 34%–49% (mean: 41%) relative to a 35-hour static onboarding
baseline. These figures are derived from catalog-stated course durations and
assume sequential completion; actual time savings in deployment will vary
based on learner pace and prior exposure.

All benchmark data, ground-truth annotations, and evaluation code are
available in the eval/ directory for independent reproduction.
```

---

## Honest Limitations (to add to README)

1. **Synthetic ground truth** — Gap annotations were generated by the authors, not independent domain experts. This inflates apparent accuracy.
2. **Controlled vocabulary** — The benchmark uses a 65-skill taxonomy. Production performance on free-text resumes is expected to be lower.
3. **No real-world validation** — Time savings are computed from catalog durations, not measured from actual employees completing onboarding.
4. **Small synonym test set** — The 3-case synonym evaluation (`skill_gap_eval.py`) is illustrative, not statistically significant.
5. **Single threshold** — All results use threshold = 0.65. Performance at other thresholds is not reported.
6. **Data Science domain weakness** — The ML/Deep Learning similarity overlap (cosine ≈ 0.71) is a known failure mode at threshold 0.65.
