"""Supabase gateway. Database access is isolated here for safe reuse and testing."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_client() -> Client:
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
    except Exception:
        st.error("CardVault needs SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets.")
        st.stop()


def restore_session(client: Client) -> None:
    access = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")
    if not (access and refresh):
        return
    try:
        client.auth.set_session(access, refresh)
    except Exception:
        clear_session()


def save_session(response: Any) -> None:
    if response.session and response.user:
        st.session_state.access_token = response.session.access_token
        st.session_state.refresh_token = response.session.refresh_token
        st.session_state.user_id = response.user.id
        st.session_state.user_email = response.user.email


def clear_session() -> None:
    for key in ("access_token", "refresh_token", "user_id", "user_email"):
        st.session_state.pop(key, None)


def ensure_default_collection(client: Client, user_id: str) -> str:
    response = client.table("collections").select("id,name").eq("user_id", user_id).order("created_at").limit(1).execute()
    if response.data:
        collection_id = response.data[0]["id"]
    else:
        inserted = client.table("collections").insert({
            "user_id": user_id,
            "name": "Adolis García — Rangers Era",
            "sport": "Baseball",
            "team": "Texas Rangers",
            "player_name": "Adolis García",
            "description": "Rangers-era Adolis García personal collection",
        }).execute()
        collection_id = inserted.data[0]["id"]
    client.table("cards").update({"collection_id": collection_id}).eq("user_id", user_id).is_("collection_id", "null").execute()
    return collection_id


def fetch_collections(client: Client, user_id: str) -> pd.DataFrame:
    result = client.table("collections").select("*").eq("user_id", user_id).order("created_at").execute()
    return pd.DataFrame(result.data or [])


def fetch_cards(client: Client, collection_id: str) -> pd.DataFrame:
    result = client.table("cards").select("*").eq("collection_id", collection_id).order("year", desc=True).order("set_name").execute()
    return pd.DataFrame(result.data or [])


def upload_image(client: Client, user_id: str, uploaded_file: Any) -> str:
    if uploaded_file is None:
        return ""
    extension = Path(uploaded_file.name).suffix.lower() or ".jpg"
    path = f"{user_id}/{uuid4().hex}{extension}"
    client.storage.from_("card-images").upload(
        path=path,
        file=uploaded_file.getvalue(),
        file_options={"content-type": uploaded_file.type, "upsert": "false"},
    )
    return path


@st.cache_data(ttl=1800, show_spinner=False)
def _signed_url(_client: Client, path: str) -> str | None:
    try:
        result = _client.storage.from_("card-images").create_signed_url(path, 3600)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception:
        return None


def signed_url(client: Client, path: str | None) -> str | None:
    return _signed_url(client, path) if path else None


def update_card(client: Client, card_id: str, values: dict[str, Any]) -> None:
    client.table("cards").update(values).eq("id", card_id).execute()


def insert_card(client: Client, values: dict[str, Any]) -> None:
    client.table("cards").insert(values).execute()


def create_collection(client: Client, values: dict[str, Any]) -> None:
    client.table("collections").insert(values).execute()


def fetch_staged_cards(client: Client, collection_id: str) -> pd.DataFrame:
    """Fetch candidate checklist rows isolated from the live cards table."""
    result = client.table("checklist_staging").select("*").eq("collection_id", collection_id).order("year", desc=True).order("set_name").execute()
    return pd.DataFrame(result.data or [])


def insert_staged_cards(client: Client, records: list[dict[str, Any]]) -> None:
    for start in range(0, len(records), 100):
        client.table("checklist_staging").insert(records[start:start + 100]).execute()


def update_staged_card(client: Client, staging_id: str, values: dict[str, Any]) -> None:
    client.table("checklist_staging").update(values).eq("id", staging_id).execute()
