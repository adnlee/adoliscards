"""Checklist diagnostics and duplicate detection."""

from __future__ import annotations

import pandas as pd


IDENTITY_COLUMNS = ["year", "set_name", "card_number", "parallel"]


def duplicate_cards(cards: pd.DataFrame) -> pd.DataFrame:
    columns = [column for column in IDENTITY_COLUMNS if column in cards]
    return cards[cards.duplicated(columns, keep=False)].sort_values(columns) if columns else cards.iloc[0:0]


def missing_value_counts(cards: pd.DataFrame) -> pd.DataFrame:
    important = ["year", "set_name", "card_number", "status", "category", "storage_location"]
    rows = []
    for column in important:
        if column in cards:
            values = cards[column]
            missing = int(values.isna().sum() + values.fillna("").astype(str).str.strip().eq("").sum())
            rows.append({"Field": column.replace("_", " ").title(), "Missing": missing})
    return pd.DataFrame(rows)


def coverage(cards: pd.DataFrame) -> float:
    if cards.empty:
        return 0.0
    required = [c for c in ["year", "set_name", "card_number", "status"] if c in cards]
    if not required:
        return 0.0
    filled = cards[required].fillna("").astype(str).apply(lambda col: col.str.strip().ne(""))
    return float(filled.to_numpy().mean() * 100)
