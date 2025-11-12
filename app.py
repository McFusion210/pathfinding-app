import math
import re
from datetime import datetime
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
GOA_ACCENT = "#0070C4"
GOA_BG = "#F7FAFC"
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
        .goa-title {{
            font-weight: 700; 
            font-size: 20px;
            letter-spacing: 0.2px;
        }}
        .goa-subtitle {{
            font-size: 12.5px; 
            opacity: 0.9; 
            margin-top: 2px;
        }}

        /* Cards */
        .program-card {{
            background: white;
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
            padding: 16px 18px;
            transition: transform .06s ease, box-shadow .06s ease, border-color .06s ease;
            box-shadow: 0 0 0 rgba(0,0,0,0);
        }}
        .program-card:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 22px rgba(0,0,0,0.06);
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
        .muted {{
            color: #5b6b7c;
            font-size: 12.5px;
        }}

        .hr {{
            height: 1px;
            background: {CARD_BORDER};
            margin: 10px 0 14px 0;
        }}

        .inline-actions a, .inline-actions button {{
            margin-right: 16px;
            font-size: 14px;
            text-decoration: none !important;
        }}

        /* Subtle link styling */
        .stMarkdown a {{
            text-decoration: none;
            border-bottom: 1px solid rgba(0,0,0,0.14);
        }}
        .stMarkdown a:hover {{
            border-bottom-color: rgba(0,0,0,0.3);
        }}

        /* Compact checkboxes in sidebar */
        section[data-testid="stSidebar"] .stCheckbox > label p {{
            margin-bottom: 0 !important;
        }}

        /* Tighten vertical rhythm a bit */
        .stMarkdown p {{
            margin: 0.2rem 0 0.6rem 0;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# ------- DATA LOAD -------
# =========================

@st.cache_data(show_spinner=False)
def load_data(uploaded: Optional[bytes]) -> pd.DataFrame:
    """
    Load from user upload (CSV/XLSX), else attempt local 'data/repository.csv' or 'data/repository.xlsx'.
    Expects the following columns (case-insensitive tolerant):
      Program Name, Program Description, Eligibility Description, Organization Name,
      Funding Amount, Program Website, Email Address, Phone Number, Geographic Region,
      Meta Tags, Last Checked (MT), Operational Status, Sources, Notes, _key_norm, Contact Page (Derived)
    """
    cols_normal = [
        "Program Name", "Program Description", "Eligibility Description", "Organization Name",
        "Funding Amount", "Program Website", "Email Address", "Phone Number", "Geographic Region",
        "Meta Tags", "Last Checked (MT)", "Operational Status", "Sources", "Notes", "_key_norm", "Contact Page (Derived)"
    ]

    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        # Soft-match columns by stripping and lowering
        mapping = {}
        for c in df.columns:
            lc = re.sub(r"\s+", " ", str(c)).strip().lower()
            mapping[c] = lc
        # build reverse lookup
        desired = {re.sub(r"\s+", " ", c).strip().lower(): c for c in cols_normal}
        out_cols = {}
        for src, lc in mapping.items():
            if lc in desired:
                out_cols[src] = desired[lc]
        df = df.rename(columns=out_cols)
        # ensure all expected exist
        for c in cols_normal:
            if c not in df.columns:
                df[c] = ""
        return df[cols_normal]

    if uploaded:
        if uploaded.name.lower().endswith(".xlsx"):
            df = pd.read_excel(uploaded)
        else:
            df = pd.read_csv(uploaded)
        return normalize_columns(df)

    # Fallback to repo files
    try:
        df = pd.read_csv("data/repository.csv")
        return normalize_columns(df)
    except Exception:
        pass
    try:
        df = pd.read_excel("data/repository.xlsx")
        return normalize_columns(df)
    except Exception:
        pass

    # If nothing found, create empty scaffold
    return pd.DataFrame(columns=cols_normal)


# =========================
# --------- STATE ---------
# =========================
if "favs" not in st.session_state:
    st.session_state.favs = set()

def toggle_fav(key_norm: str):
    if key_norm in st.session_state.favs:
        st.session_state.favs.remove(key_norm)
    else:
        st.session_state.favs.add(key_norm)

# =========================
# ------- HEADER UI -------
# =========================
st.markdown(
    f"""
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
    uploaded = st.file_uploader("Load repository (.csv / .xlsx)", type=["csv", "xlsx"])
    df = load_data(uploaded)

    st.markdown("**Sort results by**")
    sort_choice = st.selectbox(
        "",
        ["Relevance", "Program Name A–Z", "Program Name Z–A", "Last Checked (Newest)"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("**Results per page**")
    per_page = st.selectbox("", [10, 25, 50, 100], index=1, label_visibility="collapsed")

    st.markdown("---")

    # Region filter
    st.markdown("**Region**")
    all_regions = sorted(
        {r.strip() for r in ";".join(df["Geographic Region"].dropna().astype(str)).split(";") if r.strip()}
    )
    selected_regions = st.multiselect("",
                                      options=all_regions,
                                      label_visibility="collapsed")

    st.markdown("**Funding (Type)**")
    # Derive a rough "type" based on keywords in Meta Tags or Funding Amount
    def derive_type(row) -> List[str]:
        tags = str(row.get("Meta Tags", "")).lower()
        types = []
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

    all_types = sorted({t for lst in df["Funding Type"] for t in (lst if isinstance(lst, list) else [lst])})
    selected_types = st.multiselect("", options=all_types, label_visibility="collapsed")

# =========================
# ------- SEARCH BAR ------
# =========================
st.caption("🔎 Search programs")
query = st.text_input("Try 'grant', 'mentorship', or 'startup'…", label_visibility="collapsed").strip()

# Tip text
st.caption("Tip: Search matches similar terms (e.g., typing mentor finds mentorship).")

# =========================
# ------- FILTER LOGIC ----
# =========================
def search_filter(_df: pd.DataFrame) -> pd.DataFrame:
    out = _df.copy()

    # text search across key fields
    if query:
        pat = re.escape(query)
        mask = (
            out["Program Name"].astype(str).str.contains(pat, case=False, na=False)
            | out["Program Description"].astype(str).str.contains(pat, case=False, na=False)
            | out["Eligibility Description"].astype(str).str.contains(pat, case=False, na=False)
            | out["Organization Name"].astype(str).str.contains(pat, case=False, na=False)
            | out["Meta Tags"].astype(str).str.contains(pat, case=False, na=False)
        )
        out = out[mask]

    # region filter (OR across checked regions)
    if selected_regions:
        def region_match(val: str) -> bool:
            regions = [x.strip() for x in str(val).split(";")]
            return any(r in regions for r in selected_regions)
        out = out[out["Geographic Region"].apply(region_match)]

    # funding type filter (OR)
    if selected_types:
        def type_match(val):
            vals = val if isinstance(val, list) else [val]
            return any(t in vals for t in selected_types)
        out = out[out["Funding Type"].apply(type_match)]

    # sort
    if sort_choice == "Program Name A–Z":
        out = out.sort_values("Program Name", na_position="last")
    elif sort_choice == "Program Name Z–A":
        out = out.sort_values("Program Name", ascending=False, na_position="last")
    elif sort_choice == "Last Checked (Newest)":
        # attempt to parse date
        def parse_dt(s):
            try:
                return pd.to_datetime(s, errors="coerce")
            except Exception:
                return pd.NaT
        out["_lc"] = out["Last Checked (MT)"].apply(parse_dt)
        out = out.sort_values("_lc", ascending=False, na_position="last").drop(columns=["_lc"])

    return out

filtered = search_filter(df)

# =========================
# ------ SUMMARY ROW ------
# =========================
st.markdown(f"### {len(filtered):,} Programs Found")

# CSV download
csv_bytes = filtered.drop(columns=["Funding Type"], errors="ignore").to_csv(index=False).encode("utf-8")
st.download_button("Download results (CSV)", data=csv_bytes, file_name="pathfinding_results.csv", mime="text/csv")

# =========================
# -------- PAGINATION -----
# =========================
page = st.session_state.get("page", 1)
max_page = max(1, math.ceil(len(filtered) / per_page))

col_prev, col_gap, col_next = st.columns([0.1, 0.8, 0.1])
with col_prev:
    if st.button("◀ Prev", disabled=page <= 1, use_container_width=True):
        page = max(1, page - 1)
with col_next:
    if st.button("Next ▶", disabled=page >= max_page, use_container_width=True):
        page = min(max_page, page + 1)

st.session_state.page = page

start = (page - 1) * per_page
end = start + per_page
page_df = filtered.iloc[start:end].reset_index(drop=True)

# =========================
# ---- RENDER PROGRAMS ----
# =========================

def fmt_money(val: str) -> str:
    s = str(val).strip()
    if not s or s.lower() in {"nan", "unknown", "not stated", "unknown / not stated"}:
        return ""
    # Add $ if a number is present but not already formatted
    try:
        # remove commas and $ for parse
        num = float(re.sub(r"[,$ ]", "", s))
        return f"${num:,.0f}"
    except Exception:
        # if text already has $ or words, just return as-is
        return s if "$" in s else s

def safe_value(s: str) -> str:
    if not s:
        return ""
    return s

for _, row in page_df.iterrows():
    program_name = safe_value(row["Program Name"])
    program_desc = safe_value(row["Program Description"])
    eligibility = str(row["Eligibility Description"]).strip()
    funding = fmt_money(row["Funding Amount"])
    website = str(row["Program Website"]).strip()
    email = str(row["Email Address"]).strip()
    phone = str(row["Phone Number"]).strip()
    org = str(row["Organization Name"]).strip()
    last_checked = str(row["Last Checked (MT)"]).strip()
    status = str(row["Operational Status"]).strip()
    sources = str(row["Sources"]).strip()
    notes = str(row["Notes"]).strip()
    key_norm = str(row["_key_norm"]).strip() or f"key_{_}"

    # Status badge
    status_badge_class = "badge-success" if status.lower().startswith("operational") else ""
    status_label = status if status else "Status: Unknown"

    with st.container():
        st.markdown('<div class="program-card">', unsafe_allow_html=True)

        # Top badges
        left, right = st.columns([0.7, 0.3])
        with left:
            st.markdown(
                f'<span class="badge {status_badge_class}">{status_label}</span>'
                f'<span class="badge">Last checked: {last_checked or "—"}</span>',
                unsafe_allow_html=True,
            )
        with right:
            if org:
                st.markdown(f'<div style="text-align:right" class="muted">{org}</div>', unsafe_allow_html=True)

        # 1) Program Name
        st.markdown(f"### {program_name}")

        # 2) Program Description
        if program_desc:
            st.markdown(program_desc)

        # Divider
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # 3) Eligibility + Funding (Eligibility above Funding per your order)
        if eligibility and eligibility.lower() not in {"unknown / not stated", "unknown", "not stated"}:
            st.markdown(f"**Eligibility:** {eligibility}")

        if funding:
            st.markdown(f"**Funding:** {funding}")

        # If you also want to show any long-form program notes or sources, keep them within the card:
        if notes:
            st.markdown(f"<span class='muted'>Notes:</span> {notes}", unsafe_allow_html=True)
        if sources:
            st.markdown(f"<span class='muted'>Sources:</span> {sources}", unsafe_allow_html=True)

        # 4) Website / Email / Call / Favourite (single row)
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
                # Normalize phone digits for tel: link
                tel = re.sub(r"[^0-9+]", "", phone)
                st.markdown(f"[Call](tel:{tel})")
        with c4:
            fav_key = f"fav_{key_norm}"
            is_fav = key_norm in st.session_state.favs
            label = "★ Favourited" if is_fav else "☆ Favourite"
            if st.button(label, key=fav_key):
                toggle_fav(key_norm)
                st.experimental_rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# Footer pagination controls (repeat for convenience)
st.markdown("")
col_prev2, col_mid2, col_next2 = st.columns([0.1, 0.8, 0.1])
with col_prev2:
    if st.button("◀ Prev ", key="prev_bottom", disabled=page <= 1, use_container_width=True):
        st.session_state.page = max(1, page - 1)
        st.experimental_rerun()
with col_next2:
    if st.button("Next ▶ ", key="next_bottom", disabled=page >= max_page, use_container_width=True):
        st.session_state.page = min(max_page, page + 1)
        st.experimental_rerun()
