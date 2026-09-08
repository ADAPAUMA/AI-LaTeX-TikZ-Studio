"""
app_pages/login.py
------------------
Renders the login page for the TikZ AI Studio.
Called from app.py when st.session_state["logged_in"] is False
and st.session_state["auth_page"] == "login".
"""

import streamlit as st
from auth import verify_user


def render_login_page() -> None:
    """Render the full-page login form."""

    # ── Centred card layout ──────────────────────────────────────────────────
    _, col, _ = st.columns([1, 1.6, 1])

    with col:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #2563eb 100%);
                border-radius: 14px;
                padding: 2.2rem 2.4rem 1.8rem;
                margin-bottom: 1.5rem;
                text-align: center;
            ">
                <div style="font-size: 2.4rem; margin-bottom: 0.3rem;">📐</div>
                <div style="font-size: 1.55rem; font-weight: 700; color: #fff; letter-spacing: -0.02em;">
                    AI LaTeX TikZ Studio
                </div>
                <div style="font-size: 0.88rem; color: #93c5fd; margin-top: 0.4rem;">
                    Sign in to generate publication-ready academic diagrams
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Sign In")

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
            "<div style='text-align:center; font-size:0.88rem;'>Don't have an account?</div>",
            unsafe_allow_html=True,
        )
        if st.button("📝 Create Account", use_container_width=True):
            st.session_state["auth_page"] = "register"
            st.rerun()

        # Demo / guest shortcut — lets the app run without credentials
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🚀 Quick Demo (skip sign-in)"):
            st.caption(
                "Use the demo account to explore the studio immediately. "
                "Your diagrams won't be saved between sessions."
            )
            if st.button("▶ Enter as Guest", use_container_width=True):
                st.session_state["logged_in"] = True
                st.session_state["username"] = "guest"
                st.session_state["auth_page"] = "dashboard"
                st.rerun()
