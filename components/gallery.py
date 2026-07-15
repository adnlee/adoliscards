"""Reusable visual gallery."""

from typing import Any

import pandas as pd
import streamlit as st

from components.card_tile import card_tile


def gallery(client: Any, cards: pd.DataFrame, *, columns: int = 4, quick_owned: bool = False) -> None:
    if cards.empty:
        st.info("No cards match these filters.")
        return
    for start in range(0, len(cards), columns):
        slots = st.columns(columns)
        for slot, (_, row) in zip(slots, cards.iloc[start:start + columns].iterrows()):
            with slot:
                card_tile(client, row, quick_owned=quick_owned)
