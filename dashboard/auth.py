"""
Authentication module for dashboard
Simple but secure login system
"""

import streamlit as st
import hashlib
import json
from pathlib import Path

# Default credentials (should be changed by user)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"  # CHANGE THIS!

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_credentials():
    """Load credentials from file or use defaults"""
    creds_file = Path(__file__).parent / "credentials.json"

    if creds_file.exists():
        try:
            with open(creds_file, 'r') as f:
                return json.load(f)
        except:
            pass

    # Return default credentials
    return {
        "username": DEFAULT_USERNAME,
        "password_hash": hash_password(DEFAULT_PASSWORD)
    }

def save_credentials(username: str, password: str):
    """Save new credentials to file"""
    creds_file = Path(__file__).parent / "credentials.json"

    credentials = {
        "username": username,
        "password_hash": hash_password(password)
    }

    with open(creds_file, 'w') as f:
        json.dump(credentials, f)

def check_password(username: str, password: str) -> bool:
    """Verify username and password"""
    creds = load_credentials()

    if username != creds["username"]:
        return False

    return hash_password(password) == creds["password_hash"]

def login_page():
    """Display login page"""
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h1>📈 Nifty Options Trading Platform</h1>
        <h3>Login to Dashboard</h3>
    </div>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.container():
            st.markdown("---")

            username = st.text_input("Username", key="username")
            password = st.text_input("Password", type="password", key="password")

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("Login", type="primary", use_container_width=True):
                    if check_password(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")

            with col_b:
                if st.button("Reset Password", use_container_width=True):
                    st.session_state.show_reset = True
                    st.rerun()

            st.markdown("---")

            # Default credentials warning
            st.warning("⚠️ **Default credentials:** admin / admin123")
            st.info("💡 Change password after first login using Settings")

def reset_password_page():
    """Display password reset page"""
    st.markdown("### 🔐 Reset Password")

    with st.form("reset_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_username = st.text_input("New Username (optional)")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("Reset Password", type="primary")

        with col2:
            cancel = st.form_submit_button("Cancel")

        if cancel:
            st.session_state.show_reset = False
            st.rerun()

        if submitted:
            # Verify current password
            creds = load_credentials()
            if hash_password(current_password) != creds["password_hash"]:
                st.error("❌ Current password is incorrect")
                return

            # Validate new password
            if new_password != confirm_password:
                st.error("❌ New passwords do not match")
                return

            if len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
                return

            # Save new credentials
            username = new_username if new_username else creds["username"]
            save_credentials(username, new_password)

            st.success("✅ Password updated successfully!")
            st.session_state.show_reset = False
            st.session_state.authenticated = False
            st.info("Please login with your new credentials")
            time.sleep(2)
            st.rerun()

def require_authentication():
    """Decorator to require authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if 'show_reset' not in st.session_state:
        st.session_state.show_reset = False

    if st.session_state.show_reset:
        reset_password_page()
        st.stop()

    if not st.session_state.authenticated:
        login_page()
        st.stop()

def logout():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()
