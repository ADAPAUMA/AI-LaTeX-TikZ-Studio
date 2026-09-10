"""
app_pages/login.py
------------------
Renders the 3D Glassmorphic login page for the IBM Watson & TikZ AI Studio.
Called from app.py when st.session_state["logged_in"] is False
and st.session_state["auth_page"] == "login".
"""

import streamlit as st
from auth import verify_user


def render_login_page() -> None:
    """Render the 3D Glassmorphic login form."""

    # ── Centred 3D card layout ──────────────────────────────────────────────────
    _, col, _ = st.columns([1, 1.6, 1])

    with col:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 58, 138, 0.8) 50%, rgba(99, 102, 241, 0.7) 100%);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 20px;
                padding: 2.5rem 2.4rem 2rem;
                margin-bottom: 1.5rem;
                text-align: center;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 35px rgba(99, 102, 241, 0.3);
            ">
                <div style="font-size: 3rem; margin-bottom: 0.4rem; filter: drop-shadow(0 0 15px rgba(59,130,246,0.6));">🤖</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em; text-shadow: 0 4px 12px rgba(0,0,0,0.4);">
                    IBM Watson & TikZ 3D Studio
                </div>
                <div style="font-size: 0.92rem; color: #93c5fd; margin-top: 0.5rem; line-height: 1.5;">
                    Sign in to access your interactive 3D AI Chatbot Dashboard & Diagram Generator
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<h4 style='color:#f8fafc; font-weight:700;'>Sign In</h4>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("🔑 Sign In", use_container_width=True, type="primary")

        if submitted:
            if not username.strip() or not password.strip():
                st.warning("Please enter both username and password.")
            elif verify_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username.strip().lower()
                st.session_state["auth_page"] = "dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

        st.markdown("---")
        st.markdown(
            "<div style='text-align:center; font-size:0.9rem; color:#cbd5e1;'>Don't have an account?</div>",
            unsafe_allow_html=True,
        )
        if st.button("📝 Create Account", use_container_width=True):
            st.session_state["auth_page"] = "register"
            st.rerun()

        # Demo / guest shortcut — lets the app run without credentials
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🚀 Quick Demo (skip sign-in)"):
            st.caption(
                "Use the demo account to explore the 3D studio immediately. "
                "Your session will be active as guest."
            )
            if st.button("▶ Enter as Guest", use_container_width=True):
                st.session_state["logged_in"] = True
                st.session_state["username"] = "guest"
                st.session_state["auth_page"] = "dashboard"
                st.rerun()
