# 🎯 SkillBridge — Stop Wasting People's Time on Day One

*What if your first week at a new job only taught you what you actually didn't know?*

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?logo=streamlit)](https://streamlit.io)
[![LLaMA](https://img.shields.io/badge/LLaMA-3.2-green?logo=meta)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📽️ See It in Action First

| | Link |
|---|---|
| 🚀 **Live App** | [https://ai-adaptive.streamlit.app/](https://ai-adaptive.streamlit.app/) — click any persona, no login needed |
| 🎬 **Demo Video** | [Watch Demo](https://drive.google.com/file/d/1s-PGnysEhXAVUj2eCx1PkN_iGX0gOkg0/view?usp=drivesdk) |
| 📊 **5-Slide Deck** | [View Deck](https://drive.google.com/file/d/1tAtDKwcUdOA6YQR_oqpUofOhV-g86rDT/view?usp=drivesdk) |

No API key. No file upload. Just click **Junior Dev** or **Warehouse** and watch the engine work.

---

## The Problem We're Solving

Picture your first week at a new company. You're a senior engineer with 6 years of Python experience — and you're sitting through a 3-hour "Introduction to Python" module because that's what everyone does.

That's not onboarding. That's just expensive waiting.

Most companies run the same 35-hour onboarding program for every new hire, regardless of what they already know. A warehouse worker joining as a supervisor gets the same curriculum as a fresh graduate. A sales rep moving into marketing gets courses she already mastered.

**SkillBridge fixes this.** It reads what you already know, reads what the role actually needs, figures out the gap — and builds the shortest possible path from where you are to where you need to be. No fluff. No repetition. Just the learning that actually matters.

In a 500-person company with typical annual turnover, this approach saves an estimated **1,400–1,750 person-hours every year.** That's a full-time employee's worth of time — given back.

*(Note: this is a modelled projection based on our measured 41% mean pathway reduction, not a surveyed outcome.)*

---

## How It Actually Works

The engine has five moving parts that connect into one clean pipeline:

```
Your Resume + Job Description
         │
         ▼
  [ LLM Parsing ]
  GPT-4o-mini (or LLaMA 3.2 locally)
  Extracts skills, experience level, role context
  Strict JSON schema → zero hallucination by design
         │
         ▼
  [ Semantic Matching ]
  all-MiniLM-L6-v2 embeddings (384-dim, LRU-cached)
  Cosine similarity matrix across all skill pairs
  "scikit-learn" matches "Machine Learning" ✓
  "JS" matches "JavaScript" ✓
  Threshold: cosine ≥ 0.65 → matched, below → gap
         │
         ▼
  [ Gap Prioritization ]
  Lowest cosine score = highest urgency
  Adaptive confidence = 0.6×similarity + 0.4×coverage
         │
         ▼
  [ Greedy Set-Cover Optimizer ]
  efficiency = gaps_covered / duration_hours
  Marginal re-scoring at every step
  No two courses ever cover the same gap twice
         │
         ▼
  [ Prerequisite DAG ]
  27 directed edges — Python before ML,
  Communication before Leadership before Strategy
  Topological sort ensures logical learning order
         │
         ▼
  Your personalized pathway — minimum time, maximum readiness
```

The key design choice we're proud of: **marginal re-scoring.** At each optimizer step, every remaining course is re-evaluated against only the *still-open* gaps. This stops the optimizer from picking a course that looks great on paper but covers something already learned. Most set-cover implementations skip this — ours doesn't.

The full algorithm name: **Marginal-gain greedy set-cover with topological prerequisite constraint.**

---

## What the Numbers Actually Say

We believe in honest benchmarks. Here's what we measured — and what we didn't:

> Full methodology and failure analysis: [`eval/credible_claims.md`](eval/credible_claims.md)
> Raw results: [`eval/benchmark_results.json`](eval/benchmark_results.json)

| What we measured | Result | The honest context |
|---|---|---|
| Pathway time reduction | **34–49%, mean 41%** (σ ≈ 4.5pp) | vs 35h baseline; catalog hours, not real learner time |
| Semantic matching F1 | **0.984** (precision 0.989, recall 0.986) | n=60 skill pairs, 6 domains, synthetic ground truth |
| Keyword baseline F1 | **0.993** | Keyword wins on clean labels — semantic wins on raw resume text |
| Weakest domain | **Data Science: F1 = 0.927** | "Machine Learning" and "Deep Learning" sit too close in cosine space |
| Prerequisite edges | **27 directed edges** | Manually curated — human judgement, not learned from data |

We're not hiding the keyword baseline result. On perfectly clean, normalized skill labels a simple string matcher does fine. Where semantic matching earns its keep is on *real* resume text — abbreviations, synonyms, paraphrases — which is exactly what we're solving.

---

## The Reasoning Trace

Every analysis produces a transparent 4-step log showing exactly how every decision was made:

```
STEP 1 · EXTRACT SKILLS
  Resume  → 3 raw skills → normalized: Communication, Git, Python
  JD      → 5 raw skills → normalized: Agile, Git, JavaScript, Python, SQL

STEP 2 · SEMANTIC MATCHING  (threshold: cosine ≥ 0.65)
  Matched → Git, Python
  Method  → all-MiniLM-L6-v2 cosine similarity

STEP 3 · GAP IDENTIFICATION
  Gaps    → Agile, JavaScript, SQL

STEP 4 · OPTIMIZE COURSES
  SQL for Beginners         efficiency 0.20 gaps/hr  →  covers: SQL
  Agile & Scrum Masterclass efficiency 0.20 gaps/hr  →  covers: Agile
  JavaScript & React        efficiency 0.25 gaps/hr  →  covers: JavaScript

  Final pathway: JavaScript & React → SQL for Beginners → Agile & Scrum
  Total: 18h  ·  Baseline: 35h  ·  Saved: 17h (49%)
```

You can reproduce this trace for any of the 8 built-in personas — or upload your own resume and JD.

---

## Who It Works For

We specifically built SkillBridge to handle *both* sides of the workforce — desk roles and operational roles:

| Role type | Transition | Skills handled |
|---|---|---|
| 💻 Technical | Junior Dev → Software Engineer | Python, SQL, JavaScript, Agile, Docker |
| 🔬 Senior Tech | Engineer → Senior Engineer | React, AWS, Machine Learning, System Design |
| 💼 Sales | Sales Manager → Sales Lead | CRM, Negotiation, Leadership, Marketing |
| 📣 Marketing | Marketing Executive → Marketing Manager | SEO, Tableau, Content Marketing, Strategy |
| 👥 HR | HR Executive → HR Manager | Recruitment, Training, Coaching, Strategy |
| 🏭 **Warehouse** *(Operational)* | Associate → Supervisor | Safety Compliance, Leadership, Training |
| 🔧 **Field Ops** *(Operational)* | Technician → Senior Tech | Documentation, Time Management, Quality Control |
| 🔀 Cross-Domain | Sales Rep → Marketing Manager | Tableau, Data Analysis, Brand Management |

A logistics company onboarding a warehouse supervisor gets the same quality of analysis as a tech company onboarding a senior engineer. The engine doesn't care what the role is — it only cares about the gap.

---

## Try It Yourself — 8 Instant Demos

Open [https://ai-adaptive.streamlit.app/](https://ai-adaptive.streamlit.app/) and click any button. No upload, no key, no waiting:

| Persona | What it demonstrates |
|---|---|
| 🧑💻 Junior Dev | Classic tech gap — SQL, JavaScript, Agile missing |
| 👨💼 Senior Engineer | Narrow gap — React and System Design only |
| 💼 Sales Role | Soft-skill gaps — Leadership, CRM, Marketing |
| 📣 Marketing Role | Cross-skill gaps — Tableau, Content Strategy |
| 👥 HR Role | People-skill gaps — Coaching, Training design |
| 🏭 Warehouse | Operational promotion — Safety + Leadership gap |
| 🔧 Field Tech | Field role — Documentation, QC, Time Management |
| 🔀 Cross-Domain | Career change — hardest case, most dramatic savings |

---

## Features

| | What it does |
|---|---|
| 📋 **Executive Summary** | Readiness %, gap count, hours saved — the one screen your manager needs |
| 🤖 **AI Intelligence Report** | Plain-English strengths, gaps, and "why this path" written by the LLM |
| 🧠 **Semantic Matching** | Handles synonyms, abbreviations, paraphrases — not just exact keywords |
| 🔮 **What-If Simulation** | Add or remove a course and watch the gap count update live |
| 📅 **Timeline View** | Gantt chart — your learning schedule with real start and end dates |
| 🤖 **AI Chat Agent** | Ask anything about your roadmap in plain English |
| 📤 **Export** | PDF for employees, CSV for HR systems, plain text for email |
| 🔎 **Reasoning Trace** | Full 4-step breakdown — every AI decision is explainable |

---

## Grounding and Reliability

All LLM calls enforce a strict JSON schema against the 65-skill O*NET taxonomy. If the model returns a skill not in the taxonomy, it is silently dropped before reaching the pathway generator. The engine cannot recommend a course for a hallucinated skill — not because we prompt it not to, but because the architecture makes it structurally impossible.

The LLM cascade: GPT-4o-mini → LLaMA 3.2 → phi4:mini. If the first model fails or returns malformed JSON, the next takes over automatically. The app has never shown an error screen in testing.

---

## Datasets & Models Used

| Source | What we used it for |
|---|---|
| [O*NET 30.2](https://www.onetcenter.org/db_releases.html) | The 65-skill taxonomy that anchors everything |
| [Resume Dataset — Kaggle](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset/data) | Validating persona skill extraction |
| [Jobs & JD Dataset — Kaggle](https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description) | JD parsing test cases |
| [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Embedding model (384-dim, 22M params, Apache 2.0) |
| [LLaMA 3.2](https://ollama.com) | Local LLM backend (Meta, open weights) |
| GPT-4o-mini | Primary LLM when OpenAI key is provided |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.35, Plotly, Matplotlib |
| AI / NLP | LLaMA 3.2, GPT-4o-mini, sentence-transformers |
| Graph Engine | NetworkX — skill graph + prerequisite DAG |
| Document Parsing | PyMuPDF (fitz) |
| Export | ReportLab (PDF), Pandas (CSV) |
| Embedding Model | all-MiniLM-L6-v2 (384-dim, 22M params) |

---

## Evaluation

Run the quick harness to verify the semantic engine works on your machine:

```bash
python eval/skill_gap_eval.py
```

```
✅ PASS: Synonym detection — scikit-learn == Machine Learning
✅ PASS: Abbreviation — JS == JavaScript
✅ PASS: Paraphrase — People Management == Leadership

Accuracy: 3/3
```

These 3 cases are illustrative. The full n=60 benchmark lives in `eval/benchmark_results.json`.

---

## Project Structure

```
ai-adaptive-onboarding/
│
├── app.py                       # Streamlit UI — all tabs, chat, export
├── parser.py                    # PyMuPDF + LLM parsing with cascade fallback
├── gap_logic.py                 # 65-skill taxonomy + normalization + gap compute
├── semantic_engine.py           # Cosine similarity + greedy set-cover optimizer
├── path_generator.py            # Prerequisite DAG + topological sort + AI report
├── catalog.py                   # Course catalog loader
├── config.py                    # Model names, Ollama URL, timeouts
│
├── eval/
│   ├── skill_gap_eval.py        # Quick 3-case harness (run this to verify)
│   ├── benchmark_results.json   # Full n=60 benchmark results
│   └── credible_claims.md       # Methodology, limitations, failure analysis
│
├── course_catalog.json          # 65 courses, beginner → advanced
├── samples/
│   └── sample_jd_software_engineer.txt
│
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
git clone https://github.com/Tanupanchal26/ai-adaptive-onboarding.git
cd ai-adaptive-onboarding
pip install -r requirements.txt
streamlit run app.py
```

For LLM-powered parsing → install [Ollama](https://ollama.com) and run `ollama pull llama3.2`
For GPT-4o-mini → add `OPENAI_API_KEY` to `.streamlit/secrets.toml`
For the demo personas → no key needed at all

---

* SkillBridge Hackathon 2026*
*Powered by LLaMA 3.2 · GPT-4o-mini · sentence-transformers · NetworkX · Streamlit · PyMuPDF*
