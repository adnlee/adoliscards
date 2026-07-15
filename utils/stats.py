"""Pure collection statistics; all values come from supplied database rows."""

from __future__ import annotations

import pandas as pd


def numeric_series(cards: pd.DataFrame, column: str) -> pd.Series:
    if column not in cards:
        return pd.Series(dtype="float64")
    return pd.to_numeric(cards[column], errors="coerce").fillna(0)


def summary(cards: pd.DataFrame) -> dict[str, float | int]:
    total = len(cards)
    statuses = cards.get("status", pd.Series(dtype="object")).fillna("")
    owned = int(statuses.eq("Owned").sum())
    return {
        "tracked": total,
        "owned": owned,
        "need": int(statuses.eq("Need").sum()),
        "incoming": int(statuses.eq("Incoming").sum()),
        "completion": owned / total * 100 if total else 0.0,
        "value": float(numeric_series(cards, "estimated_value").sum()),
        "invested": float(numeric_series(cards, "price_paid").sum()),
    }


def year_progress(cards: pd.DataFrame) -> pd.DataFrame:
    if cards.empty:
        return pd.DataFrame(columns=["Year", "Owned", "Total", "Complete"])
    result = (
        cards.assign(_owned=cards["status"].eq("Owned").astype(int))
        .groupby("year", dropna=False, as_index=False)
        .agg(Owned=("_owned", "sum"), Total=("id", "count"))
        .rename(columns={"year": "Year"})
    )
    result["Complete"] = result["Owned"].div(result["Total"]).mul(100)
    return result.sort_values("Year", ascending=False)


def set_progress(cards: pd.DataFrame) -> pd.DataFrame:
    if cards.empty:
        return pd.DataFrame(columns=["Year", "Set", "Owned", "Total", "Missing", "Complete"])
    result = (
        cards.assign(_owned=cards["status"].eq("Owned").astype(int))
        .groupby(["year", "set_name"], dropna=False, as_index=False)
        .agg(Owned=("_owned", "sum"), Total=("id", "count"))
        .rename(columns={"year": "Year", "set_name": "Set"})
    )
    result["Missing"] = result["Total"] - result["Owned"]
    result["Complete"] = result["Owned"].div(result["Total"]).mul(100)
    return result.sort_values(["Complete", "Total"], ascending=[False, False])
