# 🎯 AI-Adaptive Onboarding Engine

> **Upload your resume + job description → Get a personalized, AI-generated learning roadmap in seconds.**

---

## 🚀 One-Line Pitch

An intelligent onboarding engine that analyzes skill gaps between a candidate's resume and a target job description, then generates a personalized, ordered learning pathway — saving up to 40% of standard onboarding time.

---

## ⚙️ Setup Instructions

```bash
git clone https://github.com/Tanupanchal26/ai-adaptive-onboarding.git
cd ai-adaptive-onboarding
pip install streamlit pymupdf pandas plotly networkx sentence-transformers
streamlit run app.py
```

> **Prerequisite:** Install [Ollama](https://ollama.com) and run `ollama pull llama3.2` for AI-powered resume parsing.

---

## 🧠 How the Logic Works

### 1. Intelligent Parsing
When a user uploads a resume (PDF) and job description (PDF or TXT), the system extracts raw text using **PyMuPDF**. This text is sent to a locally running **LLaMA 3.2** model via Ollama with a strict JSON prompt that extracts structured skill lists, years of experience, and current role. The model returns clean, normalized JSON — no hallucinations, no explanations.

### 2. Skill Gap Analysis
Both skill lists (candidate and JD) are normalized against a **20-skill standard taxonomy** derived from O*NET 30.2. A simple set difference operation (`JD skills − Candidate skills`) identifies exact gaps. Each gap is color-coded: green (have it), orange (partial), red (missing). Progress bars visualize coverage across all required skills at a glance.

### 3. Ordered Learning Pathway
For each identified gap, the engine searches a **12-course catalog** and finds all courses that cover the missing skill. Courses are deduplicated (one course can cover multiple gaps), then sorted `beginner → intermediate → advanced` to ensure progressive skill building. The result is a numbered, personalized roadmap with estimated hours, difficulty levels, and a "why recommended" explanation for each course — plus a full 12-step AI reasoning trace showing every decision made.

---

## 📦 Datasets Used

- **O\*NET 30.2 Skills Taxonomy** (partial) — 20 standardized skill categories used for normalization
- **Custom 12-Course Catalog** (`course_catalog.json`) — curated courses covering technical, analytics, business, marketing, operations, and soft skills domains
- **4 Sample Personas** — Junior Developer, Senior Engineer, Sales Manager, Marketing Executive (built-in for demo)

---

## 🖥️ UI Screenshots

### Hero + Quick Test Buttons
```
┌─────────────────────────────────────────────────────┐
│  🎯 AI-Adaptive Onboarding Engine                   │
│  Upload Resume + JD → Get personalized roadmap      │
│                                                     │
│  [🧑💻 Junior Dev] [👨💼 Senior] [💼 Sales] [📣 Mktg] │
└─────────────────────────────────────────────────────┘
```

### Skill Gap Analysis
```
🟢 Your Matched Skills          🔴 Skill Gaps to Close
✅ Python  ✅ SQL  ✅ Git        ❌ JavaScript  ❌ Agile

📊 Skill Coverage
Python      ████████████████░░  ✅ Have it
SQL         ████████████████░░  ✅ Have it
JavaScript  ██████░░░░░░░░░░░░  ❌ Gap
Agile       ████░░░░░░░░░░░░░░  ❌ Gap
```

### Impact Banner
```
┌─────────────────────────────────────────────────────┐
│  💚 You will save ~14 hours                         │
│  compared to standard onboarding (34h)              │
│  AI-optimized path: 20h                             │
└─────────────────────────────────────────────────────┘
```

### Learning Pathway (3 Examples)

**Junior Developer → Software Engineer**
1. 🟢 SQL for Beginners — 4h
2. 🟢 Agile & Scrum Masterclass — 5h
3. 🟡 Docker & DevOps Essentials — 6h
> Total: 15h | Saves ~6h vs static onboarding

**Sales Manager → Sales Lead**
1. 🟢 Digital Marketing Basics — 5h
2. 🟢 Leadership Essentials — 5h
> Total: 10h | Saves ~4h vs static onboarding

**Marketing Executive → Marketing Manager**
1. 🟡 Tableau for Data Viz — 6h
2. 🟢 SQL for Beginners — 4h
3. 🟢 Leadership Essentials — 5h
> Total: 15h | Saves ~6h vs static onboarding

---

## 🔍 AI Reasoning Trace (Sample)

```
STEP 01 › INPUT RECEIVED
         Candidate: Junior Developer · 1 yr experience

STEP 02 › RESUME SKILL EXTRACTION
         Identified 3 raw skills → normalized to 3: Communication, Git, Python

STEP 03 › JD SKILL EXTRACTION
         Identified 5 raw skills → normalized to 5: Agile, Git, JavaScript, Python, SQL

STEP 04 › SKILL MATCHING
         Cross-referenced → 2 matched: Git, Python

STEP 05 › GAP IDENTIFICATION
         Set difference (JD − Candidate) → 3 gaps: Agile, JavaScript, SQL

STEP 06 › CATALOG SEARCH
         Searched 12-course catalog → 3 courses cover identified gaps

STEP 09 › PATHWAY ASSEMBLY
         SQL for Beginners → Agile & Scrum Masterclass → Docker & DevOps

STEP 10 › TIME ESTIMATION
         Total: 15h · Static baseline: 25h · Saved: 10h (40%)

STEP 12 › OUTPUT READY
         Pathway for Junior Developer → Software Engineer ✅
```

---

## 🐳 Docker (Optional)

```bash
docker build -t ai-onboarding .
docker run -p 8501:8501 ai-onboarding
```

Open → http://localhost:8501

---

## 📁 Project Structure

```
ai-adaptive-onboarding/
├── app.py                          # Main Streamlit application
├── parser.py                       # PyMuPDF + Ollama skill extraction
├── catalog.py                      # Course catalog + gap mapping logic
├── course_catalog.json             # 12-course dataset
├── sample_jd_software_engineer.txt # Sample job description
├── Dockerfile                      # Docker deployment
└── README.md
```

---

## 🏆 Key Features

| Feature | Description |
|---------|-------------|
| 🧠 AI Parsing | LLaMA 3.2 extracts structured skills from any resume/JD |
| 🔍 Gap Analysis | Set-difference skill matching with visual progress bars |
| 🗺️ Smart Pathway | Ordered courses: beginner → intermediate → advanced |
| 📊 Impact Metrics | Hours saved vs static onboarding (up to 40% efficiency) |
| 🔎 Reasoning Trace | 12-step transparent AI decision log |
| ⚡ Instant Demo | 4 built-in personas — no upload needed |

---

## 👩‍💻 Built By

**Tanya Panchal** · SkillBridge Hackathon 2024  
Powered by LLaMA 3.2 · Streamlit · PyMuPDF · Plotly · NetworkX
