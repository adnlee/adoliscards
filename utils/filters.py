"""Collection filtering and sorting controls."""

from __future__ import annotations

import pandas as pd
import streamlit as st

SORTS = {
    "Recently updated": ("updated_at", False),
    "Year: newest": ("year", False),
    "Year: oldest": ("year", True),
    "Set: A–Z": ("set_name", True),
    "Card number": ("card_number", True),
    "Date acquired": ("date_acquired", False),
    "Purchase price: high": ("price_paid", False),
    "Purchase price: low": ("price_paid", True),
    "Estimated value: high": ("estimated_value", False),
    "Estimated value: low": ("estimated_value", True),
}
SEARCH_COLUMNS = ["year", "set_name", "card_number", "parallel", "serial_number", "category", "notes"]


def searchable_mask(cards: pd.DataFrame, query: str) -> pd.Series:
    if not query.strip() or cards.empty:
        return pd.Series(True, index=cards.index)
    columns = [column for column in SEARCH_COLUMNS if column in cards]
    if not columns:
        return pd.Series(False, index=cards.index)
    return cards[columns].fillna("").astype(str).apply(
        lambda column: column.str.contains(query.strip(), case=False, regex=False)
    ).any(axis=1)


def _contains(cards: pd.DataFrame, column: str, value: str) -> pd.Series:
    source = cards[column] if column in cards else pd.Series("", index=cards.index)
    return source.fillna("").astype(str).str.contains(value, case=False, regex=False)


def _numbered(cards: pd.DataFrame) -> pd.Series:
    serial = cards["serial_number"] if "serial_number" in cards else pd.Series("", index=cards.index)
    return _contains(cards, "category", "number") | serial.fillna("").astype(str).str.strip().ne("")


def collection_filters(cards: pd.DataFrame, *, need_only: bool = False) -> pd.DataFrame:
    """Render complete collector controls and return a filtered, sorted copy."""
    filtered = cards.copy()
    if need_only and "status" in filtered:
        filtered = filtered[~filtered["status"].isin(["Owned", "Incoming", "Not Chasing"])]

    search = st.text_input("Search collection", placeholder="Year, set, card #, parallel, serial, category, notes…")
    filtered = filtered[searchable_mask(filtered, search)]

    row1 = st.columns(4)
    years = sorted(filtered.get("year", pd.Series(dtype=int)).dropna().unique(), reverse=True)
    sets = sorted(filtered.get("set_name", pd.Series(dtype=str)).dropna().astype(str).unique())
    statuses = sorted(filtered.get("status", pd.Series(dtype=str)).dropna().astype(str).unique())
    categories = sorted(filtered.get("category", pd.Series(dtype=str)).dropna().astype(str).unique())
    selected_years = row1[0].multiselect("Year", years)
    selected_sets = row1[1].multiselect("Set", sets)
    selected_statuses = row1[2].multiselect("Status", statuses)
    selected_categories = row1[3].multiselect("Category", categories)

    row2 = st.columns([1, 1, 1, 1.3])
    priorities = sorted(filtered.get("priority", pd.Series(dtype=str)).dropna().astype(str).unique())
    selected_priorities = row2[0].multiselect("Priority", priorities)
    special = row2[1].multiselect("Card type", ["Autograph", "Relic", "Numbered"])
    favorites = row2[2].toggle("Favorites only", key=f"favorites_{'need' if need_only else 'collection'}")
    sort_name = row2[3].selectbox("Sort", list(SORTS))

    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)]
    if selected_sets:
        filtered = filtered[filtered["set_name"].isin(selected_sets)]
    if selected_statuses:
        filtered = filtered[filtered["status"].isin(selected_statuses)]
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]
    if selected_priorities:
        filtered = filtered[filtered["priority"].isin(selected_priorities)]
    if favorites and "favorite" in filtered:
        filtered = filtered[filtered["favorite"].fillna(False).astype(bool)]
    for card_type in special:
        if card_type == "Autograph":
            filtered = filtered[_contains(filtered, "category", "auto")]
        elif card_type == "Relic":
            filtered = filtered[_contains(filtered, "category", "relic")]
        elif card_type == "Numbered":
            filtered = filtered[_numbered(filtered)]

    sort_column, ascending = SORTS[sort_name]
    if sort_column in filtered:
        if sort_column in {"price_paid", "estimated_value"}:
            filtered = filtered.assign(_sort=pd.to_numeric(filtered[sort_column], errors="coerce")).sort_values("_sort", ascending=ascending, na_position="last").drop(columns="_sort")
        else:
            filtered = filtered.sort_values(sort_column, ascending=ascending, na_position="last", kind="stable")
    return filtered
