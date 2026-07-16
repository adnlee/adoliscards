"""CSV normalization retained from CardVault 3.1."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd


IMPORT_IDENTITY_COLUMNS = ["year", "manufacturer", "set_name", "card_number", "variation", "serial_number"]


def _identity_text(value: Any) -> str:
    if value is None or (not isinstance(value, (list, dict, tuple, set)) and pd.isna(value)):
        return ""
    return " ".join(str(value).strip().casefold().split())


def _identity_year(value: Any) -> str:
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return _identity_text(value)


def import_identity(record: Mapping[str, Any] | pd.Series) -> tuple[str, ...]:
    """Return the exact normalized import identity, including parallel and numbering."""
    variation = record.get("variation", "")
    if not _identity_text(variation):
        variation = record.get("parallel", "")
    return (
        _identity_year(record.get("year", "")),
        _identity_text(record.get("manufacturer", "")),
        _identity_text(record.get("set_name", "")),
        _identity_text(record.get("card_number", "")),
        _identity_text(variation),
        _identity_text(record.get("serial_number", "")),
    )


def partition_import_records(
    records: list[dict[str, Any]], existing_cards: pd.DataFrame
) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], dict[str, Any]]]]:
    """Split imports into safe inserts and duplicates of live or earlier CSV rows."""
    existing_rows = existing_cards.to_dict("records") if not existing_cards.empty else []
    known = {import_identity(row): dict(row) for row in existing_rows}
    fresh: list[dict[str, Any]] = []
    duplicates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for record in records:
        key = import_identity(record)
        if key in known:
            duplicates.append((record, known[key]))
            continue
        fresh.append(record)
        known[key] = record
    return fresh, duplicates


def normalize_import(df: pd.DataFrame, user_id: str, collection_id: str) -> list[dict]:
    aliases = {"set": "set_name", "brand": "manufacturer", "card #": "card_number", "card no": "card_number", "type": "category", "variation": "parallel", "storage": "storage_location", "serial_numbered_to": "serial_number"}
    df = df.rename(columns={c: aliases.get(c.strip().lower(), c.strip().lower()) for c in df.columns})
    if "year" not in df or "set_name" not in df:
        raise ValueError("CSV must include year and set_name columns.")
    defaults = {"manufacturer": "", "card_number": "", "card_name": "Adolis Garcia", "category": "Base", "parallel": "", "serial_number": "", "status": "Need", "priority": "Core", "condition": "Raw", "grade": "", "price_paid": 0, "estimated_value": 0, "date_acquired": "", "seller": "", "storage_location": "", "image_path": "", "source_url": "", "favorite": False, "notes": ""}
    for column, default in defaults.items():
        if column not in df:
            df[column] = default
    records = []
    for row in df.fillna("").to_dict("records"):
        try:
            year = int(row["year"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid year: {row['year']!r}.") from exc
        if year < 2020:
            raise ValueError(f"Card year {year} is outside the supported Rangers-era range (2020 or later).")
        records.append({
            "user_id": user_id, "collection_id": collection_id, "year": year,
            "manufacturer": str(row["manufacturer"]).strip(), "set_name": str(row["set_name"]).strip(), "card_number": str(row["card_number"]).strip(),
            "card_name": str(row["card_name"]).strip(), "category": str(row["category"]).strip() or "Base",
            "parallel": str(row["parallel"]).strip(), "serial_number": str(row["serial_number"]).strip(),
            "status": str(row["status"]).strip() or "Need", "priority": str(row["priority"]).strip() or "Core",
            "condition": str(row["condition"]).strip() or "Raw", "grade": str(row["grade"]).strip(),
            "price_paid": float(row["price_paid"] or 0), "estimated_value": float(row["estimated_value"] or 0),
            "date_acquired": row["date_acquired"] or None, "seller": str(row["seller"]).strip(),
            "storage_location": str(row["storage_location"]).strip(), "image_path": str(row["image_path"]).strip(),
            "source_url": str(row["source_url"]).strip(), "favorite": str(row["favorite"]).lower() in {"true", "1", "yes"},
            "notes": str(row["notes"]).strip(),
        })
    return records
