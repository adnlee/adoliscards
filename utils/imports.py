"""CSV normalization retained from CardVault 3.1."""

from __future__ import annotations

import pandas as pd


def normalize_import(df: pd.DataFrame, user_id: str, collection_id: str) -> list[dict]:
    aliases = {"set": "set_name", "brand": "manufacturer", "card #": "card_number", "card no": "card_number", "type": "category", "variation": "parallel", "storage": "storage_location", "serial_numbered_to": "serial_number"}
    df = df.rename(columns={c: aliases.get(c.strip().lower(), c.strip().lower()) for c in df.columns})
    if "year" not in df or "set_name" not in df:
        raise ValueError("CSV must include year and set_name columns.")
    defaults = {"card_number": "", "card_name": "Adolis Garcia", "category": "Base", "parallel": "", "serial_number": "", "status": "Need", "priority": "Core", "condition": "Raw", "grade": "", "price_paid": 0, "estimated_value": 0, "date_acquired": "", "seller": "", "storage_location": "", "image_path": "", "source_url": "", "favorite": False, "notes": ""}
    for column, default in defaults.items():
        if column not in df:
            df[column] = default
    records = []
    for row in df.fillna("").to_dict("records"):
        records.append({
            "user_id": user_id, "collection_id": collection_id, "year": int(row["year"]),
            "set_name": str(row["set_name"]).strip(), "card_number": str(row["card_number"]).strip(),
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
