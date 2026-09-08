"""
app.py
------
Streamlit front-end for the AI-Powered LaTeX TikZ Diagram Generator & Chatbot Studio.

Run with:
    streamlit run app.py
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional

import streamlit as st

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from granite_client import GraniteClient, GraniteClientError
from tikz_generator import TikZGenerator, format_output, DiagramResult
from prompt_templates import CATEGORIZED_PROMPT_SUGGESTIONS
from renderer import render_pdf, render_svg, is_latex_available, is_pdf2svg_available, is_inkscape_available
from validator import validate_tikz, format_validation_report
from auth import get_user_info

# Lazy import of page renderers to avoid circular issues
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
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LaTeX TikZ AI Diagram Generator & Chatbot Studio",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Modern Academic & Sleek Studio Interface
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main Background & Font */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #2563eb 100%);
        color: white;
        padding: 1.8rem 2rem;
        border-radius: 12px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
        margin-bottom: 1.5rem;
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
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
    .badge-demo { background-color: #78350f; color: #fef08a; border: 1px solid #d97706; }
    .badge-ok { background-color: #1e3a8a; color: #bfdbfe; border: 1px solid #3b82f6; }
    .badge-warn { background-color: #451a03; color: #fed7aa; border: 1px solid #f97316; }

    /* Cards & Containers */
    .studio-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .card-header {
        font-size: 1.05rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Code Blocks */
    .stCodeBlock {
        font-size: 0.84rem;
        border-radius: 8px;
    }

    /* Custom Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }

    /* Info & Status Boxes */
    .status-box {
        padding: 0.8rem 1rem;
        border-radius: 8px;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }
    .info-box { background: #eff6ff; border-left: 4px solid #3b82f6; color: #1e40af; }
    .success-box { background: #f0fdf4; border-left: 4px solid #22c55e; color: #166534; }
    .warn-box { background: #fffbeb; border-left: 4px solid #f59e0b; color: #92400e; }
    .error-box { background: #fef2f2; border-left: 4px solid #ef4444; color: #991b1b; }

    /* Chat Messages styling */
    .chat-tikz-preview {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 0.8rem;
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
        # Auth state
        "logged_in": False,
        "username": "",
        "auth_page": "login",   # "login" | "register" | "dashboard"
        # App state
        "diagram_result": None,
        "output": None,
        "pdf_bytes": None,
        "svg_content": None,
        "history": [],
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "👋 **Welcome to AI LaTeX TikZ Diagram Studio!**\n\n"
                    "I can help you build **publication-ready academic diagrams** "
                    "(Neural Networks, Transformers, ML Pipelines, Cloud Systems, Flowcharts, State Diagrams, UML) in clean TikZ code.\n\n"
                    "💡 **Try asking me:**\n"
                    "- *\"Create a CNN architecture with Conv, MaxPool, Dense, and Softmax layers\"*\n"
                    "- *\"Draw a Transformer encoder diagram with multi-head attention\"*\n"
                    "- *\"Design a microservices system with API Gateway, Order Service, and Database\"*\n\n"
                    "You can also pick a prompt suggestion from the sidebar!"
                ),
                "result": None,
            }
        ],
        "watsonx_api_key": os.getenv("WATSONX_API_KEY", ""),
        "watsonx_url": os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
        "watsonx_project_id": os.getenv("WATSONX_PROJECT_ID", ""),
        "granite_model_id": os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"),
        "injected_prompt": "",
        "active_tab": 0,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


_init_state()

# ---------------------------------------------------------------------------
# Generator Instance Helper
# ---------------------------------------------------------------------------
def _get_generator() -> TikZGenerator:
    """Return TikZGenerator configured with current credentials or smart fallback."""
    client = GraniteClient(
        api_key=st.session_state.get("watsonx_api_key"),
        base_url=st.session_state.get("watsonx_url"),
        project_id=st.session_state.get("watsonx_project_id"),
        model_id=st.session_state.get("granite_model_id"),
    )
    return TikZGenerator(client=client, auto_correct=True)

# ---------------------------------------------------------------------------
# Sidebar UI
# ---------------------------------------------------------------------------
def _render_sidebar() -> None:
    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg",
            width=80,
        )
        st.title("📐 TikZ AI Studio")
        st.caption("Publication-Ready Academic Diagrams")

        # ---- Logged-in user profile ----
        if st.session_state.get("logged_in"):
            username = st.session_state.get("username", "User")
            info = get_user_info(username) or {}
            avatar_letter = username[0].upper()
            st.markdown(
                f"""
                <div style="
                    display:flex; align-items:center; gap:0.7rem;
                    background: linear-gradient(135deg,#1e3a8a,#2563eb);
                    border-radius:10px; padding:0.7rem 1rem; margin-bottom:0.5rem;
                ">
                    <div style="
                        width:38px; height:38px; border-radius:50%;
                        background:#fff; color:#1e3a8a;
                        display:flex; align-items:center; justify-content:center;
                        font-weight:800; font-size:1.1rem; flex-shrink:0;
                    ">{avatar_letter}</div>
                    <div>
                        <div style="font-weight:700; color:#fff; font-size:0.9rem;">{username}</div>
                        <div style="color:#bfdbfe; font-size:0.72rem;">{info.get('email','')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🚪 Sign Out", use_container_width=True, key="logout_btn"):
                st.session_state["logged_in"] = False
                st.session_state["username"] = ""
                st.session_state["auth_page"] = "login"
                st.rerun()

        st.markdown("---")

        # --- Sidebar Settings Expander ---
        with st.expander("⚙️ API & Model Credentials", expanded=False):
            st.caption("Configure IBM watsonx.ai keys or run in Smart AI Engine mode.")

            api_key = st.text_input(
                "WATSONX_API_KEY",
                value=st.session_state["watsonx_api_key"],
                type="password",
                placeholder="Paste IBM Cloud IAM Key",
            )
            project_id = st.text_input(
                "WATSONX_PROJECT_ID",
                value=st.session_state["watsonx_project_id"],
                placeholder="e.g. 5d1f8...",
            )
            url = st.text_input(
                "WATSONX_URL",
                value=st.session_state["watsonx_url"],
            )
            model = st.selectbox(
                "Model",
                options=["ibm/granite-13b-instruct-v2", "ibm/granite-3-8b-instruct", "meta-llama/llama-3-70b-instruct"],
                index=0,
            )


            if st.button("💾 Save Credentials", use_container_width=True):
                st.session_state["watsonx_api_key"] = api_key
                st.session_state["watsonx_project_id"] = project_id
                st.session_state["watsonx_url"] = url
                st.session_state["granite_model_id"] = model
                st.success("Credentials saved!")
                st.rerun()

        # --- Categorized Prompt Suggestions ---
        st.markdown("### 💡 Prompt Suggestions")
        st.caption("Click any suggestion to fill input:")

        for category, prompts in CATEGORIZED_PROMPT_SUGGESTIONS.items():
            with st.expander(category, expanded=False):
                for p in prompts:
                    short_title = p if len(p) <= 60 else p[:57] + "..."
                    if st.button(f"📋 {short_title}", key=f"sugg_{hash(p)}", use_container_width=True):
                        st.session_state["injected_prompt"] = p
                        st.session_state["_trigger_gen"] = True

        st.markdown("---")

        # --- Rendering Engine Status ---
        st.markdown("### 🛠️ Compiler & Engine Status")
        latex_ok = is_latex_available()
        pdf2svg_ok = is_pdf2svg_available() or is_inkscape_available()

        client = GraniteClient(
            api_key=st.session_state["watsonx_api_key"],
            base_url=st.session_state["watsonx_url"],
            project_id=st.session_state["watsonx_project_id"],
        )
        engine_status = "🟢 watsonx.ai Granite" if client.is_configured() else "🟡 Smart AI Fallback"

        st.markdown(
            f"- **AI Engine:** `{engine_status}`\n"
            f"- **pdflatex:** `{'✅ Available' if latex_ok else '❌ Not Found'}`\n"
            f"- **SVG Engine:** `{'✅ Available' if pdf2svg_ok else '⚠️ PDF Fallback'}`"
        )

        if not latex_ok:
            st.caption("ℹ️ Install TeX Live / MiKTeX locally to compile direct PDF/SVG previews.")

        st.markdown("---")
        st.markdown("<small style='color: #64748b;'>Built with IBM Granite · Streamlit · TikZ</small>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header Banner
# ---------------------------------------------------------------------------
def _render_header() -> None:
    client = GraniteClient(
        api_key=st.session_state["watsonx_api_key"],
        base_url=st.session_state["watsonx_url"],
        project_id=st.session_state["watsonx_project_id"],
    )
    is_online = client.is_configured()
    latex_ok = is_latex_available()

    badge_ai = (
        '<span class="badge badge-online">🟢 watsonx.ai Granite LLM</span>'
        if is_online
        else '<span class="badge badge-demo">⚡ Smart AI Engine (Demo Mode)</span>'
    )
    badge_latex = (
        '<span class="badge badge-ok">✅ pdflatex Ready</span>'
        if latex_ok
        else '<span class="badge badge-warn">ℹ️ LaTeX Preview Pending</span>'
    )

    st.markdown(
        f"""
        <div class="hero-banner">
            <h1 class="hero-title">📐 AI LaTeX TikZ Diagram Studio</h1>
            <p class="hero-subtitle">Describe any academic, engineering, or architecture diagram in plain English — receive publication-ready LaTeX TikZ code instantly.</p>
            <div class="badge-container">
                {badge_ai}
                {badge_latex}
                <span class="badge badge-ok">📄 IEEE / ACM / Springer Ready</span>
                <span class="badge badge-ok">💬 AI Conversational Chatbot</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Helper: Render Diagram Output Tabs & Controls
# ---------------------------------------------------------------------------
def _render_diagram_result(result: DiagramResult, key_prefix: str = "main") -> None:
    """Render comprehensive tabs for LaTeX code, preamble, preview, and download."""
    output = format_output(result)

    st.subheader(f"📊 {output['title']}")

    # Warnings / Auto-correction notices
    if output["auto_corrected"]:
        st.markdown(
            '<div class="status-box warn-box">⚡ The generated code had minor validation issues. IBM Granite automatically corrected them.</div>',
            unsafe_allow_html=True,
        )
    for w in output.get("warnings", []):
        st.markdown(f'<div class="status-box info-box">ℹ️ {w}</div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "📄 LaTeX Code",
        "📦 Preamble",
        "💬 Explanation",
        "✅ Validation",
        "📖 Compile",
        "🖼 Preview & Render",
    ])

    with tabs[0]:
        st.markdown("**Complete Standalone TikZ Code** (Copy into Overleaf or TeX editor):")
        st.code(output["tikz_code"], language="latex", line_numbers=True)

    with tabs[1]:
        st.markdown("**Required Packages & Libraries:**")
        st.code(output["preamble_check"], language="latex")

    with tabs[2]:
        st.markdown("**Diagram Explanation:**")
        st.write(output["explanation"])

    with tabs[3]:
        st.markdown("**Validation Checklist:**")
        val_text = output["validation_report"]
        if "ERROR" in val_text:
            st.markdown(f'<div class="status-box error-box"><pre style="margin:0;">{val_text}</pre></div>', unsafe_allow_html=True)
        elif "WARNING" in val_text:
            st.markdown(f'<div class="status-box warn-box"><pre style="margin:0;">{val_text}</pre></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-box success-box"><pre style="margin:0;">{val_text}</pre></div>', unsafe_allow_html=True)

    with tabs[4]:
        st.markdown("**Compilation Guide:**")
        st.code(output["compile_instructions"], language=None)
        st.markdown("🌐 **Overleaf:** Paste into [Overleaf.com](https://overleaf.com) to compile online instantly.")

    with tabs[5]:
        st.markdown("**PDF & SVG Preview:**")
        if not is_latex_available():
            st.info("pdflatex is not detected on local server path. You can still copy the LaTeX code above or open in Overleaf.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📄 Render PDF", key=f"{key_prefix}_render_pdf", use_container_width=True):
                    with st.spinner("Compiling with pdflatex..."):
                        rr = render_pdf(output["tikz_code"])
                        if rr.success:
                            st.session_state["pdf_bytes"] = rr.pdf_bytes
                            st.success("PDF compiled successfully!")
                        else:
                            st.error(f"Render failed: {rr.message}")
            with c2:
                if st.button("🖼 Render SVG", key=f"{key_prefix}_render_svg", use_container_width=True):
                    with st.spinner("Converting TikZ to SVG..."):
                        rr = render_svg(output["tikz_code"])
                        if rr.success:
                            st.session_state["svg_content"] = rr.svg_content
                            st.success("SVG rendered!")
                        else:
                            st.error(f"SVG render failed: {rr.message}")

            pdf_b = st.session_state.get("pdf_bytes")
            svg_c = st.session_state.get("svg_content")

            if pdf_b:
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_b,
                    file_name="diagram.pdf",
                    mime="application/pdf",
                    key=f"{key_prefix}_dl_pdf",
                )
            if svg_c:
                st.download_button(
                    "⬇️ Download SVG",
                    data=svg_c,
                    file_name="diagram.svg",
                    mime="image/svg+xml",
                    key=f"{key_prefix}_dl_svg",
                )
                st.markdown("**SVG Visual Render:**")
                st.components.v1.html(svg_c, height=450, scrolling=True)

# ---------------------------------------------------------------------------
# TAB 1: 💬 AI Diagram Chatbot Studio
# ---------------------------------------------------------------------------
def _render_tab_chatbot() -> None:
    st.markdown("### 💬 AI Diagram Conversational Assistant")
    st.caption("Chat with AI to create, refine, and edit LaTeX TikZ diagrams step-by-step.")

    # Injected prompt notice or chip
    injected = st.session_state.get("injected_prompt")
    if injected:
        st.info(f"💡 Suggestion loaded: *\"{injected}\"* (Send message below)")

    # Display chat message history
    for idx, msg in enumerate(st.session_state["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("result"):
                with st.expander("🔍 View LaTeX Code & Preview Details", expanded=(idx == len(st.session_state["messages"]) - 1)):
                    _render_diagram_result(msg["result"], key_prefix=f"chat_{idx}")

    # Chat input
    user_input = st.chat_input("Describe your diagram or enter changes (e.g., 'Make nodes light blue')...")

    # If prompt was injected from sidebar button, use it
    if st.session_state.pop("_trigger_gen", False) and injected:
        user_input = injected
        st.session_state["injected_prompt"] = ""

    if user_input:
        # Append user message
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate Assistant response
        with st.chat_message("assistant"):
            with st.spinner("AI engine is generating your TikZ diagram..."):
                generator = _get_generator()
                last_result = st.session_state.get("diagram_result")

                try:
                    # Decide if this is a refinement instruction or new generation
                    is_refinement = False
                    if last_result and len(user_input.split()) < 15:
                        refine_keywords = ["color", "blue", "red", "green", "dashed", "arrow", "node", "add", "remove", "change", "vertical", "horizontal", "make", "style"]
                        if any(k in user_input.lower() for k in refine_keywords):
                            is_refinement = True

                    if is_refinement and last_result:
                        result = generator.refine(last_result, user_input)
                    else:
                        result = generator.generate(user_input)

                    st.session_state["diagram_result"] = result
                    st.session_state["output"] = format_output(result)
                    st.session_state["history"].insert(0, result)
                    st.session_state["history"] = st.session_state["history"][:10]

                    response_text = (
                        f"✨ **Generated {result.diagram_type.replace('_', ' ').title()} Diagram!**\n\n"
                        f"{result.explanation}\n\n"
                        f"Below is your publication-ready TikZ code. You can copy it, view the preamble, or render PDF/SVG!"
                    )

                    st.markdown(response_text)
                    _render_diagram_result(result, key_prefix=f"chat_new_{len(st.session_state['messages'])}")

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": response_text,
                        "result": result,
                    })

                except Exception as exc:
                    err_msg = f"❌ Generation error: {exc}"
                    st.error(err_msg)
                    logger.exception("Chat generation error")
                    st.session_state["messages"].append({"role": "assistant", "content": err_msg})

# ---------------------------------------------------------------------------
# TAB 2: ⚡ Quick Diagram Generator & Editor
# ---------------------------------------------------------------------------
def _render_tab_generator() -> None:
    st.markdown("### ⚡ Interactive Diagram Generator & Editor")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<div class="card-header">1 · Describe Your Diagram</div>', unsafe_allow_html=True)
        injected = st.session_state.get("injected_prompt", "")

        description = st.text_area(
            "Natural Language Description",
            value=injected if injected else "",
            height=140,
            placeholder="e.g. Create a machine learning data pipeline with Data Ingestion, Data Preprocessing, IBM Granite Model Training, and Model Evaluation.",
            key="gen_prompt_input",
        )

        b_col1, b_col2 = st.columns([1, 1])
        with b_col1:
            gen_clicked = st.button("🚀 Generate Diagram", type="primary", use_container_width=True)
        with b_col2:
            if st.button("🗑 Clear Session", use_container_width=True):
                st.session_state["diagram_result"] = None
                st.session_state["output"] = None
                st.session_state["pdf_bytes"] = None
                st.session_state["svg_content"] = None
                st.session_state["injected_prompt"] = ""
                st.rerun()

        if gen_clicked:
            if not description.strip():
                st.warning("Please enter a diagram description.")
            else:
                with st.spinner("Generating TikZ diagram..."):
                    try:
                        generator = _get_generator()
                        result = generator.generate(description)
                        st.session_state["diagram_result"] = result
                        st.session_state["output"] = format_output(result)
                        st.session_state["history"].insert(0, result)
                        st.session_state["history"] = st.session_state["history"][:10]
                        st.session_state["injected_prompt"] = ""
                    except Exception as exc:
                        st.error(f"Generation error: {exc}")

        # Refinement section if diagram exists
        result = st.session_state.get("diagram_result")
        if result:
            st.markdown("---")
            st.markdown('<div class="card-header">2 · Refine Diagram</div>', unsafe_allow_html=True)
            refinement = st.text_input(
                "Refinement Instruction",
                placeholder="e.g. 'Change node color to light blue' or 'Make arrows dashed'",
                key="studio_refine_input",
            )
            if st.button("🔧 Apply Refinement", use_container_width=True):
                if refinement.strip():
                    with st.spinner("Applying refinement..."):
                        try:
                            generator = _get_generator()
                            refined = generator.refine(result, refinement)
                            st.session_state["diagram_result"] = refined
                            st.session_state["output"] = format_output(refined)
                            st.session_state["history"].insert(0, refined)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Refinement error: {exc}")

    with col_right:
        st.markdown('<div class="card-header">Diagram Output & Live View</div>', unsafe_allow_html=True)
        result = st.session_state.get("diagram_result")
        if result:
            _render_diagram_result(result, key_prefix="studio")
        else:
            st.info("💡 Enter a diagram description on the left or select a prompt suggestion from the sidebar to generate code!")

# ---------------------------------------------------------------------------
# TAB 3: 🎨 Diagram Template Gallery
# ---------------------------------------------------------------------------
def _render_tab_gallery() -> None:
    st.markdown("### 🎨 Academic Diagram Template Gallery")
    st.caption("Select any publication-grade template to load and customize in the studio.")

    templates = [
        {
            "title": "🤖 Machine Learning Pipeline",
            "desc": "Sequential 4-stage ML pipeline (Ingestion -> Preprocessing -> Granite Model Training -> Evaluation).",
            "prompt": "Create a machine learning data pipeline with four stages: Data Ingestion, Data Preprocessing, IBM Granite Model Training, and Model Evaluation. Arrange horizontally with arrows.",
            "category": "ML / Data Science",
        },
        {
            "title": "🧠 Convolutional Neural Network (CNN)",
            "desc": "CNN architecture showing Input Image, Conv Layer 3x3, Max Pooling, Dense Layer, and Softmax output.",
            "prompt": "Draw a CNN architecture with Input Image (32x32x3), Conv Layer 3x3, Max Pooling layer (16x16), Dense FC layer (128 units), and Softmax Output.",
            "category": "Deep Learning",
        },
        {
            "title": "⚡ Transformer Encoder Layer",
            "desc": "Standard Transformer Encoder block with Positional Encoding, Multi-Head Attention, Add & Norm, and FFN.",
            "prompt": "Create a Transformer encoder diagram showing Input Embedding, Positional Encoding, Multi-Head Attention, Add & Norm, Feed Forward Network, and Add & Norm.",
            "category": "Deep Learning",
        },
        {
            "title": "☁️ Microservices Architecture",
            "desc": "Cloud microservices topology featuring Client App, API Gateway, User Service, Order Service, Payment Service, and DB Cluster.",
            "prompt": "Design a microservices system with API Gateway, User Service, Order Service, Payment Gateway, and PostgreSQL Database cluster.",
            "category": "System Design",
        },
        {
            "title": "🔄 User Authentication Flowchart",
            "desc": "Decision flowchart for login credentials validation, granting access, or showing authentication error.",
            "prompt": "Draw a decision flowchart for user authentication: Start -> Enter Credentials -> Is Credentials Valid? -> Grant Access / Show Error.",
            "category": "Flowcharts",
        },
        {
            "title": "📊 Traffic Light State Machine",
            "desc": "Finite state machine showing traffic light state transitions: Red -> Green -> Yellow -> Red with timers.",
            "prompt": "Draw a State Machine diagram for a traffic light with Red (40s), Green (30s), and Yellow (5s) states and transitions.",
            "category": "State Machines",
        },
    ]

    cols = st.columns(2)
    for idx, t in enumerate(templates):
        with cols[idx % 2]:
            st.markdown(
                f"""
                <div class="studio-card">
                    <div style="font-size:0.75rem; font-weight:700; color:#2563eb; text-transform:uppercase;">{t['category']}</div>
                    <div style="font-size:1.1rem; font-weight:600; color:#0f172a; margin:0.3rem 0;">{t['title']}</div>
                    <div style="font-size:0.85rem; color:#475569; margin-bottom:0.8rem;">{t['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"🚀 Load {t['title'].split()[-1]} Template", key=f"tmpl_{idx}", use_container_width=True):
                st.session_state["injected_prompt"] = t["prompt"]
                generator = _get_generator()
                result = generator.generate(t["prompt"])
                st.session_state["diagram_result"] = result
                st.session_state["output"] = format_output(result)
                st.session_state["history"].insert(0, result)
                st.success(f"Loaded '{t['title']}'! Check Generator or Chatbot tab.")
                st.rerun()

# ---------------------------------------------------------------------------
# TAB 4: 🛠️ TikZ Syntax Validator & Fixer
# ---------------------------------------------------------------------------
def _render_tab_validator() -> None:
    st.markdown("### 🛠️ Standalone TikZ Validator & Auto-Fixer")
    st.caption("Paste any raw TikZ / LaTeX code block to check syntax errors, missing packages, and auto-correct.")

    code_to_check = st.text_area(
        "Paste LaTeX / TikZ Code",
        height=240,
        placeholder="\\documentclass{standalone}\n\\usepackage{tikz}\n\\begin{document}\n\\begin{tikzpicture}\n  \\node (a) {Test};\n\\end{tikzpicture}\n\\end{document}",
    )

    if st.button("🔍 Validate TikZ Code", type="primary", use_container_width=True):
        if not code_to_check.strip():
            st.warning("Please paste LaTeX code to validate.")
        else:
            val_res = validate_tikz(code_to_check)
            report = format_validation_report(val_res)

            st.markdown("### Validation Report")
            if val_res.is_valid:
                st.success("✅ Valid TikZ Code! No errors found.")
            else:
                st.error("❌ Validation Issues Found!")

            st.code(report, language=None)

            if not val_res.is_valid:
                if st.button("⚡ Attempt Auto-Correction", use_container_width=True):
                    generator = _get_generator()
                    corrected, new_val, auto_c = generator._attempt_correction(code_to_check, val_res)
                    st.markdown("### Corrected Code:")
                    st.code(corrected, language="latex")
                    st.info("New Validation Status: " + ("✅ Valid" if new_val.is_valid else "⚠️ Remaining Errors"))

# ---------------------------------------------------------------------------
# TAB 5: 📜 History & Saved Gallery
# ---------------------------------------------------------------------------
def _render_tab_history() -> None:
    st.markdown("### 📜 Generation History")

    history: list[DiagramResult] = st.session_state.get("history", [])
    if not history:
        st.info("No diagrams generated in this session yet. Generate diagrams in Chatbot or Generator tabs to view history.")
        return

    for idx, item in enumerate(history):
        with st.expander(f"Diagram #{idx+1} — {item.diagram_type.replace('_', ' ').title()} ({item.description[:60]}...)"):
            st.markdown(f"**Prompt:** *{item.description}*")
            st.code(item.tikz_code[:500] + ("\n..." if len(item.tikz_code) > 500 else ""), language="latex")

            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"🔄 Restore #{idx+1} to Studio", key=f"hist_rst_{idx}", use_container_width=True):
                    st.session_state["diagram_result"] = item
                    st.session_state["output"] = format_output(item)
                    st.success(f"Restored #{idx+1} to Generator Studio!")
                    st.rerun()
            with c2:
                st.download_button(
                    f"⬇️ Download TeX #{idx+1}",
                    data=item.tikz_code,
                    file_name=f"diagram_{idx+1}.tex",
                    mime="text/x-tex",
                    key=f"hist_dl_{idx}",
                    use_container_width=True,
                )

# ---------------------------------------------------------------------------
# Main UI Entrypoint
# ---------------------------------------------------------------------------
def main() -> None:
    _init_state()

    # If not logged in → show login or register (no sidebar shown)
    if not st.session_state.get("logged_in"):
        auth_page = st.session_state.get("auth_page", "login")
        if auth_page == "register":
            _get_register_renderer()()
        else:
            _get_login_renderer()()
        return

    # ---- Authenticated: render full dashboard ----
    _render_sidebar()
    _render_header()

    tabs = st.tabs([
        "💬 AI Chatbot Studio",
        "⚡ Diagram Generator",
        "🎨 Template Gallery",
        "🛠️ TikZ Validator",
        "📜 History",
    ])

    with tabs[0]:
        _render_tab_chatbot()

    with tabs[1]:
        _render_tab_generator()

    with tabs[2]:
        _render_tab_gallery()

    with tabs[3]:
        _render_tab_validator()

    with tabs[4]:
        _render_tab_history()


if __name__ == "__main__":
    main()
