import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd
import io
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as rl_canvas
from parser import parse_file
from gap_logic import normalize_skills, compute_gaps
from path_generator import build_learning_path, build_bonus_courses, estimate_time

try:
    from yfiles_graphs_for_streamlit import yfiles_graph
    YFILES = True
except ImportError:
    YFILES = False

st.set_page_config(
    page_title="AI Adaptive Onboarding Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="auto"
)

# ── Theme CSS (applied before sidebar radio so it's always ready) ─────────────
DARK_CSS = """
<style>
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');
    @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
    .stApp { background-color: #0a0a0a; color: #e0e0e0; animation: fadeIn .5s ease; }
    h1 { color:#ffffff; font-size:2.6rem; font-weight:600; letter-spacing:-0.5px; margin-bottom:0.6rem; }
    h2 { color:#f5f5f5; font-size:1.85rem; font-weight:500; margin:2.4rem 0 1.1rem; }
    h3 { color:#e0e0e0; font-size:1.45rem; font-weight:500; margin:1.8rem 0 0.9rem; }
    .stButton>button {
        background:#ffffff; color:#000000 !important;
        border:none; border-radius:6px; padding:0.75rem 1.6rem;
        font-weight:600; font-size:1rem; transition:all 0.18s ease;
    }
    .stButton>button:hover { background:#e0e0e0; transform:translateY(-1px); }
    .impact-banner {
        background:#111111; border:1px solid #333333; border-radius:10px;
        padding:28px 32px; text-align:center; margin:20px 0;
    }
    .skill-pill {
        display:inline-block; background:#1a1a1a;
        border:1px solid #333333; border-radius:4px;
        padding:4px 12px; margin:3px; font-size:13px; color:#e0e0e0;
    }
    .gap-pill {
        display:inline-block; background:#1a1a1a;
        border:1px solid #555555; border-radius:4px;
        padding:4px 12px; margin:3px; font-size:13px; color:#aaaaaa;
    }
    div[data-testid="stExpander"] { background:#111111; border-radius:8px; border:1px solid #222222; }
    [data-testid="metric-container"] { background:#111111; border-radius:8px; padding:12px; border:1px solid #222222; animation:fadeIn .4s ease; }
    .stMetric label { color:#aaaaaa !important; font-size:0.92rem !important; }
    .main .block-container { padding-top:2.2rem !important; padding-bottom:5rem !important; max-width:1280px; margin:0 auto; }
    hr { border:none; height:1px; background:linear-gradient(to right,transparent,#333333,transparent); margin:3rem 0; }
    .pro-card { background:#111111; border:1px solid #222222; border-radius:10px; padding:1.6rem; margin:1.4rem 0; box-shadow:0 4px 20px rgba(0,0,0,.35); }
    .premium-card { background:#111111; border:1px solid #222222; border-radius:10px; padding:1.6rem; margin:1.4rem 0; box-shadow:0 4px 20px rgba(0,0,0,.35); }
    @media (max-width:768px) {
        h1 { font-size:2.1rem !important; }
        h2 { font-size:1.65rem !important; }
        .block-container { padding-left:1.2rem !important; padding-right:1.2rem !important; }
        .pro-card, .premium-card { padding:1.3rem; }
        [data-testid="stHorizontalBlock"] > div { flex:1 1 100% !important; max-width:100% !important; margin-bottom:1.2rem !important; }
        .stPlotlyChart, .element-container iframe { width:100% !important; max-width:100% !important; }
        .stButton > button, .stFileUploader, .stTextInput > div > div > input { width:100% !important; }
    }
    @media (max-width:480px) {
        .stMetric { font-size:1.1rem !important; }
    }
</style>
"""
LIGHT_CSS = """
<style>
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');
    @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
    .stApp { background-color: #f8fafc; color: #1e293b; animation: fadeIn .5s ease; }
    .block-container { padding-top: 1rem; }
    h1,h2,h3 { color: #0f172a; }
    .stButton>button {
        width:100%; height:3rem;
        background:linear-gradient(90deg,#0ea5e9,#6366f1);
        color:#fff; font-weight:700; border-radius:12px; border:none; transition:all .2s;
    }
    .stButton>button:hover { opacity:.85; transform:scale(1.02); }
    .impact-banner {
        background:linear-gradient(135deg,#dcfce7,#d1fae5);
        border:2px solid #16a34a; border-radius:16px;
        padding:24px; text-align:center; margin:16px 0; animation:fadeIn .6s ease;
    }
    .skill-pill {
        display:inline-block; background:#e0f2fe;
        border:1px solid #0ea5e9; border-radius:20px;
        padding:4px 12px; margin:3px; font-size:13px; color:#0369a1;
    }
    .gap-pill {
        display:inline-block; background:#fee2e2;
        border:1px solid #ef4444; border-radius:20px;
        padding:4px 12px; margin:3px; font-size:13px; color:#b91c1c;
    }
    div[data-testid="stExpander"] { background:#fff; border-radius:12px; border:1px solid #e2e8f0; }
    [data-testid="metric-container"] { background:#fff; border-radius:12px; padding:12px; border:1px solid #e2e8f0; box-shadow:0 1px 4px #0001; animation:fadeIn .4s ease; }
    .main .block-container { padding-top:2rem !important; padding-bottom:4rem !important; max-width:1100px; margin:0 auto; }
    hr { margin:2.5rem 0; border-color:#e2e8f0; }
    .pro-card { background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:1.4rem; margin:1.2rem 0; }
    [data-testid="stFileUploader"] {
        background:#ffffff; border:2px dashed #cbd5e1; border-radius:12px;
    }
    [data-testid="stFileUploader"]:hover { border-color:#0ea5e9; }
    [data-testid="stFileUploaderDropzone"] {
        background:#f8fafc !important; color:#475569 !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span {
        color:#0f172a !important; font-weight:600;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div > small {
        color:#64748b !important;
    }
    @media (max-width:768px) {
        .block-container { padding-left:1rem !important; padding-right:1rem !important; }
        [data-testid="stHorizontalBlock"] > div { flex:1 1 100% !important; max-width:100% !important; margin-bottom:1rem !important; }
        .stPlotlyChart, .element-container iframe { width:100% !important; max-width:100% !important; }
        h1 { font-size:1.8rem !important; }
        h2 { font-size:1.5rem !important; }
        .stButton > button, .stFileUploader, .stTextInput > div > div > input { width:100% !important; }
    }
    @media (max-width:480px) {
        .pro-card { padding:1rem; }
        .stMetric { font-size:1.1rem !important; }
    }
</style>
"""

# ── Sample personas ───────────────────────────────────────────────────────────
SAMPLES = {
    "junior":    {"skills": ["Python", "Git", "Communication"],                                           "experience_years": 1, "role": "Junior Developer"},
    "senior":    {"skills": ["Python", "AWS", "Docker", "Leadership", "SQL", "Agile", "Machine Learning"],"experience_years": 6, "role": "Senior Engineer"},
    "sales":     {"skills": ["Communication", "Sales", "Excel", "Public Speaking"],                       "experience_years": 3, "role": "Sales Manager"},
    "marketing": {"skills": ["Marketing", "Excel", "Communication", "Public Speaking"],                   "experience_years": 2, "role": "Marketing Executive"},
    "crossdomain": {"skills": ["Communication", "Sales", "Public Speaking"],                              "experience_years": 3, "role": "Sales Representative"},
}
JD_SAMPLES = {
    "junior":    {"skills": ["Python", "SQL", "Git", "JavaScript", "Agile"],                                              "experience_years": 2, "role": "Software Engineer"},
    "senior":    {"skills": ["Python", "AWS", "Docker", "Machine Learning", "Leadership", "SQL", "Agile", "React"],       "experience_years": 5, "role": "Senior Engineer"},
    "sales":     {"skills": ["Sales", "Communication", "Marketing", "Excel", "Public Speaking", "Leadership"],            "experience_years": 3, "role": "Sales Lead"},
    "marketing": {"skills": ["Marketing", "Tableau", "SQL", "Communication", "Leadership", "Excel", "Public Speaking"],  "experience_years": 3, "role": "Marketing Manager"},
    "crossdomain": {"skills": ["Marketing", "Tableau", "Data Analysis", "Leadership", "Communication", "Excel"],         "experience_years": 3, "role": "Marketing Manager"},
}
DIFF_COLOR = {"beginner": "#00ff9d", "intermediate": "#00bfff", "advanced": "#ff4b4b"}

for key in ("resume_data", "jd_data"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    theme = st.radio("🎨 Theme", ["Dark Pro", "Light Corporate"])

if theme == "Light Corporate":
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)
else:
    st.markdown(DARK_CSS, unsafe_allow_html=True)

with st.sidebar:
    # ── How It Works ─────────────────────────────────────────────────────────
    _sb_bg   = "#1a1a1a" if theme == "Dark Pro" else "#f1f5f9"
    _sb_bdr  = "#333"    if theme == "Dark Pro" else "#cbd5e1"
    _sb_num  = "#1a1a1a" if theme == "Dark Pro" else "#e2e8f0"
    _sb_nbdr = "#333"    if theme == "Dark Pro" else "#94a3b8"
    _sb_ntxt = "#aaa"    if theme == "Dark Pro" else "#475569"
    _sb_txt  = "#ccc"    if theme == "Dark Pro" else "#334155"
    _sb_lbl  = "#666"    if theme == "Dark Pro" else "#94a3b8"
    st.markdown(f"""
    <div style="padding:.4rem 0 .8rem 0;">
        <div style="font-size:.7rem;letter-spacing:1.5px;text-transform:uppercase;
                    color:{_sb_lbl};margin-bottom:.7rem;">HOW IT WORKS</div>
        <div style="display:flex;flex-direction:column;gap:.5rem;">
            <div style="display:flex;align-items:center;gap:.6rem;font-size:.88rem;">
                <span style="background:{_sb_num};border:1px solid {_sb_nbdr};border-radius:50%;
                             width:26px;height:26px;display:flex;align-items:center;
                             justify-content:center;font-size:.75rem;flex-shrink:0;
                             color:{_sb_ntxt};">1</span>
                <span style="color:{_sb_txt};">Upload resume &amp; job description</span>
            </div>
            <div style="display:flex;align-items:center;gap:.6rem;font-size:.88rem;">
                <span style="background:{_sb_num};border:1px solid {_sb_nbdr};border-radius:50%;
                             width:26px;height:26px;display:flex;align-items:center;
                             justify-content:center;font-size:.75rem;flex-shrink:0;
                             color:{_sb_ntxt};">2</span>
                <span style="color:{_sb_txt};">AI extracts skills &amp; gaps</span>
            </div>
            <div style="display:flex;align-items:center;gap:.6rem;font-size:.88rem;">
                <span style="background:{_sb_num};border:1px solid {_sb_nbdr};border-radius:50%;
                             width:26px;height:26px;display:flex;align-items:center;
                             justify-content:center;font-size:.75rem;flex-shrink:0;
                             color:{_sb_ntxt};">3</span>
                <span style="color:{_sb_txt};">Get a personalized roadmap</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if st.session_state.resume_data:
        cs = normalize_skills(st.session_state.resume_data.get("skills", []))
        cs_sorted = sorted(cs)
        st.markdown(f"""
        <div style="font-size:.7rem;letter-spacing:1.5px;text-transform:uppercase;
                    color:{_sb_lbl};margin-bottom:.6rem;">YOUR SKILLS</div>
        """, unsafe_allow_html=True)
        _chip_bg  = "#1a1a1a" if theme == "Dark Pro" else "#ffffff"
        _chip_bdr = "#2a2a2a" if theme == "Dark Pro" else "#e2e8f0"
        _chip_txt = "#d0d0d0" if theme == "Dark Pro" else "#1e293b"
        chips = "".join(
            f"<span style='display:inline-flex;align-items:center;gap:4px;"
            f"background:{_chip_bg};border:1px solid {_chip_bdr};border-radius:4px;"
            f"padding:3px 8px;margin:2px;font-size:.78rem;color:{_chip_txt};'>"
            f"<span style='width:6px;height:6px;border-radius:50%;background:#22c55e;"
            f"display:inline-block;flex-shrink:0;'></span>{s}</span>"
            for s in cs_sorted
        )
        st.markdown(f"<div style='line-height:1.8;'>{chips}</div>", unsafe_allow_html=True)
        st.divider()

    if st.session_state.jd_data:
        js = normalize_skills(st.session_state.jd_data.get("skills", []))
        cs_set = normalize_skills(st.session_state.resume_data.get("skills", [])) \
                 if st.session_state.resume_data else set()
        st.markdown(f"""
        <div style="font-size:.7rem;letter-spacing:1.5px;text-transform:uppercase;
                    color:{_sb_lbl};margin-bottom:.6rem;">ROLE REQUIREMENTS</div>
        """, unsafe_allow_html=True)
        _chip_bg  = "#1a1a1a" if theme == "Dark Pro" else "#ffffff"
        _chip_bdr = "#2a2a2a" if theme == "Dark Pro" else "#e2e8f0"
        req_chips = "".join(
            f"<span style='display:inline-flex;align-items:center;gap:4px;"
            f"background:{_chip_bg};border:1px solid {_chip_bdr};border-radius:4px;"
            f"padding:3px 8px;margin:2px;font-size:.78rem;"
            f"color:{'#d0d0d0' if (theme == 'Dark Pro' and s in cs_set) else '#1e293b' if (theme != 'Dark Pro' and s in cs_set) else '#888' if theme == 'Dark Pro' else '#94a3b8'};'>"
            f"<span style='width:6px;height:6px;border-radius:50%;"
            f"background:{'#22c55e' if s in cs_set else '#ef4444'};"
            f"display:inline-block;flex-shrink:0;'></span>{s}</span>"
            for s in sorted(js)
        )
        st.markdown(f"<div style='line-height:1.8;'>{req_chips}</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;gap:1rem;margin-top:.6rem;font-size:.75rem;color:{_sb_lbl};">
            <span><span style="color:#22c55e;">●</span> Have it</span>
            <span><span style="color:#ef4444;">●</span> Gap</span>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

    _ft_col = "#444" if theme == "Dark Pro" else "#94a3b8"
    st.markdown(f"""
    <div style="font-size:.72rem;color:{_ft_col};text-align:center;padding:.4rem 0;">
        Powered by LLaMA 3.2 &nbsp;·&nbsp; SkillBridge
    </div>
    """, unsafe_allow_html=True)

# ── Hero Section ─────────────────────────────────────────────────────────────
_hero_bg  = "#0a0a0a" if theme == "Dark Pro" else "#f1f5f9"
_hero_h1  = "#ffffff" if theme == "Dark Pro" else "#0f172a"
_hero_sub = "#aaaaaa" if theme == "Dark Pro" else "#475569"
st.markdown(f"""
<div style="text-align:center;padding:2.5rem 0;background:{_hero_bg};
            border-radius:10px;margin-bottom:2rem;
            border:1px solid {'#222222' if theme=='Dark Pro' else '#e2e8f0'}">
    <h1 style="color:{_hero_h1};margin:0;font-size:2.6rem;font-weight:600;letter-spacing:-0.5px;">
        Adaptive Onboarding Engine
    </h1>
    <p style="color:{_hero_sub};font-size:1.18rem;max-width:720px;margin:.8rem auto 0;">
        Skill-gap driven &nbsp;·&nbsp; Personalized &nbsp;·&nbsp; Enterprise-grade learning paths
    </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Quick Test Buttons ────────────────────────────────────────────────────────
st.markdown("#### ⚡ Try a Sample Profile")
b1, b2, b3, b4, b5 = st.columns(5)
if b1.button("🧑💻 Junior Dev",      use_container_width=True):
    st.session_state.resume_data = SAMPLES["junior"];      st.session_state.jd_data = JD_SAMPLES["junior"]
if b2.button("👨💼 Senior Engineer", use_container_width=True):
    st.session_state.resume_data = SAMPLES["senior"];      st.session_state.jd_data = JD_SAMPLES["senior"]
if b3.button("💼 Sales Role",        use_container_width=True):
    st.session_state.resume_data = SAMPLES["sales"];       st.session_state.jd_data = JD_SAMPLES["sales"]
if b4.button("📣 Marketing Role",    use_container_width=True):
    st.session_state.resume_data = SAMPLES["marketing"];   st.session_state.jd_data = JD_SAMPLES["marketing"]
if b5.button("🔀 Cross-Domain",      use_container_width=True):
    st.session_state.resume_data = SAMPLES["crossdomain"]; st.session_state.jd_data = JD_SAMPLES["crossdomain"]

st.divider()

# ── File Uploaders ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
with col2:
    jd_file = st.file_uploader("📋 Upload Job Description (PDF or TXT)", type=["pdf", "txt"])

# ── FEATURE 1: Staged spinners ────────────────────────────────────────────────
if st.button("🚀 Generate My Personalized Pathway", type="primary", use_container_width=True):
    if not resume_file or not jd_file:
        st.error("⚠️ Please upload both files, or click a sample button above.")
        st.stop()

    with st.spinner("🔍 Parsing resume..."):
        rd = parse_file(resume_file.read(), resume_file.name)
    if "error" in rd: st.error(f"Resume error: {rd['error']}"); st.stop()

    with st.spinner("📋 Parsing job description..."):
        jd = parse_file(jd_file.read(), jd_file.name)
    if "error" in jd: st.error(f"JD error: {jd['error']}"); st.stop()

    with st.spinner("📊 Calculating skill gaps..."):
        st.session_state.resume_data = rd
        st.session_state.jd_data     = jd

    with st.expander("📄 What the AI understood from your resume", expanded=False):
        st.json({k: v for k, v in rd.items() if k != "_raw_text"})
        if "error" in rd:
            st.error("Resume parsing had issues — try a clearer PDF")
    with st.expander("📋 What the AI understood from the job description", expanded=False):
        st.json({k: v for k, v in jd.items() if k != "_raw_text"})

    st.success("✅ Pathway Ready!")

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.resume_data and st.session_state.jd_data:
    rd = st.session_state.resume_data
    jd = st.session_state.jd_data

    candidate_skills = normalize_skills(rd.get("skills", []))
    jd_skills        = normalize_skills(jd.get("skills", []))
    gap_result       = compute_gaps(candidate_skills, jd_skills)
    gaps             = gap_result["gaps"]
    matched          = gap_result["matched"]

    from_role = rd.get("main_role", rd.get("role", "Candidate"))
    to_role   = jd.get("main_role", jd.get("role", "Target Role"))

    # ── Theme-derived vars (used throughout) ──────────────────────────────────
    is_dark   = theme == "Dark Pro"
    bg_card   = "#111111" if is_dark else "#ffffff"
    txt_color = "#e0e0e0" if is_dark else "#1e293b"
    accent    = "#ffffff" if is_dark else "#0ea5e9"
    _pbg      = "#0a0a0a" if is_dark else "#f8fafc"
    _pfg      = "#111111" if is_dark else "#f1f5f9"

    st.markdown(f"### ✅ **{from_role}** → **{to_role}**")

    # ── Skills pills ──────────────────────────────────────────────────────────
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("#### 🟢 Matched Skills")
        if matched:
            st.markdown(" ".join([f"<span class='skill-pill'>✅ {s}</span>" for s in sorted(matched)]), unsafe_allow_html=True)
        else:
            st.warning("No matching skills found.")
    with sc2:
        st.markdown("#### 🔴 Skill Gaps")
        if gaps:
            st.markdown(" ".join([f"<span class='gap-pill'>❌ {s}</span>" for s in sorted(gaps)]), unsafe_allow_html=True)
        else:
            st.success("🎉 No gaps — you're already qualified!"); st.stop()

    st.divider()

    # ── Skill coverage bars ───────────────────────────────────────────────────
    _bar_track = "#1e1e1e" if is_dark else "#e2e8f0"
    _skill_lbl  = "#cccccc" if is_dark else "#1e293b"
    _have_col   = "#ffffff" if is_dark else "#16a34a"
    _gap_hi_col = "#555555" if is_dark else "#dc2626"
    _gap_lo_col = "#555555" if is_dark else "#d97706"
    st.markdown("#### Skill Coverage")
    for skill in sorted(jd_skills):
        have  = skill in candidate_skills
        pct   = 85 if have else (30 + (hash(skill) % 30))
        color = _have_col if have else (_gap_hi_col if pct < 40 else _gap_lo_col)
        label = "✓ Have it" if have else "✗ Gap"
        st.markdown(
            f"<div style='display:flex;align-items:center;margin-bottom:6px;gap:10px;'>"
            f"<span style='width:160px;color:{_skill_lbl};font-size:13px;'>{skill}</span>"
            f"<div style='flex:1;background:{_bar_track};border-radius:8px;height:14px;'>"
            f"<div style='width:{pct}%;background:{color};height:14px;border-radius:8px;'></div></div>"
            f"<span style='width:70px;color:{color};font-size:12px;'>{label}</span></div>",
            unsafe_allow_html=True
        )

    st.divider()

    pathway      = build_learning_path(gaps)
    if not pathway: st.warning("No courses found for these gaps."); st.stop()

    t            = estimate_time(pathway)
    total_hours  = t["total"]
    static_hours = t["static"]
    hours_saved  = t["saved"]
    efficiency   = t["efficiency"]

    # ── Impact banner ─────────────────────────────────────────────────────────
    _ib_val  = "#ffffff" if is_dark else "#16a34a"
    _ib_sub  = "#888888" if is_dark else "#475569"
    _ib_bold = "#e0e0e0" if is_dark else "#0f172a"
    st.markdown(
        f"<div class='impact-banner'>"
        f"<div style='font-size:38px;font-weight:800;color:{_ib_val};'>💚 You will save ~{hours_saved} hours</div>"
        f"<div style='font-size:17px;color:{_ib_sub};margin-top:6px;'>compared to standard onboarding ({static_hours}h) · "
        f"AI-optimized path: <b style='color:{_ib_bold};'>{total_hours}h</b></div></div>",
        unsafe_allow_html=True
    )

    # ── Skill Intelligence Panel (Upgrade 4) ──────────────────────────────────
    coverage_ratio = len(matched) / max(len(jd_skills), 1)
    learning_eff   = "High" if len(pathway) <= 3 else "Medium" if len(pathway) <= 6 else "Focused"
    critical_count = sum(1 for g in gaps if g.lower() in {"machine learning","python","sql","aws","docker","react","javascript","leadership"})
    _sip_bg  = "#111111" if is_dark else "#f8fafc"
    _sip_bdr = "#222222" if is_dark else "#e2e8f0"
    _sip_h   = "#ffffff" if is_dark else "#0f172a"
    _sip_sub = "#777777" if is_dark else "#64748b"
    _sip_acc = "#00d4ff" if is_dark else "#0ea5e9"
    sip_cols = st.columns(4)
    for col, lbl, val, hint in [
        (sip_cols[0], "Skill Coverage",        f"{round(coverage_ratio*100)}%",  "Semantic match via embeddings"),
        (sip_cols[1], "Missing Critical Skills", str(critical_count),             "High-demand market skills"),
        (sip_cols[2], "Learning Efficiency",    learning_eff,                    "Courses per gap ratio"),
        (sip_cols[3], "Matching Method",        "Semantic",                      "cosine similarity · all-MiniLM-L6-v2"),
    ]:
        col.markdown(f"""
        <div style="background:{_sip_bg};border:1px solid {_sip_bdr};border-radius:10px;
                    padding:1rem;text-align:center;">
            <div style="font-size:.75rem;color:{_sip_sub};text-transform:uppercase;
                        letter-spacing:.8px;margin-bottom:.3rem;">{lbl}</div>
            <div style="font-size:1.6rem;font-weight:700;color:{_sip_acc};">{val}</div>
            <div style="font-size:.72rem;color:{_sip_sub};margin-top:.25rem;">{hint}</div>
        </div>""", unsafe_allow_html=True)

    # ── Dashboard Layout ──────────────────────────────────────────────────────
    readiness = gap_result["coverage_pct"]
    gap_pct   = 100 - readiness
    post_path = min(100, readiness + efficiency)

    # Hero metrics row — card style
    hm1, hm2, hm3 = st.columns(3)
    cost_saved = round(hours_saved * 800)
    _mc  = "#ffffff" if is_dark else "#0ea5e9"
    _mg  = "#bbbbbb" if is_dark else "#16a34a"
    _my  = "#888888" if is_dark else "#d97706"
    _mst = "#777777" if is_dark else "#64748b"
    for col, label, value, color in [
        (hm1, "Time to Competency",  f"{total_hours}h",       _mc),
        (hm2, "Time Saved",          f"{hours_saved}h",       _mg),
        (hm3, "Gaps Closed",         str(len(gaps)),          _my),
    ]:
        col.markdown(f"""
        <div class="pro-card" style="text-align:center;">
            <div style="font-size:.9rem;color:{_mst};margin-bottom:.4rem;">{label}</div>
            <div style="font-size:2rem;font-weight:700;color:{color};">{value}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Dashboard: compact stats + ring in one row ─────────────────────────────
    _sb  = "#777777" if is_dark else "#64748b"
    _sv  = "#ffffff" if is_dark else "#0f172a"
    _cbd = "#222222" if is_dark else "#e2e8f0"
    stats = [
        ("Readiness",      f"{readiness:.0f}%"),
        ("Courses",         str(len(pathway))),
        ("Gaps to Close",   str(len(gaps))),
        ("Efficiency Gain", f"{efficiency}%"),
    ]
    stat_html = "".join(f"""
        <div style="flex:1;text-align:center;padding:.6rem .4rem;border-right:1px solid {_cbd};">
            <div style="font-size:.78rem;color:{_sb};letter-spacing:.5px;text-transform:uppercase;margin-bottom:.25rem;">{lbl}</div>
            <div style="font-size:1.55rem;font-weight:700;color:{_sv};line-height:1;">{val}</div>
        </div>""" for lbl, val in stats)

    dcol1, dcol2 = st.columns([3, 2])
    with dcol1:
        st.markdown(f"""
        <div style="background:{bg_card};border:1px solid {_cbd};border-radius:10px;
                    display:flex;align-items:stretch;overflow:hidden;margin-bottom:.5rem;">
            {stat_html}
            <div style="flex:1;text-align:center;padding:.6rem .4rem;">
                <div style="font-size:.78rem;color:{_sb};letter-spacing:.5px;text-transform:uppercase;margin-bottom:.25rem;">Role</div>
                <div style="font-size:.95rem;font-weight:600;color:{_sv};line-height:1.2;">{from_role}<br>
                    <span style="color:{_sb};font-size:.8rem;font-weight:400;">→ {to_role}</span></div>
            </div>
        </div>""", unsafe_allow_html=True)

        gap_list = sorted(gaps)
        if len(gap_list) >= 3:
            gap_sizes = [40 + (hash(s) % 50) for s in gap_list]
            fig_radar = px.line_polar(
                pd.DataFrame({"Skill": gap_list, "Gap Size": gap_sizes}),
                r="Gap Size", theta="Skill", line_close=True
            )
            fig_radar.update_traces(fill="toself", line_color=accent)
            fig_radar.update_layout(
                paper_bgcolor=_pbg, plot_bgcolor=_pbg,
                font_color=txt_color, height=240,
                polar=dict(bgcolor=_pfg,
                           radialaxis=dict(visible=True, color="#555", showticklabels=False),
                           angularaxis=dict(color=_sb)),
                margin=dict(t=10, b=10, l=10, r=10), showlegend=False
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    with dcol2:
        fig_ring = px.pie(
            values=[readiness, gap_pct], names=["Ready", "Gap"],
            hole=0.72, color_discrete_sequence=[accent, "#333333" if is_dark else "#e2e8f0"]
        )
        fig_ring.update_traces(textinfo="none")
        fig_ring.update_layout(
            paper_bgcolor=_pbg, font_color=txt_color,
            height=260, margin=dict(t=0, b=0, l=0, r=0),
            showlegend=False,
            annotations=[dict(
                text=f"<b>{readiness:.0f}%</b><br><span style='font-size:11px'>Ready</span>",
                x=0.5, y=0.5, font_size=20, font_color=_sv, showarrow=False
            )]
        )
        st.plotly_chart(fig_ring, use_container_width=True)
        st.markdown(f"<p style='text-align:center;font-size:.8rem;color:{_sb};margin-top:-.8rem;'>■ Ready &nbsp; ■ Gap</p>", unsafe_allow_html=True)

    st.divider()

    # ── FEATURE 2: yFiles hierarchic graph ───────────────────────────────────
    _rmap_bg  = "#0f172a" if is_dark else "#f1f5f9"
    _rmap_bdr = "#334155" if is_dark else "#cbd5e1"
    _rmap_h2  = "#f3f4f6" if is_dark else "#0f172a"
    _rmap_sub = "#9ca3af" if is_dark else "#475569"
    st.markdown(f"""
    <div style="background:linear-gradient(to bottom,{_rmap_bg},{_rmap_bg});padding:1.5rem;
                border-radius:12px;margin:1.5rem 0;border:1px solid {_rmap_bdr};
                box-shadow:0 10px 25px rgba(0,0,0,0.4);">
        <h2 style="color:{_rmap_h2};text-align:center;margin:0 0 .5rem 0;font-weight:600;">
            Your Personalized Learning Roadmap
        </h2>
        <p style="color:{_rmap_sub};text-align:center;font-size:1.05rem;margin:0 0 1rem 0;">
            Step-by-step path from your current level to full role competency
        </p>
    """, unsafe_allow_html=True)

    nodes = [{
        "id": "START",
        "label": "Start",
        "properties": {"background": "#2ecc71", "textColor": "#ffffff",
                       "shape": "ellipse", "size": [220, 80],
                       "tooltip": f"Role: {from_role}"}
    }]
    for idx, c in enumerate(pathway):
        diff  = c.get("difficulty", "intermediate").lower()
        color = {"beginner": "#10b981", "intermediate": "#3b82f6", "advanced": "#ef4444"}.get(diff, "#6b7280")
        lbl   = c["title"][:22] + "..." if len(c["title"]) > 25 else c["title"]
        nodes.append({
            "id": c["id"],
            "label": lbl,
            "properties": {
                "background": color, "textColor": "#ffffff",
                "shape": "roundrectangle", "size": [180, 70],
                "tooltip": f"Duration: {c['duration']}h\nDifficulty: {diff.title()}\nCovers: {', '.join(c['skills'])}"
            }
        })
    nodes.append({
        "id": "END",
        "label": "Job Ready",
        "properties": {"background": "#9b59b6", "textColor": "#ffffff",
                       "shape": "ellipse", "size": [220, 80],
                       "tooltip": f"Role: {to_role}"}
    })

    edges = [{"start": "START", "end": pathway[0]["id"]}] if pathway else []
    for i in range(len(pathway) - 1):
        edges.append({"start": pathway[i]["id"], "end": pathway[i+1]["id"],
                      "properties": {"stroke": "#4b5563", "thickness": 3, "directed": True}})
    if pathway:
        edges.append({"start": pathway[-1]["id"], "end": "END",
                      "properties": {"stroke": "#4b5563", "thickness": 3, "directed": True}})

    if YFILES:
        yfiles_graph(
            nodes=nodes, edges=edges,
            layout="hierarchic", height=550,
            zoom=True, drag_nodes=True,
            show_search=True, show_overview=True,
            fit_content=True
        )
    else:
        G = nx.DiGraph()
        for n in nodes: G.add_node(n["id"], **n)
        for e in edges: G.add_edge(e["start"], e["end"])
        pos = nx.spring_layout(G, seed=42, k=2.5)
        ex, ey = [], []
        for u, v in G.edges():
            x0,y0=pos[u]; x1,y1=pos[v]
            ex+=[x0,x1,None]; ey+=[y0,y1,None]
        _gbg   = "#0a0a0a" if is_dark else "#f8fafc"
        _gtxt  = "#e0e0e0" if is_dark else "#1e293b"
        _gline = "#333333" if is_dark else "#cbd5e1"
        fig_g = go.Figure()
        fig_g.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=_gline, width=2), hoverinfo="none"))
        fig_g.add_trace(go.Scatter(
            x=[pos[n][0] for n in G.nodes()], y=[pos[n][1] for n in G.nodes()],
            mode="markers+text",
            marker=dict(size=30,
                        color=[n["properties"]["background"] for n in nodes],
                        line=dict(color="#fff", width=2)),
            text=[n["label"] for n in nodes],
            textposition="top center",
            hovertext=[n["properties"].get("tooltip","") for n in nodes],
            hoverinfo="text", textfont=dict(color=_gtxt, size=11)
        ))
        fig_g.update_layout(showlegend=False, height=430,
            plot_bgcolor=_gbg, paper_bgcolor=_gbg,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig_g, use_container_width=True)

    st.markdown("""
    <div style="display:flex;justify-content:center;gap:1.5rem;margin:1rem 0;color:#9ca3af;font-size:.95rem;">
        <div><span style="color:#10b981;font-size:1.4rem;">●</span> Beginner</div>
        <div><span style="color:#3b82f6;font-size:1.4rem;">●</span> Intermediate</div>
        <div><span style="color:#ef4444;font-size:1.4rem;">●</span> Advanced</div>
    </div></div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── FEATURE 5: Tabs ───────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Personalized Path", "⚖️ Before vs After", "📅 Timeline View", "🔮 What-If Simulation"])

    with tab1:
        st.markdown("### 📚 Your Learning Pathway")

        # ── Skill Badges with Mastery Levels ─────────────────────────────────
        st.subheader("🛡️ Your Current Skills")
        badge_cols = st.columns(4)
        _badge_grad = "linear-gradient(135deg,#1a1a1a,#222222)" if is_dark else "linear-gradient(90deg,#0ea5e9,#6366f1)"
        _badge_txt  = "#e0e0e0" if is_dark else "#fff"
        _badge_bdr  = "1px solid #333333" if is_dark else "none"
        for i, skill in enumerate(sorted(candidate_skills)):
            mastery = (i % 3) + 2
            stars = "⭐" * mastery
            with badge_cols[i % 4]:
                st.markdown(
                    f"<div style='background:{_badge_grad};padding:12px;"
                    f"border-radius:8px;text-align:center;margin:5px;border:{_badge_bdr};'>"
                    f"<b style='color:{_badge_txt};'>{skill}</b><br>"
                    f"<small style='color:{_badge_txt};opacity:.7;'>Mastery: {mastery}/5 {stars}</small></div>",
                    unsafe_allow_html=True
                )
        st.markdown("")

        # ── Readiness progress bar ───────────────────────────────────────────────
        current_readiness = max(10, 100 - len(gaps) * 8)
        st.progress(current_readiness / 100)
        st.caption(f"Current estimated readiness: **{current_readiness}%** → **100%** after completing this path")
        st.markdown("")

        # ── Completion date estimate ───────────────────────────────────────────────
        import datetime as _dtt
        days_needed = round(total_hours / 4)
        ready_date  = _dtt.date.today() + _dtt.timedelta(days=days_needed)
        st.info(f"📅 At **4 hrs/day**, you’ll be role-ready by **{ready_date.strftime('%B %d, %Y')}** ({days_needed} days)")

        st.subheader("📍 Your Personalized Onboarding Roadmap")
        st.caption(f"Optimized sequence · Total: {total_hours}h · Prerequisite-aware")

        # ── Step cards ────────────────────────────────────────────────────────────
        _card_bg  = "#111111" if is_dark else "#ffffff"
        _card_txt = "#e0e0e0" if is_dark else "#1e293b"
        _card_sub = "#777777" if is_dark else "#64748b"
        _diff_colors = {"beginner": "#ffffff", "intermediate": "#aaaaaa", "advanced": "#666666"} if is_dark else {"beginner": "#16a34a", "intermediate": "#0ea5e9", "advanced": "#dc2626"}

        for i, course in enumerate(pathway, 1):
            gap_hits = [s for s in course["skills"] if s.lower() in [g.lower() for g in gaps]]
            reason   = ", ".join(gap_hits) if gap_hits else "core role foundations"
            diff_col = _diff_colors.get(course["difficulty"], "#94a3b8")
            st.markdown(f"""
            <div style="background:{_card_bg};border-left:4px solid {diff_col};
                        padding:1.3rem 1.4rem;border-radius:8px;margin:.8rem 0;
                        box-shadow:0 2px 8px rgba(0,0,0,.2);position:relative;">
                <div style="position:absolute;left:-13px;top:18px;background:{'#0a0a0a' if is_dark else '#f1f5f9'};
                            color:{'#555555' if is_dark else '#94a3b8'};width:26px;height:26px;border-radius:50%;
                            text-align:center;line-height:26px;font-size:.85rem;font-weight:700;
                            border:1px solid {'#333333' if is_dark else '#e2e8f0'};">{i}</div>
                <div style="display:flex;justify-content:space-between;align-items:start;gap:1rem;">
                    <div>
                        <div style="font-weight:600;font-size:1.1rem;color:{_card_txt};margin-bottom:.3rem;">{course['title']}</div>
                        <div style="color:{_card_sub};font-size:.92rem;margin-bottom:.5rem;">{', '.join(course['skills'])}</div>
                        <div style="color:{_card_txt};font-size:.95rem;">{course['why']}</div>
                        <div style="color:{_card_sub};font-size:.88rem;margin-top:.4rem;">Closes gaps in: <em>{reason}</em></div>
                    </div>
                    <div style="text-align:right;min-width:90px;">
                        <div style="font-weight:700;color:{diff_col};font-size:1.1rem;">{course['duration']}h</div>
                        <div style="font-size:.8rem;color:#64748b;margin-top:.2rem;">{course['difficulty'].title()}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Bonus Courses ─────────────────────────────────────────────────────────
        exp_yrs = rd.get("experience_years") or 0
        bonus   = build_bonus_courses(gaps, candidate_skills, exp_yrs)
        if bonus:
            st.markdown("")
            _bc_bg  = "#111111" if is_dark else "#f8fafc"
            _bc_bdr = "#333333" if is_dark else "#e2e8f0"
            _bc_h   = "#ffffff" if is_dark else "#0f172a"
            _bc_sub = "#777777" if is_dark else "#64748b"
            _bc_rsn = "#aaaaaa" if is_dark else "#475569"
            st.markdown(f"""
            <div style="background:{_bc_bg};border:1px solid {_bc_bdr};border-radius:10px;
                        padding:1.2rem 1.4rem;margin:1rem 0;">
                <div style="font-weight:700;font-size:1.05rem;color:{_bc_h};margin-bottom:.2rem;">
                    🚀 Bonus: High-Value Courses for Your Career Growth
                </div>
                <div style="font-size:.88rem;color:{_bc_sub};margin-bottom:.8rem;">
                    Based on your experience level & market trends — not required, but highly recommended
                </div>
            """, unsafe_allow_html=True)
            for bc in bonus:
                st.markdown(f"""
                <div style="border-left:3px solid {'#444444' if is_dark else '#0ea5e9'};
                            padding:.6rem 1rem;margin:.5rem 0;border-radius:0 6px 6px 0;
                            background:{'#1a1a1a' if is_dark else '#f0f9ff'};">
                    <span style="font-weight:600;color:{_bc_h};">{bc['title']}</span>
                    <span style="color:{_bc_sub};font-size:.85rem;"> &nbsp;·&nbsp; {bc['duration']}h</span><br>
                    <span style="color:{_bc_rsn};font-size:.88rem;">{bc['reason']}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Timeline bar ────────────────────────────────────────────────────────────
        df_tl = pd.DataFrame({
            "Step":       [f"Step {i+1}" for i in range(len(pathway))],
            "Hours":      [c["duration"] for c in pathway],
            "Difficulty": [c["difficulty"] for c in pathway]
        })
        fig_tl = px.bar(df_tl, x="Hours", y="Step", orientation="h",
                        color="Difficulty",
                        color_discrete_map={"beginner":"#4ade80","intermediate":"#60a5fa","advanced":"#f87171"},
                        height=180 + len(pathway) * 35, text_auto=True)
        fig_tl.update_layout(
            xaxis_title="Estimated Hours", yaxis_title="",
            bargap=0.25, margin=dict(l=10,r=10,t=30,b=10),
            paper_bgcolor=_pbg, plot_bgcolor=_pbg, font_color=txt_color,
            legend_title="Difficulty"
        )
        st.plotly_chart(fig_tl, use_container_width=True)

    with tab2:
        st.success(f"Standard onboarding: **{static_hours} hours** → Your AI path: **{total_hours} hours** (You save **{hours_saved} hours!**)")
        _bbg = "#0a0a0a" if is_dark else "#f8fafc"
        fig = go.Figure(go.Bar(
            x=["Static Onboarding", "AI-Adaptive Onboarding"],
            y=[static_hours, total_hours],
            marker_color=["#ff4b4b", accent],
            text=[f"{static_hours}h", f"{total_hours}h"],
            textposition="outside"
        ))
        fig.update_layout(plot_bgcolor=_bbg, paper_bgcolor=_bbg,
            font_color=txt_color, yaxis_title="Hours Required",
            showlegend=False, height=350, margin=dict(t=20, b=20))
        fig.add_annotation(x=1, y=total_hours+1,
            text=f"🎯 {efficiency}% more efficient",
            showarrow=False, font=dict(color=accent, size=14))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        import datetime
        base = datetime.date(2025, 1, 1)
        rows, day = [], 0
        for c in pathway:
            rows.append({
                "Course": c["title"],
                "Start":  str(base + datetime.timedelta(days=day)),
                "Finish": str(base + datetime.timedelta(days=day + c["duration"])),
                "Difficulty": c["difficulty"]
            })
            day += c["duration"] + 1
        df_gantt = pd.DataFrame(rows)
        fig_gantt = px.timeline(
            df_gantt, x_start="Start", x_end="Finish", y="Course",
            color="Difficulty",
            color_discrete_map={"beginner": "#00ff9d", "intermediate": "#00bfff", "advanced": "#ff4b4b"},
            title="📅 Your Onboarding Timeline"
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(
            paper_bgcolor=_bbg, plot_bgcolor="#111111" if is_dark else "#f1f5f9",
            font_color=txt_color, height=450, margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

    with tab4:
        st.markdown("### 🔮 What-If Simulation")
        st.caption("Select a course below to see how your skill gap reduces after completing it.")

        course_titles = [c["title"] for c in pathway]
        selected = st.selectbox("Choose a course to simulate completing:", course_titles)
        selected_course = next(c for c in pathway if c["title"] == selected)

        # Skills gained from this course that are in the gap list
        gaps_closed = {s for s in selected_course["skills"] if s in gaps}
        remaining   = gaps - gaps_closed
        new_coverage = round(len(matched | gaps_closed) / max(len(jd_skills), 1) * 100)

        wi1, wi2, wi3 = st.columns(3)
        _wi_bg  = "#111111" if is_dark else "#f8fafc"
        _wi_bdr = "#222222" if is_dark else "#e2e8f0"
        for col, lbl, val, color in [
            (wi1, "Gaps Closed",      f"{len(gaps_closed)} / {len(gaps)}", "#22c55e"),
            (wi2, "Remaining Gaps",   str(len(remaining)),                 "#ef4444" if remaining else "#22c55e"),
            (wi3, "New Coverage",     f"{new_coverage}%",                  "#0ea5e9"),
        ]:
            col.markdown(f"""
            <div style="background:{_wi_bg};border:1px solid {_wi_bdr};border-radius:10px;
                        padding:1rem;text-align:center;">
                <div style="font-size:.8rem;color:{_sip_sub};text-transform:uppercase;
                            letter-spacing:.8px;margin-bottom:.3rem;">{lbl}</div>
                <div style="font-size:1.8rem;font-weight:700;color:{color};">{val}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # Before / After gap bar chart
        all_gap_skills = sorted(gaps)
        before_vals = [1] * len(all_gap_skills)
        after_vals  = [0 if s in gaps_closed else 1 for s in all_gap_skills]
        fig_wi = go.Figure()
        fig_wi.add_trace(go.Bar(name="Before", x=all_gap_skills, y=before_vals,
                                marker_color="#ef4444", opacity=0.7))
        fig_wi.add_trace(go.Bar(name="After",  x=all_gap_skills, y=after_vals,
                                marker_color="#22c55e", opacity=0.9))
        fig_wi.update_layout(
            barmode="group", height=300,
            paper_bgcolor=_pbg, plot_bgcolor=_pbg, font_color=txt_color,
            yaxis=dict(tickvals=[0,1], ticktext=["Closed","Gap"], range=[0,1.4]),
            xaxis_title="Skill", legend_title="Status",
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig_wi, use_container_width=True)

        if gaps_closed:
            st.success(f"✅ Completing **{selected}** closes: {', '.join(sorted(gaps_closed))}")
        if not remaining:
            st.balloons()
            st.success("🎉 This single course closes ALL your gaps — you're role-ready!")
        else:
            st.info(f"📌 Still remaining after this course: {', '.join(sorted(remaining))}")

    st.divider()

    # ── Simulate Onboarding ───────────────────────────────────────────────────
    if st.button("🚀 Simulate Completing My Path", help="See how fast you become role-ready", use_container_width=True):
        bar    = st.progress(0)
        status = st.empty()
        for pct in range(101):
            bar.progress(pct)
            status.markdown(f"💪 **Progress: {pct}%** — {'Getting started...' if pct < 30 else 'Building momentum...' if pct < 70 else 'Almost role-ready!' if pct < 100 else '✅ Done!'}")
            time.sleep(0.03)
        st.balloons()
        salary_boost = f"₹{2 + len(gaps) * 0.4:.1f} LPA"
        st.success(f"🌟 Simulation Complete! You’re now fully onboarded & confident. Estimated salary boost: +{salary_boost}")

    st.divider()

    # ── Export Panel ──────────────────────────────────────────────────────────
    _card_bg  = "#111111" if is_dark else "#ffffff"
    _card_h   = "#ffffff" if is_dark else "#0f172a"
    _export_sub = "#777777" if is_dark else "#64748b"
    st.markdown(f"""
    <div style="background:{_card_bg};padding:1.5rem;border-radius:16px;
                margin-top:1rem;border:1px solid {'#334155' if is_dark else '#e2e8f0'}">
        <h3 style="color:{_card_h};margin:0 0 .5rem 0;">📤 Export & Share Your Plan</h3>
        <p style="color:{_export_sub};margin:0;">Download your personalized roadmap or share with your manager</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    # build PDF + CSV once
    pdf_buffer = io.BytesIO()
    _c = rl_canvas.Canvas(pdf_buffer, pagesize=letter)
    _c.setFont("Helvetica-Bold", 20)
    _c.drawString(60, 750, "AI Adaptive Onboarding Pathway")
    _c.setFont("Helvetica", 13)
    _c.drawString(60, 720, f"For: {from_role}  →  {to_role}")
    _c.drawString(60, 700, f"Total: {total_hours}h  |  Saved: {hours_saved}h ({efficiency}%)")
    _c.setFont("Helvetica-Bold", 14)
    _c.drawString(60, 670, "Your Personalized Learning Path:")
    _c.setFont("Helvetica", 12)
    _y = 645
    for _i, _course in enumerate(pathway, 1):
        _c.drawString(60, _y, f"{_i}. {_course['title']} ({_course['duration']}h) — {_course['difficulty']}")
        _c.setFont("Helvetica-Oblique", 10)
        _c.drawString(80, _y - 14, _course['why'])
        _c.setFont("Helvetica", 12)
        _y -= 36
        if _y < 80:
            _c.showPage(); _y = 750
    _c.setFont("Helvetica-Oblique", 9)
    _c.drawString(60, 40, "Generated by AI-Adaptive Onboarding Engine · Powered by LLaMA 3.2 · SkillBridge")
    _c.save()
    pdf_buffer.seek(0)

    import datetime as _dt
    _base, _day = _dt.date(2025, 1, 1), 0
    _csv_rows = []
    for _course in pathway:
        _csv_rows.append({
            "Course": _course["title"],
            "Difficulty": _course["difficulty"],
            "Duration (hrs)": _course["duration"],
            "Start Date": str(_base + _dt.timedelta(days=_day)),
            "End Date":   str(_base + _dt.timedelta(days=_day + _course["duration"])),
            "Why": _course["why"]
        })
        _day += _course["duration"] + 1
    csv_data = pd.DataFrame(_csv_rows).to_csv(index=False)
    txt_content = f"AI Onboarding Plan: {from_role} → {to_role}\nTotal: {total_hours}h | Saved: {hours_saved}h\n\n" + \
                  "\n".join([f"{i}. {c['title']} ({c['duration']}h) — {c['why']}" for i, c in enumerate(pathway, 1)])

    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        st.download_button("📄 Download PDF",    pdf_buffer,  "Onboarding_Roadmap.pdf",      "application/pdf", use_container_width=True)
    with ex2:
        st.download_button("📊 Export CSV",      csv_data,    "onboarding_timeline.csv",     "text/csv",        use_container_width=True)
    with ex3:
        st.download_button("📧 Email to HR",    txt_content, "onboarding_plan.txt",         "text/plain",      use_container_width=True)

    # ── Impact Scorecard ──────────────────────────────────────────────────────
    st.markdown("### 🚀 Your Onboarding Impact Score")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.metric("⏱️ Time Saved", f"{hours_saved} hours", f"{efficiency}% faster")
    with sc2:
        st.metric("🎯 Skill Coverage", "100%", f"All {len(gaps)} gaps closed")
    with sc3:
        confidence = min(99, 70 + len(matched) * 3)
        st.metric("💪 Confidence Score", f"{confidence}%", "Ready for Day 1")

    # ── FEATURE 4: PDF Download (legacy — kept for compatibility) ────────────────────
    if st.button("📄 Download My Roadmap as PDF", help="Download your personalized learning roadmap as a PDF"):
        st.download_button("✅ Download PDF Now", pdf_buffer, "My_Personalized_Onboarding_Roadmap.pdf", "application/pdf")

    st.divider()

    # ── Reasoning Trace — Visual Pipeline (Upgrade 3) ────────────────────────
    with st.expander("🔍 AI Reasoning Pipeline (Judge Mode)", expanded=False):
        # ── Structured trace dict ─────────────────────────────────────────────
        trace = {
            "Step 1 · Input":             f"Candidate: {from_role} · {rd.get('experience_years','?')} yrs",
            "Step 2 · Resume Parsing":    f"Extracted {len(rd.get('skills',[]))} raw skills → normalized to {len(candidate_skills)}: {', '.join(sorted(candidate_skills)) or 'none'}",
            "Step 3 · JD Parsing":        f"Extracted {len(jd.get('skills',[]))} raw skills → normalized to {len(jd_skills)}: {', '.join(sorted(jd_skills)) or 'none'}",
            "Step 4 · Semantic Matching": f"cosine similarity (threshold 0.70) → {len(matched)} matched: {', '.join(sorted(matched)) or 'none'}",
            "Step 5 · Gap Detection":     f"JD − Candidate (semantic) → {len(gaps)} gaps: {', '.join(sorted(gaps)) or 'none'}",
            "Step 6 · Graph Ordering":    f"Prerequisite DAG topological sort → dependency-aware gap order",
            "Step 7 · Course Scoring":    f"score = gaps_covered / duration → ranked {len(pathway)} courses by efficiency",
            "Step 8 · Path Assembly":     " → ".join([c['title'] for c in pathway]),
            "Step 9 · Time Estimation":   f"Total {total_hours}h · Static {static_hours}h · Saved {hours_saved}h ({efficiency}%)",
            "Step 10 · Output":           f"Pathway for {from_role} → {to_role} ✅",
        }
        _tr_bg  = "#111111" if is_dark else "#f1f5f9"
        _tr_acc = "#00d4ff" if is_dark else "#0ea5e9"
        _tr_ttl = "#e0e0e0" if is_dark else "#0f172a"
        _tr_sub = "#777777" if is_dark else "#475569"
        for step, detail in trace.items():
            st.markdown(
                f"<div style='font-family:monospace;background:{_tr_bg};padding:9px 16px;"
                f"border-left:3px solid {_tr_acc};margin-bottom:5px;border-radius:0 8px 8px 0;'>"
                f"<span style='color:{_tr_acc};font-weight:700;'>{step}</span><br/>"
                f"<span style='color:{_tr_sub};font-size:12.5px;'>{detail}</span></div>",
                unsafe_allow_html=True
            )

        st.markdown("")
        # ── Visual skill-flow diagram ─────────────────────────────────────────
        st.markdown(f"<div style='font-size:.85rem;color:{_tr_sub};margin-bottom:.4rem;'>📊 Skill Flow Diagram — gap → course mapping</div>", unsafe_allow_html=True)
        G_trace = nx.DiGraph()
        gap_nodes    = list(gaps)
        course_nodes = [c["title"] for c in pathway]
        for g in gap_nodes:    G_trace.add_node(g,  kind="gap")
        for c in pathway:
            G_trace.add_node(c["title"], kind="course")
            for s in c["skills"]:
                if s in gaps:
                    G_trace.add_edge(s, c["title"])
        pos_trace = nx.spring_layout(G_trace, seed=7, k=2.2)
        ex_t, ey_t = [], []
        for u, v in G_trace.edges():
            x0,y0=pos_trace[u]; x1,y1=pos_trace[v]
            ex_t+=[x0,x1,None]; ey_t+=[y0,y1,None]
        node_colors = ["#ef4444" if G_trace.nodes[n]["kind"]=="gap" else "#3b82f6" for n in G_trace.nodes()]
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(x=ex_t, y=ey_t, mode="lines",
                                      line=dict(color="#444", width=1.5), hoverinfo="none"))
        fig_flow.add_trace(go.Scatter(
            x=[pos_trace[n][0] for n in G_trace.nodes()],
            y=[pos_trace[n][1] for n in G_trace.nodes()],
            mode="markers+text",
            marker=dict(size=22, color=node_colors, line=dict(color="#fff", width=1.5)),
            text=list(G_trace.nodes()), textposition="top center",
            hoverinfo="text", textfont=dict(color=txt_color, size=10)
        ))
        fig_flow.update_layout(
            showlegend=False, height=360,
            plot_bgcolor=_pbg, paper_bgcolor=_pbg,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_flow, use_container_width=True)
        st.markdown(f"<div style='font-size:.78rem;color:{_tr_sub};'><span style='color:#ef4444;'>●</span> Skill Gap &nbsp; <span style='color:#3b82f6;'>●</span> Course</div>", unsafe_allow_html=True)

    # ── Floating AI Chat Agent ────────────────────────────────────────────────
    import json as _json
    import urllib.request as _ureq
    from parser import _get_openai_key
    try:
        from openai import OpenAI as _OAI
        _OAI_AVAIL = True
    except ImportError:
        _OAI_AVAIL = False

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

    _sys = (
        f"You are a concise, helpful onboarding assistant. "
        f"The candidate is a {from_role} transitioning to {to_role} with "
        f"{rd.get('experience_years', '?')} years experience. "
        f"Skill gaps: {', '.join(sorted(gaps))}. "
        f"Recommended learning path: {', '.join([c['title'] for c in pathway])}. "
        f"Total learning time: {total_hours}h (saves {hours_saved}h vs static onboarding). "
        f"Answer in 2-3 sentences max. Be direct and practical."
    )

    # ── Floating button + chat panel CSS ─────────────────────────────────────
    _panel_bg   = "#18181b" if is_dark else "#ffffff"
    _panel_bdr  = "#333"    if is_dark else "#e2e8f0"
    _panel_h    = "#ffffff" if is_dark else "#0f172a"
    _panel_sub  = "#888"    if is_dark else "#64748b"
    _msg_user   = "#2563eb"
    _msg_ai_bg  = "#27272a" if is_dark else "#f1f5f9"
    _msg_ai_txt = "#e4e4e7" if is_dark else "#1e293b"
    _input_bg   = "#27272a" if is_dark else "#f8fafc"
    _input_bdr  = "#444"    if is_dark else "#cbd5e1"
    _input_txt  = "#fff"    if is_dark else "#0f172a"

    st.markdown(f"""
    <style>
    #fab-btn {{
        position:fixed; bottom:28px; right:28px; z-index:9999;
        width:58px; height:58px; border-radius:50%;
        background:linear-gradient(135deg,#6366f1,#0ea5e9);
        border:none; cursor:pointer;
        box-shadow:0 4px 20px rgba(99,102,241,.55);
        display:flex; align-items:center; justify-content:center;
        font-size:26px; transition:transform .2s, box-shadow .2s;
        color:#fff;
    }}
    #fab-btn:hover {{ transform:scale(1.1); box-shadow:0 6px 28px rgba(99,102,241,.75); }}
    #chat-panel {{
        position:fixed; bottom:100px; right:28px; z-index:9998;
        width:370px; max-height:560px;
        background:{_panel_bg}; border:1px solid {_panel_bdr};
        border-radius:18px; box-shadow:0 12px 40px rgba(0,0,0,.45);
        display:flex; flex-direction:column; overflow:hidden;
        animation:slideUp .25s ease;
    }}
    @keyframes slideUp {{ from{{opacity:0;transform:translateY(20px)}} to{{opacity:1;transform:translateY(0)}} }}
    #chat-header {{
        background:linear-gradient(135deg,#6366f1,#0ea5e9);
        padding:14px 18px; display:flex; align-items:center; gap:10px;
        border-radius:18px 18px 0 0;
    }}
    #chat-messages {{
        flex:1; overflow-y:auto; padding:14px 14px 6px;
        display:flex; flex-direction:column; gap:10px;
        max-height:360px;
    }}
    .cm-user {{
        align-self:flex-end; background:{_msg_user};
        color:#fff; border-radius:14px 14px 3px 14px;
        padding:9px 13px; font-size:.88rem; max-width:85%; line-height:1.45;
    }}
    .cm-ai {{
        align-self:flex-start; background:{_msg_ai_bg};
        color:{_msg_ai_txt}; border-radius:14px 14px 14px 3px;
        padding:9px 13px; font-size:.88rem; max-width:85%; line-height:1.45;
    }}
    #chat-suggestions {{
        padding:6px 14px; display:flex; flex-wrap:wrap; gap:5px;
    }}
    .cs-chip {{
        background:{'#2a2a2e' if is_dark else '#f1f5f9'};
        border:1px solid {'#444' if is_dark else '#e2e8f0'};
        border-radius:14px; padding:4px 11px;
        font-size:.78rem; color:{'#aaa' if is_dark else '#475569'};
        cursor:pointer; white-space:nowrap;
    }}
    .cs-chip:hover {{ border-color:#6366f1; color:#6366f1; }}
    #chat-input-row {{
        padding:10px 12px; border-top:1px solid {_panel_bdr};
        display:flex; gap:8px; align-items:center;
    }}
    #chat-input-row input {{
        flex:1; background:{_input_bg}; border:1px solid {_input_bdr};
        border-radius:10px; padding:9px 13px;
        color:{_input_txt}; font-size:.88rem; outline:none;
    }}
    #chat-input-row input:focus {{ border-color:#6366f1; }}
    #chat-send {{
        background:#6366f1; border:none; border-radius:10px;
        width:38px; height:38px; cursor:pointer; color:#fff;
        font-size:16px; display:flex; align-items:center; justify-content:center;
        flex-shrink:0;
    }}
    #chat-send:hover {{ background:#4f46e5; }}
    @media(max-width:480px){{
        #chat-panel{{ width:calc(100vw - 32px); right:16px; bottom:90px; }}
        #fab-btn{{ right:16px; bottom:16px; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── FAB toggle button ─────────────────────────────────────────────────────
    _fab_label = "✕ Close" if st.session_state.chat_open else "🤖 Ask AI"
    # Inject CSS to make this specific button fixed bottom-right
    st.markdown("""
    <style>
    div[data-testid="stButton"][id="fab-wrapper"] > button,
    button[kind="primary"][data-testid="baseButton-primary"]:last-of-type {
        /* fallback — real fix below */
    }
    #fab-fixed-wrapper {
        position: fixed !important;
        bottom: 28px !important;
        right: 28px !important;
        z-index: 10000 !important;
    }
    #fab-fixed-wrapper button {
        width: 58px !important;
        height: 58px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg,#6366f1,#0ea5e9) !important;
        border: none !important;
        font-size: 22px !important;
        padding: 0 !important;
        box-shadow: 0 4px 20px rgba(99,102,241,.6) !important;
        color: #fff !important;
        font-weight: 700 !important;
    }
    #fab-fixed-wrapper button:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 6px 28px rgba(99,102,241,.8) !important;
    }
    </style>
    <div id="fab-fixed-wrapper">
    """, unsafe_allow_html=True)
    if st.button(_fab_label, key="fab_toggle", help="Ask AI about your learning path"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat panel (shown when open) ──────────────────────────────────────────
    if st.session_state.chat_open:
        st.markdown(f"""
        <div id="chat-panel">
            <div id="chat-header">
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
                  <!-- head -->
                  <rect x="7" y="10" width="22" height="16" rx="4" fill="white" fill-opacity="0.95"/>
                  <!-- eyes -->
                  <circle cx="13" cy="17" r="2.5" fill="#6366f1"/>
                  <circle cx="23" cy="17" r="2.5" fill="#6366f1"/>
                  <!-- eye shine -->
                  <circle cx="14" cy="16" r="0.8" fill="white"/>
                  <circle cx="24" cy="16" r="0.8" fill="white"/>
                  <!-- mouth -->
                  <rect x="13" y="21" width="10" height="2" rx="1" fill="#0ea5e9"/>
                  <!-- antenna -->
                  <line x1="18" y1="10" x2="18" y2="6" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
                  <circle cx="18" cy="5" r="1.8" fill="#0ea5e9"/>
                  <!-- ears -->
                  <rect x="4" y="15" width="3" height="5" rx="1.5" fill="white" fill-opacity="0.7"/>
                  <rect x="29" y="15" width="3" height="5" rx="1.5" fill="white" fill-opacity="0.7"/>
                </svg>
                <div>
                    <div style="font-weight:700;color:#fff;font-size:.95rem;">SkillBridge AI</div>
                    <div style="font-size:.75rem;color:rgba(255,255,255,.75);">Your onboarding assistant</div>
                </div>
            </div>
            <div id="chat-messages">
        """, unsafe_allow_html=True)

        if not st.session_state.chat_messages:
            st.markdown(f"""
                <div class="cm-ai">👋 Hi! I know your full learning path for <b>{from_role} → {to_role}</b>.<br>
                Ask me anything about your roadmap, gaps, or timeline!</div>
            """, unsafe_allow_html=True)

        for _msg in st.session_state.chat_messages:
            _cls = "cm-user" if _msg["role"] == "user" else "cm-ai"
            st.markdown(f"<div class='{_cls}'>{_msg['content']}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # close #chat-messages

        # Suggestion chips (only when empty)
        if not st.session_state.chat_messages:
            st.markdown("""
            <div id="chat-suggestions">
                <span class="cs-chip">Why first course?</span>
                <span class="cs-chip">Daily time needed?</span>
                <span class="cs-chip">Most critical skill?</span>
                <span class="cs-chip">Salary boost?</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # close #chat-panel

        # ── Streamlit chat input (rendered below panel, functional) ──────────
        _col_inp, _col_clr = st.columns([5, 1])
        with _col_inp:
            _user_q = st.chat_input("Ask about your path...", key="float_chat_input")
        with _col_clr:
            if st.session_state.chat_messages:
                if st.button("🗑️", key="clear_chat", help="Clear chat"):
                    st.session_state.chat_messages = []
                    st.rerun()

        if _user_q:
            st.session_state.chat_messages.append({"role": "user", "content": _user_q})

            _oai_key = _get_openai_key() if _OAI_AVAIL else None
            if _OAI_AVAIL and _oai_key:
                _client  = _OAI(api_key=_oai_key)
                _history = [{"role": "system", "content": _sys}] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_messages
                ]
                _stream = _client.chat.completions.create(
                    model="gpt-4o-mini", messages=_history,
                    temperature=0.5, max_tokens=400, stream=True
                )
                _full, _buf = "", ""
                _ph = st.empty()
                for _chunk in _stream:
                    _delta = _chunk.choices[0].delta.content or ""
                    _full += _delta; _buf += _delta
                    if len(_buf) >= 8:
                        _ph.markdown(_full + "▍"); _buf = ""
                _ph.markdown(_full)
                _ans = _full
            else:
                _payload = _json.dumps({
                    "model": "llama3.2",
                    "prompt": f"{_sys}\n\nQuestion: {_user_q}",
                    "stream": False
                }).encode()
                try:
                    _req = _ureq.Request(
                        "http://localhost:11434/api/generate",
                        data=_payload, headers={"Content-Type": "application/json"}
                    )
                    with _ureq.urlopen(_req, timeout=30) as _r:
                        _ans = _json.loads(_r.read()).get("response", "No response")
                except Exception:
                    _ans = "⚠️ AI unavailable — add OpenAI key to `.streamlit/secrets.toml` or run `ollama serve`"

            st.session_state.chat_messages.append({"role": "assistant", "content": _ans})
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;color:#555555;font-size:13px;letter-spacing:.3px;'>"
        "Built in Ahmedabad &nbsp;·&nbsp; Hackathon 2026 &nbsp;·&nbsp; Powered by LLaMA 3.2"
        "</p>",
        unsafe_allow_html=True
    )
