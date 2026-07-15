"""CardVault navigation and collection switcher."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from utils.database import clear_session, create_collection


NAVIGATION = ["Dashboard", "Collection", "Set Progress", "Wishlist", "Purchases", "Add Card", "Import", "Analytics", "Database Health", "Backup"]
ICONS = {"Dashboard": "⌂", "Collection": "▦", "Set Progress": "◫", "Wishlist": "♡", "Purchases": "◷", "Add Card": "+", "Import": "⇩", "Analytics": "⌁", "Database Health": "✓", "Backup": "⇧"}


def sidebar(client: Any, collections: pd.DataFrame, cards_by_collection: dict[str, int], user_id: str) -> tuple[str, str]:
    with st.sidebar:
        st.markdown('<div class="cv-brand"><b>Card<span>Vault</span></b><small>COLLECTION INTELLIGENCE · 4.0</small></div>', unsafe_allow_html=True)
        names = collections["name"].tolist()
        selected_name = st.selectbox("Active collection", names)
        collection_id = str(collections.loc[collections["name"].eq(selected_name), "id"].iloc[0])
        row = collections.loc[collections["id"].astype(str).eq(collection_id)].iloc[0]
        st.markdown(f'<div class="cv-profile"><b>{row.get("player_name") or selected_name}</b><span>{row.get("team") or "Personal collection"}</span><small>{cards_by_collection.get(collection_id, 0):,} cards tracked</small></div>', unsafe_allow_html=True)
        labels = [f'{ICONS[name]}  {name}' for name in NAVIGATION]
        chosen = st.radio("Navigation", labels, label_visibility="collapsed")
        page = chosen.split("  ", 1)[1]
        with st.expander("New collection"):
            with st.form("new_collection"):
                name = st.text_input("Collection name")
                sport = st.text_input("Sport", value="Baseball")
                team = st.text_input("Team", value="Texas Rangers")
                player = st.text_input("Player", value="Adolis García")
                submitted = st.form_submit_button("Create collection", use_container_width=True)
            if submitted and name.strip():
                create_collection(client, {"user_id": user_id, "name": name.strip(), "sport": sport.strip(), "team": team.strip(), "player_name": player.strip()})
                st.rerun()
        if st.button("Sign out", use_container_width=True):
            try:
                client.auth.sign_out()
            finally:
                clear_session()
            st.rerun()
    return page, collection_id
