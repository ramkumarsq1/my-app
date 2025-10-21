"""
Authentication module for dashboard
Simple but secure login system
"""

import streamlit as st
import hashlib
import json
import time
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
                creds = json.load(f)
                # Debug: Show what was loaded (remove in production)
                st.sidebar.write(f"Debug: Loaded credentials for user: {creds.get('username', 'N/A')}")
                return creds
        except Exception as e:
            st.error(f"Error loading credentials: {e}")
            pass

    # Return default credentials
    default_creds = {
        "username": DEFAULT_USERNAME,
        "password_hash": hash_password(DEFAULT_PASSWORD)
    }
    # Debug info
    st.sidebar.write(f"Debug: Using default credentials (admin/admin123)")
    return default_creds

def save_credentials(username: str, password: str):
    """Save new credentials to file"""
    creds_file = Path(__file__).parent / "credentials.json"

    credentials = {
        "username": username,
        "password_hash": hash_password(password)
    }

    try:
        with open(creds_file, 'w') as f:
            json.dump(credentials, f)
        st.success(f"Credentials saved to {creds_file}")
    except Exception as e:
        st.error(f"Error saving credentials: {e}")

def check_password(username: str, password: str) -> bool:
    """Verify username and password"""
    try:
        creds = load_credentials()

        # Debug information (remove in production)
        st.sidebar.write(f"Debug: Checking username: '{username}'")
        st.sidebar.write(f"Debug: Expected username: '{creds.get('username', '')}'")
        st.sidebar.write(f"Debug: Username match: {username == creds.get('username', '')}")

        if username != creds["username"]:
            st.error(f"Username mismatch: '{username}' != '{creds['username']}'")
            return False

        input_hash = hash_password(password)
        expected_hash = creds["password_hash"]

        # Debug password hash comparison
        st.sidebar.write(f"Debug: Input hash: {input_hash[:10]}...")
        st.sidebar.write(f"Debug: Expected hash: {expected_hash[:10]}...")
        st.sidebar.write(f"Debug: Password match: {input_hash == expected_hash}")

        return input_hash == expected_hash

    except Exception as e:
        st.error(f"Error checking password: {e}")
        return False

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

            # Show debug info
            with st.expander("🔧 Debug Info (click to expand)"):
                st.write("**Default Credentials:**")
                st.code(f"Username: {DEFAULT_USERNAME}\nPassword: {DEFAULT_PASSWORD}")

                creds = load_credentials()
                st.write("**Current Stored Credentials:**")
                st.write(f"Username: {creds.get('username', 'N/A')}")
                st.write(f"Password Hash: {creds.get('password_hash', 'N/A')[:20]}...")

            username = st.text_input("Username", key="username", value="")
            password = st.text_input("Password", type="password", key="password", value="")

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("Login", type="primary", use_container_width=True):
                    if not username or not password:
                        st.error("Please enter both username and password")
                    elif check_password(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                        st.info("💡 Try default credentials: admin / admin123")

            with col_b:
                if st.button("Reset Password", use_container_width=True):
                    st.session_state.show_reset = True
                    st.rerun()

            st.markdown("---")

            # Default credentials warning
            st.warning("⚠️ **Default credentials:** admin / admin123")
            st.info("💡 Change password after first login using Settings")

            # Quick reset button for testing
            if st.button("🔄 Reset to Default Credentials", help="Delete saved credentials and use defaults"):
                creds_file = Path(__file__).parent / "credentials.json"
                if creds_file.exists():
                    creds_file.unlink()
                    st.success("✅ Credentials reset to defaults!")
                    st.info("Use: admin / admin123")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("Already using default credentials")

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
