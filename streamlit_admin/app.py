import streamlit as st
import requests
from datetime import datetime

API_URL = "http://admin_api:8001"

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Session state to manage login
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None

# --- Login Form ---
def login_form():
    st.title("🔐 Admin Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            try:
                res = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
                if res.status_code == 200:
                    st.session_state.auth_token = res.json()["access_token"]
                    st.success("Logged in successfully!")
                else:
                    st.error(res.json().get("detail", "Login failed"))
            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- Authenticated Dashboard ---
def admin_dashboard():
    st.title("🛠️ Admin Dashboard")

    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

    # --- Helper: Fetch users and tokens ---
    @st.cache_data(ttl=60)
    def get_users():
        r = requests.get(f"{API_URL}/users", headers=headers)
        if r.status_code == 200:
            return r.json()
        return []

    @st.cache_data(ttl=60)
    def get_tokens_for_user(user_id):
        r = requests.get(f"{API_URL}/users/{user_id}/tokens", headers=headers)
        if r.status_code == 200:
            return r.json()
        return []

    users = get_users()
    user_name_to_id = {u["name"]: u["id"] for u in users}
    user_names = list(user_name_to_id.keys())
    print(f"Users: {user_names}")

    # --- Register New User ---
    with st.expander("📧 Register New User"):
        name = st.text_input("New User Name")
        email = st.text_input("New User Email")
        password = st.text_input("Password", type="password")
        if st.button("Register User"):
            r = requests.post(f"{API_URL}/register", json={"name":name, "email": email, "password": password})
            st.success("User registered" if r.status_code == 200 else r.text)

    # --- Create Token for User ---
    with st.expander("🔑 Create Token for User"):
        if user_names:
            selected_user_name = st.selectbox("Select User", user_names)
            desc = st.text_input("Description")
            expires_at = st.date_input("Expires at", value=None)
            token_display = st.empty() 
            if st.button("Generate Token"):
                payload = {"description": desc}
                if expires_at:
                    payload["expires_at"] = str(expires_at)
                user_id = user_name_to_id[selected_user_name]
                r = requests.post(f"{API_URL}/users/{user_id}/tokens", json=payload)
                if r.status_code == 200:
                    token_value = r.json().get("token")
                    st.success(f"Token created: {r.json()['token']}")
                    token_display.code(token_value, language="text")
                    st.info("Give this token to the user. They must use it as a Bearer token in the Authorization header for API requests.")
                else:
                    st.error(r.text)
        else:
            st.info("No users available. Please register a user first.")

    # --- Assign Policy to Token ---
    with st.expander("🧾 Assign Policy to Token"):
        if user_names:
            selected_user_name = st.selectbox("Select User (for token)", user_names, key="policy_user")
            user_id = user_name_to_id[selected_user_name]
            tokens = get_tokens_for_user(user_id)
            token_options = {t["description"] or t["token"]: t["id"] for t in tokens}
            if token_options:
                selected_token_desc = st.selectbox("Select Token", list(token_options.keys()))
                token_id = token_options[selected_token_desc]
            else:
                st.info("No tokens found for this user.")
                token_id = None

            model_name = st.text_input("Model Name (e.g., gpt-4o)")
            rate_limit = st.number_input("Rate Limit Per Minute", min_value=1, value=10)
            quota = st.number_input("Monthly Quota Tokens (optional)", value=1000)
            if st.button("Add Policy") and token_id:
                payload = {
                    "model_name": model_name,
                    "rate_limit_per_minute": rate_limit,
                    "monthly_quota_tokens": quota,
                }
                r = requests.post(f"{API_URL}/tokens/{token_id}/policies", json=payload)
                if r.status_code == 200:
                    st.success("Policy assigned successfully")
                else:
                    st.error(r.text)
        else:
            st.info("No users available. Please register a user first.")

    # --- Logout ---
    if st.button("Logout"):
        st.session_state.auth_token = None
        st.experimental_rerun()

# --- Main ---
if st.session_state.auth_token:
    admin_dashboard()
else:
    login_form()
