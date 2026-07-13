
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
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
      --navy:#081426;
      --navy2:#0d1c31;
      --red:#d91f35;
      --green:#1f9d55;
      --gold:#d99a21;
      --blue:#377dff;
      --text:#10213b;
      --muted:#68758a;
      --line:#e7ebf1;
      --soft:#f7f9fc;
      --white:#ffffff;
    }

    html, body, [class*="css"] {
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp { background:var(--soft); }
    .block-container { padding:1rem 1.35rem 3rem; max-width:1600px; }

    section[data-testid="stSidebar"] {
      background:linear-gradient(180deg,var(--navy),#0a172a 78%);
      border-right:1px solid rgba(255,255,255,.05);
    }

    section[data-testid="stSidebar"] * { color:#f6f8fb; }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea {
      color:#10213b !important;
    }

    .brand-wrap { padding:.25rem .1rem 1rem; }
    .brand {
      font-size:1.7rem;
      font-weight:900;
      letter-spacing:-.045em;
      line-height:1;
    }
    .brand span { color:var(--red); }
    .brand-sub {
      margin-top:6px;
      color:#9fb0c5;
      font-size:.72rem;
      letter-spacing:.03em;
    }

    .profile-box {
      background:rgba(255,255,255,.065);
      border:1px solid rgba(255,255,255,.08);
      border-radius:18px;
      padding:14px;
      margin:4px 0 16px;
    }

    .profile-title { font-weight:850; font-size:1rem; }
    .profile-sub { color:#b6c2d2; font-size:.82rem; margin-top:3px; }
    .profile-count {
      display:inline-block;
      margin-top:9px;
      background:rgba(255,255,255,.11);
      border-radius:999px;
      padding:4px 9px;
      font-size:.76rem;
      font-weight:800;
    }

    div[data-testid="stRadio"] label {
      border-radius:12px;
      padding:7px 9px;
      margin:1px 0;
      transition:.15s ease;
    }
    div[data-testid="stRadio"] label:hover {
      background:rgba(255,255,255,.07);
    }

    .page-head {
      display:flex;
      align-items:flex-start;
      justify-content:space-between;
      gap:16px;
      margin-bottom:14px;
    }

    .page-title {
      font-size:2.05rem;
      font-weight:900;
      letter-spacing:-.04em;
      color:var(--text);
      line-height:1.05;
    }

    .page-subtitle {
      color:var(--muted);
      font-size:.92rem;
      margin-top:6px;
    }

    .metric-grid {
      display:grid;
      grid-template-columns:repeat(4,minmax(0,1fr));
      gap:16px;
      margin-bottom:18px;
    }

    .metric-card {
      background:#fff;
      border:1px solid var(--line);
      border-radius:18px;
      padding:18px;
      box-shadow:0 5px 18px rgba(13,31,54,.045);
      min-height:128px;
      position:relative;
      overflow:hidden;
    }

    .metric-card:after {
      content:"";
      position:absolute;
      right:-20px;
      bottom:-35px;
      width:95px;
      height:95px;
      border-radius:50%;
      opacity:.08;
      background:currentColor;
    }

    .metric-card.red { color:var(--red); background:linear-gradient(135deg,#fff,#fff5f6); }
    .metric-card.green { color:var(--green); background:linear-gradient(135deg,#fff,#f2fff7); }
    .metric-card.blue { color:var(--blue); background:linear-gradient(135deg,#fff,#f4f8ff); }
    .metric-card.gold { color:var(--gold); background:linear-gradient(135deg,#fff,#fff9eb); }

    .metric-icon { font-size:1.28rem; margin-bottom:10px; }
    .metric-label {
      color:#506078;
      font-size:.72rem;
      text-transform:uppercase;
      letter-spacing:.075em;
      font-weight:850;
    }
    .metric-value {
      color:var(--text);
      font-size:1.95rem;
      line-height:1;
      font-weight:900;
      margin-top:11px;
    }
    .metric-foot {
      color:var(--muted);
      font-size:.8rem;
      margin-top:9px;
    }

    .panel {
      background:#fff;
      border:1px solid var(--line);
      border-radius:18px;
      padding:18px;
      box-shadow:0 5px 18px rgba(13,31,54,.04);
      margin-bottom:16px;
    }

    .panel-title {
      font-size:1rem;
      font-weight:850;
      color:var(--text);
      margin-bottom:12px;
    }

    .set-row {
      display:grid;
      grid-template-columns:32px 1fr 70px 1.2fr 48px;
      gap:10px;
      align-items:center;
      padding:10px 0;
      border-bottom:1px solid #f0f2f6;
    }
    .set-row:last-child { border-bottom:none; }

    .rank {
      width:26px;
      height:26px;
      border-radius:50%;
      display:flex;
      align-items:center;
      justify-content:center;
      background:#f0f3f8;
      color:#5c687b;
      font-size:.78rem;
      font-weight:850;
    }

    .progress-track {
      height:7px;
      border-radius:999px;
      background:#edf0f4;
      overflow:hidden;
    }

    .progress-fill {
      height:100%;
      border-radius:999px;
      background:linear-gradient(90deg,#23a35b,#57c784);
    }

    .card-shell {
      background:#fff;
      border:1px solid var(--line);
      border-radius:18px;
      padding:10px;
      box-shadow:0 4px 16px rgba(13,31,54,.045);
      margin-bottom:12px;
      min-height:315px;
    }

    .card-placeholder {
      height:205px;
      border-radius:14px;
      border:1px solid #dde3eb;
      background:
        radial-gradient(circle at 50% 28%, rgba(217,31,53,.11), transparent 34%),
        linear-gradient(160deg,#f9fbfd,#eef2f7);
      display:flex;
      flex-direction:column;
      align-items:center;
      justify-content:center;
      color:#6e7b8f;
      text-align:center;
      margin-bottom:10px;
    }

    .placeholder-icon { font-size:2rem; margin-bottom:7px; }
    .placeholder-title { font-weight:850; color:#33435d; }
    .placeholder-sub { font-size:.75rem; color:#8490a1; margin-top:3px; }

    .card-title {
      font-weight:850;
      color:var(--text);
      font-size:.93rem;
      line-height:1.25;
      margin-top:3px;
    }

    .card-meta {
      color:var(--muted);
      font-size:.79rem;
      margin-top:5px;
      min-height:18px;
    }

    .badge-row { margin-top:8px; }

    .pill {
      display:inline-block;
      border-radius:999px;
      padding:4px 8px;
      font-size:.7rem;
      font-weight:850;
      margin:0 4px 4px 0;
    }

    .pill-owned { background:#e5f7eb; color:#1d7a43; }
    .pill-need { background:#ffe9ec; color:#a71d2a; }
    .pill-incoming { background:#fff4d5; color:#8a6712; }
    .pill-blue { background:#eaf1ff; color:#275dbf; }
    .pill-purple { background:#f1eaff; color:#6d3ec2; }
    .pill-gold { background:#fff3d2; color:#8a6712; }

    .summary-row {
      display:flex;
      justify-content:space-between;
      align-items:center;
      padding:10px 0;
      border-bottom:1px solid #f0f2f6;
      color:#4e5d73;
      font-size:.9rem;
    }
    .summary-row:last-child { border-bottom:none; }

    .summary-count {
      background:#f1f4f8;
      color:#23334d;
      padding:2px 8px;
      border-radius:999px;
      font-weight:850;
      font-size:.78rem;
    }

    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button {
      border-radius:12px;
      font-weight:800;
    }

    @media (max-width:1000px) {
      .metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
    }

    @media (max-width:700px) {
      .block-container { padding:.6rem .55rem 2rem; }
      .page-title { font-size:1.55rem; }
      .metric-grid { grid-template-columns:1fr 1fr; gap:10px; }
      .metric-card { padding:14px; min-height:108px; }
      .metric-value { font-size:1.45rem; }
      .metric-icon { font-size:1rem; }
      .set-row { grid-template-columns:28px 1fr 58px; }
      .set-row .hide-mobile { display:none; }
      .card-shell { min-height:280px; }
      .card-placeholder { height:165px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_client():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
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

    st.markdown('<div class="page-title">🗃️ CardVault</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Your private sports-card collection manager.</div>',
        unsafe_allow_html=True,
    )

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
        file_options={"content-type": uploaded_file.type, "upsert": "false"},
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
        "manufacturer": "",
        "card_number": "",
        "card_name": "Adolis Garcia",
        "category": "Base",
        "variation": "",
        "serial_numbered_to": "",
        "status": "Need",
        "priority": "Core",
        "condition": "Raw",
        "grade": "",
        "price_paid": 0,
        "estimated_value": 0,
        "date_acquired": "",
        "seller": "",
        "storage_location": "",
        "image_path": "",
        "source_url": "",
        "favorite": False,
        "notes": "",
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


def build_year_progress(cards: pd.DataFrame) -> pd.DataFrame:
    if cards.empty:
        return pd.DataFrame(columns=["Year", "Owned", "Total", "Complete"])

    result = (
        cards.assign(_owned=(cards["status"] == "Owned").astype(int))
        .groupby("year", as_index=False)
        .agg(Owned=("_owned", "sum"), Total=("id", "count"))
        .rename(columns={"year": "Year"})
    )

    result["Complete"] = result["Owned"] / result["Total"] * 100
    return result.sort_values("Year")


def build_set_progress(cards: pd.DataFrame) -> pd.DataFrame:
    if cards.empty:
        return pd.DataFrame(columns=["Year", "Set", "Owned", "Total", "Complete"])

    result = (
        cards.assign(_owned=(cards["status"] == "Owned").astype(int))
        .groupby(["year", "set_name"], as_index=False)
        .agg(Owned=("_owned", "sum"), Total=("id", "count"))
        .rename(columns={"year": "Year", "set_name": "Set"})
    )

    result["Complete"] = result["Owned"] / result["Total"] * 100
    return result.sort_values(["Complete", "Total"], ascending=[False, False])


def apply_filters(df: pd.DataFrame, need_only: bool = False) -> pd.DataFrame:
    filtered = df.copy()

    if need_only:
        filtered = filtered[
            ~filtered["status"].isin(["Owned", "Incoming", "Not Chasing"])
        ]

    search = st.text_input(
        "Search",
        placeholder="Search Chrome, autograph, /25, 2024...",
    )

    years = sorted(
        filtered["year"].dropna().unique().tolist(),
        reverse=True,
    ) if not filtered.empty else []

    sets = sorted(
        filtered["set_name"].dropna().astype(str).unique().tolist()
    ) if not filtered.empty else []

    categories = sorted(
        filtered["category"].dropna().astype(str).unique().tolist()
    ) if not filtered.empty else []

    statuses = sorted(
        filtered["status"].dropna().astype(str).unique().tolist()
    ) if not filtered.empty else []

    f1, f2, f3, f4 = st.columns(4)
    selected_years = f1.multiselect("Year", years)
    selected_sets = f2.multiselect("Set", sets)
    selected_categories = f3.multiselect("Category", categories)
    selected_statuses = f4.multiselect("Status", statuses)

    favorites_only = st.toggle("Favorites only")

    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)]

    if selected_sets:
        filtered = filtered[filtered["set_name"].isin(selected_sets)]

    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]

    if selected_statuses:
        filtered = filtered[filtered["status"].isin(selected_statuses)]

    if favorites_only:
        filtered = filtered[filtered["favorite"] == True]

    if search and not filtered.empty:
        cols = [
            "year",
            "set_name",
            "card_number",
            "card_name",
            "parallel",
            "serial_number",
            "category",
            "notes",
        ]

        available_cols = [col for col in cols if col in filtered.columns]

        mask = filtered[available_cols].fillna("").astype(str).apply(
            lambda col: col.str.contains(search, case=False, regex=False)
        ).any(axis=1)

        filtered = filtered[mask]

    return filtered


def badges_for_row(row) -> str:
    badges = []

    category = str(row.get("category") or "")
    parallel = str(row.get("parallel") or "")
    serial = str(row.get("serial_number") or "")
    priority = str(row.get("priority") or "")

    if "Auto" in category:
        badges.append('<span class="pill pill-purple">AUTO</span>')

    if "Relic" in category:
        badges.append('<span class="pill pill-gold">RELIC</span>')

    if category == "Numbered" or serial:
        display = f"/{serial}" if serial and serial.isdigit() else "NUMBERED"
        badges.append(f'<span class="pill pill-blue">{display}</span>')

    if parallel:
        badges.append(f'<span class="pill pill-blue">{parallel}</span>')

    if priority in ("Dream", "Grail"):
        badges.append(f'<span class="pill pill-gold">{priority.upper()}</span>')

    return "".join(badges)


def render_card_tile(client, row, quick_owned: bool = False):
    image = signed_url(client, row.get("image_path", "") or "")

    st.markdown('<div class="card-shell">', unsafe_allow_html=True)

    if image:
        st.image(image, use_container_width=True)
    else:
        st.markdown(
            """
            <div class="card-placeholder">
              <div class="placeholder-icon">🃏</div>
              <div class="placeholder-title">CardVault</div>
              <div class="placeholder-sub">Add front photo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    status = row.get("status") or "Need"

    status_badge = {
        "Owned": '<span class="pill pill-owned">OWNED</span>',
        "Incoming": '<span class="pill pill-incoming">INCOMING</span>',
    }.get(status, '<span class="pill pill-need">NEED IT</span>')

    card_num = row.get("card_number") or ""
    parallel = row.get("parallel") or ""

    meta_parts = []

    if card_num:
        meta_parts.append(f"#{card_num}")

    if parallel:
        meta_parts.append(parallel)

    if row.get("category"):
        meta_parts.append(str(row.get("category")))

    meta = " • ".join(meta_parts)

    st.markdown(
        f"""
        <div class="card-title">{int(row['year'])} {row['set_name']}</div>
        <div class="card-meta">{meta}</div>
        <div class="badge-row">{status_badge}{badges_for_row(row)}</div>
        """,
        unsafe_allow_html=True,
    )

    if quick_owned and status != "Owned":
        if st.button(
            "Mark Owned",
            key=f"quick_owned_{row['id']}",
            use_container_width=True,
        ):
            client.table("cards").update({
                "status": "Owned",
                "date_acquired": date.today().isoformat(),
            }).eq("id", row["id"]).execute()

            st.rerun()

    with st.expander("Manage"):
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

        paid = c1.number_input(
            "Price paid",
            min_value=0.0,
            value=float(row.get("price_paid") or 0),
            step=.25,
            key=f"paid_{row['id']}",
        )

        value = c2.number_input(
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

        photo = st.file_uploader(
            "Add/replace front photo",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"photo_{row['id']}",
        )

        b1, b2 = st.columns(2)

        if b1.button(
            "Save",
            key=f"save_{row['id']}",
            use_container_width=True,
        ):
            image_path = row.get("image_path") or ""

            if photo:
                image_path = upload_image(
                    client,
                    st.session_state.user_id,
                    photo,
                )

            acquired = row.get("date_acquired") or None

            if new_status == "Owned" and not acquired:
                acquired = date.today().isoformat()

            client.table("cards").update({
                "status": new_status,
                "favorite": favorite,
                "price_paid": paid,
                "estimated_value": value,
                "storage_location": storage,
                "notes": notes,
                "image_path": image_path,
                "date_acquired": acquired,
            }).eq("id", row["id"]).execute()

            st.rerun()

        if b2.button(
            "Delete",
            key=f"delete_{row['id']}",
            use_container_width=True,
        ):
            client.table("cards").delete().eq("id", row["id"]).execute()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


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

with st.sidebar:
    st.markdown(
        """
        <div class="brand-wrap">
          <div class="brand">Card<span>Vault</span></div>
          <div class="brand-sub">PERSONAL COLLECTION MANAGER</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_name = st.selectbox(
        "Collection",
        collection_names,
        label_visibility="collapsed",
    )

    selected_collection_id = collection_map[selected_name]

    selected_collection = collections[
        collections["id"] == selected_collection_id
    ].iloc[0]

    cards = fetch_cards(client, selected_collection_id)

    st.markdown(
        f"""
        <div class="profile-box">
          <div class="profile-title">
            {selected_collection.get('player_name') or selected_name}
          </div>
          <div class="profile-sub">
            {selected_collection.get('team') or ''}
          </div>
          <span class="profile-count">{len(cards)} cards</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🃏 Collection",
            "📚 Set Progress",
            "🎯 Need It",
            "➕ Add Card",
            "📥 Import",
            "📊 Analytics",
            "💾 Backup",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    with st.expander("Create collection"):
        with st.form("new_collection_form"):
            new_name = st.text_input("Collection name")
            sport = st.text_input("Sport")
            team = st.text_input("Team")
            player_name = st.text_input("Player")
            description = st.text_area("Description")
            create = st.form_submit_button(
                "Create",
                use_container_width=True,
            )

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

        for key in (
            "access_token",
            "refresh_token",
            "user_id",
            "user_email",
        ):
            st.session_state.pop(key, None)

        st.rerun()


page = page.split(" ", 1)[1]


if page == "Dashboard":
    st.markdown(
        """
        <div class="page-head">
          <div>
            <div class="page-title">Dashboard</div>
            <div class="page-subtitle">Your collection at a glance.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if cards.empty:
        st.info("This collection is empty.")
    else:
        total = len(cards)
        owned = int((cards["status"] == "Owned").sum())
        need = int((cards["status"] == "Need").sum())
        spent = float(
            pd.to_numeric(
                cards["price_paid"],
                errors="coerce",
            ).fillna(0).sum()
        )
        value = float(
            pd.to_numeric(
                cards["estimated_value"],
                errors="coerce",
            ).fillna(0).sum()
        )
        set_count = int(cards["set_name"].nunique())
        completion = (owned / total * 100) if total else 0

        st.markdown(
            f"""
            <div class="metric-grid">
              <div class="metric-card red">
                <div class="metric-icon">🃏</div>
                <div class="metric-label">Total Cards</div>
                <div class="metric-value">{total}</div>
                <div class="metric-foot">{owned} owned</div>
              </div>
              <div class="metric-card green">
                <div class="metric-icon">💵</div>
                <div class="metric-label">Collection Value</div>
                <div class="metric-value">${value:,.2f}</div>
                <div class="metric-foot">${spent:,.2f} invested</div>
              </div>
              <div class="metric-card blue">
                <div class="metric-icon">📚</div>
                <div class="metric-label">Sets</div>
                <div class="metric-value">{set_count}</div>
                <div class="metric-foot">tracked products</div>
              </div>
              <div class="metric-card gold">
                <div class="metric-icon">🏆</div>
                <div class="metric-label">Overall Progress</div>
                <div class="metric-value">{completion:.1f}%</div>
                <div class="metric-foot">{need} cards needed</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, right = st.columns([1.35, 1])

        with left:
            st.markdown(
                '<div class="panel"><div class="panel-title">Progress by Year</div>',
                unsafe_allow_html=True,
            )

            year_progress = build_year_progress(cards)

            st.dataframe(
                year_progress,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Complete": st.column_config.ProgressColumn(
                        "Complete",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%",
                    )
                },
            )

            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown(
                '<div class="panel"><div class="panel-title">Sets Closest to Completion</div>',
                unsafe_allow_html=True,
            )

            set_progress = build_set_progress(cards)

            for idx, row in enumerate(
                set_progress.head(5).itertuples(),
                start=1,
            ):
                st.markdown(
                    f"""
                    <div class="set-row">
                      <div class="rank">{idx}</div>
                      <div style="font-weight:800;color:#22314b;">
                        {int(row.Year)} {row.Set}
                      </div>
                      <div style="color:#5f6d82;font-size:.82rem;">
                        {row.Owned}/{row.Total}
                      </div>
                      <div class="progress-track hide-mobile">
                        <div class="progress-fill" style="width:{row.Complete:.1f}%"></div>
                      </div>
                      <div style="font-weight:850;color:#263750;font-size:.82rem;">
                        {row.Complete:.0f}%
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

        lower_left, lower_right = st.columns([1.55, .85])

        with lower_left:
            st.markdown(
                '<div class="panel"><div class="panel-title">Recent Added</div>',
                unsafe_allow_html=True,
            )

            recent = cards.sort_values(
                ["created_at", "updated_at"],
                ascending=False,
            ).head(4)

            cols = st.columns(4)

            for col, (_, row) in zip(cols, recent.iterrows()):
                with col:
                    render_card_tile(client, row)

            st.markdown("</div>", unsafe_allow_html=True)

        with lower_right:
            st.markdown(
                '<div class="panel"><div class="panel-title">Collection Summary</div>',
                unsafe_allow_html=True,
            )

            category_counts = cards["category"].fillna("Other").value_counts()

            for label in [
                "Base",
                "Autograph",
                "Relic",
                "Relic/Autograph",
                "Numbered",
                "Parallel",
                "Insert",
            ]:
                count = int(category_counts.get(label, 0))

                st.markdown(
                    f"""
                    <div class="summary-row">
                      <span>{label}</span>
                      <span class="summary-count">{count}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)


elif page == "Collection":
    st.markdown(
        """
        <div class="page-title">Collection</div>
        <div class="page-subtitle">
          Browse and manage your complete checklist.
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtered = apply_filters(cards)

    st.caption(f"{len(filtered)} cards")

    for start in range(0, len(filtered), 4):
        cols = st.columns(4)
        chunk = filtered.iloc[start:start + 4]

        for col, (_, row) in zip(cols, chunk.iterrows()):
            with col:
                render_card_tile(client, row)


elif page == "Set Progress":
    st.markdown(
        """
        <div class="page-title">Set Progress</div>
        <div class="page-subtitle">
          Track completion by product and year.
        </div>
        """,
        unsafe_allow_html=True,
    )

    progress = build_set_progress(cards)

    if progress.empty:
        st.info("No cards yet.")
    else:
        years = sorted(
            progress["Year"].unique().tolist(),
            reverse=True,
        )

        selected_years = st.multiselect("Year", years)

        if selected_years:
            progress = progress[
                progress["Year"].isin(selected_years)
            ]

        st.dataframe(
            progress,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Complete": st.column_config.ProgressColumn(
                    "Complete",
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                )
            },
        )

        choices = [""] + [
            f"{int(row.Year)} — {row.Set}"
            for row in progress.itertuples()
        ]

        selected = st.selectbox("Open a set", choices)

        if selected:
            year_text, set_name = selected.split(" — ", 1)

            set_cards = cards[
                (cards["year"] == int(year_text))
                & (cards["set_name"] == set_name)
            ]

            st.caption(f"{len(set_cards)} checklist entries")

            for start in range(0, len(set_cards), 4):
                cols = st.columns(4)
                chunk = set_cards.iloc[start:start + 4]

                for col, (_, row) in zip(cols, chunk.iterrows()):
                    with col:
                        render_card_tile(client, row)


elif page == "Need It":
    st.markdown(
        """
        <div class="page-title">Need It</div>
        <div class="page-subtitle">
          Shopping mode for card shows, shops, and online browsing.
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtered = apply_filters(cards, need_only=True)

    st.caption(f"{len(filtered)} cards needed")

    for start in range(0, len(filtered), 3):
        cols = st.columns(3)
        chunk = filtered.iloc[start:start + 3]

        for col, (_, row) in zip(cols, chunk.iterrows()):
            with col:
                render_card_tile(client, row, quick_owned=True)


elif page == "Add Card":
    st.markdown(
        """
        <div class="page-title">Add Card</div>
        <div class="page-subtitle">
          Add a checklist entry or a new pickup.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("add_card_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        year = c1.number_input(
            "Year",
            min_value=1900,
            max_value=2100,
            value=2026,
        )
        set_name = c2.text_input("Set *")

        c3, c4 = st.columns(2)
        card_number = c3.text_input("Card number")
        card_name = c4.text_input("Card name")

        c5, c6 = st.columns(2)
        category = c5.selectbox("Category", CATEGORY_OPTIONS)
        parallel = c6.text_input("Parallel")

        c7, c8 = st.columns(2)
        serial_number = c7.text_input("Serial number")
        status = c8.selectbox("Status", STATUS_OPTIONS[:-1])

        priority = st.selectbox("Priority", PRIORITY_OPTIONS)
        photo = st.file_uploader(
            "Front photo",
            type=["png", "jpg", "jpeg", "webp"],
        )
        notes = st.text_area("Notes")

        add = st.form_submit_button(
            "Add card",
            use_container_width=True,
        )

    if add:
        if not set_name.strip():
            st.error("Set is required.")
        else:
            image_path = upload_image(
                client,
                user_id,
                photo,
            ) if photo else ""

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
                "date_acquired": (
                    date.today().isoformat()
                    if status == "Owned"
                    else None
                ),
            }).execute()

            st.success("Card added.")


elif page == "Import":
    st.markdown(
        """
        <div class="page-title">Import</div>
        <div class="page-subtitle">
          Upload an import-ready CSV checklist.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader("Choose CSV", type=["csv"])

    if uploaded:
        preview = pd.read_csv(uploaded)

        st.dataframe(
            preview.head(25),
            use_container_width=True,
        )

        st.caption(f"{len(preview)} rows")

        if st.button(
            "Import checklist",
            use_container_width=True,
        ):
            try:
                records = normalize_import(
                    preview,
                    user_id,
                    selected_collection_id,
                )

                existing = set()

                if not cards.empty:
                    existing = set(
                        zip(
                            cards["year"].astype(str),
                            cards["set_name"].fillna("").astype(str).str.lower(),
                            cards["card_number"].fillna("").astype(str).str.lower(),
                            cards["parallel"].fillna("").astype(str).str.lower(),
                        )
                    )

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
                    client.table("cards").insert(
                        new_records[start:start + 100]
                    ).execute()

                st.success(
                    f"Imported {len(new_records)} cards; "
                    f"skipped {len(records) - len(new_records)} duplicates."
                )

            except Exception as exc:
                st.error(f"Import failed: {exc}")


elif page == "Analytics":
    st.markdown(
        """
        <div class="page-title">Analytics</div>
        <div class="page-subtitle">
          Break down your collection by category, year, and status.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if cards.empty:
        st.info("No cards yet.")
    else:
        a, b = st.columns(2)

        with a:
            st.subheader("Cards by year")
            st.bar_chart(cards.groupby("year").size())

        with b:
            st.subheader("Cards by category")
            st.bar_chart(
                cards["category"].fillna("Other").value_counts()
            )

        st.subheader("Status breakdown")

        status_counts = (
            cards["status"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Cards")
        )

        st.dataframe(
            status_counts,
            hide_index=True,
            use_container_width=True,
        )


elif page == "Backup":
    st.markdown(
        """
        <div class="page-title">Backup / Export</div>
        <div class="page-subtitle">
          Download a complete CSV backup of the active collection.
        </div>
        """,
        unsafe_allow_html=True,
    )

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
