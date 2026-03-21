"""
chat.py — SkillBridge floating AI chat agent
"""
import json
import urllib.request
import streamlit as st
from datetime import datetime


def _build_system_prompt(from_role, to_role, experience_years, gaps, pathway, total_hours, hours_saved):
    return (
        f"You are a concise, helpful onboarding assistant for SkillBridge. "
        f"The candidate is a {from_role} transitioning to {to_role} with "
        f"{experience_years} years experience. "
        f"Skill gaps: {', '.join(sorted(gaps)) or 'none'}. "
        f"Recommended learning path: {', '.join(c['title'] for c in pathway)}. "
        f"Total learning time: {total_hours}h (saves {hours_saved}h vs 35h static baseline). "
        f"Answer in 2-3 sentences max. Be direct and practical."
    )


def generate_response(user_q: str, system_prompt: str) -> str:
    """Try GPT-4o-mini → LLaMA 3.2 → fallback message."""
    try:
        from parser import _get_openai_key
        from openai import OpenAI
        key = _get_openai_key()
        if key:
            history = [{"role": "system", "content": system_prompt}] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.get("chat_messages", [])
            ]
            client = OpenAI(api_key=key)
            stream = client.chat.completions.create(
                model="gpt-4o-mini", messages=history,
                temperature=0.5, max_tokens=400, stream=True
            )
            full, buf = "", ""
            ph = st.empty()
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full += delta; buf += delta
                if len(buf) >= 8:
                    ph.markdown(full + "▍"); buf = ""
            ph.markdown(full)
            return full
    except Exception:
        pass

    try:
        payload = json.dumps({
            "model": "llama3.2",
            "prompt": f"{system_prompt}\n\nQuestion: {user_q}",
            "stream": False
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get("response", "No response")
    except Exception:
        return "⚠️ AI unavailable — add OpenAI key to `.streamlit/secrets.toml` or run `ollama serve`"


def _time_label():
    return datetime.now().strftime("%I:%M %p").lstrip("0")


def render_chat(from_role, to_role, rd, gaps, pathway, total_hours, hours_saved, is_dark):
    """Render the full floating chat UI + handle message submission."""

    # ── Theme tokens ──────────────────────────────────────────────────────────
    bg          = "#111113" if is_dark else "#ffffff"
    border      = "#2a2a2e" if is_dark else "#e2e8f0"
    user_bubble = "#4f46e5"
    ai_bg       = "#1e1e22" if is_dark else "#f1f5f9"
    ai_txt      = "#e4e4e7" if is_dark else "#1e293b"
    time_txt    = "rgba(255,255,255,.35)" if is_dark else "rgba(0,0,0,.35)"
    chip_bg     = "#1e1e22" if is_dark else "#f8fafc"
    chip_bdr    = "#333"    if is_dark else "#e2e8f0"
    chip_txt    = "#94a3b8" if is_dark else "#64748b"
    inp_bg      = "#18181b" if is_dark else "#f8fafc"
    inp_bdr     = "#333"    if is_dark else "#e2e8f0"
    inp_txt     = "#f4f4f5" if is_dark else "#0f172a"
    scrollbar   = "#2a2a2e" if is_dark else "#e2e8f0"

    st.markdown(f"""
    <style>
    /* ── Panel ── */
    #sb-chat-panel {{
        position:fixed; bottom:96px; right:24px; z-index:9998;
        width:360px; max-height:580px;
        background:{bg}; border:1px solid {border};
        border-radius:20px; box-shadow:0 20px 60px rgba(0,0,0,.5);
        display:flex; flex-direction:column; overflow:hidden;
        animation:sbSlideUp .22s cubic-bezier(.16,1,.3,1);
    }}
    @keyframes sbSlideUp {{
        from {{ opacity:0; transform:translateY(16px) scale(.97) }}
        to   {{ opacity:1; transform:translateY(0)   scale(1)   }}
    }}

    /* ── Header ── */
    #sb-chat-header {{
        background:linear-gradient(135deg,#4f46e5 0%,#0ea5e9 100%);
        padding:14px 16px; display:flex; align-items:center;
        gap:11px; flex-shrink:0;
    }}
    .sb-avatar {{
        width:38px; height:38px; border-radius:50%;
        background:rgba(255,255,255,.18); display:flex;
        align-items:center; justify-content:center;
        font-size:18px; flex-shrink:0;
    }}
    .sb-header-info {{ flex:1; min-width:0; }}
    .sb-header-name {{
        font-weight:700; color:#fff; font-size:.93rem;
        letter-spacing:.01em; line-height:1.2;
    }}
    .sb-header-status {{
        font-size:.72rem; color:rgba(255,255,255,.75);
        display:flex; align-items:center; gap:5px; margin-top:2px;
    }}
    .sb-status-dot {{
        width:7px; height:7px; border-radius:50%;
        background:#4ade80; flex-shrink:0;
        box-shadow:0 0 6px #4ade80;
        animation:sbPulse 2s ease-in-out infinite;
    }}
    @keyframes sbPulse {{
        0%,100% {{ opacity:1 }} 50% {{ opacity:.5 }}
    }}
    .sb-close-btn {{
        background:rgba(255,255,255,.15); border:none;
        border-radius:50%; width:28px; height:28px;
        color:#fff; font-size:14px; cursor:pointer;
        display:flex; align-items:center; justify-content:center;
        transition:background .15s;
    }}
    .sb-close-btn:hover {{ background:rgba(255,255,255,.28); }}

    /* ── Messages ── */
    #sb-chat-messages {{
        flex:1; overflow-y:auto; padding:14px 14px 8px;
        display:flex; flex-direction:column; gap:12px;
        max-height:360px;
        scrollbar-width:thin; scrollbar-color:{scrollbar} transparent;
    }}
    #sb-chat-messages::-webkit-scrollbar {{ width:4px; }}
    #sb-chat-messages::-webkit-scrollbar-thumb {{
        background:{scrollbar}; border-radius:4px;
    }}

    /* ── Bubble rows ── */
    .sb-row-user {{ display:flex; justify-content:flex-end; align-items:flex-end; gap:7px; }}
    .sb-row-ai   {{ display:flex; justify-content:flex-start; align-items:flex-end; gap:7px; }}

    .sb-mini-avatar {{
        width:26px; height:26px; border-radius:50%; flex-shrink:0;
        display:flex; align-items:center; justify-content:center;
        font-size:13px; margin-bottom:2px;
    }}
    .sb-mini-avatar-ai   {{ background:linear-gradient(135deg,#4f46e5,#0ea5e9); }}
    .sb-mini-avatar-user {{ background:linear-gradient(135deg,#7c3aed,#4f46e5); }}

    .sb-bubble-wrap {{ display:flex; flex-direction:column; max-width:82%; }}
    .sb-bubble-wrap-user {{ align-items:flex-end; }}
    .sb-bubble-wrap-ai   {{ align-items:flex-start; }}

    .sb-bubble {{
        padding:9px 13px; font-size:.86rem; line-height:1.55;
        word-break:break-word;
    }}
    .sb-bubble-user {{
        background:{user_bubble}; color:#fff;
        border-radius:16px 16px 4px 16px;
    }}
    .sb-bubble-ai {{
        background:{ai_bg}; color:{ai_txt};
        border-radius:16px 16px 16px 4px;
        border:1px solid {border};
    }}
    .sb-time {{
        font-size:.68rem; color:{time_txt};
        margin-top:3px; padding:0 3px;
    }}

    /* ── Typing indicator ── */
    .sb-typing {{
        background:{ai_bg}; border:1px solid {border};
        border-radius:16px 16px 16px 4px;
        padding:10px 14px; display:inline-flex; gap:5px; align-items:center;
    }}
    .sb-dot {{
        width:7px; height:7px; border-radius:50%;
        background:#6366f1; animation:sbBounce 1.2s ease-in-out infinite;
    }}
    .sb-dot:nth-child(2) {{ animation-delay:.2s; }}
    .sb-dot:nth-child(3) {{ animation-delay:.4s; }}
    @keyframes sbBounce {{
        0%,60%,100% {{ transform:translateY(0) }}
        30%          {{ transform:translateY(-6px) }}
    }}

    /* ── Suggestions ── */
    #sb-suggestions {{
        padding:6px 14px 10px; display:flex; flex-wrap:wrap; gap:6px;
    }}
    .sb-chip {{
        background:{chip_bg}; border:1px solid {chip_bdr};
        border-radius:20px; padding:5px 12px;
        font-size:.76rem; color:{chip_txt};
        cursor:pointer; white-space:nowrap;
        transition:all .15s;
    }}
    .sb-chip:hover {{
        border-color:#6366f1; color:#6366f1;
        background:{'#1e1e2e' if is_dark else '#eef2ff'};
    }}

    /* ── Divider ── */
    .sb-divider {{
        height:1px; background:{border}; margin:0 14px; flex-shrink:0;
    }}

    /* ── Input area ── */
    #sb-input-area {{
        padding:10px 12px 12px; flex-shrink:0;
        display:flex; align-items:center; gap:8px;
    }}

    /* ── FAB ── */
    #sb-fab-wrap {{
        position:fixed !important; bottom:24px !important;
        right:24px !important; z-index:10000 !important;
    }}
    #sb-fab-wrap button {{
        width:56px !important; height:56px !important;
        border-radius:50% !important;
        background:linear-gradient(135deg,#4f46e5,#0ea5e9) !important;
        border:none !important; font-size:22px !important;
        padding:0 !important; color:#fff !important;
        box-shadow:0 4px 24px rgba(79,70,229,.55) !important;
        transition:transform .2s, box-shadow .2s !important;
    }}
    #sb-fab-wrap button:hover {{
        transform:scale(1.1) !important;
        box-shadow:0 6px 32px rgba(79,70,229,.75) !important;
    }}
    /* Unread badge */
    .sb-badge {{
        position:absolute; top:-4px; right:-4px;
        background:#ef4444; color:#fff; border-radius:50%;
        width:18px; height:18px; font-size:.65rem;
        display:flex; align-items:center; justify-content:center;
        font-weight:700; border:2px solid {bg};
    }}
    @media(max-width:480px) {{
        #sb-chat-panel {{ width:calc(100vw - 28px); right:14px; bottom:84px; }}
        #sb-fab-wrap   {{ right:14px !important; bottom:14px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── State init ────────────────────────────────────────────────────────────
    if "chat_open"     not in st.session_state: st.session_state.chat_open     = False
    if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
    if "chat_pending"  not in st.session_state: st.session_state.chat_pending  = None

    # ── FAB ───────────────────────────────────────────────────────────────────
    unread = len(st.session_state.chat_messages) == 0 and not st.session_state.chat_open
    fab_icon = "✕" if st.session_state.chat_open else "💬"
    st.markdown('<div id="sb-fab-wrap">', unsafe_allow_html=True)
    if st.button(fab_icon, key="fab_toggle", help="Ask AI about your learning path"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.chat_open:
        return

    # ── Panel header ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div id="sb-chat-panel">
      <div id="sb-chat-header">
        <div class="sb-avatar">🤖</div>
        <div class="sb-header-info">
          <div class="sb-header-name">SkillBridge AI</div>
          <div class="sb-header-status">
            <span class="sb-status-dot"></span>
            Online · {from_role} → {to_role}
          </div>
        </div>
      </div>
      <div id="sb-chat-messages">
    """, unsafe_allow_html=True)

    # ── Welcome message ───────────────────────────────────────────────────────
    if not st.session_state.chat_messages:
        st.markdown(f"""
        <div class="sb-row-ai">
          <div class="sb-mini-avatar sb-mini-avatar-ai">🤖</div>
          <div class="sb-bubble-wrap sb-bubble-wrap-ai">
            <div class="sb-bubble sb-bubble-ai">
              👋 Hi! I know your full learning path for <b>{from_role} → {to_role}</b>.<br>
              You have <b>{len(gaps)} skill gap{'s' if len(gaps)!=1 else ''}</b> and
              <b>{total_hours}h</b> of optimized learning ahead.<br>
              Ask me anything about your roadmap!
            </div>
            <div class="sb-time">Just now</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Message history ───────────────────────────────────────────────────────
    for msg in st.session_state.chat_messages:
        t = msg.get("time", "")
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="sb-row-user">
              <div class="sb-bubble-wrap sb-bubble-wrap-user">
                <div class="sb-bubble sb-bubble-user">{msg['content']}</div>
                <div class="sb-time">{t}</div>
              </div>
              <div class="sb-mini-avatar sb-mini-avatar-user">👤</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="sb-row-ai">
              <div class="sb-mini-avatar sb-mini-avatar-ai">🤖</div>
              <div class="sb-bubble-wrap sb-bubble-wrap-ai">
                <div class="sb-bubble sb-bubble-ai">{msg['content']}</div>
                <div class="sb-time">{t}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close #sb-chat-messages

    # ── Suggestion chips (only when no history) ───────────────────────────────
    if not st.session_state.chat_messages:
        st.markdown("""
        <div id="sb-suggestions">
          <span class="sb-chip">Why this course first?</span>
          <span class="sb-chip">How long per day?</span>
          <span class="sb-chip">Most critical skill?</span>
          <span class="sb-chip">Will this boost my salary?</span>
        </div>
        """, unsafe_allow_html=True)

        # Clickable chip buttons (hidden label, styled via CSS override)
        cols = st.columns(4)
        chips = ["Why this course first?", "How long per day?", "Most critical skill?", "Will this boost my salary?"]
        for i, (col, chip) in enumerate(zip(cols, chips)):
            with col:
                if st.button(chip, key=f"chip_{i}", help=chip,
                             use_container_width=True):
                    st.session_state.chat_pending = chip
                    st.rerun()

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # ── Input row ─────────────────────────────────────────────────────────────
    col_inp, col_clr = st.columns([6, 1])
    with col_inp:
        user_q = st.chat_input("Ask about your path...", key="chat_input")
    with col_clr:
        if st.session_state.chat_messages:
            if st.button("🗑️", key="clear_chat", help="Clear conversation"):
                st.session_state.chat_messages = []
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # close #sb-chat-panel

    # ── Handle chip click ─────────────────────────────────────────────────────
    if st.session_state.chat_pending:
        user_q = st.session_state.chat_pending
        st.session_state.chat_pending = None

    # ── Process message ───────────────────────────────────────────────────────
    if user_q:
        st.session_state.chat_messages.append({
            "role": "user", "content": user_q, "time": _time_label()
        })
        sys_prompt = _build_system_prompt(
            from_role, to_role,
            rd.get("experience_years", "?"),
            gaps, pathway, total_hours, hours_saved
        )
        with st.spinner(""):
            answer = generate_response(user_q, sys_prompt)
        st.session_state.chat_messages.append({
            "role": "assistant", "content": answer, "time": _time_label()
        })
        st.rerun()
