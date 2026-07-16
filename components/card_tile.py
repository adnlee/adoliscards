"""Image-first card tile, quick actions, and complete detail editor."""

from __future__ import annotations

from datetime import date
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from utils.database import delete_card, signed_url, update_card, upload_image
from utils.formatting import money, text

STATUS_OPTIONS = ["Need", "Owned", "Incoming", "Not Chasing"]
CATEGORY_OPTIONS = ["Base", "Parallel", "Insert", "Numbered", "Autograph", "Relic", "Relic/Autograph", "Other"]
PRIORITY_OPTIONS = ["Core", "High", "Dream", "Grail", "Low"]
CONDITION_OPTIONS = ["Raw", "Graded", "Authenticated", "Other"]


def media_frame_html(image_url: str | None, alt_text: str = "Card front", *, detail: bool = False) -> str:
    """Render every card image path through one non-cropping media frame."""
    classes = "cv-card-image-frame cv-detail-image-frame" if detail else "cv-card-image-frame"
    if image_url:
        return (
            f'<div class="{classes}">'
            f'<img src="{escape(image_url, quote=True)}" alt="{escape(alt_text, quote=True)}" />'
            '</div>'
        )
    return (
        f'<div class="{classes} cv-card-image-placeholder">'
        '<div><b>CV</b><span>IMAGE PENDING</span><small>CardVault checklist</small></div>'
        '</div>'
    )


def _badges(row: pd.Series) -> str:
    values = []
    if row.get("favorite"):
        values.append("★ FAVORITE")
    if row.get("parallel"):
        values.append(str(row.get("parallel")))
    if row.get("serial_number"):
        values.append(f'/{row.get("serial_number")}')
    return "".join(f'<span class="cv-pill">{text(value)}</span>' for value in values)


def _choice_index(options: list[str], value: Any) -> int:
    return options.index(value) if value in options else 0


def _date_value(value: Any) -> date | None:
    if value is None or pd.isna(value) or not str(value).strip():
        return None
    try:
        return pd.to_datetime(value).date()
    except (TypeError, ValueError):
        return None


@st.dialog("Delete Card")
def _delete_confirmation(client: Any, card_id: str, image_path: str, card_label: str) -> None:
    """Require an explicit destructive confirmation before deleting a card."""
    st.warning(f"Delete {card_label}? This cannot be undone.")
    confirm, cancel = st.columns(2)
    if confirm.button("Delete permanently", type="primary", use_container_width=True, key=f"confirm_delete_{card_id}"):
        try:
            delete_card(client, card_id, image_path)
        except Exception as exc:
            st.error(f"Card could not be deleted: {exc}")
            return
        st.session_state["_cardvault_deleted_toast"] = f"Deleted {card_label}."
        st.rerun()
    if cancel.button("Cancel", use_container_width=True, key=f"cancel_delete_{card_id}"):
        st.rerun()


def card_tile(client: Any, row: pd.Series, *, compact: bool = False, quick_owned: bool = False, all_cards: pd.DataFrame | None = None) -> None:
    card_id = str(row["id"])
    image = signed_url(client, row.get("image_path"))
    alt = f"{row.get('year') or ''} {row.get('set_name') or ''} #{row.get('card_number') or ''}".strip()
    st.markdown(media_frame_html(image, alt), unsafe_allow_html=True)
    st.markdown(
        f'<div class="cv-tile-copy"><span class="cv-status {text(row.get("status", "Need")).lower().replace(" ", "-")}">{text(row.get("status", "Need"))}</span>'
        f'<h3>{text(row.get("year"))} {text(row.get("set_name"))}</h3>'
        f'<p>#{text(row.get("card_number"))} · {text(row.get("category"))}</p><div class="cv-badge-slot">{_badges(row)}</div>'
        f'<div class="cv-price">{money(row.get("estimated_value"))}</div></div>', unsafe_allow_html=True)

    action_owned, action_favorite = st.columns(2)
    if row.get("status") != "Owned":
        label = "✓ Owned" if compact or quick_owned else "Mark Owned"
        if action_owned.button(label, key=f"own_{card_id}", use_container_width=True):
            update_card(client, card_id, {"status": "Owned", "date_acquired": date.today().isoformat()})
            st.rerun()
    else:
        action_owned.caption("✓ Owned")
    favorite = bool(row.get("favorite"))
    if action_favorite.button("★" if favorite else "☆", key=f"fav_{card_id}", help="Toggle favorite", use_container_width=True):
        update_card(client, card_id, {"favorite": not favorite})
        st.rerun()

    with st.expander("Open card"):
        card_detail(client, row, all_cards=all_cards)


def card_detail(client: Any, row: pd.Series, *, all_cards: pd.DataFrame | None = None) -> None:
    """Edit every existing card field; updates target only the selected row ID."""
    card_id = str(row["id"])
    front, facts = st.columns([.85, 1.15])
    front_url = signed_url(client, row.get("image_path"))
    front.markdown(media_frame_html(front_url, "Front image", detail=True), unsafe_allow_html=True)
    facts.markdown(
        f"### {text(row.get('year'))} {text(row.get('set_name'))}\n"
        f"**Card:** #{text(row.get('card_number'))}  \n"
        f"**Parallel:** {text(row.get('parallel'))}  \n"
        f"**Serial:** {text(row.get('serial_number'))}  \n"
        f"**Status:** {text(row.get('status'))}  \n"
        f"**Value:** {money(row.get('estimated_value'))}"
    )

    with st.form(f"detail_{card_id}"):
        c1, c2 = st.columns(2)
        year = c1.number_input("Year", min_value=2020, max_value=2100, value=int(row.get("year") or date.today().year))
        set_name = c2.text_input("Set", value=str(row.get("set_name") or ""))
        card_number = c1.text_input("Card number", value=str(row.get("card_number") or ""))
        card_name = c2.text_input("Card name", value=str(row.get("card_name") or ""))
        category = c1.selectbox("Category", CATEGORY_OPTIONS, index=_choice_index(CATEGORY_OPTIONS, row.get("category")))
        parallel = c2.text_input("Parallel", value=str(row.get("parallel") or ""))
        serial = c1.text_input("Serial number", value=str(row.get("serial_number") or ""))
        status = c2.selectbox("Status", STATUS_OPTIONS, index=_choice_index(STATUS_OPTIONS, row.get("status")))
        priority = c1.selectbox("Priority", PRIORITY_OPTIONS, index=_choice_index(PRIORITY_OPTIONS, row.get("priority")))
        condition = c2.selectbox("Condition", CONDITION_OPTIONS, index=_choice_index(CONDITION_OPTIONS, row.get("condition")))
        grade = c1.text_input("Grade", value=str(row.get("grade") or ""))
        seller = c2.text_input("Seller", value=str(row.get("seller") or ""))
        paid = c1.number_input("Purchase price", min_value=0.0, value=float(row.get("price_paid") or 0), step=0.25)
        estimated = c2.number_input("Estimated value", min_value=0.0, value=float(row.get("estimated_value") or 0), step=0.25)
        acquired = c1.date_input("Date acquired", value=_date_value(row.get("date_acquired")), format="MM/DD/YYYY")
        storage = c2.text_input("Storage location", value=str(row.get("storage_location") or ""))
        source_url = st.text_input("Checklist source URL", value=str(row.get("source_url") or ""))
        notes = st.text_area("Notes", value=str(row.get("notes") or ""))
        favorite = st.toggle("Favorite", value=bool(row.get("favorite")))
        image = st.file_uploader("Upload or replace front image", type=["jpg", "jpeg", "png", "webp"])
        saved = st.form_submit_button("Save Card", use_container_width=True)
    if saved:
        if not set_name.strip():
            st.error("Set name cannot be blank.")
        else:
            image_path = row.get("image_path") or ""
            if image:
                image_path = upload_image(client, st.session_state.user_id, image)
            if status == "Owned" and acquired is None:
                acquired = date.today()
            update_card(client, card_id, {
                "year": int(year), "set_name": set_name.strip(), "card_number": card_number.strip(),
                "card_name": card_name.strip(), "category": category, "parallel": parallel.strip(),
                "serial_number": serial.strip(), "status": status, "priority": priority,
                "condition": condition, "grade": grade.strip(), "price_paid": paid,
                "estimated_value": estimated, "date_acquired": acquired.isoformat() if acquired else None,
                "seller": seller.strip(), "storage_location": storage.strip(), "source_url": source_url.strip(),
                "favorite": favorite, "notes": notes.strip(), "image_path": image_path,
            })
            st.success("Card details saved.")
            st.rerun()

    if st.button("Delete Card", type="primary", use_container_width=True, key=f"delete_{card_id}"):
        label = f"{text(row.get('year'))} {text(row.get('set_name'))} #{text(row.get('card_number'))}"
        _delete_confirmation(client, card_id, str(row.get("image_path") or ""), label)

    if all_cards is not None and not all_cards.empty:
        related = all_cards[
            all_cards["year"].eq(row.get("year"))
            & all_cards["set_name"].fillna("").eq(row.get("set_name"))
            & all_cards["id"].astype(str).ne(card_id)
        ].head(6)
        if not related.empty:
            st.markdown("#### Related cards")
            for related_row in related.itertuples():
                st.caption(f"#{getattr(related_row, 'card_number', '') or '—'} · {getattr(related_row, 'parallel', '') or getattr(related_row, 'category', '') or 'Card'} · {getattr(related_row, 'status', '')}")
