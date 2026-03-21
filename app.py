import streamlit as st
from parser import parse_file

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

    # ── Error handling ────────────────────────────────────────────────────────
    if "error" in resume_data:
        st.error(f"Resume parsing failed: {resume_data['error']}")
        st.stop()
    if "error" in jd_data:
        st.error(f"JD parsing failed: {jd_data['error']}")
        st.stop()

    st.success("✅ Extraction complete!")
    st.divider()

    # ── Show extracted skills side by side ────────────────────────────────────
    r_col, j_col = st.columns(2)

    with r_col:
        st.markdown("### 🟢 Your Skills")
        st.markdown(f"**Role:** {resume_data.get('role', 'N/A')}")
        st.markdown(f"**Experience:** {resume_data.get('experience_years', 'N/A')} years")
        skills = resume_data.get("skills", [])
        if skills:
            for s in skills:
                st.markdown(f"- ✅ {s}")
        else:
            st.warning("No skills extracted.")

    with j_col:
        st.markdown("### 🔵 Role Requirements")
        st.markdown(f"**Target Role:** {jd_data.get('role', 'N/A')}")
        st.markdown(f"**Experience Required:** {jd_data.get('experience_years', 'N/A')} years")
        req_skills = jd_data.get("skills", [])
        if req_skills:
            for s in req_skills:
                st.markdown(f"- 📌 {s}")
        else:
            st.warning("No requirements extracted.")

    # ── Gap preview ───────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔍 Skill Gap Preview")
    candidate_set = {s.lower() for s in skills}
    required_set  = {s.lower() for s in req_skills}
    gaps = required_set - candidate_set
    matched = required_set & candidate_set

    g1, g2 = st.columns(2)
    with g1:
        st.success(f"✅ **{len(matched)} skills matched**")
        for s in sorted(matched):
            st.markdown(f"  - {s}")
    with g2:
        st.error(f"❌ **{len(gaps)} skills missing**")
        for s in sorted(gaps):
            st.markdown(f"  - {s}")

    st.info("🗺️ Full learning path generation coming in the next step!")
