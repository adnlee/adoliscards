"""Premium CardVault overview dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from components.gallery import gallery
from components.page_title import page_title
from components.stat_card import stat_card
from utils.formatting import money, text
from utils.stats import set_progress, summary, year_progress


def _progress_rows(data: pd.DataFrame, label_columns: list[str], limit: int = 6) -> None:
    for row in data.head(limit).to_dict("records"):
        label = " ".join(text(row.get(column), "") for column in label_columns)
        complete = float(row.get("Complete") or 0)
        st.markdown(f'<div class="cv-progress-row"><div class="cv-progress-label"><b>{label}</b><small>{int(row.get("Owned",0))}/{int(row.get("Total",0))} owned</small></div><div class="cv-track"><div class="cv-fill" style="width:{complete:.1f}%"></div></div><strong>{complete:.0f}%</strong></div>', unsafe_allow_html=True)


def render(client: Any, cards: pd.DataFrame) -> None:
    page_title("Dashboard", "A live view of your Adolis García collection.")
    values = summary(cards)
    first = st.columns(4)
    metrics = [
        ("Cards tracked", f'{values["tracked"]:,}', "▦", f'{values["owned"]:,} owned', "red"),
        ("Owned", f'{values["owned"]:,}', "✓", f'{values["completion"]:.1f}% complete', "green"),
        ("Need", f'{values["need"]:,}', "◇", "Checklist gaps", "gold"),
        ("Incoming", f'{values["incoming"]:,}', "→", "On the way", "blue"),
    ]
    for column, metric in zip(first, metrics):
        with column: stat_card(*metric)
    second = st.columns(3)
    more = [
        ("Completion", f'{values["completion"]:.1f}%', "◫", "Across all tracked cards", "red"),
        ("Collection value", money(values["value"]), "$", "Estimated market value", "green"),
        ("Money invested", money(values["invested"]), "◷", "Recorded purchase prices", "blue"),
    ]
    for column, metric in zip(second, more):
        with column: stat_card(*metric)
    if cards.empty:
        st.info("Add or import cards to populate the dashboard.")
        return
    left, right = st.columns([1.05, .95])
    with left:
        st.markdown('<div class="cv-panel"><div class="cv-panel-title">Progress by year</div>', unsafe_allow_html=True)
        _progress_rows(year_progress(cards), ["Year"])
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="cv-panel"><div class="cv-panel-title">Closest sets to completion</div>', unsafe_allow_html=True)
        _progress_rows(set_progress(cards), ["Year", "Set"])
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="cv-panel"><div class="cv-panel-title">Recent pickups</div>', unsafe_allow_html=True)
    pickups = cards[cards["status"].eq("Owned")].copy()
    sort_column = "date_acquired" if "date_acquired" in pickups else "created_at"
    pickups = pickups.sort_values(sort_column, ascending=False, na_position="last").head(4)
    gallery(client, pickups, columns=4)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="cv-panel"><div class="cv-panel-title">Collection summary</div>', unsafe_allow_html=True)
    counts = cards.get("category", pd.Series(dtype=str)).fillna("Other").value_counts().rename_axis("Category").reset_index(name="Cards")
    st.bar_chart(counts.set_index("Category"))
    st.markdown("</div>", unsafe_allow_html=True)
