"""
chat.py — SkillBridge floating AI chat agent
Separated from app.py for clean code structure.
"""
import json
import urllib.request
import streamlit as st


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


def render_chat(from_role, to_role, rd, gaps, pathway, total_hours, hours_saved, is_dark):
    """Render the full floating chat UI + handle message submission."""
    _panel_bg   = "#18181b" if is_dark else "#ffffff"
    _panel_bdr  = "#333"    if is_dark else "#e2e8f0"
    _msg_user   = "#2563eb"
    _msg_ai_bg  = "#27272a" if is_dark else "#f1f5f9"
    _msg_ai_txt = "#e4e4e7" if is_dark else "#1e293b"
    _input_bg   = "#27272a" if is_dark else "#f8fafc"
    _input_bdr  = "#444"    if is_dark else "#cbd5e1"
    _input_txt  = "#fff"    if is_dark else "#0f172a"

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
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
        display:flex; flex-direction:column; gap:10px; max-height:360px;
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
    #fab-fixed-wrapper {{
        position:fixed !important; bottom:28px !important;
        right:28px !important; z-index:10000 !important;
    }}
    #fab-fixed-wrapper button {{
        width:58px !important; height:58px !important;
        border-radius:50% !important;
        background:linear-gradient(135deg,#6366f1,#0ea5e9) !important;
        border:none !important; font-size:22px !important;
        padding:0 !important; box-shadow:0 4px 20px rgba(99,102,241,.6) !important;
        color:#fff !important; font-weight:700 !important;
    }}
    #fab-fixed-wrapper button:hover {{
        transform:scale(1.1) !important;
        box-shadow:0 6px 28px rgba(99,102,241,.8) !important;
    }}
    @media(max-width:480px) {{
        #chat-panel{{ width:calc(100vw - 32px); right:16px; bottom:90px; }}
        #fab-fixed-wrapper{{ right:16px !important; bottom:16px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── FAB toggle ────────────────────────────────────────────────────────────
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    fab_label = "✕" if st.session_state.chat_open else "💬"
    st.markdown('<div id="fab-fixed-wrapper">', unsafe_allow_html=True)
    if st.button(fab_label, key="fab_toggle", help="Ask AI about your learning path"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.chat_open:
        return

    # ── Chat panel HTML ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div id="chat-panel">
        <div id="chat-header">
            <svg width="32" height="32" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
              <rect x="7" y="10" width="22" height="16" rx="4" fill="white" fill-opacity="0.95"/>
              <circle cx="13" cy="17" r="2.5" fill="#6366f1"/>
              <circle cx="23" cy="17" r="2.5" fill="#6366f1"/>
              <circle cx="14" cy="16" r="0.8" fill="white"/>
              <circle cx="24" cy="16" r="0.8" fill="white"/>
              <rect x="13" y="21" width="10" height="2" rx="1" fill="#0ea5e9"/>
              <line x1="18" y1="10" x2="18" y2="6" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="18" cy="5" r="1.8" fill="#0ea5e9"/>
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
            <div class="cm-ai">👋 Hi! I know your full learning path for
            <b>{from_role} → {to_role}</b>.<br>
            Ask me anything about your roadmap, gaps, or timeline!</div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.chat_messages:
        cls = "cm-user" if msg["role"] == "user" else "cm-ai"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close #chat-messages

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

    # ── Input row ─────────────────────────────────────────────────────────────
    col_inp, col_clr = st.columns([5, 1])
    with col_inp:
        user_q = st.chat_input("Ask about your path...", key="chat_input")
    with col_clr:
        if st.session_state.chat_messages:
            if st.button("🗑", key="clear_chat", help="Clear chat"):
                st.session_state.chat_messages = []
                st.rerun()

    if user_q:
        st.session_state.chat_messages.append({"role": "user", "content": user_q})
        sys_prompt = _build_system_prompt(
            from_role, to_role,
            rd.get("experience_years", "?"),
            gaps, pathway, total_hours, hours_saved
        )
        with st.spinner("🤖 Thinking..."):
            answer = generate_response(user_q, sys_prompt)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.rerun()
