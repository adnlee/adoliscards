"""Read-only collection quality diagnostics."""

from typing import Any

import pandas as pd
import streamlit as st

from components.page_title import page_title
from utils.checklist import coverage, duplicate_cards, missing_value_counts
from utils.stats import year_progress


def render(client: Any, cards: pd.DataFrame) -> None:
    page_title("Database Health", "Read-only quality checks; no records are altered.")
    missing_images = cards[cards.get("image_path", pd.Series(index=cards.index, dtype=str)).fillna("").str.strip().eq("")]
    missing_price = cards[cards.get("price_paid", pd.Series(index=cards.index, dtype=float)).fillna(0).eq(0)]
    duplicates = duplicate_cards(cards)
    metrics = st.columns(4)
    metrics[0].metric("Missing images", len(missing_images)); metrics[1].metric("Duplicate cards", len(duplicates)); metrics[2].metric("Missing purchase price", len(missing_price)); metrics[3].metric("Checklist coverage", f"{coverage(cards):.1f}%")
    st.subheader("Missing values"); st.dataframe(missing_value_counts(cards), hide_index=True, use_container_width=True)
    st.subheader("Progress by year"); st.dataframe(year_progress(cards), hide_index=True, use_container_width=True)
    if not duplicates.empty:
        st.subheader("Potential duplicates")
        st.dataframe(duplicates, hide_index=True, use_container_width=True)
