"""Collection filtering and sorting controls."""

from __future__ import annotations

import pandas as pd
import streamlit as st


SORTS = {
    "Newest added": ("created_at", False),
    "Year: newest": ("year", False),
    "Year: oldest": ("year", True),
    "Set name": ("set_name", True),
    "Highest value": ("estimated_value", False),
}


def collection_filters(cards: pd.DataFrame, *, need_only: bool = False) -> pd.DataFrame:
    """Render responsive controls and return a filtered copy."""
    filtered = cards.copy()
    if need_only and "status" in filtered:
        filtered = filtered[~filtered["status"].isin(["Owned", "Incoming", "Not Chasing"])]

    search = st.text_input("Search collection", placeholder="Set, parallel, number, notes…")
    c1, c2, c3, c4 = st.columns(4)
    years = sorted(filtered.get("year", pd.Series(dtype=int)).dropna().unique(), reverse=True)
    sets = sorted(filtered.get("set_name", pd.Series(dtype=str)).dropna().astype(str).unique())
    statuses = sorted(filtered.get("status", pd.Series(dtype=str)).dropna().astype(str).unique())
    selected_years = c1.multiselect("Year", years)
    selected_sets = c2.multiselect("Product", sets)
    selected_statuses = c3.multiselect("Status", statuses)
    sort_name = c4.selectbox("Sort", list(SORTS))
    favorites = st.toggle("Favorites only", key=f"favorites_{'need' if need_only else 'all'}")

    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)]
    if selected_sets:
        filtered = filtered[filtered["set_name"].isin(selected_sets)]
    if selected_statuses:
        filtered = filtered[filtered["status"].isin(selected_statuses)]
    if favorites and "favorite" in filtered:
        filtered = filtered[filtered["favorite"].fillna(False)]
    if search:
        searchable = [c for c in ["year", "set_name", "card_number", "card_name", "category", "parallel", "serial_number", "notes"] if c in filtered]
        mask = filtered[searchable].fillna("").astype(str).apply(
            lambda col: col.str.contains(search, case=False, regex=False)
        ).any(axis=1)
        filtered = filtered[mask]

    sort_column, ascending = SORTS[sort_name]
    if sort_column in filtered:
        filtered = filtered.sort_values(sort_column, ascending=ascending, na_position="last")
    return filtered
