# 🎯 SkillBridge — Adaptive Onboarding Engine v2.0

> **This system dynamically adapts onboarding pathways using semantic understanding and optimization algorithms to minimize learning time.**

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?logo=streamlit)](https://streamlit.io)
[![LLaMA](https://img.shields.io/badge/LLaMA-3.2-green?logo=meta)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🚀 One-Line Pitch

An enterprise-grade onboarding intelligence platform that performs **semantic skill-gap analysis** between any resume and job description, then generates a **prerequisite-aware, efficiency-ranked learning pathway** — reducing required onboarding time by **34–49% (mean: 41%)** relative to a 35-hour static baseline, across 8 evaluated role transitions.

---

## 💥 Impact Statement

> Traditional onboarding is static, generic, and wasteful — forcing every employee through the same 35-hour program regardless of what they already know.
>
> **SkillBridge eliminates that waste.** By semantically understanding a candidate's existing skills and the exact requirements of their target role, it generates the *minimum viable learning path* — personalized, ordered by prerequisites, and optimized for maximum efficiency per hour invested.
>
> Under the assumption of a 500-person organization with 20% annual turnover and a mean pathway reduction of 41% relative to a 35-hour static baseline, the estimated aggregate time saving is approximately **1,400–1,750 person-hours per year** (lower bound: mean reduction; upper bound: best-case). This is a modelled projection, not a measured outcome.

---

## ⚙️ Quick Start

```bash
git clone https://github.com/Tanupanchal26/ai-adaptive-onboarding.git
cd ai-adaptive-onboarding
pip install -r requirements.txt
streamlit run app.py
```

> **No uploads needed for demo** — click any persona button (Junior Dev, Sales Manager, etc.) to see the full engine in action instantly.
>
> **AI Prerequisite:** Install [Ollama](https://ollama.com) and run `ollama pull llama3.2` for local LLM-powered resume parsing.  
> **Optional:** Add `OPENAI_API_KEY` to `.streamlit/secrets.toml` to use GPT-4o-mini instead.

---

## 🧠 How the Engine Works

### System Architecture

```
Resume / JD
    │
    ▼
[LLM Parse]  ←  GPT-4o-mini / LLaMA 3.2 / phi4:mini (cascade fallback)
    │
    ▼
[Skills]  →  Normalized against 65-skill O*NET taxonomy via semantic similarity
    │
    ▼
[Embeddings]  →  all-MiniLM-L6-v2 · 384-dim · LRU-cached per session
    │
    ▼
[Gap Analysis]  →  Cosine similarity matrix (J×C) · threshold 0.65
    │              Adaptive confidence = 0.6×avg_sim + 0.4×coverage
    │              Gap prioritization: lowest cosine = highest urgency
    ▼
[Optimizer]  →  Greedy set-cover · efficiency = gaps_covered / duration_hrs
    │            Marginal re-scoring at each step · no redundant courses
    ▼
[Prerequisite DAG]  →  27 directed edges · topological sort
    │                   Python→ML, Docker→K8s, Communication→Leadership→Strategy
    ▼
[Pathway]  →  Minimum viable course set · prerequisite-ordered · efficiency-ranked
    │
    ▼
[Feedback Loop]  →  Gap weights adapt per confidence signal
                     Critical gaps (top-3 by urgency) re-ranked dynamically
```

### Core Statement

> Uses **semantic similarity** (cosine via sentence-transformers) + **greedy set-cover optimization** + **adaptive confidence scoring** (similarity quality × coverage breadth) to generate the minimum viable, prerequisite-aware learning path for any role transition.

### Measured Performance

> Full methodology and failure analysis: [`eval/credible_claims.md`](eval/credible_claims.md)

| Metric | Value | Context |
|---|---|---|
| Pathway time reduction | **34–49%, mean 41% (σ ≈ 4.5pp)** | 8 role transitions vs 35h static baseline |
| Semantic gap detection F1 | **0.984** (precision 0.989, recall 0.986) | n=60 pairs, 6 domains, threshold=0.65 |
| Keyword baseline F1 | **0.993** | Same dataset — semantic advantage is synonym handling, not raw F1 |
| Weakest domain (semantic) | **Data Science F1 = 0.927** | ML/Deep Learning cosine overlap at threshold 0.65 |
| Prerequisite relationships modeled | **27 directed edges** | Manually defined DAG |
| Courses in catalog | **65 (beginner → advanced)** | Fixed catalog |

---
### 1 · Intelligent Document Parsing
Resume and job description files (PDF or TXT) are extracted via **PyMuPDF**. The raw text is sent to **LLaMA 3.2** (or GPT-4o-mini) with a strict JSON-schema prompt that returns structured skill lists, years of experience, current role, education level, and certifications — with zero hallucination tolerance enforced by `response_format: json_schema`.

### 2 · Semantic Skill Matching (`semantic_engine.py`)

Raw skills are first normalized against a **65-skill taxonomy** (O\*NET 30.2 derived, covering both technical and non-technical domains). Matching then uses **cosine similarity** via `all-MiniLM-L6-v2` (sentence-transformers):

```
sim[jd_skill, candidate_skill] = (E_jd · E_cand) / (‖E_jd‖ · ‖E_cand‖)
```

Any JD skill with `max(sim) ≥ 0.65` across all candidate embeddings is marked **matched**. This correctly handles synonyms like `"ML" ↔ "Machine Learning"`, `"JS" ↔ "JavaScript"`, and `"People Management" ↔ "Leadership"` — which naive set-difference would miss entirely.

**Why this matters:** A keyword-matching system would mark a candidate with "scikit-learn" as missing "Machine Learning". SkillBridge's semantic encoder understands they are the same concept — eliminating false gaps and preventing unnecessary course assignments.

### 3 · Greedy Set-Cover Optimization (`semantic_engine.optimize_courses`)

Every course in the 65-course catalog is scored by:

```
efficiency_score = gaps_covered / duration_hours
```

The optimizer runs a **greedy set-cover** algorithm:
1. Score every course against the current open gap set
2. Select the course with the highest `gaps/hr` ratio
3. Remove covered gaps from the open set
4. Repeat until all gaps are closed

This produces a **near-optimal, non-redundant** course selection — no two selected courses cover the same gap twice. The result is the shortest possible path to role readiness.

### 4 · Prerequisite-Aware Pathway Assembly (`path_generator.py`)

A **directed acyclic graph** (NetworkX `DiGraph`) encodes 27 prerequisite relationships across both technical and non-technical domains:

- Technical: `Python → Machine Learning`, `Docker → Kubernetes`, `HTML → JavaScript → React`
- Non-technical: `Communication → Leadership → Strategy`, `Sales → Negotiation → CRM`, `Marketing → SEO → Brand Management`

Gaps are topologically sorted through this graph so foundational skills are always learned before advanced ones. The final pathway is deduplicated by course ID and capped to the minimum set that closes all gaps.

### 5 · AI Intelligence Report

After pathway generation, an LLM (GPT-4o-mini or LLaMA 3.2) produces a human-readable **3-part intelligence report**:
- **Strengths** — what the candidate already does well
- **Areas to Develop** — the most critical gaps to address first
- **Path Rationale** — why this specific learning sequence is optimal

---

## 🏆 Key Features

| Feature | Description |
|---|---|
| 📋 **Executive Summary** | Role readiness %, gap count, optimized time, and savings — at a glance |
| 🤖 **AI Intelligence Report** | LLM-generated strengths, weaknesses, and path rationale |
| 🧠 **Semantic Matching** | Cosine similarity via `all-MiniLM-L6-v2` — handles synonyms, abbreviations, paraphrases |
| 🔍 **Gap Analysis** | Visual coverage bars, skill pills, and a NetworkX skill graph |
| 🗺️ **Smart Pathway** | Prerequisite DAG + greedy set-cover → shortest path to role readiness |
| 📊 **Impact Metrics** | Hours saved vs 35h static baseline, role readiness score, skill coverage % |
| 🔮 **What-If Simulation** | Select any course and instantly see how gap count and coverage change |
| 📅 **Timeline View** | Gantt chart of your learning schedule with start/end dates |
| 🤖 **AI Chat Agent** | Floating assistant answers questions about your roadmap |
| 📤 **Export** | Download roadmap as PDF, CSV timeline, or plain-text HR summary |
| 🔎 **Reasoning Trace** | 4-step transparent breakdown of every AI decision made |
| ⚡ **Instant Demo** | 8 built-in personas (tech + non-tech) — no upload needed |

---

## 📊 Measured Impact

> All figures are reproducible from `eval/benchmark_results.json`. Methodology and limitations: [`eval/credible_claims.md`](eval/credible_claims.md).

| Metric | Value | Caveat |
|---|---|---|
| Pathway time reduction | **34–49%, mean 41%** | Relative to 35h static baseline; catalog durations, not real learner time |
| Semantic gap detection F1 | **0.984** | n=60, synthetic ground truth, normalized skill labels |
| Keyword baseline F1 | **0.993** | Semantic advantage is synonym resolution, not F1 gain on clean labels |
| Worst-case domain F1 | **0.927 (Data Science)** | ML↔Deep Learning overlap at cosine threshold 0.65 |
| Roles covered | **6 domains, 8 demo transitions** | Validated on built-in personas only |
| Prerequisite relationships | **27 directed edges** | Manually curated, not learned |

---

## 🌐 Role Coverage

The engine is domain-agnostic and validated across both role families:

| Domain | Example Transition | Key Skills Handled |
|---|---|---|
| 💻 Technical | Junior Dev → Software Engineer | Python, SQL, JavaScript, Agile, Docker |
| 🔬 Senior Tech | Engineer → Senior Engineer | React, AWS, Machine Learning, System Design |
| 💼 Sales | Sales Manager → Sales Lead | CRM, Negotiation, Leadership, Marketing |
| 📣 Marketing | Marketing Executive → Marketing Manager | SEO, Tableau, Content Marketing, Strategy |
| 👥 HR | HR Executive → HR Manager | Recruitment, Training, Coaching, Strategy |
| 🏭 Warehouse | Warehouse Associate → Supervisor | Safety Compliance, Leadership, Training |
| 🔧 Field Ops | Field Technician → Senior Tech | Documentation, Time Management, Quality Control |
| 🔀 Cross-Domain | Sales Rep → Marketing Manager | Tableau, Data Analysis, Brand Management |

---

## 🛡️ Grounding and Reliability

### Zero-hallucination enforcement
All LLM calls use `response_format: {"type": "json_schema"}` with a strict schema
that rejects any skill not present in the 65-skill O*NET taxonomy. If the LLM returns
an unrecognized skill, it is silently dropped and never reaches the pathway generator.
This eliminates hallucinated course recommendations by design.

---

## 🔬 Advanced Features

### Semantic Skill Normalization
The 65-skill taxonomy spans O\*NET technical categories and business/soft-skill domains. When a resume says `"scikit-learn"`, the semantic encoder maps it to `"Machine Learning"` in the taxonomy — ensuring the gap analysis is meaningful rather than literal. Embeddings are LRU-cached per session so the same skill string is never encoded twice.

### Dual LLM Backend with Graceful Fallback
The parser attempts **GPT-4o-mini** first (if `OPENAI_API_KEY` is set) using structured JSON output mode for maximum accuracy. It falls back to **LLaMA 3.2** via Ollama for fully local, offline operation. A second fallback to `phi4:mini` handles cases where LLaMA returns malformed JSON. The AI Insight section follows the same cascade — the UI never breaks regardless of LLM availability.

### Greedy Set-Cover Optimization
The course optimizer is a greedy set-cover approximation with marginal re-scoring: at each step it re-evaluates every remaining course against only the *still-open* gaps, ensuring the selected course always has the highest marginal efficiency. This prevents selecting courses that cover already-closed gaps — a subtle but critical correctness property.

### Prerequisite DAG with Topological Sort
27 directed edges model real-world learning dependencies. The topological sort ensures a candidate who needs both `Python` and `Machine Learning` always learns Python first — even if the ML course has a higher efficiency score. The DAG covers both technical and non-technical skill chains.

### Executive Summary + AI Intelligence Report
Every analysis begins with a single-glance **Executive Summary** (readiness %, gaps, optimized hours, savings %) and ends with an **AI Intelligence Report** — three human-readable sentences explaining strengths, critical gaps, and why the specific path was chosen. Both are generated fresh for every candidate.

---

## 🔍 AI Reasoning Trace (Sample — Junior Dev)

```
STEP 1 · EXTRACT SKILLS
  Resume  → 3 raw skills → normalized: Communication, Git, Python
  JD      → 5 raw skills → normalized: Agile, Git, JavaScript, Python, SQL

STEP 2 · SEMANTIC MATCHING  (threshold: cosine ≥ 0.65)
  Matched → Git, Python
  Method  → all-MiniLM-L6-v2 cosine similarity

STEP 3 · GAP IDENTIFICATION
  Gaps    → Agile, JavaScript, SQL  (JD − matched)

STEP 4 · OPTIMIZE COURSES
  SQL for Beginners         score 0.20 gaps/hr  covers: SQL
  Agile & Scrum Masterclass score 0.20 gaps/hr  covers: Agile
  JavaScript & React        score 0.25 gaps/hr  covers: JavaScript
  Pathway: JavaScript & React → SQL for Beginners → Agile & Scrum
  Total: 18h · Baseline: 35h · Saved: 17h (49%)
```

---

## 🖥️ Demo Personas

Eight built-in personas let evaluators test the engine **instantly without uploading any files**:

| Button | From → To | Gaps Demonstrated | Time Saved |
|---|---|---|---|
| 🧑💻 Junior Dev | Junior Developer → Software Engineer | SQL, JavaScript, Agile | ~49% |
| 👨💼 Senior Engineer | Senior Engineer → Senior Engineer+ | React, System Design | ~35% |
| 💼 Sales Role | Sales Manager → Sales Lead | CRM, Leadership, Marketing | ~40% |
| 📣 Marketing Role | Marketing Executive → Marketing Manager | Tableau, Content Marketing, Strategy | ~42% |
| 👥 HR Role | HR Executive → HR Manager | Training, Coaching, Strategy | ~38% |
| 🏭 Warehouse | Warehouse Associate → Supervisor | Safety Compliance, Leadership, Training | ~41% |
| 🔧 Field Tech | Field Technician → Senior Field Tech | Documentation, Time Management, Quality Control | ~38% |
| 🔀 Cross-Domain | Sales Rep → Marketing Manager | Tableau, Data Analysis, Brand Management | ~45% |

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.35, Plotly, Matplotlib |
| AI / NLP | LLaMA 3.2 (Ollama), GPT-4o-mini (OpenAI), sentence-transformers |
| Graph Engine | NetworkX (skill graph + prerequisite DAG) |
| Document Parsing | PyMuPDF (fitz) |
| Export | ReportLab (PDF), Pandas (CSV) |
| Embedding Model | `all-MiniLM-L6-v2` (384-dim, 22M params) |

---

## 📊 Evaluation Results

Run `python eval/skill_gap_eval.py` to reproduce:

```
✅ PASS: Synonym detection: scikit-learn == Machine Learning
✅ PASS: Abbreviation: JS == JavaScript
✅ PASS: Paraphrase: People Management == Leadership

Accuracy: 3/3 = 100%
```

| Metric | Value | Note |
|---|---|---|
| Synonym detection accuracy | **3/3 test cases** | Illustrative only — sample too small for a percentage claim |
| Semantic vs keyword F1 delta | **−0.009** (0.984 vs 0.993) | Semantic advantage is synonym handling on raw text, not F1 on normalized labels |

---

## 📁 Project Structure

```
ai-adaptive-onboarding/
│
├── app.py                  # Streamlit UI — hero, upload, results, tabs, chat
├── parser.py               # Document parsing — PyMuPDF + LLaMA/GPT-4o-mini
├── gap_logic.py            # Skill taxonomy (65 skills) + normalize_skills + compute_gaps
├── semantic_engine.py      # Cosine similarity matching + greedy set-cover optimizer
├── path_generator.py       # Prerequisite DAG + pathway assembly + AI insight generator
├── catalog.py              # Catalog loader utilities
├── config.py               # LLM model names, Ollama URL, timeout config
│
├── eval/
│   └── skill_gap_eval.py   # Evaluation harness — O*NET ground-truth test cases
│
├── course_catalog.json     # 65-course dataset (beginner → intermediate → advanced)
│
├── samples/
│   └── sample_jd_software_engineer.txt   # Sample JD for testing
│
├── .streamlit/
│   └── secrets.toml        # OPENAI_API_KEY (optional, gitignored)
│
├── Dockerfile              # Docker deployment
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🐳 Docker

```bash
docker build -t skillbridge-v2 .
docker run -p 8501:8501 skillbridge-v2
```

Open → [http://localhost:8501](http://localhost:8501)

---

## 👩💻 Built By

**Tanya Panchal** · SkillBridge Hackathon 2025  
Powered by LLaMA 3.2 · GPT-4o-mini · Streamlit · sentence-transformers · NetworkX · PyMuPDF
