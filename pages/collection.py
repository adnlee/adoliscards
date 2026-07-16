"""Searchable collection gallery with compact and table alternatives."""

from typing import Any

import pandas as pd
import streamlit as st

from components.gallery import gallery
from components.page_title import page_title
from utils.filters import collection_filters


def render(client: Any, cards: pd.DataFrame) -> None:
    page_title("Collection Gallery", "Browse, filter, favorite, and manage every tracked card.")
    filtered = collection_filters(cards)
    header, mode_column = st.columns([3, 1])
    header.caption(f"{len(filtered):,} of {len(cards):,} cards")
    mode = mode_column.selectbox("View", ["Gallery", "Compact", "Table"], label_visibility="collapsed")
    if mode == "Gallery":
        gallery(client, filtered, columns=4, all_cards=cards)
    elif mode == "Compact":
        gallery(client, filtered, columns=6, all_cards=cards)
    else:
        columns = [column for column in ["year", "set_name", "card_number", "category", "parallel", "serial_number", "status", "price_paid", "estimated_value", "storage_location", "favorite"] if column in filtered]
        st.dataframe(filtered[columns], hide_index=True, use_container_width=True)
