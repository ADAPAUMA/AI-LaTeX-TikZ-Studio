"""
app.py
------
Streamlit front-end for IBM Watson Assistant & Granite AI Chatbot Dashboard.
Enhanced with 3D Glassmorphism, Micro-Animations, and Premium Visual Design.

Run with:
    streamlit run app.py
"""

import logging
import sys
import os
from pathlib import Path

import streamlit as st

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from granite_client import GraniteClient
from tikz_generator import TikZGenerator, format_output
from auth import get_user_info

# Lazy import of page renderers
def _get_login_renderer():
    from app_pages.login import render_login_page
    return render_login_page

def _get_register_renderer():
    from app_pages.register import render_register_page
    return render_register_page

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration — Sidebar completely removed / collapsed
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="IBM Watson Assistant & Granite AI 3D Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — Ultra-Premium 3D Glassmorphism, Neon Glow & Animations
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Hide Streamlit sidebar and toggle button completely */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    .main .block-container {
        max-width: 1240px;
        padding-top: 1rem;
        padding-bottom: 2.5rem;
    }

    /* Global App Styling */
    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #090d16 50%, #020617 100%);
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
        color: #f8fafc;
    }

    /* Keyframe Animations */
    @keyframes float3d {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-8px) rotate(1deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    @keyframes glowPulse {
        0% { box-shadow: 0 0 15px rgba(37, 99, 235, 0.4); }
        50% { box-shadow: 0 0 35px rgba(99, 102, 241, 0.8); }
        100% { box-shadow: 0 0 15px rgba(37, 99, 235, 0.4); }
    }
    @keyframes statusPulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* 3D Glassmorphic Hero Banner */
    .hero-banner-3d {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 58, 138, 0.75) 50%, rgba(99, 102, 241, 0.65) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.8), 0 0 30px rgba(59, 130, 246, 0.2);
        margin-bottom: 1.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1.2rem;
        position: relative;
        overflow: hidden;
        animation: float3d 6s ease-in-out infinite;
    }
    .hero-banner-3d::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 60%);
        pointer-events: none;
    }
    .hero-title-3d {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #ffffff 0%, #93c5fd 60%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .hero-subtitle-3d {
        font-size: 1.02rem;
        color: #cbd5e1;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        max-width: 650px;
        line-height: 1.5;
    }

    /* 3D Glowing Status Badges */
    .badge-container-3d {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 0.8rem;
    }
    .badge-3d {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 1rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .badge-3d:hover {
        transform: translateY(-3px) scale(1.04);
    }
    .badge-online-3d {
        background: rgba(6, 78, 59, 0.8);
        color: #6ee7b7;
        border: 1px solid #10b981;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
    }
    .badge-online-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        animation: statusPulse 2s infinite;
    }
    .badge-ibm-3d {
        background: rgba(30, 58, 138, 0.8);
        color: #93c5fd;
        border: 1px solid #3b82f6;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
    }
    .badge-au-3d {
        background: rgba(88, 28, 135, 0.8);
        color: #f0abfc;
        border: 1px solid #c084fc;
        box-shadow: 0 0 15px rgba(192, 132, 252, 0.4);
    }

    /* 3D Glassmorphism Cards */
    .glass-card-3d {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        padding: 1.8rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin-bottom: 1.8rem;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .glass-card-3d:hover {
        transform: translateY(-6px) rotateX(1deg);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 30px 60px -15px rgba(99, 102, 241, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    .glass-card-header {
        font-size: 1.25rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        letter-spacing: -0.01em;
    }

    /* 3D Grid & Stats Cards */
    .grid-3d {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1.2rem;
        margin-top: 1.2rem;
    }
    .card-item-3d {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        padding: 1.2rem 1.4rem;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #6366f1;
        transition: all 0.3s ease;
    }
    .card-item-3d:hover {
        transform: translateY(-4px) scale(1.02);
        background: linear-gradient(145deg, rgba(30, 58, 138, 0.6) 0%, rgba(15, 23, 42, 0.95) 100%);
        border-left-color: #a855f7;
        box-shadow: 0 12px 25px -5px rgba(99, 102, 241, 0.3);
    }
    .card-item-title-3d {
        font-weight: 700;
        color: #f1f5f9;
        font-size: 0.96rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .card-item-desc-3d {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* Glowing Code Box */
    .integration-box-3d {
        margin-top: 1.5rem;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #a5b4fc;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
    }
    .integration-box-3d code {
        color: #38bdf8;
        font-weight: 600;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 0.5rem;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        border-radius: 10px;
        color: #94a3b8;
        font-weight: 700;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.5) !important;
    }

    /* Custom Buttons */
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "logged_in": False,
        "username": "",
        "auth_page": "login",
        "watsonx_api_key": os.getenv("WATSONX_API_KEY", "h4pKEjuby26VmDxdvgE1w8MlF3zU1u7h4nal1J-s8zUe"),
        "watsonx_url": os.getenv("WATSONX_URL", "https://api.au-syd.assistant.watson.cloud.ibm.com/instances/785a5ddf-e0d3-41ec-a953-10230a5bd29d"),
        "watsonx_project_id": os.getenv("WATSONX_PROJECT_ID", "785a5ddf-e0d3-41ec-a953-10230a5bd29d"),
        "granite_model_id": os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"),
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "👋 **Welcome to IBM Watson Assistant & Granite AI 3D Studio!**\n\n"
                    "I am your AI Chatbot. How can I help you today? Ask me any questions, request LaTeX TikZ diagram code, or explore machine learning architecture!"
                ),
            }
        ],
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

_init_state()

# ---------------------------------------------------------------------------
# Header Banner with 3D Glassmorphism
# ---------------------------------------------------------------------------
def _render_header() -> None:
    username = st.session_state.get("username", "User")
    info = get_user_info(username) or {}
    avatar_letter = username[0].upper() if username else "U"

    col_title, col_user = st.columns([3.2, 1])

    with col_title:
        st.markdown(
            f"""
            <div class="hero-banner-3d">
                <div style="position:relative; z-index:2;">
                    <div style="display:flex; align-items:center; gap:0.7rem; margin-bottom:0.5rem;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg" style="height:28px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4)) brightness(0) invert(1);" />
                        <span style="font-weight:800; font-size:1.25rem; color:#bfdbfe; letter-spacing:-0.01em;">IBM Watson Assistant</span>
                    </div>
                    <h1 class="hero-title-3d">🤖 AI Chatbot 3D Studio</h1>
                    <p class="hero-subtitle-3d">Next-generation conversational AI powered by IBM Watson Assistant & IBM Granite LLM.</p>
                    <div class="badge-container-3d">
                        <span class="badge-3d badge-online-3d">
                            <span class="badge-online-dot"></span> Watson Integration Active
                        </span>
                        <span class="badge-3d badge-ibm-3d">⚡ Integration: bad150a7...</span>
                        <span class="badge-3d badge-au-3d">🌏 Region: au-syd</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_user:
        st.markdown(
            f"""
            <div style="
                background: rgba(15, 23, 42, 0.85);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
                padding: 1.2rem;
                box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);
                display: flex;
                flex-direction: column;
                gap: 0.6rem;
            ">
                <div style="display:flex; align-items:center; gap:0.8rem;">
                    <div style="
                        width:46px; height:46px; border-radius:50%;
                        background: linear-gradient(135deg,#3b82f6,#8b5cf6);
                        color:#ffffff; display:flex; align-items:center;
                        justify-content:center; font-weight:800; font-size:1.3rem;
                        box-shadow: 0 0 20px rgba(139, 92, 246, 0.5);
                    ">{avatar_letter}</div>
                    <div>
                        <div style="font-weight:800; color:#f8fafc; font-size:1rem;">{username}</div>
                        <div style="color:#94a3b8; font-size:0.78rem;">{info.get('email', 'Logged in User')}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚪 Sign Out", use_container_width=True, key="hdr_signout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["auth_page"] = "login"
            st.rerun()

# ---------------------------------------------------------------------------
# 3D Chatbot Information Component
# ---------------------------------------------------------------------------
def _render_chatbot_info() -> None:
    st.markdown(
        """
        <div class="glass-card-3d">
            <div class="glass-card-header">
                💡 IBM Watson Assistant 3D Capabilities & Overview
            </div>
            <div style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;">
                Welcome to the <b>IBM Watson Assistant 3D Studio</b>. This AI chatbot integration brings enterprise-grade conversational AI capabilities directly into your dashboard. Ask questions, request LaTeX TikZ diagram code, explore AI workflows, or interact naturally with Watson Assistant.
            </div>
            
            <div class="grid-3d">
                <div class="card-item-3d">
                    <div class="card-item-title-3d">🧠 Natural Language Understanding</div>
                    <div class="card-item-desc-3d">Understands intent, entity extraction, and contextual multi-turn dialogue using IBM NLU.</div>
                </div>
                <div class="card-item-3d">
                    <div class="card-item-title-3d">⚡ Instant Assistance</div>
                    <div class="card-item-desc-3d">Real-time code generation, academic explanations, troubleshooting guidance, and instant solutions.</div>
                </div>
                <div class="card-item-3d">
                    <div class="card-item-title-3d">🔒 Enterprise Cloud Security</div>
                    <div class="card-item-desc-3d">Hosted securely on IBM Cloud Sydney region (<code>au-syd</code>) with high-availability API endpoints.</div>
                </div>
                <div class="card-item-3d">
                    <div class="card-item-title-3d">📐 TikZ & LaTeX Studio Engine</div>
                    <div class="card-item-desc-3d">Generates publication-ready LaTeX TikZ code, neural net diagrams, flowcharts, and vector previews.</div>
                </div>
            </div>

            <div class="integration-box-3d">
                ⚡ <b>Live Integration Status:</b><br/>
                • <b>Integration ID:</b> <code>bad150a7-6816-40db-9249-10be96c432f4</code><br/>
                • <b>Region:</b> <code>https://integrations.au-syd.assistant.watson.appdomain.cloud</code><br/>
                • <b>Service Instance ID:</b> <code>785a5ddf-e0d3-41ec-a953-10230a5bd29d</code><br/>
                • <b>API Endpoint:</b> <code>https://api.au-syd.assistant.watson.cloud.ibm.com/instances/785a5ddf-e0d3-41ec-a953-10230a5bd29d</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# IBM Watson Assistant Interactive WebChat Widget
# ---------------------------------------------------------------------------
def _render_watson_chatbot() -> None:
    st.markdown("### 🤖 IBM Watson Assistant WebChat")
    st.caption("Official IBM Watson Assistant webchat widget. Integration ID: bad150a7-6816-40db-9249-10be96c432f4")

    watson_script_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <style>
        body {
          margin: 0;
          padding: 0;
          font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
          background-color: transparent;
        }
        #watson-chat-wrapper {
          width: 100%;
          height: 610px;
          border-radius: 16px;
          border: 1px solid rgba(255, 255, 255, 0.15);
          background: #ffffff;
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(59, 130, 246, 0.25);
          position: relative;
          overflow: hidden;
        }
        #loading-msg {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          color: #0f172a;
          font-size: 1rem;
          font-weight: 600;
          text-align: center;
        }
        .spinner {
          border: 4px solid #e2e8f0;
          border-top: 4px solid #3b82f6;
          border-radius: 50%;
          width: 40px;
          height: 40px;
          animation: spin 1s linear infinite;
          margin: 0 auto 14px auto;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>
    </head>
    <body>
      <div id="watson-chat-wrapper">
        <div id="loading-msg">
          <div class="spinner"></div>
          <div>Loading IBM Watson Assistant Chatbot (bad150a7...)...</div>
        </div>
      </div>

      <script>
        window.watsonAssistantChatOptions = {
          integrationID: "bad150a7-6816-40db-9249-10be96c432f4",
          region: "https://integrations.au-syd.assistant.watson.appdomain.cloud",
          serviceInstanceID: "785a5ddf-e0d3-41ec-a953-10230a5bd29d",
          element: document.getElementById('watson-chat-wrapper'),
          showLauncher: false,
          openChatByDefault: true,
          onLoad: async (instance) => {
            document.getElementById('loading-msg').style.display = 'none';
            await instance.render();
          }
        };
        setTimeout(function(){
          const t=document.createElement('script');
          t.src="https://web-chat.global.assistant.watson.appdomain.cloud/versions/" + (window.watsonAssistantChatOptions.clientVersion || 'latest') + "/WatsonAssistantChatEntry.js";
          t.onerror = function() {
            document.getElementById('loading-msg').innerHTML = '<div style="color:#dc2626; font-weight:700;">⚠️ IBM Watson WebChat script could not be loaded.</div><div style="font-size:0.85rem; color:#64748b; margin-top:6px;">Please check network/ad-blocker settings or use the interactive AI Chat tab below.</div>';
          };
          document.head.appendChild(t);
        }, 500);
      </script>
    </body>
    </html>
    """

    st.components.v1.html(watson_script_html, height=630, scrolling=True)

# ---------------------------------------------------------------------------
# Native Interactive AI Chatbot (IBM Granite AI Powered)
# ---------------------------------------------------------------------------
def _render_native_ai_chatbot() -> None:
    st.markdown("### 💬 Interactive AI Chat Studio (Granite AI Engine)")
    st.caption("Ask questions, request TikZ diagram code, or chat with IBM Granite AI directly.")

    for idx, msg in enumerate(st.session_state["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("result"):
                with st.expander("🔍 View Generated Diagram Details"):
                    st.code(msg["result"].tikz_code, language="latex")

    user_input = st.chat_input("Ask IBM Granite AI a question or request a diagram...")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("IBM Granite AI is processing your request..."):
                client = GraniteClient(
                    api_key=st.session_state.get("watsonx_api_key"),
                    base_url=st.session_state.get("watsonx_url"),
                    project_id=st.session_state.get("watsonx_project_id"),
                    model_id=st.session_state.get("granite_model_id"),
                )
                generator = TikZGenerator(client=client, auto_correct=True)

                try:
                    # If prompt looks like diagram request
                    if any(k in user_input.lower() for k in ["diagram", "tikz", "draw", "flowchart", "architecture", "pipeline", "cnn", "transformer", "network"]):
                        result = generator.generate(user_input)
                        output = format_output(result)
                        resp = f"✨ **IBM Granite AI Generated Diagram!**\n\n{result.explanation}\n\n```latex\n{result.tikz_code}\n```"
                        st.markdown(resp)
                        st.session_state["messages"].append({"role": "assistant", "content": resp, "result": result})
                    else:
                        resp = f"🤖 **IBM Granite AI Answer:**\n\nI processed your query: *\"{user_input}\"*\n\nIBM Granite AI is ready to assist you with academic research, architecture design, and LaTeX diagram generation."
                        st.markdown(resp)
                        st.session_state["messages"].append({"role": "assistant", "content": resp})

                except Exception as exc:
                    err_msg = f"❌ AI Assistant error: {exc}"
                    st.error(err_msg)
                    st.session_state["messages"].append({"role": "assistant", "content": err_msg})

# ---------------------------------------------------------------------------
# Main UI Entrypoint
# ---------------------------------------------------------------------------
def main() -> None:
    _init_state()

    # If not logged in → show login or register
    if not st.session_state.get("logged_in"):
        auth_page = st.session_state.get("auth_page", "login")
        if auth_page == "register":
            _get_register_renderer()()
        else:
            _get_login_renderer()()
        return

    # ---- Authenticated Dashboard ----
    _render_header()
    _render_chatbot_info()

    # Tabs for Chatbot Interfaces
    chat_tabs = st.tabs([
        "🤖 IBM Watson WebChat",
        "💬 Interactive AI Chat Studio (Granite AI)",
    ])

    with chat_tabs[0]:
        _render_watson_chatbot()

    with chat_tabs[1]:
        _render_native_ai_chatbot()


if __name__ == "__main__":
    main()
