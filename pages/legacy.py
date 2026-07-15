"""Preserved CardVault workflows pending their dedicated 4.0 redesign."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from components.gallery import gallery
from components.page_title import page_title
from utils.database import insert_card, upload_image
from utils.filters import collection_filters
from utils.imports import normalize_import
from utils.stats import set_progress

STATUS_OPTIONS = ["Need", "Owned", "Incoming"]
CATEGORY_OPTIONS = ["Base", "Parallel", "Insert", "Numbered", "Autograph", "Relic", "Relic/Autograph", "Other"]


def set_progress_page(client: Any, cards: pd.DataFrame) -> None:
    page_title("Set Progress", "Track completion by product and inspect missing cards.")
    progress = set_progress(cards)
    if progress.empty:
        st.info("No cards yet.")
        return
    st.dataframe(progress, hide_index=True, use_container_width=True, column_config={"Complete": st.column_config.ProgressColumn("Complete", min_value=0, max_value=100, format="%.1f%%")})
    labels = [""] + [f'{int(row.Year)} — {row.Set}' for row in progress.itertuples()]
    selected = st.selectbox("Open a product", labels)
    if selected:
        year, set_name = selected.split(" — ", 1)
        product = cards[cards["year"].eq(int(year)) & cards["set_name"].eq(set_name)]
        missing = product[~product["status"].eq("Owned")]
        st.subheader(f"Missing cards · {len(missing)}")
        gallery(client, missing, columns=4, quick_owned=True)


def wishlist_page(client: Any, cards: pd.DataFrame) -> None:
    page_title("Wishlist", "A focused shopping list built from cards marked Need.")
    gallery(client, collection_filters(cards, need_only=True), columns=3, quick_owned=True)


def purchases_page(client: Any, cards: pd.DataFrame) -> None:
    page_title("Purchases", "Owned-card history from recorded acquisition dates and prices.")
    owned = cards[cards["status"].eq("Owned")].copy()
    if owned.empty:
        st.info("No owned cards are recorded yet.")
        return
    paid = pd.to_numeric(owned.get("price_paid", 0), errors="coerce").fillna(0)
    a, b, c = st.columns(3)
    a.metric("Purchases", len(owned)); b.metric("Total spent", f"${paid.sum():,.2f}"); c.metric("Average", f"${paid.mean():,.2f}")
    sort_col = "date_acquired" if "date_acquired" in owned else "created_at"
    owned = owned.sort_values(sort_col, ascending=False, na_position="last")
    gallery(client, owned, columns=4)


def add_card_page(client: Any, user_id: str, collection_id: str) -> None:
    page_title("Add Card", "Add a checklist entry or record a new pickup.")
    with st.form("add_card", clear_on_submit=True):
        c1, c2 = st.columns(2)
        year = c1.number_input("Year", min_value=1900, max_value=2100, value=date.today().year)
        set_name = c2.text_input("Set *")
        card_number = c1.text_input("Card number")
        card_name = c2.text_input("Card name", value="Adolis García")
        category = c1.selectbox("Category", CATEGORY_OPTIONS)
        parallel = c2.text_input("Parallel")
        serial = c1.text_input("Serial number")
        status = c2.selectbox("Status", STATUS_OPTIONS)
        image = st.file_uploader("Front image", type=["jpg", "jpeg", "png", "webp"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add card", use_container_width=True)
    if submitted:
        if not set_name.strip():
            st.error("Set is required.")
            return
        path = upload_image(client, user_id, image) if image else ""
        insert_card(client, {"user_id": user_id, "collection_id": collection_id, "year": int(year), "set_name": set_name.strip(), "card_number": card_number.strip(), "card_name": card_name.strip(), "category": category, "parallel": parallel.strip(), "serial_number": serial.strip(), "status": status, "image_path": path, "notes": notes.strip(), "date_acquired": date.today().isoformat() if status == "Owned" else None})
        st.success("Card added.")


def import_page(client: Any, cards: pd.DataFrame, user_id: str, collection_id: str) -> None:
    page_title("Import", "Upload the same CSV checklists supported by CardVault 3.1.")
    uploaded = st.file_uploader("Choose CSV", type=["csv"])
    if not uploaded:
        return
    frame = pd.read_csv(uploaded)
    st.dataframe(frame.head(25), use_container_width=True)
    if st.button("Import checklist", use_container_width=True):
        try:
            records = normalize_import(frame, user_id, collection_id)
            existing = set(zip(cards.get("year", pd.Series(dtype=str)).astype(str), cards.get("set_name", pd.Series(dtype=str)).fillna("").str.lower(), cards.get("card_number", pd.Series(dtype=str)).fillna("").str.lower(), cards.get("parallel", pd.Series(dtype=str)).fillna("").str.lower()))
            fresh = []
            for record in records:
                key = (str(record["year"]), record["set_name"].lower(), record["card_number"].lower(), record["parallel"].lower())
                if key not in existing:
                    fresh.append(record); existing.add(key)
            for start in range(0, len(fresh), 100):
                client.table("cards").insert(fresh[start:start + 100]).execute()
            st.success(f"Imported {len(fresh)} cards; skipped {len(records)-len(fresh)} duplicates.")
        except Exception as exc:
            st.error(f"Import failed: {exc}")


def analytics_page(cards: pd.DataFrame) -> None:
    page_title("Analytics", "Collection distribution by year, category, and status.")
    if cards.empty:
        st.info("No cards yet."); return
    a, b = st.columns(2)
    a.bar_chart(cards.groupby("year").size())
    b.bar_chart(cards["category"].fillna("Other").value_counts())
    st.bar_chart(cards["status"].fillna("Unknown").value_counts())


def backup_page(cards: pd.DataFrame, name: str) -> None:
    page_title("Backup / Export", "Download a complete CSV copy of the active collection.")
    if cards.empty:
        st.info("Nothing to export."); return
    st.download_button("Download collection CSV", cards.to_csv(index=False).encode("utf-8"), file_name=f'{name.replace(" ", "_")}.csv', mime="text/csv", use_container_width=True)
