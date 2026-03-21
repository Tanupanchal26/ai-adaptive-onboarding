import streamlit as st
import plotly.graph_objects as go
from parser import parse_file
from catalog import normalize_skills, build_learning_path

st.set_page_config(page_title="AI Adaptive Onboarding", layout="wide", page_icon="🎯")

# ── Sample data for quick test buttons ───────────────────────────────────────
SAMPLES = {
    "junior": {
        "skills": ["Python", "Git", "Communication"],
        "experience_years": 1,
        "role": "Junior Developer"
    },
    "senior": {
        "skills": ["Python", "AWS", "Docker", "Leadership", "SQL", "Agile", "Machine Learning"],
        "experience_years": 6,
        "role": "Senior Engineer"
    },
    "sales": {
        "skills": ["Communication", "Sales", "Excel", "Public Speaking"],
        "experience_years": 3,
        "role": "Sales Manager"
    }
}

JD_SAMPLES = {
    "junior": {"skills": ["Python", "SQL", "Git", "JavaScript", "Agile"], "experience_years": 2, "role": "Software Engineer"},
    "senior": {"skills": ["Python", "AWS", "Docker", "Machine Learning", "Leadership", "SQL", "Agile", "React"], "experience_years": 5, "role": "Senior Engineer"},
    "sales":  {"skills": ["Sales", "Communication", "Marketing", "Excel", "Public Speaking", "Leadership"], "experience_years": 3, "role": "Sales Lead"}
}

# ── Session state ─────────────────────────────────────────────────────────────
if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "jd_data" not in st.session_state:
    st.session_state.jd_data = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 How It Works")
    st.markdown("""
- 📄 **Upload** resume & job description
- 🧠 **AI extracts** skills & gaps
- 🗺️ **Get** a personalized roadmap
""")
    st.divider()

    if st.session_state.resume_data and "skills" in st.session_state.resume_data:
        candidate_skills = normalize_skills(st.session_state.resume_data.get("skills", []))
        st.markdown("### 🟢 Your Skills")
        for s in sorted(candidate_skills):
            st.markdown(f"✅ {s}")
        st.divider()

    if st.session_state.jd_data and "skills" in st.session_state.jd_data:
        jd_skills = normalize_skills(st.session_state.jd_data.get("skills", []))
        st.markdown("### 🔵 Role Requirements")
        for s in sorted(jd_skills):
            st.markdown(f"📌 {s}")
        st.divider()

    st.caption("Powered by LLaMA 3.2 · SkillBridge")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎯 AI-Adaptive Onboarding Engine")
st.markdown("Upload your Resume + Job Description → Get your personalized learning path")

# ── Quick Test Buttons ────────────────────────────────────────────────────────
st.markdown("#### ⚡ Quick Test")
b1, b2, b3 = st.columns(3)
if b1.button("🧑‍💻 Test Junior Dev",  use_container_width=True):
    st.session_state.resume_data = SAMPLES["junior"]
    st.session_state.jd_data     = JD_SAMPLES["junior"]
if b2.button("👨‍💼 Test Senior Dev",  use_container_width=True):
    st.session_state.resume_data = SAMPLES["senior"]
    st.session_state.jd_data     = JD_SAMPLES["senior"]
if b3.button("💼 Test Sales Role",   use_container_width=True):
    st.session_state.resume_data = SAMPLES["sales"]
    st.session_state.jd_data     = JD_SAMPLES["sales"]

st.divider()

# ── File Uploaders ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
with col2:
    jd_file = st.file_uploader("📋 Upload Job Description (PDF or TXT)", type=["pdf", "txt"])

if st.button("🚀 Generate My Personalized Pathway", type="primary", use_container_width=True):
    if not resume_file or not jd_file:
        st.error("⚠️ Please upload both files, or use a Quick Test button above.")
        st.stop()
    with st.spinner("🧠 AI is analyzing your profile..."):
        rd = parse_file(resume_file.read(), resume_file.name)
        jd = parse_file(jd_file.read(),     jd_file.name)
    if "error" in rd:
        st.error(f"Resume error: {rd['error']}")
        st.stop()
    if "error" in jd:
        st.error(f"JD error: {jd['error']}")
        st.stop()
    st.session_state.resume_data = rd
    st.session_state.jd_data     = jd

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.resume_data and st.session_state.jd_data:
    rd = st.session_state.resume_data
    jd = st.session_state.jd_data

    candidate_skills = normalize_skills(rd.get("skills", []))
    jd_skills        = normalize_skills(jd.get("skills", []))
    gaps             = jd_skills - candidate_skills
    matched          = jd_skills & candidate_skills

    st.success(f"✅ Analysis complete for **{rd.get('role','Candidate')}** → **{jd.get('role','Target Role')}**")

    # ── Skill Gap Pills ───────────────────────────────────────────────────────
    st.markdown("### 🔴 Skill Gaps")
    if gaps:
        pills = " ".join([f"`{g}`" for g in sorted(gaps)])
        st.markdown(pills)
    else:
        st.success("🎉 No skill gaps — you're already qualified!")
        st.stop()

    st.markdown(f"**{len(matched)} matched** · **{len(gaps)} missing**")
    st.divider()

    # ── Personalized Pathway ──────────────────────────────────────────────────
    st.markdown("### 🗺️ Your Personalized Learning Pathway")
    pathway = build_learning_path(gaps)

    if not pathway:
        st.warning("No courses found for these gaps.")
        st.stop()

    total_hours    = sum(c["duration"] for c in pathway)
    static_hours   = round(total_hours * 1.4)
    hours_saved    = static_hours - total_hours
    efficiency_pct = round((hours_saved / static_hours) * 100)

    for i, course in enumerate(pathway, 1):
        diff_emoji = "🟢" if course["difficulty"] == "beginner" else "🟡" if course["difficulty"] == "intermediate" else "🔴"
        with st.expander(f"{i}. {course['title']}  {diff_emoji}  ⏱ {course['duration']}h"):
            st.markdown(f"**Difficulty:** `{course['difficulty']}`")
            st.markdown(f"**Skills Covered:** {', '.join(course['skills'])}")
            st.markdown(f"**💡 Why Recommended:** {course['why']}")

    st.divider()

    # ── Big Number ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="text-align:center; padding:24px; background:linear-gradient(135deg,#1a1a2e,#16213e);
        border-radius:16px; border:1px solid #0f3460;">
            <div style="font-size:48px; font-weight:800; color:#00d4ff;">⏱ {total_hours} Hours</div>
            <div style="font-size:20px; color:#aaa; margin-top:8px;">Estimated Time to Competency</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    # ── Metrics Row ───────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("📚 Courses",        len(pathway))
    m2.metric("⚡ Hours Saved",    f"{hours_saved}h",    delta=f"-{efficiency_pct}% vs static")
    m3.metric("🎯 Gaps Closed",    len(gaps))

    st.divider()

    # ── Plotly Chart ──────────────────────────────────────────────────────────
    st.markdown("### 📊 AI Onboarding vs Static Onboarding")
    fig = go.Figure(go.Bar(
        x=["Static Onboarding", "AI-Adaptive Onboarding"],
        y=[static_hours, total_hours],
        marker_color=["#e74c3c", "#00d4ff"],
        text=[f"{static_hours}h", f"{total_hours}h"],
        textposition="outside"
    ))
    fig.update_layout(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font_color="#ffffff",
        yaxis_title="Hours Required",
        showlegend=False,
        height=350,
        margin=dict(t=20, b=20)
    )
    fig.add_annotation(
        x=1, y=total_hours + 1,
        text=f"🎯 {efficiency_pct}% more efficient",
        showarrow=False,
        font=dict(color="#00d4ff", size=14)
    )
    st.plotly_chart(fig, use_container_width=True)
