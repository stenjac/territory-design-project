"""
Simple Authentication Examples for Territory Dashboard

Add one of these to the top of territory_dashboard.py to protect access
"""

import streamlit as st
import hmac
import hashlib

# ============================================================================
# OPTION 1: Simple Password Protection
# ============================================================================

def simple_password_check():
    """
    Basic password protection - good for small teams

    Usage: Add this at the top of territory_dashboard.py:
        if not simple_password_check():
            st.stop()
    """

    def password_entered():
        # In production, store this in .streamlit/secrets.toml
        CORRECT_PASSWORD = "TerritoryOps2024"  # Change this!

        if hmac.compare_digest(st.session_state["password"], CORRECT_PASSWORD):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Check if already authenticated
    if st.session_state.get("password_correct", False):
        return True

    # Show login form
    st.title("🔒 Territory Dashboard Login")
    st.text_input(
        "Enter Password:",
        type="password",
        on_change=password_entered,
        key="password"
    )

    if "password_correct" in st.session_state:
        st.error("😕 Incorrect password")

    return False


# ============================================================================
# OPTION 2: Username + Password Authentication
# ============================================================================

def username_password_check():
    """
    Username and password authentication - good for tracking users

    Usage: Add this at the top of territory_dashboard.py:
        user = username_password_check()
        if not user:
            st.stop()
        st.sidebar.write(f"👤 Logged in as: {user}")
    """

    # In production, store these in .streamlit/secrets.toml or database
    VALID_USERS = {
        "sales_ops": "ops2024",
        "john.doe": "password123",
        "jane.smith": "secure456"
    }

    def login_submitted():
        username = st.session_state["username"]
        password = st.session_state["password"]

        if username in VALID_USERS and hmac.compare_digest(
            password, VALID_USERS[username]
        ):
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = username
            # Clear credentials from session
            del st.session_state["username"]
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    # Check if already authenticated
    if st.session_state.get("authenticated", False):
        return st.session_state["current_user"]

    # Show login form
    st.title("🔒 Territory Dashboard Login")
    st.text_input("Username:", key="username")
    st.text_input("Password:", type="password", key="password")
    st.button("Login", on_click=login_submitted)

    if "authenticated" in st.session_state and not st.session_state["authenticated"]:
        st.error("😕 Invalid username or password")

    return None


# ============================================================================
# OPTION 3: Role-Based Access Control (RBAC)
# ============================================================================

def role_based_check():
    """
    Role-based authentication - different permissions for different users

    Usage: Add this at the top of territory_dashboard.py:
        user, role = role_based_check()
        if not user:
            st.stop()

        # Then use role to control features:
        if role == "admin":
            st.sidebar.button("Run Rebalancing")
        elif role == "viewer":
            st.info("You have read-only access")
    """

    # In production, store in database
    USERS = {
        "admin": {
            "password": "admin2024",
            "role": "admin",
            "name": "Sales Ops Admin"
        },
        "manager": {
            "password": "manager2024",
            "role": "manager",
            "name": "Sales Manager"
        },
        "rep": {
            "password": "rep2024",
            "role": "viewer",
            "name": "Sales Rep"
        }
    }

    def login_submitted():
        username = st.session_state["username"]
        password = st.session_state["password"]

        if username in USERS and hmac.compare_digest(
            password, USERS[username]["password"]
        ):
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = username
            st.session_state["user_role"] = USERS[username]["role"]
            st.session_state["user_name"] = USERS[username]["name"]
            del st.session_state["username"]
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    # Check if authenticated
    if st.session_state.get("authenticated", False):
        return (
            st.session_state["current_user"],
            st.session_state["user_role"]
        )

    # Show login form
    st.title("🔒 Territory Dashboard Login")
    st.text_input("Username:", key="username")
    st.text_input("Password:", type="password", key="password")
    st.button("Login", on_click=login_submitted)

    if "authenticated" in st.session_state and not st.session_state["authenticated"]:
        st.error("😕 Invalid credentials")

    st.info("""
    **Demo Accounts:**
    - admin / admin2024 (Full access)
    - manager / manager2024 (View + export)
    - rep / rep2024 (View only)
    """)

    return None, None


# ============================================================================
# OPTION 4: IP-Based Access Control
# ============================================================================

def ip_whitelist_check():
    """
    IP-based authentication - restrict to corporate network

    Usage: Add this at the top of territory_dashboard.py:
        if not ip_whitelist_check():
            st.stop()
    """
    import streamlit.web.server.server as server

    # Whitelist of allowed IP addresses or ranges
    ALLOWED_IPS = [
        "192.168.1.",    # Corporate network (any IP starting with this)
        "10.0.0.",       # VPN network
        "127.0.0.1",     # Localhost
    ]

    # Get client IP
    try:
        session = server.Server.get_current()._session_mgr.list_active_sessions()[0]
        client_ip = session.ws.request.remote_ip
    except:
        client_ip = "unknown"

    # Check if IP is allowed
    allowed = any(client_ip.startswith(ip) for ip in ALLOWED_IPS)

    if not allowed:
        st.error(f"🚫 Access Denied")
        st.error(f"Your IP address ({client_ip}) is not authorized to access this dashboard.")
        st.info("Please connect via corporate VPN or contact IT support.")
        return False

    return True


# ============================================================================
# OPTION 5: Environment-Based Secrets
# ============================================================================

def secrets_based_check():
    """
    Use Streamlit secrets for credentials - most secure

    Create .streamlit/secrets.toml:
        [auth]
        password = "your_secure_password"

        [users]
        admin = "admin_password"
        user1 = "user1_password"

    Usage: Add this at the top of territory_dashboard.py:
        if not secrets_based_check():
            st.stop()
    """

    def password_entered():
        # Access secrets from .streamlit/secrets.toml
        if hmac.compare_digest(
            st.session_state["password"],
            st.secrets["auth"]["password"]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Territory Dashboard Login")
    st.text_input(
        "Enter Password:",
        type="password",
        on_change=password_entered,
        key="password"
    )

    if "password_correct" in st.session_state:
        st.error("😕 Incorrect password")

    return False


# ============================================================================
# RECOMMENDED IMPLEMENTATION FOR PRODUCTION
# ============================================================================

"""
For production deployment:

1. Create .streamlit/secrets.toml:

    [auth]
    [auth.users]
    admin = "hashed_password_here"
    sales_ops = "hashed_password_here"

2. Add to .gitignore:
    .streamlit/secrets.toml

3. Use hashed passwords instead of plaintext:

    import hashlib

    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(password, hashed):
        return hash_password(password) == hashed

4. Add session timeout:

    import time

    if "login_time" in st.session_state:
        if time.time() - st.session_state["login_time"] > 3600:  # 1 hour
            st.session_state.clear()
            st.rerun()

5. Log access attempts:

    import logging

    logging.basicConfig(filename='access.log', level=logging.INFO)
    logging.info(f"Login attempt: {username} at {datetime.now()}")
"""

if __name__ == "__main__":
    st.title("Authentication Examples")
    st.write("See code for implementation details")

    # Test each method
    option = st.radio("Select authentication method:", [
        "Simple Password",
        "Username + Password",
        "Role-Based Access",
    ])

    if option == "Simple Password":
        if simple_password_check():
            st.success("✅ Authenticated!")
            st.balloons()
    elif option == "Username + Password":
        user = username_password_check()
        if user:
            st.success(f"✅ Welcome, {user}!")
            st.balloons()
    elif option == "Role-Based Access":
        user, role = role_based_check()
        if user:
            st.success(f"✅ Welcome, {user}!")
            st.info(f"Role: {role}")
            st.balloons()
