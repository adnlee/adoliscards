"""Read-only checklist diagnostics for real CardVault database rows."""

from __future__ import annotations

import pandas as pd

IDENTITY_COLUMNS = ["year", "set_name", "card_number", "parallel"]
SUSPICIOUS_CARD_NUMBERS = {"", "?", "-", "0", "n/a", "na", "none", "null", "tbd", "unknown"}


def _column(cards: pd.DataFrame, name: str, default: object = "") -> pd.Series:
    """Return a column aligned to the input frame, even when the schema is partial."""
    if name in cards:
        return cards[name]
    return pd.Series(default, index=cards.index)


def _blank(series: pd.Series) -> pd.Series:
    return series.isna() | series.fillna("").astype(str).str.strip().eq("")


def _normalized(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.casefold()


def duplicate_cards(cards: pd.DataFrame) -> pd.DataFrame:
    """Return every row participating in an exact normalized checklist duplicate."""
    if cards.empty:
        return cards.copy()
    normalized = pd.DataFrame(index=cards.index)
    for column in IDENTITY_COLUMNS:
        normalized[column] = _normalized(_column(cards, column))
    duplicate_mask = normalized.duplicated(IDENTITY_COLUMNS, keep=False)
    result = cards.loc[duplicate_mask].copy()
    if result.empty:
        return result
    result["duplicate_key"] = normalized.loc[duplicate_mask, IDENTITY_COLUMNS].agg(" | ".join, axis=1)
    sort_columns = [column for column in IDENTITY_COLUMNS if column in result]
    return result.sort_values(sort_columns, kind="stable") if sort_columns else result


def suspicious_card_number_mask(cards: pd.DataFrame) -> pd.Series:
    values = _normalized(_column(cards, "card_number"))
    suspicious_literal = values.isin(SUSPICIOUS_CARD_NUMBERS)
    punctuation_only = values.str.fullmatch(r"[^a-z0-9]+", na=False)
    repeated_placeholder = values.str.fullmatch(r"(?:x+|tba|pending)", na=False)
    return suspicious_literal | punctuation_only | repeated_placeholder


def diagnostic_masks(cards: pd.DataFrame) -> dict[str, pd.Series]:
    """Build named issue masks without writing to the database."""
    owned = _normalized(_column(cards, "status")).eq("owned")
    estimated = pd.to_numeric(_column(cards, "estimated_value", 0), errors="coerce").fillna(0)
    paid = pd.to_numeric(_column(cards, "price_paid", 0), errors="coerce").fillna(0)
    return {
        "missing_front_image": _blank(_column(cards, "image_path")),
        "missing_estimated_value": estimated.le(0),
        "owned_missing_purchase_price": owned & paid.le(0),
        "owned_missing_storage": owned & _blank(_column(cards, "storage_location")),
        "suspicious_card_number": suspicious_card_number_mask(cards),
        "blank_set_name": _blank(_column(cards, "set_name")),
        "blank_category": _blank(_column(cards, "category")),
    }


def health_summary(cards: pd.DataFrame) -> dict[str, int]:
    statuses = _normalized(_column(cards, "status"))
    masks = diagnostic_masks(cards)
    return {
        "total": len(cards),
        "owned": int(statuses.eq("owned").sum()),
        "need": int(statuses.eq("need").sum()),
        "incoming": int(statuses.eq("incoming").sum()),
        "duplicates": len(duplicate_cards(cards)),
        **{name: int(mask.sum()) for name, mask in masks.items()},
    }


def incomplete_records(cards: pd.DataFrame) -> pd.DataFrame:
    """Return one row per problematic card with an export-friendly issue column."""
    if cards.empty:
        result = cards.copy()
        result["health_issues"] = pd.Series(dtype=str)
        return result
    masks = diagnostic_masks(cards)
    labels = {
        "missing_front_image": "Missing front image",
        "missing_estimated_value": "Missing estimated value",
        "owned_missing_purchase_price": "Owned without purchase price",
        "owned_missing_storage": "Owned without storage location",
        "suspicious_card_number": "Blank or suspicious card number",
        "blank_set_name": "Blank set name",
        "blank_category": "Blank category",
    }
    issue_text = pd.Series("", index=cards.index, dtype="object")
    for name, mask in masks.items():
        issue_text.loc[mask] = issue_text.loc[mask].apply(
            lambda existing, label=labels[name]: f"{existing}; {label}".strip("; ")
        )
    affected = issue_text.ne("")
    result = cards.loc[affected].copy()
    result["health_issues"] = issue_text.loc[affected]
    return result


def missing_value_counts(cards: pd.DataFrame) -> pd.DataFrame:
    labels = {
        "image_path": "Front Image",
        "estimated_value": "Estimated Value",
        "price_paid": "Owned Purchase Price",
        "storage_location": "Owned Storage Location",
        "card_number": "Card Number",
        "set_name": "Set Name",
        "category": "Category",
    }
    summary = health_summary(cards)
    counts = {
        "image_path": summary["missing_front_image"],
        "estimated_value": summary["missing_estimated_value"],
        "price_paid": summary["owned_missing_purchase_price"],
        "storage_location": summary["owned_missing_storage"],
        "card_number": summary["suspicious_card_number"],
        "set_name": summary["blank_set_name"],
        "category": summary["blank_category"],
    }
    return pd.DataFrame([{"Check": labels[key], "Affected Cards": value} for key, value in counts.items()])


def coverage(cards: pd.DataFrame) -> float:
    """Return core checklist-field coverage for backwards-compatible reporting."""
    if cards.empty:
        return 0.0
    required = [column for column in ["year", "set_name", "card_number", "status"] if column in cards]
    if not required:
        return 0.0
    complete = pd.DataFrame({column: ~_blank(cards[column]) for column in required})
    return float(complete.to_numpy().mean() * 100)
