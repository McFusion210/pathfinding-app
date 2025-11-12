import math
import re
from typing import List, Optional

import pandas as pd
import streamlit as st

# =========================
# ---- APP CONFIG / CSS ----
# =========================
st.set_page_config(
    page_title="Alberta Pathfinding Tool",
    page_icon="✅",
    layout="wide",
)

GOA_PRIMARY = "#003A70"  # deep navy
CARD_BORDER = "#E6EAF0"

st.markdown(
    f"""
    <style>
        /* Sticky global header */
        .goa-sticky {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: {GOA_PRIMARY};
            color: white;
            padding: 14px 18px;
            border-bottom: 1px solid rgba(255,255,255,0.15);
        }}
        .goa-title {{ font-weight: 700; font-size: 20px; letter-spacing: .2px; }}
        .goa-subtitle {{ font-size: 12.5px; opacity: .9; margin-top: 2px; }}

        /* Cards */
        .program-card {{
            background: #fff;
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
            padding: 16px 18px;
            transition: transform .06s ease, box-shadow .06s ease, border-color .06s ease;
        }}
        .program-card:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 22px rgba(0,0,0,.06);
            border-color: #d7dfea;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 12px;
            line-height: 1;
            border: 1px solid #d9e3ef;
            background: #f0f5fb;
            color: #284b72;
            margin-right: 8px;
        }}
        .badge-success {{
            background: #eefbf0;
            border-color: #d9f2df;
            color: #225c2f;
        }}
        .muted {{ color: #5b6b7c; font-size: 12.5px; }}

        .hr {{ height: 1px; background: {CARD_BORDER}; margin: 10px 0 14px 0; }}

        /* Sidebar spacing tweak for compact look */
        section[data-testid="stSidebar"] .stMarkdown p {{ margin-bottom: .35rem; }}
        .stMarkdown p {{ margin: .2rem 0 .6rem 0; }}

        /* Link underline on hover only */
        .stMarkdown a {{ text-decoration: none; border-bottom: 1px solid rgba(0,0,0,.14); }}
        .stMarkdown a:hover {{ border-bottom-color: rgba(0,0,0,.35); }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# ------- HELPERS ---------
# =========================
def find_column(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    """Find a column whose name matches any alias (case-insensitive, ignores extra spaces)."""
    target = {re.sub(r"\s+", " ", a).strip().lower() for a in aliases}
    for col in df.columns:
        key = re.sub(r"\s+", " ", str(col)).strip().lower()
        if key in target:
            return col
    return None


# =========================
# ------- DATA LOAD -------
# =========================
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    expected = [
        "Program Name",
        "Program Description",
        "Eligibility Description",
        "Organization Name",
        "Funding Amount",
        "Program Website",
        "Email Address",
        "Phone Number",
        "Geographic Region",
        "Meta Tags",
        "Last Checked (MT)",
        "Operational Status",
        "_key_norm",
    ]

    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        canon = {re.sub(r"\s+", " ", c).strip().lower(): c for c in expected}
        rename = {}
        for c in df.columns:
            lc = re.sub(r"\s+", " ", str(c)).strip().lower()
            if lc in canon:
                rename[c] = canon[lc]
        df = df.rename(columns=rename)
        for c in expected:
            if c not in df.columns:
                df[c] = ""
        return df

    # Try CSV then XLSX in /data
    for path in ("data/repository.csv", "data/repository.xlsx"):
        try:
            df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
            return normalize(df)
        except Exception:
            continue

    return pd.DataFrame(columns=expected)


df = load_data()

# =========================
# --------- STATE ---------
# =========================
if "favs" not in st.session_state:
    st.session_state.favs = set()
if "page" not in st.session_state:
    st.session_state.page = 1

def toggle_fav(key_norm: str):
    if key_norm in st.session_state.favs:
        st.session_state.favs.remove(key_norm)
    else:
        st.session_state.favs.add(key_norm)

# =========================
# ------- HEADER UI -------
# =========================
st.markdown(
    """
    <div class="goa-sticky">
      <div class="goa-title">Alberta Pathfinding Tool</div>
      <div class="goa-subtitle">Small Business Supports &amp; Funding Repository</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# ------- SIDEBAR ---------
# =========================
with st.sidebar:
    st.subheader("Filters")

    sort_choice = st.selectbox(
        "Sort results by",
        ["Relevance", "Program Name A–Z", "Program Name Z–A", "Last Checked (Newest)"],
        index=0,
    )

    per_page = st.selectbox(
        "Results per page",
        [10, 25, 50, 100],
        index=1,
    )

    st.markdown("---")

    # Region
    region_col = find_column(df, ["Geographic Region", "Region"])
    selected_regions: List[str] = []
    if region_col:
        all_regions = sorted(
            {r.strip() for r in ";".join(df[region_col].dropna().astype(str)).split(";") if r.strip()}
        )
        selected_regions = st.multiselect("Region", options=all_regions)

    # Funding Type (derived from meta tags once)
    def derive_type(row) -> List[str]:
        tags = str(row.get("Meta Tags", "")).lower()
        types: List[str] = []
        if "grant" in tags or "non-repayable" in tags:
            types.append("Grant")
        if "loan" in tags or "microloan" in tags:
            types.append("Loan")
        if "financing" in tags and "loan" not in types:
            types.append("Financing")
        if "subsidy" in tags:
            types.append("Subsidy")
        if "tax" in tags:
            types.append("Tax Credit")
        return types or ["Other"]

    if "Funding Type" not in df.columns:
        df["Funding Type"] = df.apply(derive_type, axis=1)

    all_funding_types = sorted(
        {t for lst in df["Funding Type"] for t in (lst if isinstance(lst, list) else [lst])}
    )
    selected_funding_types = st.multiselect("Funding (Type)", options=all_funding_types)

    # Activity filter (if column exists)
    activity_col = find_column(df, ["Activity", "Activity Tags", "Activity (MT)"])
    selected_activities: List[str] = []
    if activity_col:
        all_activities = sorted(
            {a.strip() for a in ";".join(df[activity_col].dropna().astype(str)).split(";") if a.strip()}
        )
        selected_activities = st.multiselect("Activity", options=all_activities)

    # Audience filter
    audience_col = find_column(df, ["Audience", "Target Audience", "Audience (MT)"])
    selected_audiences: List[str] = []
    if audience_col:
        all_audiences = sorted(
            {a.strip() for a in ";".join(df[audience_col].dropna().astype(str)).split(";") if a.strip()}
        )
        selected_audiences = st.multiselect("Audience", options=all_audiences)

    # Stage / Business Stage filter
    stage_col = find_column(df, ["Business Stage", "Stage", "Business Stage (MT)"])
    selected_stages: List[str] = []
    if stage_col:
        all_stages = sorted(
            {s.strip() for s in ";".join(df[stage_col].dropna().astype(str)).split(";") if s.strip()}
        )
        selected_stages = st.multiselect("Business Stage", options=all_stages)

# =========================
# ------- SEARCH BAR ------
# =========================
st.caption("🔎 Search programs")
query = st.text_input(
    "Search programs",
    placeholder="Try 'grant', 'mentorship', or 'startup'…",
).strip()
st.caption("Tip: Search matches similar terms (e.g., typing mentor finds mentorship).")

# =========================
# ------- FILTER LOGIC ----
# =========================
def contains_any(value: str, selected: List[str]) -> bool:
    """True if any selected option is present in a semicolon-separated cell."""
    if not selected:
        return True
    parts = [p.strip() for p in str(value).split(";")]
    return any(s in parts for s in selected)

def search_filter(_df: pd.DataFrame) -> pd.DataFrame:
    out = _df.copy()

    # TEXT SEARCH – simple substring across key fields (no regex; should “just work”)
    if query:
        q = query.lower()
        search_cols = [
            "Program Name",
            "Program Description",
            "Eligibility Description",
            "Organization Name",
            "Meta Tags",
        ]
        mask = pd.Series(False, index=out.index)
        for col in search_cols:
            if col in out.columns:
                mask |= out[col].astype(str).str.lower().str.contains(q, na=False)
        out = out[mask]

    # REGION
    if region_col and selected_regions:
        out = out[out[region_col].apply(lambda v: contains_any(v, selected_regions))]

    # FUNDING TYPE
    if selected_funding_types:
        def ft_match(val):
            vals = val if isinstance(val, list) else [val]
            return any(t in vals for t in selected_funding_types)
        out = out[out["Funding Type"].apply(ft_match)]

    # ACTIVITY
    if activity_col and selected_activities:
        out = out[out[activity_col].apply(lambda v: contains_any(v, selected_activities))]

    # AUDIENCE
    if audience_col and selected_audiences:
        out = out[out[audience_col].apply(lambda v: contains_any(v, selected_audiences))]

    # STAGE
    if stage_col and selected_stages:
        out = out[ out[stage_col].apply(lambda v: contains_any(v, selected_stages)) ]

    # SORT
    if sort_choice == "Program Name A–Z":
        out = out.sort_values("Program Name", na_position="last")
    elif sort_choice == "Program Name Z–A":
        out = out.sort_values("Program Name", ascending=False, na_position="last")
    elif sort_choice == "Last Checked (Newest)":
        out["_lc"] = pd.to_datetime(out["Last Checked (MT)"], errors="coerce")
        out = out.sort_values("_lc", ascending=False, na_position="last").drop(columns=["_lc"])

    return out


filtered = search_filter(df)

# =========================
# ------ SUMMARY ROW ------
# =========================
st.markdown(f"### {len(filtered):,} Programs Found")
csv_bytes = filtered.drop(columns=["Funding Type"], errors="ignore").to_csv(index=False).encode("utf-8")
st.download_button(
    "Download results (CSV)",
    data=csv_bytes,
    file_name="pathfinding_results.csv",
    mime="text/csv",
)

# =========================
# -------- PAGINATION -----
# =========================
page = st.session_state.page
max_page = max(1, math.ceil(len(filtered) / per_page))
prev_col, spacer, next_col = st.columns([0.1, 0.8, 0.1])
with prev_col:
    if st.button("◀ Prev", disabled=page <= 1, use_container_width=True):
        st.session_state.page = max(1, page - 1)
        st.experimental_rerun()
with next_col:
    if st.button("Next ▶", disabled=page >= max_page, use_container_width=True):
        st.session_state.page = min(max_page, page + 1)
        st.experimental_rerun()

start = (st.session_state.page - 1) * per_page
end = start + per_page
page_df = filtered.iloc[start:end].reset_index(drop=True)

# =========================
# ---- RENDER PROGRAMS ----
# =========================
def fmt_money(val: str) -> str:
    s = str(val).strip()
    if not s or s.lower() in {"nan", "unknown", "not stated", "unknown / not stated"}:
        return ""
    try:
        num = float(re.sub(r"[,$ ]", "", s))
        return f"${num:,.0f}"
    except Exception:
        return s if "$" in s else s

for i, row in page_df.iterrows():
    program_name = str(row["Program Name"]).strip()
    program_desc = str(row["Program Description"]).strip()
    eligibility = str(row["Eligibility Description"]).strip()
    funding = fmt_money(row["Funding Amount"])
    website = str(row["Program Website"]).strip()
    email = str(row["Email Address"]).strip()
    phone = str(row["Phone Number"]).strip()
    org = str(row["Organization Name"]).strip()
    last_checked = str(row["Last Checked (MT)"]).strip()
    status = str(row["Operational Status"]).strip()
    key_norm = str(row["_key_norm"]).strip() or f"key_{i}"

    status_badge_class = "badge-success" if status.lower().startswith("operational") else ""
    status_label = status if status else "Status: Unknown"

    st.markdown('<div class="program-card">', unsafe_allow_html=True)

    # Status + last checked badges
    st.markdown(
        f'<span class="badge {status_badge_class}">{status_label}</span>'
        f'<span class="badge">Last checked: {last_checked or "—"}</span>',
        unsafe_allow_html=True,
    )

    # Program name + org
    st.markdown(f"### {program_name}")
    if org:
        st.markdown(f"<span class='muted'>{org}</span>", unsafe_allow_html=True)

    # Description
    if program_desc:
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown(program_desc)

    # Eligibility & Funding
    show_elig = eligibility and eligibility.lower() not in {"unknown", "not stated", "unknown / not stated"}
    show_fund = bool(funding)
    if show_elig or show_fund:
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        if show_elig:
            st.markdown(f"**Eligibility:** {eligibility}")
        if show_fund:
            st.markdown(f"**Funding:** {funding}")

    # Contact row
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        if website and website.lower() not in {"nan", "none", ""}:
            st.markdown(f"[Website]({website})")
    with c2:
        if email and email.lower() not in {"nan", "none", ""}:
            st.markdown(f"[Email](mailto:{email})")
    with c3:
        if phone and phone.lower() not in {"nan", "none", ""}:
            tel = re.sub(r"[^0-9+]", "", phone)
            st.markdown(f"[Call](tel:{tel})")
    with c4:
        is_fav = key_norm in st.session_state.favs
        label = "★ Favourited" if is_fav else "☆ Favourite"
        if st.button(label, key=f"fav_{key_norm}"):
            toggle_fav(key_norm)
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# Bottom pager
st.markdown("")
prev2, space2, next2 = st.columns([0.1, 0.8, 0.1])
with prev2:
    if st.button("◀ Prev ", key="prev_bottom", disabled=st.session_state.page <= 1, use_container_width=True):
        st.session_state.page = max(1, st.session_state.page - 1)
        st.experimental_rerun()
with next2:
    if st.button("Next ▶ ", key="next_bottom", disabled=st.session_state.page >= max_page, use_container_width=True):
        st.session_state.page = min(max_page, st.session_state.page + 1)
        st.experimental_rerun()
