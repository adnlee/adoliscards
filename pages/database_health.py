"""Database Health page calculated entirely from the active Supabase collection."""

from typing import Any

import pandas as pd
import streamlit as st

from components.page_title import page_title
from utils.checklist import duplicate_cards, health_summary, incomplete_records, missing_value_counts
from utils.stats import year_progress


def _csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def render(client: Any, cards: pd.DataFrame) -> None:
    del client  # This page is deliberately read-only.
    page_title("Database Health", "Live quality checks for the active collection. No records are changed.")
    summary = health_summary(cards)

    first = st.columns(4)
    first[0].metric("Checklist entries", f'{summary["total"]:,}')
    first[1].metric("Owned", f'{summary["owned"]:,}')
    first[2].metric("Need", f'{summary["need"]:,}')
    first[3].metric("Incoming", f'{summary["incoming"]:,}')
    second = st.columns(4)
    second[0].metric("Duplicate candidates", f'{summary["duplicates"]:,}')
    second[1].metric("Missing images", f'{summary["missing_front_image"]:,}')
    second[2].metric("Missing values", f'{summary["missing_estimated_value"]:,}')
    second[3].metric("Suspicious numbers", f'{summary["suspicious_card_number"]:,}')

    st.subheader("Quality checks")
    st.dataframe(missing_value_counts(cards), hide_index=True, use_container_width=True)

    duplicates = duplicate_cards(cards)
    incomplete = incomplete_records(cards)
    export_left, export_right = st.columns(2)
    export_left.download_button(
        "Export duplicate candidates",
        _csv(duplicates),
        file_name="cardvault_duplicate_candidates.csv",
        mime="text/csv",
        disabled=duplicates.empty,
        use_container_width=True,
    )
    export_right.download_button(
        "Export incomplete records",
        _csv(incomplete),
        file_name="cardvault_incomplete_records.csv",
        mime="text/csv",
        disabled=incomplete.empty,
        use_container_width=True,
    )

    duplicate_tab, incomplete_tab, progress_tab = st.tabs(["Duplicates", "Incomplete records", "Progress by year"])
    with duplicate_tab:
        if duplicates.empty:
            st.success("No exact duplicate candidates found.")
        else:
            st.dataframe(duplicates, hide_index=True, use_container_width=True)
    with incomplete_tab:
        if incomplete.empty:
            st.success("No incomplete records found.")
        else:
            columns = ["health_issues"] + [column for column in incomplete.columns if column != "health_issues"]
            st.dataframe(incomplete[columns], hide_index=True, use_container_width=True)
    with progress_tab:
        st.dataframe(year_progress(cards), hide_index=True, use_container_width=True)
