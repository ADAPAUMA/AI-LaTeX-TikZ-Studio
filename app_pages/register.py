"""
app_pages/register.py
---------------------
Renders the registration page for the TikZ AI Studio.
Called from app.py when st.session_state["auth_page"] == "register".
"""

import streamlit as st
from auth import register_user, user_exists


def render_register_page() -> None:
    """Render the full-page account creation form."""

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
                    Create an Account
                </div>
                <div style="font-size: 0.88rem; color: #93c5fd; margin-top: 0.4rem;">
                    Join AI LaTeX TikZ Studio
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### New Account")

        with st.form("register_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Choose a username (min 3 chars)")
            email    = st.text_input("Email (optional)", placeholder="you@university.edu")
            password = st.text_input("Password", type="password", placeholder="At least 6 characters")
            confirm  = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
            submitted = st.form_submit_button("✅ Create Account", use_container_width=True, type="primary")

        if submitted:
            username = username.strip()
            password = password.strip()
            confirm  = confirm.strip()

            if not username or not password:
                st.warning("Username and password are required.")
            elif len(username) < 3:
                st.warning("Username must be at least 3 characters.")
            elif len(password) < 6:
                st.warning("Password must be at least 6 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif user_exists(username):
                st.error(f"Username '{username}' is already taken. Please choose another.")
            else:
                ok = register_user(username, password, email)
                if ok:
                    st.success("🎉 Account created! You can now sign in.")
                    st.session_state["auth_page"] = "login"
                    st.rerun()
                else:
                    st.error("Registration failed. Please try a different username.")

        st.markdown("---")
        st.markdown(
            "<div style='text-align:center; font-size:0.88rem;'>Already have an account?</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔑 Back to Sign In", use_container_width=True):
            st.session_state["auth_page"] = "login"
            st.rerun()
