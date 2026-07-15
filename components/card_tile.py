"""Image-first card tile and complete card-detail editor."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from utils.database import signed_url, update_card, upload_image
from utils.formatting import money, text

STATUS_OPTIONS = ["Need", "Owned", "Incoming", "Not Chasing"]


def _badges(row: pd.Series) -> str:
    values = []
    if row.get("favorite"):
        values.append("★ FAVORITE")
    if row.get("parallel"):
        values.append(str(row.get("parallel")))
    if row.get("serial_number"):
        values.append(f'/{row.get("serial_number")}')
    return "".join(f'<span class="cv-pill">{text(value)}</span>' for value in values)


def card_tile(client: Any, row: pd.Series, *, compact: bool = False, quick_owned: bool = False) -> None:
    card_id = str(row["id"])
    image = signed_url(client, row.get("image_path"))
    if image:
        st.image(image, use_container_width=True)
    else:
        st.markdown('<div class="cv-placeholder"><b>CV</b><span>Front image needed</span></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="cv-tile-copy"><span class="cv-status {text(row.get("status", "Need")).lower().replace(" ", "-")}">{text(row.get("status", "Need"))}</span>'
        f'<h3>{text(row.get("year"))} {text(row.get("set_name"))}</h3>'
        f'<p>#{text(row.get("card_number"))} · {text(row.get("category"))}</p>{_badges(row)}'
        f'<div class="cv-price">{money(row.get("estimated_value"))}</div></div>', unsafe_allow_html=True)
    if quick_owned and row.get("status") != "Owned" and st.button("Mark owned", key=f"own_{card_id}", use_container_width=True):
        update_card(client, card_id, {"status": "Owned", "date_acquired": date.today().isoformat()})
        st.rerun()
    with st.expander("Card details"):
        card_detail(client, row)


def card_detail(client: Any, row: pd.Series) -> None:
    """Render all stored card fields and safe edits without schema changes."""
    card_id = str(row["id"])
    front, back = st.columns(2)
    front_url = signed_url(client, row.get("image_path"))
    if front_url:
        front.image(front_url, caption="Front", use_container_width=True)
    else:
        front.caption("No front image")
    back.caption("Back image is not present in the current schema.")
    c1, c2 = st.columns(2)
    c1.markdown(f"**Year**  \n{text(row.get('year'))}\n\n**Set**  \n{text(row.get('set_name'))}\n\n**Card number**  \n{text(row.get('card_number'))}")
    c2.markdown(f"**Parallel**  \n{text(row.get('parallel'))}\n\n**Serial number**  \n{text(row.get('serial_number'))}\n\n**Condition / grade**  \n{text(row.get('condition'))} · {text(row.get('grade'))}")
    with st.form(f"detail_{card_id}"):
        a, b = st.columns(2)
        status = a.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(row.get("status")) if row.get("status") in STATUS_OPTIONS else 0)
        favorite = b.toggle("Favorite", value=bool(row.get("favorite")))
        paid = a.number_input("Purchase price", min_value=0.0, value=float(row.get("price_paid") or 0), step=0.25)
        value = b.number_input("Estimated value", min_value=0.0, value=float(row.get("estimated_value") or 0), step=0.25)
        storage = st.text_input("Storage", value=str(row.get("storage_location") or ""))
        notes = st.text_area("Notes", value=str(row.get("notes") or ""))
        image = st.file_uploader("Replace front image", type=["jpg", "jpeg", "png", "webp"])
        saved = st.form_submit_button("Save card", use_container_width=True)
    if saved:
        image_path = row.get("image_path") or ""
        if image:
            image_path = upload_image(client, st.session_state.user_id, image)
        acquired = row.get("date_acquired") or (date.today().isoformat() if status == "Owned" else None)
        update_card(client, card_id, {"status": status, "favorite": favorite, "price_paid": paid, "estimated_value": value, "storage_location": storage, "notes": notes, "image_path": image_path, "date_acquired": acquired})
        st.success("Card saved.")
        st.rerun()
