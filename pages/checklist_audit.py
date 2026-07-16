"""Verified master-checklist staging, audit, review, and safe promotion UI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from components.page_title import page_title
from utils.database import fetch_cards, fetch_staged_cards, insert_card, insert_staged_cards, update_staged_card
from utils.master_checklist import (
    VERIFICATION_STATUSES,
    audit_checklist,
    identity_key,
    live_record_from_staging,
    normalize_staging_import,
    promotion_candidates,
    with_identity,
)

AUDIT_LABELS = {
    "live_missing_from_staging": "Live missing from staging",
    "staged_missing_from_live": "Staged missing from live",
    "exact_duplicates": "Exact duplicates",
    "probable_duplicates": "Probable duplicates",
    "year_conflicts": "Year conflicts",
    "card_number_conflicts": "Card-number conflicts",
    "variation_conflicts": "Variation conflicts",
    "records_without_sources": "Without sources",
    "needs_manual_review": "Needs manual review",
}


def _csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def _staging_import(client: Any, staged: pd.DataFrame, user_id: str, collection_id: str) -> None:
    st.subheader("Stage a verified checklist CSV")
    st.caption("Candidates are isolated from live cards. Importing never creates or changes a collection card.")
    upload = st.file_uploader("Verified checklist CSV", type=["csv"], key="staging_csv")
    if not upload:
        return
    preview = pd.read_csv(upload, dtype={"card_number": str})
    st.dataframe(preview.head(50), hide_index=True, use_container_width=True)
    try:
        records = normalize_staging_import(preview, user_id, collection_id)
    except Exception as exc:
        st.error(f"Checklist validation failed: {exc}")
        return
    existing_keys = set(with_identity(staged).get("identity_key", []))
    fresh, duplicates = [], []
    for record in records:
        if identity_key(record) in existing_keys:
            duplicates.append(record)
        else:
            fresh.append(record)
            existing_keys.add(identity_key(record))
    st.caption(f"{len(fresh)} new candidates · {len(duplicates)} exact staged duplicates skipped")
    if st.button("Import candidates to staging", disabled=not fresh, use_container_width=True):
        insert_staged_cards(client, fresh)
        st.success(f"Staged {len(fresh)} candidate records. No live cards were changed.")
        st.rerun()


def _audit_exports(live: pd.DataFrame, staged: pd.DataFrame) -> None:
    audits = audit_checklist(live, staged)
    st.subheader("Checklist audit")
    metric_columns = st.columns(3)
    metric_columns[0].metric("Live cards", len(live))
    metric_columns[1].metric("Staged candidates", len(staged))
    metric_columns[2].metric("Needs review", len(audits["needs_manual_review"]))
    tabs = st.tabs(list(AUDIT_LABELS.values()))
    for tab, (key, label) in zip(tabs, AUDIT_LABELS.items()):
        frame = audits[key]
        with tab:
            st.caption(f"{len(frame)} records")
            st.download_button(
                f"Export {label} CSV", _csv(frame), file_name=f"cardvault_{key}.csv",
                mime="text/csv", disabled=frame.empty, key=f"export_{key}", use_container_width=True,
            )
            if frame.empty:
                st.success("No records in this audit category.")
            else:
                st.dataframe(frame, hide_index=True, use_container_width=True)


def _review_staging(client: Any, staged: pd.DataFrame) -> None:
    st.subheader("Manual review")
    if staged.empty:
        st.info("Import candidate records to begin review.")
        return
    labels = {
        str(row.id): f"{int(row.year)} · {getattr(row, 'manufacturer', '') or '—'} · {row.set_name} · #{row.card_number or '—'} · {getattr(row, 'variation', '') or 'Base'}"
        for row in staged.itertuples()
    }
    selected_id = st.selectbox("Candidate", list(labels), format_func=labels.get)
    row = staged[staged["id"].astype(str).eq(selected_id)].iloc[0]
    with st.form("candidate_review"):
        source_url = st.text_input("Source URL", value=str(row.get("source_url") or ""))
        status = st.selectbox("Verification status", VERIFICATION_STATUSES, index=VERIFICATION_STATUSES.index(row.get("verification_status")) if row.get("verification_status") in VERIFICATION_STATUSES else 0)
        notes = st.text_area("Verification notes", value=str(row.get("verification_notes") or ""))
        save = st.form_submit_button("Save review", use_container_width=True)
    if save:
        if status == "Verified" and not source_url.strip():
            st.error("A source URL is required before a candidate can be marked Verified.")
        else:
            update_staged_card(client, selected_id, {
                "source_url": source_url.strip(), "verification_status": status,
                "verification_notes": notes.strip(),
                "verified_at": datetime.now(timezone.utc).isoformat() if status == "Verified" else None,
            })
            st.success("Review saved.")
            st.rerun()


def _promotion(client: Any, live: pd.DataFrame, staged: pd.DataFrame, user_id: str, collection_id: str) -> None:
    st.subheader("Reviewed promotion")
    promotable, skipped = promotion_candidates(staged, live)
    st.caption(f"{len(promotable)} verified candidates eligible · {len(skipped)} candidates blocked or already live")
    if promotable.empty:
        st.info("No verified, unique candidates are currently eligible for promotion.")
        return
    label_map = {
        str(row.id): f"{int(row.year)} · {row.set_name} · #{row.card_number or '—'} · {getattr(row, 'variation', '') or 'Base'}"
        for row in promotable.itertuples()
    }
    selected = st.multiselect("Verified candidates to promote", list(label_map), format_func=label_map.get)
    confirmed = st.checkbox("I reviewed these verified records and want to add them as Need cards.")
    if st.button("Promote selected records", disabled=not selected or not confirmed, type="primary", use_container_width=True):
        # Re-read live rows immediately before inserts to avoid stale duplicate checks.
        latest_live = fetch_cards(client, collection_id)
        latest_staged = fetch_staged_cards(client, collection_id)
        latest_promotable, _ = promotion_candidates(latest_staged, latest_live)
        latest_promotable = latest_promotable[latest_promotable["id"].astype(str).isin(selected)]
        inserted = 0
        for _, row in latest_promotable.iterrows():
            insert_card(client, live_record_from_staging(row, user_id, collection_id))
            update_staged_card(client, str(row["id"]), {"verification_status": "Promoted"})
            inserted += 1
        st.success(f"Promoted {inserted} verified records. Existing live cards were not changed.")
        st.rerun()


def render(client: Any, live: pd.DataFrame, user_id: str, collection_id: str) -> None:
    page_title("Checklist Audit", "Stage verified external checklists, resolve conflicts, and promote reviewed records safely.")
    try:
        staged = fetch_staged_cards(client, collection_id)
    except Exception as exc:
        st.error("Checklist staging is not installed. Run cardvault_checklist_staging_migration.sql in Supabase first.")
        st.caption(str(exc))
        return
    import_tab, audit_tab, review_tab, promote_tab = st.tabs(["Import to staging", "Audit", "Review", "Promote"])
    with import_tab:
        _staging_import(client, staged, user_id, collection_id)
    with audit_tab:
        _audit_exports(live, staged)
    with review_tab:
        _review_staging(client, staged)
    with promote_tab:
        _promotion(client, live, staged, user_id, collection_id)
