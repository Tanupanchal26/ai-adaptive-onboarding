import streamlit as st
from parser import parse_file
from catalog import normalize_skills, build_learning_path

st.set_page_config(page_title="AI Adaptive Onboarding", layout="wide", page_icon="🎯")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 How It Works")
    st.markdown("""
- 📄 **Upload** your resume & job description
- 🧠 **AI extracts** your skills vs. role requirements
- 🗺️ **Get a personalized** learning roadmap instantly
""")
    st.divider()
    st.caption("Powered by LLaMA 3.2 · SkillBridge")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎯 AI-Adaptive Onboarding Engine")
st.markdown("Upload your Resume + Job Description → Get your personalized learning path")
st.divider()

# ── File Uploaders ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
with col2:
    jd_file = st.file_uploader("📋 Upload Job Description (PDF or TXT)", type=["pdf", "txt"])

st.markdown("")

# ── Main Action ───────────────────────────────────────────────────────────────
if st.button("🚀 Generate My Personalized Pathway", type="primary", use_container_width=True):
    if not resume_file or not jd_file:
        st.error("⚠️ Please upload both your resume and the job description.")
        st.stop()

    with st.spinner("🧠 AI is analyzing your profile..."):
        resume_data = parse_file(resume_file.read(), resume_file.name)
        jd_data     = parse_file(jd_file.read(),     jd_file.name)

    if "error" in resume_data:
        st.error(f"Resume parsing failed: {resume_data['error']}")
        st.stop()
    if "error" in jd_data:
        st.error(f"JD parsing failed: {jd_data['error']}")
        st.stop()

    st.success("✅ Extraction complete!")
    st.divider()

    # ── Normalize & compute gaps ──────────────────────────────────────────────
    candidate_skills = normalize_skills(resume_data.get("skills", []))
    jd_skills        = normalize_skills(jd_data.get("skills", []))
    gaps             = jd_skills - candidate_skills
    matched          = jd_skills & candidate_skills

    # ── Skills columns ────────────────────────────────────────────────────────
    r_col, j_col = st.columns(2)
    with r_col:
        st.markdown("### 🟢 Your Skills")
        st.markdown(f"**Role:** {resume_data.get('role', 'N/A')}")
        st.markdown(f"**Experience:** {resume_data.get('experience_years', 'N/A')} yrs")
        for s in sorted(candidate_skills):
            st.markdown(f"- ✅ {s}")

    with j_col:
        st.markdown("### 🔵 Role Requirements")
        st.markdown(f"**Target Role:** {jd_data.get('role', 'N/A')}")
        st.markdown(f"**Experience Required:** {jd_data.get('experience_years', 'N/A')} yrs")
        for s in sorted(jd_skills):
            st.markdown(f"- 📌 {s}")

    st.divider()

    # ── Skill Gap Analysis ────────────────────────────────────────────────────
    st.markdown("## 🔍 Skill Gap Analysis")
    m_col, g_col = st.columns(2)

    with m_col:
        st.success(f"✅ {len(matched)} Skills Matched")
        for s in sorted(matched):
            st.markdown(f"- {s}")

    with g_col:
        st.error(f"❌ {len(gaps)} Skills Missing")
        for s in sorted(gaps):
            level = "intermediate" if s in {"Machine Learning","AWS","Docker","Tableau","Leadership","Project Management"} else "beginner"
            st.markdown(f"- **{s}** *(start: {level})*")

    st.divider()

    # ── Personalized Learning Pathway ─────────────────────────────────────────
    st.markdown("## 🗺️ Your Personalized Learning Pathway")

    if not gaps:
        st.balloons()
        st.success("🎉 You already have all the required skills for this role!")
        st.stop()

    pathway = build_learning_path(gaps)

    if not pathway:
        st.warning("No matching courses found. Check back soon as we expand our catalog!")
        st.stop()

    total_hours = sum(c["duration"] for c in pathway)

    # Summary bar
    c1, c2, c3 = st.columns(3)
    c1.metric("📚 Courses", len(pathway))
    c2.metric("🕐 Total Hours", f"{total_hours}h")
    c3.metric("🎯 Gaps to Close", len(gaps))

    st.markdown("")

    # Numbered pathway list
    for i, course in enumerate(pathway, 1):
        diff_emoji = "🟢" if course["difficulty"] == "beginner" else "🟡" if course["difficulty"] == "intermediate" else "🔴"
        with st.container():
            st.markdown(
                f"**{i}. {course['title']}** {diff_emoji} `{course['difficulty']}`"
                f" &nbsp;|&nbsp; ⏱ {course['duration']} hours"
            )
            st.caption(f"💡 {course['why']}")
            st.markdown("---")

    st.info(f"✅ Complete all {len(pathway)} courses in ~{total_hours} hours to be fully job-ready!")
