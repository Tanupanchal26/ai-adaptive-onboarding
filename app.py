import streamlit as st
from parser import parse_file
from catalog import normalize_skills, get_courses_for_gaps

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

    # ── Normalize skills ──────────────────────────────────────────────────────
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
            # Proficiency hint based on skill type
            level = "beginner"
            if s in {"Machine Learning", "AWS", "Docker", "Tableau"}:
                level = "intermediate"
            elif s in {"Leadership", "Project Management"}:
                level = "intermediate"
            st.markdown(f"- **{s}** *(start: {level})*")

    st.divider()

    # ── Recommended Courses ───────────────────────────────────────────────────
    if gaps:
        st.markdown("## 📚 Recommended Courses to Close Gaps")
        courses = get_courses_for_gaps(gaps)
        if courses:
            total_hours = sum(c["duration"] for c in courses)
            st.info(f"🕐 Total learning time: **{total_hours} hours** across {len(courses)} courses")
            for c in courses:
                badge = "🟢" if c["difficulty"] == "beginner" else "🟡"
                st.markdown(
                    f"{badge} **{c['title']}** — {c['duration']}h · "
                    f"`{c['difficulty']}` · Skills: {', '.join(c['skills'])}"
                )
        else:
            st.warning("No matching courses found in catalog for these gaps.")
    else:
        st.balloons()
        st.success("🎉 You already have all the required skills for this role!")
