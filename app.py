"""
app.py
------
Streamlit front-end for IBM Watson Assistant & Granite AI Chatbot Dashboard.

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
    page_title="IBM Watson Assistant & Granite AI Chatbot Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — Hide Sidebar completely & Modern Premium Aesthetic
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Remove Streamlit sidebar and toggle button completely */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    .main .block-container {
        max-width: 1200px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    /* Main Background & Fonts */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #2563eb 100%);
        color: white;
        padding: 1.8rem 2rem;
        border-radius: 14px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .hero-left {
        flex: 1;
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #93c5fd;
        margin-top: 0.4rem;
        margin-bottom: 0.8rem;
    }

    /* Status Badges */
    .badge-container {
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-top: 0.6rem;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-online { background-color: #064e3b; color: #a7f3d0; border: 1px solid #059669; }
    .badge-ibm { background-color: #1e3a8a; color: #bfdbfe; border: 1px solid #3b82f6; }
    .badge-au { background-color: #581c87; color: #e9d5ff; border: 1px solid #a855f7; }

    /* Information Cards */
    .info-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
    .info-card-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .info-item {
        background: #f1f5f9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2563eb;
    }
    .info-item-title {
        font-weight: 700;
        color: #1e293b;
        font-size: 0.92rem;
        margin-bottom: 0.3rem;
    }
    .info-item-desc {
        font-size: 0.84rem;
        color: #475569;
        line-height: 1.4;
    }

    /* Container for Watson Chatbot */
    .chatbot-section {
        background: #ffffff;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
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
        "watsonx_api_key": os.getenv("WATSONX_API_KEY", ""),
        "watsonx_url": os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
        "watsonx_project_id": os.getenv("WATSONX_PROJECT_ID", ""),
        "granite_model_id": os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"),
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "👋 **Welcome to IBM Watson & Granite AI Assistant Studio!**\n\n"
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
# Header Banner
# ---------------------------------------------------------------------------
def _render_header() -> None:
    username = st.session_state.get("username", "User")
    info = get_user_info(username) or {}
    avatar_letter = username[0].upper() if username else "U"

    col_title, col_user = st.columns([3.2, 1])

    with col_title:
        st.markdown(
            f"""
            <div class="hero-banner">
                <div class="hero-left">
                    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.4rem;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg" style="height:26px; filter: brightness(0) invert(1);" />
                        <span style="font-weight:700; font-size:1.2rem; color:#bfdbfe;">IBM Watson Assistant</span>
                    </div>
                    <h1 class="hero-title">🤖 AI Chatbot Dashboard</h1>
                    <p class="hero-subtitle">Interactive Conversational Assistant powered by IBM Watson Assistant & IBM Granite AI.</p>
                    <div class="badge-container">
                        <span class="badge badge-online">🟢 Watson Integration Active</span>
                        <span class="badge badge-ibm">⚡ Watson Assistant v2</span>
                        <span class="badge badge-au">🌏 Region: au-syd</span>
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
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                padding: 1rem;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            ">
                <div style="display:flex; align-items:center; gap:0.7rem;">
                    <div style="
                        width:42px; height:42px; border-radius:50%;
                        background: linear-gradient(135deg,#1e3a8a,#2563eb);
                        color:#ffffff; display:flex; align-items:center;
                        justify-content:center; font-weight:800; font-size:1.2rem;
                    ">{avatar_letter}</div>
                    <div>
                        <div style="font-weight:700; color:#0f172a; font-size:0.95rem;">{username}</div>
                        <div style="color:#64748b; font-size:0.75rem;">{info.get('email', 'Logged in User')}</div>
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
# Chatbot Information Component
# ---------------------------------------------------------------------------
def _render_chatbot_info() -> None:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-header">
                💡 IBM Watson Assistant Chatbot Information & Capabilities
            </div>
            <div style="color: #475569; font-size: 0.92rem; line-height: 1.6;">
                Welcome to the official <b>IBM Watson Assistant Chatbot Studio</b>. This AI chatbot integration brings enterprise-grade conversational AI capabilities directly into your dashboard. Ask questions, request LaTeX TikZ diagram code, explore AI workflows, or interact naturally with Watson Assistant.
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-item-title">🧠 Natural Language Understanding</div>
                    <div class="info-item-desc">Understands intent, entity extraction, and contextual conversations using IBM's industry-leading NLU engine.</div>
                </div>
                <div class="info-item">
                    <div class="info-item-title">⚡ Instant Assistance</div>
                    <div class="info-item-desc">Real-time answers to queries, code generation, troubleshooting guidance, and interactive multi-turn dialog.</div>
                </div>
                <div class="info-item">
                    <div class="info-item-title">🔒 Enterprise Integration</div>
                    <div class="info-item-desc">Hosted securely on IBM Cloud Sydney region (<code>au-syd</code>) with custom integration parameters.</div>
                </div>
                <div class="info-item">
                    <div class="info-item-title">📐 Academic & Code Support</div>
                    <div class="info-item-desc">Generates LaTeX TikZ diagrams, algorithmic explanations, flowcharts, and system architecture summaries.</div>
                </div>
            </div>

            <div style="margin-top: 1.2rem; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 0.8rem 1rem; font-size: 0.84rem; color: #1e40af;">
                ℹ️ <b>Integration Details:</b><br/>
                • <b>Integration ID:</b> <code>26d3863c-6db9-4b25-a018-f114f6d5d4de</code><br/>
                • <b>Region:</b> <code>https://integrations.au-syd.assistant.watson.appdomain.cloud</code><br/>
                • <b>Service Instance ID:</b> <code>785a5ddf-e0d3-41ec-a953-10230a5bd29d</code>
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
    st.caption("Official IBM Watson Assistant webchat widget. If blocked by browser extensions, use the interactive AI Chat tab below.")

    watson_script_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <style>
        body {
          margin: 0;
          padding: 0;
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          background-color: #f8fafc;
        }
        #watson-chat-wrapper {
          width: 100%;
          height: 600px;
          border-radius: 12px;
          border: 1px solid #cbd5e1;
          background: #ffffff;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
          position: relative;
          overflow: hidden;
        }
        #loading-msg {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          color: #475569;
          font-size: 0.95rem;
          text-align: center;
        }
        .spinner {
          border: 4px solid #e2e8f0;
          border-top: 4px solid #2563eb;
          border-radius: 50%;
          width: 36px;
          height: 36px;
          animation: spin 1s linear infinite;
          margin: 0 auto 12px auto;
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
          <div>Loading IBM Watson Assistant Chatbot...</div>
        </div>
      </div>

      <script>
        window.watsonAssistantChatOptions = {
          integrationID: "26d3863c-6db9-4b25-a018-f114f6d5d4de",
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
            document.getElementById('loading-msg').innerHTML = '<div style="color:#dc2626; font-weight:600;">⚠️ IBM Watson WebChat script could not be loaded.</div><div style="font-size:0.82rem; color:#64748b; margin-top:4px;">Please check network/ad-blocker settings or use the interactive AI Chat tab below.</div>';
          };
          document.head.appendChild(t);
        }, 500);
      </script>
    </body>
    </html>
    """

    st.components.v1.html(watson_script_html, height=620, scrolling=True)

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
