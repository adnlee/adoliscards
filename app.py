
from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
from supabase import create_client

STATUS_OPTIONS = ["Need", "Owned", "Incoming", "Upgrade Wanted", "Not Chasing", "Sold/Traded"]
PRIORITY_OPTIONS = ["Core", "Must Own", "High", "Medium", "Dream", "Grail"]
CATEGORY_OPTIONS = [
    "Base", "Insert", "Parallel", "Numbered",
    "Autograph", "Relic", "Relic/Autograph", "One of One"
]

st.set_page_config(
    page_title="CardVault",
    page_icon="🗃️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 4rem; max-width: 1280px;}
    div[data-testid="stMetric"] {
        background:#f6f8fb;
        border:1px solid #dfe5ee;
        padding:.85rem;
        border-radius:16px;
    }
    .cv-card {
        border:1px solid #dfe5ee;
        border-radius:16px;
        padding:12px;
        background:white;
        min-height:152px;
        margin-bottom:10px;
        box-shadow:0 1px 3px rgba(0,0,0,.04);
    }
    .cv-title {font-weight:700; font-size:1rem; line-height:1.25;}
    .cv-meta {color:#5b6574; font-size:.88rem; margin-top:4px;}
    .cv-pill {
        display:inline-block;
        padding:3px 8px;
        border-radius:999px;
        font-size:.76rem;
        font-weight:700;
        margin-top:8px;
    }
    .cv-owned {background:#e3f3e7;color:#1d6b34;}
    .cv-need {background:#fde8eb;color:#9e0b18;}
    .cv-incoming {background:#fff3cd;color:#7a5d00;}
    .stButton > button {border-radius:12px;}
    @media (max-width:700px) {
      .block-container {padding-left:.55rem; padding-right:.55rem;}
      h1 {font-size:1.5rem!important;}
      div[data-testid="stHorizontalBlock"] {gap:.45rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_client():
    try:
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_ANON_KEY"],
        )
    except Exception:
        st.error("Missing Supabase secrets.")
        st.stop()


def restore_session(client):
    if st.session_state.get("access_token") and st.session_state.get("refresh_token"):
        try:
            client.auth.set_session(
                st.session_state.access_token,
                st.session_state.refresh_token,
            )
        except Exception:
            for key in ("access_token", "refresh_token", "user_id", "user_email"):
                st.session_state.pop(key, None)


def save_session(response):
    if response.session and response.user:
        st.session_state.access_token = response.session.access_token
        st.session_state.refresh_token = response.session.refresh_token
        st.session_state.user_id = response.user.id
        st.session_state.user_email = response.user.email


def require_login(client):
    if st.session_state.get("user_id"):
        return

    st.title("🗃️ CardVault")
    st.caption("Your private sports-card collection manager.")

    sign_in, sign_up = st.tabs(["Sign in", "Create account"])

    with sign_in:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in", use_container_width=True)
        if submit:
            try:
                save_session(
                    client.auth.sign_in_with_password(
                        {"email": email.strip(), "password": password}
                    )
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Could not sign in: {exc}")

    with sign_up:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            submit = st.form_submit_button("Create account", use_container_width=True)
        if submit:
            try:
                response = client.auth.sign_up(
                    {"email": email.strip(), "password": password}
                )
                if response.session:
                    save_session(response)
                    st.rerun()
                st.success("Account created. Confirm your email, then sign in.")
            except Exception as exc:
                st.error(f"Could not create account: {exc}")
    st.stop()


def ensure_default_collection(client, user_id: str) -> str:
    result = (
        client.table("collections")
        .select("id,name")
        .eq("user_id", user_id)
        .order("created_at")
        .limit(1)
        .execute()
    )
    if result.data:
        collection_id = result.data[0]["id"]
    else:
        inserted = (
            client.table("collections")
            .insert({
                "user_id": user_id,
                "name": "Adolis García — Rangers Era",
                "sport": "Baseball",
                "team": "Texas Rangers",
                "player_name": "Adolis García",
                "description": "Rangers-era Adolis García personal collection",
            })
            .execute()
        )
        collection_id = inserted.data[0]["id"]

    (
        client.table("cards")
        .update({"collection_id": collection_id})
        .eq("user_id", user_id)
        .is_("collection_id", "null")
        .execute()
    )
    return collection_id


def fetch_collections(client, user_id: str) -> pd.DataFrame:
    result = (
        client.table("collections")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    return pd.DataFrame(result.data or [])


def fetch_cards(client, collection_id: str) -> pd.DataFrame:
    result = (
        client.table("cards")
        .select("*")
        .eq("collection_id", collection_id)
        .order("year", desc=True)
        .order("set_name")
        .execute()
    )
    return pd.DataFrame(result.data or [])


def upload_image(client, user_id: str, uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    ext = Path(uploaded_file.name).suffix.lower() or ".jpg"
    path = f"{user_id}/{uuid4().hex}{ext}"
    client.storage.from_("card-images").upload(
        path=path,
        file=uploaded_file.getvalue(),
        file_options={
            "content-type": uploaded_file.type,
            "upsert": "false",
        },
    )
    return path


def signed_url(client, path: str):
    if not path:
        return None
    try:
        result = client.storage.from_("card-images").create_signed_url(path, 3600)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception:
        return None


def normalize_import(df: pd.DataFrame, user_id: str, collection_id: str) -> list[dict]:
    aliases = {
        "set": "set_name",
        "brand": "manufacturer",
        "card #": "card_number",
        "card no": "card_number",
        "type": "category",
        "parallel": "variation",
        "storage": "storage_location",
    }
    df = df.rename(
        columns={c: aliases.get(c.strip().lower(), c.strip().lower()) for c in df.columns}
    )
    if "year" not in df.columns or "set_name" not in df.columns:
        raise ValueError("CSV must include year and set_name columns.")

    defaults = {
        "manufacturer": "", "card_number": "", "card_name": "Adolis Garcia",
        "category": "Base", "variation": "", "serial_numbered_to": "",
        "status": "Need", "priority": "Core", "condition": "Raw",
        "grade": "", "price_paid": 0, "estimated_value": 0,
        "date_acquired": "", "seller": "", "storage_location": "",
        "image_path": "", "source_url": "", "favorite": False, "notes": "",
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    records = []
    for row in df.fillna("").to_dict("records"):
        records.append({
            "user_id": user_id,
            "collection_id": collection_id,
            "year": int(row["year"]),
            "set_name": str(row["set_name"]).strip(),
            "card_number": str(row["card_number"]).strip(),
            "card_name": str(row["card_name"]).strip(),
            "category": str(row["category"]).strip() or "Base",
            "parallel": str(row["variation"]).strip(),
            "serial_number": str(row["serial_numbered_to"]).strip(),
            "status": str(row["status"]).strip() or "Need",
            "priority": str(row["priority"]).strip() or "Core",
            "condition": str(row["condition"]).strip() or "Raw",
            "grade": str(row["grade"]).strip(),
            "price_paid": float(row["price_paid"] or 0),
            "estimated_value": float(row["estimated_value"] or 0),
            "date_acquired": row["date_acquired"] or None,
            "seller": str(row["seller"]).strip(),
            "storage_location": str(row["storage_location"]).strip(),
            "image_path": str(row["image_path"]).strip(),
            "source_url": str(row["source_url"]).strip(),
            "favorite": bool(row["favorite"]),
            "notes": str(row["notes"]).strip(),
        })
    return records


def apply_filters(df: pd.DataFrame, *, need_only: bool = False) -> pd.DataFrame:
    filtered = df.copy()
    if need_only:
        filtered = filtered[~filtered["status"].isin(["Owned", "Incoming", "Not Chasing"])]

    years = sorted(filtered["year"].dropna().unique().tolist(), reverse=True) if not filtered.empty else []
    categories = sorted(filtered["category"].dropna().astype(str).unique().tolist()) if not filtered.empty else []
    priorities = sorted(filtered["priority"].dropna().astype(str).unique().tolist()) if not filtered.empty else []

    f1, f2, f3 = st.columns(3)
    selected_years = f1.multiselect("Year", years)
    selected_categories = f2.multiselect("Category", categories)
    selected_priorities = f3.multiselect("Priority", priorities)
    search = st.text_input("Search set, card number, parallel, or notes")
    favorites_only = st.toggle("Favorites only")

    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)]
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]
    if selected_priorities:
        filtered = filtered[filtered["priority"].isin(selected_priorities)]
    if favorites_only:
        filtered = filtered[filtered["favorite"] == True]
    if search and not filtered.empty:
        cols = ["set_name", "card_number", "card_name", "parallel", "notes"]
        mask = filtered[cols].fillna("").astype(str).apply(
            lambda col: col.str.contains(search, case=False, regex=False)
        ).any(axis=1)
        filtered = filtered[mask]

    return filtered


def gallery_card(client, row, *, quick_owned: bool = False):
    status = row.get("status") or "Need"
    pill_class = {
        "Owned": "cv-owned",
        "Incoming": "cv-incoming",
    }.get(status, "cv-need")

    image = signed_url(client, row.get("image_path", "") or "")
    if image:
        st.image(image, use_container_width=True)
    else:
        st.markdown(
            """
            <div style="height:150px;border:1px dashed #c8d0dc;border-radius:12px;
            display:flex;align-items:center;justify-content:center;color:#8893a2;
            margin-bottom:8px;">No image</div>
            """,
            unsafe_allow_html=True,
        )

    card_num = row.get("card_number") or ""
    parallel = row.get("parallel") or ""
    subtitle = " • ".join(x for x in [card_num and f"#{card_num}", parallel, row.get("category") or ""] if x)

    st.markdown(
        f"""
        <div class="cv-card">
          <div class="cv-title">{int(row['year'])} {row['set_name']}</div>
          <div class="cv-meta">{subtitle}</div>
          <span class="cv-pill {pill_class}">{status}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if quick_owned and status != "Owned":
        if st.button("Mark owned", key=f"quick_owned_{row['id']}", use_container_width=True):
            client.table("cards").update({
                "status": "Owned",
                "date_acquired": date.today().isoformat(),
            }).eq("id", row["id"]).execute()
            st.rerun()

    with st.expander("Details"):
        new_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
            key=f"status_{row['id']}",
        )
        favorite = st.toggle(
            "Favorite",
            bool(row.get("favorite", False)),
            key=f"favorite_{row['id']}",
        )
        c1, c2 = st.columns(2)
        price_paid = c1.number_input(
            "Price paid",
            min_value=0.0,
            value=float(row.get("price_paid") or 0),
            step=.25,
            key=f"paid_{row['id']}",
        )
        estimated_value = c2.number_input(
            "Estimated value",
            min_value=0.0,
            value=float(row.get("estimated_value") or 0),
            step=.25,
            key=f"value_{row['id']}",
        )
        storage = st.text_input(
            "Storage",
            value=row.get("storage_location") or "",
            key=f"storage_{row['id']}",
        )
        notes = st.text_area(
            "Notes",
            value=row.get("notes") or "",
            key=f"notes_{row['id']}",
        )

        s1, s2 = st.columns(2)
        if s1.button("Save", key=f"save_{row['id']}", use_container_width=True):
            acquired = row.get("date_acquired") or None
            if new_status == "Owned" and not acquired:
                acquired = date.today().isoformat()
            client.table("cards").update({
                "status": new_status,
                "favorite": favorite,
                "price_paid": price_paid,
                "estimated_value": estimated_value,
                "storage_location": storage,
                "notes": notes,
                "date_acquired": acquired,
            }).eq("id", row["id"]).execute()
            st.rerun()

        if s2.button("Delete", key=f"delete_{row['id']}", use_container_width=True):
            client.table("cards").delete().eq("id", row["id"]).execute()
            st.rerun()


client = get_client()
restore_session(client)
require_login(client)

user_id = st.session_state.user_id
user_email = st.session_state.user_email

ensure_default_collection(client, user_id)
collections = fetch_collections(client, user_id)
if collections.empty:
    st.error("No collection could be loaded.")
    st.stop()

collection_map = dict(zip(collections["name"], collections["id"]))
collection_names = list(collection_map.keys())

st.title("🗃️ CardVault")
st.caption(f"Signed in as {user_email}")

with st.sidebar:
    selected_name = st.selectbox("Active collection", collection_names)
    selected_collection_id = collection_map[selected_name]

    with st.expander("Create collection"):
        with st.form("new_collection_form"):
            new_name = st.text_input("Collection name")
            sport = st.text_input("Sport")
            team = st.text_input("Team")
            player_name = st.text_input("Player")
            description = st.text_area("Description")
            create = st.form_submit_button("Create collection", use_container_width=True)
        if create and new_name.strip():
            client.table("collections").insert({
                "user_id": user_id,
                "name": new_name.strip(),
                "sport": sport.strip(),
                "team": team.strip(),
                "player_name": player_name.strip(),
                "description": description.strip(),
            }).execute()
            st.rerun()

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
    ["Dashboard", "Gallery", "Need List", "Add Card", "Import", "Backup"],
    default="Dashboard",
    label_visibility="collapsed",
)

cards = fetch_cards(client, selected_collection_id)

if page == "Dashboard":
    if cards.empty:
        st.info("This collection is empty.")
    else:
        total = len(cards)
        owned = int((cards["status"] == "Owned").sum())
        need = int((cards["status"] == "Need").sum())
        incoming = int((cards["status"] == "Incoming").sum())
        spent = float(pd.to_numeric(cards["price_paid"], errors="coerce").fillna(0).sum())
        value = float(pd.to_numeric(cards["estimated_value"], errors="coerce").fillna(0).sum())

        a, b, c, d = st.columns(4)
        a.metric("Owned", f"{owned}/{total}", f"{owned/total*100:.1f}%")
        b.metric("Need", need)
        c.metric("Incoming", incoming)
        d.metric("Est. Value", f"${value:,.2f}", f"${value-spent:,.2f}")

        st.subheader("Progress by year")
        progress = (
            cards.assign(_owned=(cards["status"] == "Owned").astype(int))
            .groupby("year", as_index=False)
            .agg(Owned=("_owned", "sum"), Total=("id", "count"))
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

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("By category")
            category_counts = cards.groupby("category", as_index=False).size().rename(columns={"size": "Cards"})
            st.bar_chart(category_counts.set_index("category"))
        with c2:
            st.subheader("Recent pickups")
            recent = cards[cards["status"] == "Owned"].sort_values(
                ["date_acquired", "updated_at"], ascending=False
            ).head(8)
            if recent.empty:
                st.caption("No owned cards yet.")
            else:
                st.dataframe(
                    recent[["year", "set_name", "card_number", "date_acquired"]],
                    hide_index=True,
                    use_container_width=True,
                )

elif page in ("Gallery", "Need List"):
    filtered = apply_filters(cards, need_only=(page == "Need List"))
    st.caption(f"{len(filtered)} cards")

    columns_per_row = 2 if page == "Need List" else 3
    for start in range(0, len(filtered), columns_per_row):
        cols = st.columns(columns_per_row)
        chunk = filtered.iloc[start:start + columns_per_row]
        for col, (_, row) in zip(cols, chunk.iterrows()):
            with col:
                gallery_card(client, row, quick_owned=(page == "Need List"))

elif page == "Add Card":
    with st.form("add_card_form", clear_on_submit=True):
        year = st.number_input("Year", min_value=1900, max_value=2100, value=2026)
        set_name = st.text_input("Set *")
        card_number = st.text_input("Card number")
        card_name = st.text_input("Card name")
        category = st.selectbox("Category", CATEGORY_OPTIONS)
        parallel = st.text_input("Parallel")
        serial_number = st.text_input("Serial number")
        status = st.selectbox("Status", STATUS_OPTIONS[:-1])
        priority = st.selectbox("Priority", PRIORITY_OPTIONS)
        photo = st.file_uploader("Photo", type=["png", "jpg", "jpeg", "webp"])
        notes = st.text_area("Notes")
        add = st.form_submit_button("Add card", use_container_width=True)

    if add:
        if not set_name.strip():
            st.error("Set is required.")
        else:
            image_path = upload_image(client, user_id, photo) if photo else ""
            client.table("cards").insert({
                "user_id": user_id,
                "collection_id": selected_collection_id,
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
                "notes": notes.strip(),
                "date_acquired": date.today().isoformat() if status == "Owned" else None,
            }).execute()
            st.success("Card added.")

elif page == "Import":
    st.subheader("Import checklist CSV")
    uploaded = st.file_uploader("Choose CSV", type=["csv"])
    if uploaded:
        preview = pd.read_csv(uploaded)
        st.dataframe(preview.head(25), use_container_width=True)
        st.caption(f"{len(preview)} rows")

        if st.button("Import checklist", use_container_width=True):
            try:
                records = normalize_import(preview, user_id, selected_collection_id)
                existing = set()
                if not cards.empty:
                    existing = set(zip(
                        cards["year"].astype(str),
                        cards["set_name"].fillna("").astype(str).str.lower(),
                        cards["card_number"].fillna("").astype(str).str.lower(),
                        cards["parallel"].fillna("").astype(str).str.lower(),
                    ))

                new_records = []
                for record in records:
                    key = (
                        str(record["year"]),
                        record["set_name"].lower(),
                        record["card_number"].lower(),
                        record["parallel"].lower(),
                    )
                    if key not in existing:
                        new_records.append(record)
                        existing.add(key)

                for start in range(0, len(new_records), 100):
                    client.table("cards").insert(new_records[start:start + 100]).execute()

                st.success(
                    f"Imported {len(new_records)} cards; "
                    f"skipped {len(records) - len(new_records)} duplicates."
                )
            except Exception as exc:
                st.error(f"Import failed: {exc}")

elif page == "Backup":
    if cards.empty:
        st.info("Nothing to export.")
    else:
        csv_data = cards.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download collection CSV",
            csv_data,
            file_name=f"{selected_name.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
