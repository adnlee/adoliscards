
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st
from supabase import Client, create_client

st.set_page_config(
    page_title="Adolis Rangers PC",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 5rem; max-width: 1250px;}
    div[data-testid="stMetric"] {
        background: #f5f8fc; border: 1px solid #dfe5ee;
        padding: .8rem; border-radius: 14px;
    }
    .stButton > button {border-radius: 12px;}
    @media (max-width: 700px) {
      .block-container {padding-left: .65rem; padding-right: .65rem;}
      h1 {font-size: 1.65rem !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_OPTIONS = ["Need", "Owned", "Incoming", "Upgrade Wanted", "Not Chasing", "Sold/Traded"]
PRIORITY_OPTIONS = ["Core", "Must Own", "High", "Medium", "Dream", "Grail"]
CATEGORY_OPTIONS = ["Base", "Insert", "Parallel", "Numbered", "Autograph", "Relic", "One of One"]

SEED_CARDS = [
    (2021, "Topps Now", "405", "Rookie's 2-HR Game", "Insert"),
    (2021, "Topps Archives", "215", "Base", "Base"),
    (2021, "Topps Living Set", "424", "Living Set", "Insert"),
    (2022, "Topps", "", "Rangers card", "Base"),
    (2022, "Topps Chrome", "", "Rangers card", "Base"),
    (2022, "Topps Stadium Club", "", "Rangers card", "Base"),
    (2022, "Topps Heritage", "", "Rangers card", "Base"),
    (2022, "Topps Allen & Ginter", "", "Rangers card", "Base"),
    (2022, "Topps Finest", "", "Rangers card", "Base"),
    (2023, "Topps", "", "Rangers card", "Base"),
    (2023, "Topps Chrome", "", "Rangers card", "Base"),
    (2023, "Topps Stadium Club", "", "Rangers card", "Base"),
    (2023, "Topps Heritage", "", "Rangers card", "Base"),
    (2023, "Topps Finest", "", "Rangers card", "Base"),
    (2023, "Topps Cosmic Chrome", "", "Rangers card", "Base"),
    (2023, "Topps Chrome Black", "", "Rangers card", "Base"),
    (2023, "Topps Museum Collection", "", "Rangers card", "Base"),
    (2023, "Topps Tribute", "", "Rangers card", "Base"),
    (2024, "Topps Series 1", "106", "League Leaders", "Base"),
    (2024, "Topps Chrome", "", "Rangers card", "Base"),
    (2024, "Topps Finest", "", "Rangers card", "Base"),
    (2024, "Topps Archives Signature Series", "", "Buyback Autograph", "Autograph"),
    (2025, "Topps Series 1", "247", "Base", "Base"),
    (2025, "Topps Chrome", "90CB-4", "1990 Topps 35th Anniversary", "Insert"),
    (2025, "Topps Holiday", "PR-AG", "Player Relic", "Relic"),
    (2025, "Topps Definitive", "DHC-AG", "Helmet Collection", "Relic"),
    (2026, "Topps", "318", "Orange Sandglitter /25", "Numbered"),
]


def get_client() -> Client:
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
    except Exception:
        st.error("Supabase secrets are missing. Add them in Streamlit Cloud or .streamlit/secrets.toml.")
        st.stop()


def restore_session(client: Client) -> None:
    if st.session_state.get("access_token") and st.session_state.get("refresh_token"):
        try:
            client.auth.set_session(
                st.session_state.access_token,
                st.session_state.refresh_token,
            )
        except Exception:
            for key in ("access_token", "refresh_token", "user_id", "user_email"):
                st.session_state.pop(key, None)


def save_session(response: Any) -> None:
    session = response.session
    user = response.user
    if session and user:
        st.session_state.access_token = session.access_token
        st.session_state.refresh_token = session.refresh_token
        st.session_state.user_id = user.id
        st.session_state.user_email = user.email


def require_login(client: Client) -> None:
    if st.session_state.get("user_id"):
        return

    st.title("⚾ Adolis García Rangers PC")
    st.caption("Your private cloud card collection.")

    tab1, tab2 = st.tabs(["Sign in", "Create account"])
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in", use_container_width=True)
        if submit:
            try:
                response = client.auth.sign_in_with_password(
                    {"email": email.strip(), "password": password}
                )
                save_session(response)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not sign in: {exc}")

    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password", type="password", key="signup_password",
                help="Use at least 8 characters."
            )
            submit = st.form_submit_button("Create account", use_container_width=True)
        if submit:
            try:
                response = client.auth.sign_up(
                    {"email": email.strip(), "password": password}
                )
                if response.session:
                    save_session(response)
                    st.rerun()
                st.success("Account created. Check your email to confirm it, then sign in.")
            except Exception as exc:
                st.error(f"Could not create account: {exc}")
    st.stop()


def fetch_cards(client: Client) -> pd.DataFrame:
    result = (
        client.table("cards")
        .select("*")
        .order("year", desc=True)
        .order("set_name")
        .execute()
    )
    rows = result.data or []
    if not rows:
        return pd.DataFrame(columns=[
            "id","user_id","year","set_name","card_number","card_name","category",
            "parallel","serial_number","status","priority","condition","grade",
            "price_paid","estimated_value","date_acquired","seller","storage_location",
            "image_path","source_url","favorite","notes","created_at","updated_at"
        ])
    return pd.DataFrame(rows)


def seed_collection(client: Client, user_id: str) -> None:
    payload = [{
        "user_id": user_id,
        "year": year,
        "set_name": set_name,
        "card_number": card_number,
        "card_name": card_name,
        "category": category,
        "status": "Need",
        "priority": "Core",
    } for year, set_name, card_number, card_name, category in SEED_CARDS]
    client.table("cards").insert(payload).execute()


def upload_image(client: Client, user_id: str, uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    ext = Path(uploaded_file.name).suffix.lower() or ".jpg"
    path = f"{user_id}/{uuid4().hex}{ext}"
    client.storage.from_("card-images").upload(
        path=path,
        file=uploaded_file.getvalue(),
        file_options={"content-type": uploaded_file.type, "upsert": "false"},
    )
    return path


def signed_image_url(client: Client, path: str) -> str | None:
    if not path:
        return None
    try:
        response = client.storage.from_("card-images").create_signed_url(path, 3600)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None




def _clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _clean_text(value).lower() in {"1", "true", "yes", "y", "owned"}


def normalize_import_rows(df: pd.DataFrame, user_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Map common checklist CSV columns to the existing Supabase cards table."""
    aliases = {
        "set": "set_name",
        "brand_set": "set_name",
        "brand / set": "set_name",
        "card #": "card_number",
        "card_no": "card_number",
        "name": "card_name",
        "card": "card_name",
        "variation": "parallel",
        "serial_numbered_to": "serial_number",
        "serial #": "serial_number",
        "image_url": "external_image_url",
    }
    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower()
        renamed[col] = aliases.get(key, key.replace(" ", "_"))
    work = df.rename(columns=renamed).copy()

    errors: list[str] = []
    if "year" not in work.columns:
        errors.append("Missing required column: year")
    if "set_name" not in work.columns:
        errors.append("Missing required column: set_name (or set)")
    if errors:
        return [], errors

    payload: list[dict[str, Any]] = []
    for idx, row in work.iterrows():
        try:
            year = int(float(row.get("year")))
        except Exception:
            errors.append(f"Row {idx + 2}: invalid year")
            continue
        set_name = _clean_text(row.get("set_name"))
        if not set_name:
            errors.append(f"Row {idx + 2}: set_name is blank")
            continue

        owned_value = row.get("owned", False)
        status = _clean_text(row.get("status")) or ("Owned" if _as_bool(owned_value) else "Need")
        if status not in STATUS_OPTIONS:
            status = "Need"

        category = _clean_text(row.get("category")) or "Base"
        parallel = _clean_text(row.get("parallel"))
        card_name = _clean_text(row.get("card_name"))
        manufacturer = _clean_text(row.get("manufacturer"))
        verification = _clean_text(row.get("verification_status"))
        notes = _clean_text(row.get("notes"))
        external_image_url = _clean_text(row.get("external_image_url"))
        extra_notes = []
        if manufacturer:
            extra_notes.append(f"Manufacturer: {manufacturer}")
        if verification:
            extra_notes.append(f"Verification: {verification}")
        if external_image_url:
            extra_notes.append(f"External image URL: {external_image_url}")
        if extra_notes:
            notes = (notes + " | " if notes else "") + " | ".join(extra_notes)

        payload.append({
            "user_id": user_id,
            "year": year,
            "set_name": set_name,
            "card_number": _clean_text(row.get("card_number")),
            "card_name": card_name,
            "category": category,
            "parallel": parallel,
            "serial_number": _clean_text(row.get("serial_number")),
            "status": status,
            "priority": _clean_text(row.get("priority")) or "Core",
            "condition": _clean_text(row.get("condition")) or "Raw",
            "grade": _clean_text(row.get("grade")),
            "price_paid": float(row.get("price_paid") or 0),
            "estimated_value": float(row.get("estimated_value") or 0),
            "date_acquired": _clean_text(row.get("date_acquired")) or None,
            "seller": _clean_text(row.get("seller")),
            "storage_location": _clean_text(row.get("storage_location") or row.get("storage")),
            "image_path": "",
            "source_url": _clean_text(row.get("source_url")),
            "favorite": _as_bool(row.get("favorite", False)),
            "notes": notes,
        })
    return payload, errors


def card_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("year", "")).strip(),
        _clean_text(row.get("set_name")).lower(),
        _clean_text(row.get("card_number")).lower(),
        _clean_text(row.get("card_name")).lower(),
        _clean_text(row.get("parallel")).lower(),
    )

client = get_client()
restore_session(client)
require_login(client)

user_id = st.session_state.user_id
user_email = st.session_state.user_email

st.title("⚾ Adolis García — Rangers Era PC")
st.caption(f"Signed in as {user_email}")

with st.sidebar:
    st.subheader("Account")
    st.write(user_email)
    if st.button("Sign out", use_container_width=True):
        try:
            client.auth.sign_out()
        except Exception:
            pass
        for key in ("access_token", "refresh_token", "user_id", "user_email"):
            st.session_state.pop(key, None)
        st.rerun()

page = st.segmented_control(
    "View",
    ["Dashboard", "Collection", "Need It", "Add Card", "Import", "Backup"],
    default="Dashboard",
    label_visibility="collapsed",
)

cards = fetch_cards(client)

if cards.empty:
    st.info("Your cloud collection is empty.")
    if st.button("Load starter Rangers-era checklist", use_container_width=True):
        seed_collection(client, user_id)
        st.success("Starter checklist loaded.")
        st.rerun()

elif page == "Dashboard":
    total = len(cards)
    owned = int((cards["status"] == "Owned").sum())
    incoming = int((cards["status"] == "Incoming").sum())
    spent = float(pd.to_numeric(cards["price_paid"], errors="coerce").fillna(0).sum())
    value = float(pd.to_numeric(cards["estimated_value"], errors="coerce").fillna(0).sum())

    a, b = st.columns(2)
    a.metric("Owned", f"{owned} / {total}", f"{owned / total * 100:.1f}% complete")
    b.metric("Incoming", incoming)
    c, d = st.columns(2)
    c.metric("Total Spent", f"${spent:,.2f}")
    d.metric("Estimated Value", f"${value:,.2f}", f"${value-spent:,.2f}")

    st.subheader("Progress by year")
    progress = (
        cards.assign(owned=(cards["status"] == "Owned").astype(int))
        .groupby("year", as_index=False)
        .agg(Owned=("owned", "sum"), Total=("id", "count"))
    )
    progress["Completion %"] = progress["Owned"] / progress["Total"] * 100
    st.dataframe(
        progress,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Completion %": st.column_config.ProgressColumn(
                "Completion", min_value=0, max_value=100, format="%.1f%%"
            )
        },
    )

elif page in ("Collection", "Need It"):
    st.subheader("Need It mode" if page == "Need It" else "Collection")
    years = sorted(cards["year"].dropna().unique().tolist(), reverse=True)
    categories = sorted(cards["category"].dropna().unique().tolist())

    f1, f2 = st.columns(2)
    selected_years = f1.multiselect("Year", years)
    selected_categories = f2.multiselect("Category", categories)
    search = st.text_input("Search set, card number, variation, or notes")
    favorites_only = st.toggle("Favorites only")

    filtered = cards.copy()
    if page == "Need It":
        filtered = filtered[~filtered["status"].isin(["Owned", "Incoming", "Not Chasing"])]
    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)]
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]
    if favorites_only:
        filtered = filtered[filtered["favorite"] == True]
    if search:
        cols = ["set_name","card_number","card_name","parallel","notes"]
        mask = filtered[cols].fillna("").astype(str).apply(
            lambda col: col.str.contains(search, case=False, regex=False)
        ).any(axis=1)
        filtered = filtered[mask]

    st.caption(f"{len(filtered)} cards")

    for _, row in filtered.iterrows():
        label = (
            f"{'✅' if row['status']=='Owned' else '⬜'} "
            f"{int(row['year'])} {row['set_name']} #{row.get('card_number','') or ''} — "
            f"{row.get('card_name','') or row.get('parallel','') or row.get('category','')}"
        )
        with st.expander(label):
            image_url = signed_image_url(client, row.get("image_path", "") or "")
            if image_url:
                st.image(image_url, width=260)

            status = st.selectbox(
                "Status", STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(row["status"]) if row["status"] in STATUS_OPTIONS else 0,
                key=f"status_{row['id']}"
            )
            favorite = st.toggle("Favorite", bool(row.get("favorite", False)), key=f"fav_{row['id']}")

            x, y = st.columns(2)
            price_paid = x.number_input(
                "Price paid", min_value=0.0,
                value=float(row.get("price_paid") or 0),
                step=0.25, key=f"paid_{row['id']}"
            )
            estimated_value = y.number_input(
                "Estimated value", min_value=0.0,
                value=float(row.get("estimated_value") or 0),
                step=0.25, key=f"value_{row['id']}"
            )
            storage = st.text_input(
                "Storage", value=row.get("storage_location") or "",
                key=f"storage_{row['id']}"
            )
            notes = st.text_area(
                "Notes", value=row.get("notes") or "",
                key=f"notes_{row['id']}"
            )
            photo = st.file_uploader(
                "Add/replace photo", type=["png","jpg","jpeg","webp"],
                key=f"photo_{row['id']}"
            )

            c1, c2 = st.columns(2)
            if c1.button("Save", key=f"save_{row['id']}", use_container_width=True):
                image_path = row.get("image_path") or ""
                if photo:
                    image_path = upload_image(client, user_id, photo)
                acquired = row.get("date_acquired") or None
                if status == "Owned" and not acquired:
                    acquired = date.today().isoformat()
                payload = {
                    "status": status,
                    "favorite": favorite,
                    "price_paid": price_paid,
                    "estimated_value": estimated_value,
                    "storage_location": storage,
                    "notes": notes,
                    "image_path": image_path,
                    "date_acquired": acquired,
                }
                (
                    client.table("cards")
                    .update(payload)
                    .eq("id", row["id"])
                    .execute()
                )
                st.success("Saved")
                st.rerun()

            if c2.button("Delete", key=f"delete_{row['id']}", use_container_width=True):
                client.table("cards").delete().eq("id", row["id"]).execute()
                st.rerun()

elif page == "Add Card":
    st.subheader("Add a Rangers-era Adolis card")
    with st.form("add_card", clear_on_submit=True):
        year = st.number_input("Year", min_value=2021, max_value=2100, value=2026, step=1)
        set_name = st.text_input("Brand / set *")
        card_number = st.text_input("Card number")
        card_name = st.text_input("Card name / variation")
        category = st.selectbox("Category", CATEGORY_OPTIONS)
        parallel = st.text_input("Parallel")
        serial_number = st.text_input("Serial number")
        status = st.selectbox("Status", STATUS_OPTIONS[:-1])
        priority = st.selectbox("Priority", PRIORITY_OPTIONS)
        image = st.file_uploader("Card photo", type=["png","jpg","jpeg","webp"])
        source_url = st.text_input("Checklist or listing URL")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add card", use_container_width=True)

    if submitted:
        if not set_name.strip():
            st.error("Brand / set is required.")
        else:
            try:
                image_path = upload_image(client, user_id, image) if image else ""
                payload = {
                    "user_id": user_id,
                    "year": int(year),
                    "set_name": set_name.strip(),
                    "card_number": card_number.strip(),
                    "card_name": card_name.strip(),
                    "category": category,
                    "parallel": parallel.strip(),
                    "serial_number": serial_number.strip(),
                    "status": status,
                    "priority": priority,
                    "image_path": image_path,
                    "source_url": source_url.strip(),
                    "notes": notes.strip(),
                    "date_acquired": date.today().isoformat() if status == "Owned" else None,
                }
                client.table("cards").insert(payload).execute()
                st.success("Card added.")
            except Exception as exc:
                st.error(f"Could not add card: {exc}")


elif page == "Import":
    st.subheader("Import checklist CSV")
    st.write("Upload a checklist once; the importer maps common column names and skips exact duplicates.")
    uploaded = st.file_uploader("Choose CSV", type=["csv"], key="checklist_import")
    remove_starters = st.checkbox(
        "Delete the original 27 starter rows before importing",
        value=False,
        help="Use this only if you have not already edited or marked those starter rows as owned.",
    )

    if uploaded is not None:
        try:
            incoming_df = pd.read_csv(uploaded).fillna("")
            st.caption(f"{len(incoming_df)} rows found")
            st.dataframe(incoming_df.head(25), hide_index=True, use_container_width=True)
            normalized, import_errors = normalize_import_rows(incoming_df, user_id)
            if import_errors:
                st.error("Please fix these issues before importing:")
                for message in import_errors[:20]:
                    st.write(f"- {message}")
            else:
                existing_keys = {card_key(row) for row in cards.to_dict("records")}
                unique_rows = []
                seen = set(existing_keys)
                skipped = 0
                for row in normalized:
                    key = card_key(row)
                    if key in seen:
                        skipped += 1
                        continue
                    seen.add(key)
                    unique_rows.append(row)

                c1, c2, c3 = st.columns(3)
                c1.metric("Ready to import", len(unique_rows))
                c2.metric("Duplicates skipped", skipped)
                c3.metric("Rows in file", len(normalized))

                confirm = st.checkbox("I reviewed the preview and want to import these cards")
                if st.button(
                    "Import checklist",
                    use_container_width=True,
                    disabled=not confirm or not unique_rows,
                    type="primary",
                ):
                    try:
                        if remove_starters:
                            # Protect edited collection data: only delete untouched seed-like rows.
                            client.table("cards").delete().eq("status", "Need").eq("price_paid", 0).eq("estimated_value", 0).execute()
                        batch_size = 200
                        for start in range(0, len(unique_rows), batch_size):
                            client.table("cards").insert(unique_rows[start:start + batch_size]).execute()
                        st.success(f"Imported {len(unique_rows)} cards. Skipped {skipped} duplicates.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Import failed: {exc}")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")

elif page == "Backup":
    st.subheader("Export your collection")
    export = cards.copy()
    csv = export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV backup",
        csv,
        file_name="adolis_rangers_cloud_collection.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.caption("Photos remain in Supabase Storage. The CSV includes their storage paths.")
