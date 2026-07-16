"""Canonical identity, staging audits, and safe promotion preparation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

IDENTITY_COLUMNS = ["year", "manufacturer", "set_name", "card_number", "variation"]
VERIFICATION_STATUSES = ["Pending", "Needs Review", "Verified", "Rejected", "Promoted"]


def _series(frame: pd.DataFrame, column: str, default: object = "") -> pd.Series:
    if column in frame:
        return frame[column]
    if column == "variation" and "parallel" in frame:
        return frame["parallel"]
    return pd.Series(default, index=frame.index)


def normalize_text(value: Any) -> str:
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return ""
    return " ".join(str(value).strip().casefold().split())


def identity_key(row: pd.Series | dict[str, Any]) -> str:
    """Create year|manufacturer|set|number|variation canonical identity."""
    getter = row.get
    variation = getter("variation", getter("parallel", ""))
    try:
        year = str(int(getter("year", 0)))
    except (TypeError, ValueError):
        year = normalize_text(getter("year", ""))
    return "|".join([
        year,
        normalize_text(getter("manufacturer", "")),
        normalize_text(getter("set_name", "")),
        normalize_text(getter("card_number", "")),
        normalize_text(variation),
    ])


def with_identity(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["identity_key"] = result.apply(identity_key, axis=1) if not result.empty else pd.Series(dtype=str)
    return result


def exact_duplicates(staged: pd.DataFrame) -> pd.DataFrame:
    keyed = with_identity(staged)
    return keyed[keyed.duplicated("identity_key", keep=False)].sort_values("identity_key", kind="stable")


def _conflict_rows(frame: pd.DataFrame, fixed: list[str], differing: str) -> pd.DataFrame:
    if frame.empty:
        return with_identity(frame)
    normalized = pd.DataFrame(index=frame.index)
    for column in set(fixed + [differing]):
        if column == "year":
            normalized[column] = pd.to_numeric(_series(frame, column), errors="coerce").fillna(0).astype(int).astype(str)
        else:
            normalized[column] = _series(frame, column).map(normalize_text)
    group_size = normalized.groupby(fixed, dropna=False)[differing].transform("nunique")
    result = with_identity(frame.loc[group_size.gt(1)])
    return result.sort_values(fixed + [differing], kind="stable") if not result.empty else result


def year_conflicts(staged: pd.DataFrame) -> pd.DataFrame:
    return _conflict_rows(staged, ["manufacturer", "set_name", "card_number", "variation"], "year")


def card_number_conflicts(staged: pd.DataFrame) -> pd.DataFrame:
    return _conflict_rows(staged, ["year", "manufacturer", "set_name", "variation"], "card_number")


def variation_conflicts(staged: pd.DataFrame) -> pd.DataFrame:
    return _conflict_rows(staged, ["year", "manufacturer", "set_name", "card_number"], "variation")


def probable_duplicates(staged: pd.DataFrame) -> pd.DataFrame:
    """Candidates sharing year, set, and number but not the exact identity."""
    if staged.empty:
        return with_identity(staged)
    normalized = pd.DataFrame(index=staged.index)
    normalized["year"] = pd.to_numeric(_series(staged, "year"), errors="coerce").fillna(0).astype(int)
    for column in ["set_name", "card_number"]:
        normalized[column] = _series(staged, column).map(normalize_text)
    count = normalized.groupby(["year", "set_name", "card_number"], dropna=False)["card_number"].transform("size")
    candidates = with_identity(staged.loc[count.gt(1)])
    exact_ids = set(exact_duplicates(staged).index)
    return candidates.loc[~candidates.index.isin(exact_ids)]


def audit_checklist(live: pd.DataFrame, staged: pd.DataFrame) -> dict[str, pd.DataFrame]:
    live_keyed, staged_keyed = with_identity(live), with_identity(staged)
    live_keys, staged_keys = set(live_keyed.get("identity_key", [])), set(staged_keyed.get("identity_key", []))
    source = _series(staged_keyed, "source_url").fillna("").astype(str).str.strip()
    status = _series(staged_keyed, "verification_status").fillna("Pending").astype(str)
    audits = {
        "live_missing_from_staging": live_keyed[~live_keyed["identity_key"].isin(staged_keys)],
        "staged_missing_from_live": staged_keyed[~staged_keyed["identity_key"].isin(live_keys)],
        "exact_duplicates": exact_duplicates(staged),
        "probable_duplicates": probable_duplicates(staged),
        "year_conflicts": year_conflicts(staged),
        "card_number_conflicts": card_number_conflicts(staged),
        "variation_conflicts": variation_conflicts(staged),
        "records_without_sources": staged_keyed[source.eq("")],
    }
    conflict_indexes: set[Any] = set()
    for name in ["exact_duplicates", "probable_duplicates", "year_conflicts", "card_number_conflicts", "variation_conflicts", "records_without_sources"]:
        conflict_indexes.update(audits[name].index)
    review_mask = ~status.eq("Verified") | staged_keyed.index.isin(conflict_indexes)
    audits["needs_manual_review"] = staged_keyed[review_mask]
    return audits


def normalize_staging_import(frame: pd.DataFrame, user_id: str, collection_id: str) -> list[dict[str, Any]]:
    columns = {column: column.strip().lower() for column in frame.columns}
    frame = frame.rename(columns=columns)
    aliases = {"set": "set_name", "card #": "card_number", "parallel": "variation", "brand": "manufacturer"}
    frame = frame.rename(columns={column: aliases.get(column, column) for column in frame.columns})
    for required in ["year", "set_name", "card_number"]:
        if required not in frame:
            raise ValueError(f"Verified checklist CSV must include {required}.")
    defaults = {"manufacturer": "", "card_name": "Adolis Garcia", "category": "Base", "variation": "", "serial_number": "", "priority": "Core", "source_url": "", "verification_status": "Pending", "verification_notes": ""}
    for column, default in defaults.items():
        if column not in frame:
            frame[column] = default
    records = []
    for row in frame.fillna("").to_dict("records"):
        year = int(row["year"])
        if year < 2020:
            raise ValueError(f"Checklist year {year} is earlier than 2020.")
        status = str(row["verification_status"]).strip().title() or "Pending"
        if status not in VERIFICATION_STATUSES:
            status = "Needs Review"
        records.append({
            "user_id": user_id, "collection_id": collection_id, "year": year,
            "manufacturer": str(row["manufacturer"]).strip(), "set_name": str(row["set_name"]).strip(),
            "card_number": str(row["card_number"]).strip(), "card_name": str(row["card_name"]).strip(),
            "category": str(row["category"]).strip() or "Base", "variation": str(row["variation"]).strip(),
            "serial_number": str(row["serial_number"]).strip(), "priority": str(row["priority"]).strip() or "Core",
            "source_url": str(row["source_url"]).strip(), "verification_status": status,
            "verified_at": datetime.now(timezone.utc).isoformat() if status == "Verified" else None,
            "verification_notes": str(row["verification_notes"]).strip(),
        })
    return records


def promotion_candidates(staged: pd.DataFrame, live: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return promotable and skipped rows without mutating either input."""
    staged_keyed, live_keyed = with_identity(staged), with_identity(live)
    live_keys = set(live_keyed.get("identity_key", []))
    verified = _series(staged_keyed, "verification_status").eq("Verified")
    has_source = _series(staged_keyed, "source_url").fillna("").astype(str).str.strip().ne("")
    not_existing = ~staged_keyed["identity_key"].isin(live_keys)
    not_duplicated = ~staged_keyed.duplicated("identity_key", keep=False)
    promotable_mask = verified & has_source & not_existing & not_duplicated
    return staged_keyed[promotable_mask], staged_keyed[~promotable_mask]


def live_record_from_staging(row: pd.Series | dict[str, Any], user_id: str, collection_id: str) -> dict[str, Any]:
    """Map a verified candidate to additive live-card fields only."""
    if row.get("verification_status") != "Verified":
        raise ValueError("Only records marked Verified may be promoted.")
    return {
        "user_id": user_id, "collection_id": collection_id, "year": int(row.get("year")),
        "manufacturer": str(row.get("manufacturer") or ""), "set_name": str(row.get("set_name") or ""),
        "card_number": str(row.get("card_number") or ""), "card_name": str(row.get("card_name") or "Adolis Garcia"),
        "category": str(row.get("category") or "Base"), "parallel": str(row.get("variation") or ""),
        "serial_number": str(row.get("serial_number") or ""), "priority": str(row.get("priority") or "Core"),
        "status": "Need", "source_url": str(row.get("source_url") or ""),
        "notes": str(row.get("verification_notes") or ""),
    }
