"""CardVault 4.0 Streamlit entry point.

The entry point owns session orchestration only; UI, data access, statistics, and
page behavior live in focused modules. Existing Supabase tables remain untouched.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from components.sidebar import sidebar
from pages import collection, dashboard, database_health, legacy
from utils.database import (
    ensure_default_collection,
    fetch_cards,
    fetch_collections,
    get_client,
    restore_session,
    save_session,
)

st.set_page_config(page_title="CardVault 4.0", page_icon="🗃️", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{Path('assets/styles.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def require_login(client) -> None:
    """Preserve password authentication and registration from CardVault 3.1."""
    if st.session_state.get("user_id"):
        return
    st.markdown('<div style="max-width:520px;margin:8vh auto 1rem"><div class="cv-brand"><b style="color:#14233b">Card<span>Vault</span></b><small>COLLECTION INTELLIGENCE · 4.0</small></div></div>', unsafe_allow_html=True)
    sign_in, sign_up = st.tabs(["Sign in", "Create account"])
    with sign_in:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in", use_container_width=True)
        if submit:
            try:
                save_session(client.auth.sign_in_with_password({"email": email.strip(), "password": password}))
                st.rerun()
            except Exception as exc:
                st.error(f"Could not sign in: {exc}")
    with sign_up:
        with st.form("signup"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            submit = st.form_submit_button("Create account", use_container_width=True)
        if submit:
            try:
                response = client.auth.sign_up({"email": email.strip(), "password": password})
                if response.session:
                    save_session(response); st.rerun()
                st.success("Account created. Confirm your email, then sign in.")
            except Exception as exc:
                st.error(f"Could not create account: {exc}")
    st.stop()


client = get_client()
restore_session(client)
require_login(client)
user_id = st.session_state.user_id
ensure_default_collection(client, user_id)
collections = fetch_collections(client, user_id)
if collections.empty:
    st.error("No collection could be loaded."); st.stop()

# Fetch once per collection for accurate sidebar counts without creating data.
collection_cards = {str(row.id): fetch_cards(client, str(row.id)) for row in collections.itertuples()}
counts = {collection_id: len(frame) for collection_id, frame in collection_cards.items()}
page, collection_id = sidebar(client, collections, counts, user_id)
cards = collection_cards[collection_id]
collection_name = str(collections.loc[collections["id"].astype(str).eq(collection_id), "name"].iloc[0])

routes = {
    "Dashboard": lambda: dashboard.render(client, cards),
    "Collection": lambda: collection.render(client, cards),
    "Set Progress": lambda: legacy.set_progress_page(client, cards),
    "Wishlist": lambda: legacy.wishlist_page(client, cards),
    "Purchases": lambda: legacy.purchases_page(client, cards),
    "Add Card": lambda: legacy.add_card_page(client, user_id, collection_id),
    "Import": lambda: legacy.import_page(client, cards, user_id, collection_id),
    "Analytics": lambda: legacy.analytics_page(cards),
    "Database Health": lambda: database_health.render(client, cards),
    "Backup": lambda: legacy.backup_page(cards, collection_name),
}
routes[page]()
