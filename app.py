import os
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

UNKNOWN = "Unknown, not stated"
FUZZY_THR = 60


def embed_css() -> None:
    st.markdown(
        """
<style>
:root{
  --bg:#FFFFFF; --surface:#FFFFFF; --text:#0A0A0A; --muted:#4B5563;
  --primary:#003366; --primary-2:#007FA3; --border:#D9DEE7; --link:#007FA3;
  --fs-title:24px; --fs-body:15px; --fs-meta:13px;
}
div[data-testid="stTextInput"] > div > div {
  border-radius: 999px;
  border: 2px solid #C3D0E6;
  background: #F3F4F6;
  padding: 4px 10px;
}
div[data-testid="stTextInput"] input{
  border:none !important;
  box-shadow:none !important;
  background:transparent !important;
}
div[data-testid="stTextInput"] input::placeholder{
  color:#6B7280;
  opacity:1;
}
.goa-header{
  background:#003366;
  color:#FFFFFF;
  padding:16px 32px;
  display:flex;
  align-items:center;
  gap:16px;
  position:sticky;
  top:0;
  z-index:50;
}
.goa-header-logo{
  width:140px;
  height:auto;
}
.goa-header-text h1{
  font-size:22px;
  margin:0;
  font-weight:600;
}
.goa-header-text p{
  margin:2px 0 0 0;
  font-size:14px;
  opacity:.9;
}
.app-shell{
  padding:18px 32px 32px 32px;
  background:#F3F4F6;
}
.pf-card-marker{
  border-radius:12px;
  border:1px solid var(--border);
  padding:16px 16px 14px 16px;
  background:var(--surface);
  margin-bottom:12px;
  box-shadow:0 1px 2px rgba(15,23,42,0.04);
}
.pf-card-marker:hover{
  box-shadow:0 4px 10px rgba(15,23,42,0.08);
}
.badge{
  display:inline-flex;
  align-items:center;
  padding:2px 8px;
  border-radius:999px;
  font-size:var(--fs-meta);
  font-weight:500;
  margin-right:8px;
}
.badge-open{
  background:#DCFCE7;
  color:#166534;
}
.badge-closed{
  background:#FEE2E2;
  color:#B91C1C;
}
.badge-paused{
  background:#FEF3C7;
  color:#92400E;
}
.meta{
  font-size:var(--fs-meta);
  color:#6B7280;
}
h3.program-title{
  font-size:18px;
  margin:6px 0 2px 0;
}
.program-org{
  font-size:var(--fs-body);
  color:#4B5563;
  margin-bottom:6px;
}
.program-desc{
  font-size:var(--fs-body);
  color:#111827;
}
.meta-strip{
  display:flex;
  flex-wrap:wrap;
  gap:12px;
  margin-top:6px;
  margin-bottom:6px;
}
.meta-strip .kv{
  font-size:var(--fs-meta);
  color:#374151;
}
.placeholder{
  font-size:var(--fs-meta);
  color:#9CA3AF;
  font-style:italic;
}
html, body, p, div, span{
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Segoe UI Emoji";
  color:var(--text);
}
p{ margin:4px 0 4px 0; }
small{ font-size:var(--fs-meta); }
.skip-link {
  position:absolute; left:-9999px; top:auto; width:1px; height:1px; overflow:hidden;
}
.skip-link:focus {
  position:fixed; left:16px; top:12px; width:auto; height:auto; padding:8px 10px;
  background:#fff; color:#000; border:2px solid #000; z-index:9999;
}
.sidebar-section h3{
  font-size:16px;
  margin:0 0 4px 0;
}
.sidebar-section small{
  color:#6B7280;
}
.chips-row{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin-top:4px;
}
.chip{
  display:inline-flex;
  align-items:center;
  gap:6px;
  border-radius:999px;
  background:#E5E7EB;
  padding:2px 10px;
  font-size:12px;
  color:#374151;
}
.actions-row{
  margin-top:6px;
}
.pf-phone-line{
  display:block;
  margin-top:2px;
  font-size:var(--fs-body);
}
.pf-phone-line strong{
  font-weight:600;
}
.results-summary{
  font-size:var(--fs-meta);
  color:#4B5563;
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) a{
  color:#007FA3 !important;
  text-decoration:underline;
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) a:hover{
  opacity:.85;
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button{
  background:none !important;
  border:none !important;
  padding:0;
  margin:0;
  color:#007FA3 !important;
  text-decoration:underline;
  font-size:var(--fs-body);
  cursor:pointer;
  box-shadow:none !important;
  border-radius:0 !important;
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button:hover{
  opacity:.85;
  text-decoration:underline;
}
.block-container{
  padding-top:0 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def embed_logo_html() -> None:
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Alberta_Government_Logo.svg/320px-Alberta_Government_Logo.svg.png"
    st.markdown(
        f"""
<a href="#main" class="skip-link">Skip to main content</a>
<div class="goa-header">
  <img src="{logo_url}" alt="Government of Alberta" class="goa-header-logo" />
  <div class="goa-header-text">
    <h1>Small Business Supports Finder</h1>
    <p>Search and filter programs, services, and funding for Alberta entrepreneurs.</p>
  </div>
</div>
<div id="main" class="app-shell">
""",
        unsafe_allow_html=True,
    )


def close_shell() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def fix_mojibake(s: str) -> str:
    if not s:
        return ""
    return (
        s.replace("â€“", "-")
        .replace("Ã©", "é")
        .replace("â€™", "'")
        .replace("â€œ", '"')
        .replace("â€\x9d", '"')
    )


def sanitize_text_keep_smart(s: str) -> str:
    s = fix_mojibake(s or "")
    for b in ["•", "●", "○", "▪", "▫", "■", "□", "-·", "‣"]:
        s = s.replace(b, " ")
    s = re.sub(r"[\U0001F300-\U0001FAFF]", " ", s)
    s = re.sub(r"[\u2600-\u26FF]", " ", s)
    s = re.sub(r"[\u2700-\u27BF]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


URL_LIKE = re.compile(r"https?://|www\.|\.ca\b|\.com\b|\.org\b", re.I)


def drop_url_like(text: str) -> str:
    if not text:
        return ""
    if URL_LIKE.search(text):
        return ""
    return text


def days_since(value) -> tuple[Optional[int], Optional[str]]:
    if not value:
        return None, None
    try:
        d = pd.to_datetime(value)
    except Exception:
        return None, None
    delta = (pd.Timestamp("today").normalize() - d.normalize()).days
    return int(delta), d.date().isoformat()


def freshness_label(days: Optional[int]) -> str:
    if days is None:
        return "Last checked date not available"
    if days <= 90:
        return f"{days} days ago (recent)"
    if days <= 365:
        return f"{days} days ago"
    return f"{days} days ago (may be out of date)"


def funding_bucket(text: str) -> str:
    """Safe bucketer for Funding Amount."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return UNKNOWN

    s = sanitize_text_keep_smart(str(text))

    matches = re.findall(r"\$?\s*([\d,]+)", s)
    nums: List[int] = []

    for p in matches:
        digit_groups = re.findall(r"\d+", p)
        if not digit_groups:
            continue
        num_str = "".join(digit_groups)
        if not num_str:
            continue
        try:
            nums.append(int(num_str))
        except ValueError:
            continue

    if not nums:
        return UNKNOWN

    mx = max(nums)
    if mx < 5000:
        return "Under 5K"
    if mx < 25000:
        return "5K to 25K"
    if mx < 100000:
        return "25K to 100K"
    if mx < 500000:
        return "100K to 500K"
    return "Over 500K"


def add_dollar_signs(bucket: str) -> str:
    s = bucket.strip()
    if s.startswith("Under "):
        return "Under $" + s[len("Under ") :]
    if s.startswith("Over "):
        return "Over $" + s[len("Over ") :]
    if " to " in s:
        a, b = s.split(" to ", 1)
        return f"${a} to ${b}"
    return s


def normalize_phone(phone: str) -> tuple[str, str]:
    if not phone:
        return "", ""
    s = re.sub(r"[^\d+]", "", phone)
    digits = re.sub(r"\D", "", s)
    if not digits:
        return phone, phone
    country = ""
    if digits.startswith("1") and len(digits) == 11:
        country = "1"
        digits = digits[1:]
    elif len(digits) == 10:
        country = "1"
    else:
        return phone, (digits or phone)
    display = f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    tel = f"+{country}{digits}"
    return display, tel


def format_phone_multi(phone: str) -> str:
    if not phone:
        return ""
    chunks = re.split(r"[,/;]|\bor\b", str(phone))
    parts = []
    for ch in chunks:
        ch = ch.strip()
        if not ch:
            continue
        display, _tel = normalize_phone(ch)
        parts.append(display or ch)
    return " | ".join(parts)


def parse_email_field(raw: str):
    s = (raw or "").strip()
    if not s:
        return "", ""
    lower = s.lower()
    m = re.match(r"\[([^\]]+)\]\((mailto:[^)]+)\)", s, re.IGNORECASE)
    if m:
        label = m.group(1) or "Email"
        href = m.group(2)
        if "not publicly listed" in href.lower():
            return "Email not publicly listed. Use the program website contact page.", ""
        return label, href
    if "not publicly listed" in lower:
        return "Email not publicly listed. Use the program website contact page.", ""
    if lower.startswith("mailto:"):
        addr = s.split(":", 1)[1].strip()
        if addr and "not publicly listed" not in addr.lower():
            return "Email", f"mailto:{addr}"
        return "Email not publicly listed. Use the program website contact page.", ""
    if re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", s):
        return "Email", f"mailto:{s.lower()}"
    return s, ""


def render_description(desc_full: str, key: str) -> None:
    desc_full = sanitize_text_keep_smart(desc_full or "")
    if not desc_full:
        st.markdown("<p class='placeholder'>No description available.</p>", unsafe_allow_html=True)
        return
    short = desc_full
    limit = 260
    if len(desc_full) > limit:
        short = desc_full[:limit].rsplit(" ", 1)[0] + "..."
    state_key = f"show_more_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = False
    if st.session_state[state_key]:
        st.markdown(f"<p class='program-desc'>{desc_full}</p>", unsafe_allow_html=True)
        if st.button("Show less", key=f"less_{key}"):
            st.session_state[state_key] = False
            st.experimental_rerun()
    else:
        st.markdown(f"<p class='program-desc'>{short}</p>", unsafe_allow_html=True)
        if len(desc_full) > limit:
            if st.button("Show more", key=f"more_{key}"):
                st.session_state[state_key] = True
                st.experimental_rerun()


def map_col(df: pd.DataFrame, candidates: List[str], default: Optional[str] = None) -> str:
    cols = [c for c in df.columns if isinstance(c, str)]
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        lc = cand.lower()
        if lc in low:
            return low[lc]
    for c in cols:
        for cand in candidates:
            if cand.lower() in c.lower():
                return c
    if default and default in df.columns:
        return default
    return ""


def infer_columns(df: pd.DataFrame) -> Dict[str, str]:
    cfg = {
        "PROGRAM_NAME": map_col(df, ["Program Name", "Program", "Support name"]),
        "ORGANIZATION": map_col(df, ["Organization Name", "Organization", "Provider", "Delivery partner"]),
        "DESCRIPTION": map_col(df, ["Program Description", "Description", "Summary"]),
        "ELIGIBILITY": map_col(df, ["Eligibility Description", "Eligibility", "Eligibility highlights"]),
        "WEBSITE": map_col(df, ["Program Website", "Website", "URL", "Link"]),
        "EMAIL": map_col(df, ["Email Address", "Email", "E-mail", "Contact email"]),
        "PHONE": map_col(df, ["Phone Number", "Phone", "Telephone", "Contact phone"]),
        "REGION": map_col(df, ["Geographic Region", "Region", "Location", "Geography"]),
        "AUDIENCE": map_col(df, ["Audience", "Who is this for", "Client type"]),
        "STAGE": map_col(df, ["Stage", "Business stage"]),
        "SUPPORT_TYPE": map_col(df, ["Support type", "Support category", "Type of support"]),
        "FUNDING": map_col(df, ["Funding Amount", "Funding amount", "Funding", "Max funding"]),
        "STATUS": map_col(df, ["Operational Status", "Status", "Program status"]),
        "LAST_CHECKED": map_col(df, ["Last Checked (MT)", "Last checked", "Validated on", "Last updated"]),
        "META_TAGS": map_col(df, ["Meta Tags", "Tags", "Keywords"]),
        "KEY": map_col(df, ["_key_norm", "Key", "Unique id", "Program key"]),
    }
    return cfg


@st.cache_data(show_spinner=False)
def load_data(path: str) -> tuple[pd.DataFrame, Dict[str, str]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    col_map = infer_columns(df)
    global COLS
    COLS = col_map

    required = [
        "PROGRAM_NAME",
        "ORGANIZATION",
        "DESCRIPTION",
        "ELIGIBILITY",
        "WEBSITE",
        "EMAIL",
        "PHONE",
        "REGION",
        "AUDIENCE",
        "STAGE",
        "SUPPORT_TYPE",
        "FUNDING",
        "STATUS",
        "LAST_CHECKED",
        "META_TAGS",
        "KEY",
    ]
    for key in required:
        col_name = COLS.get(key, "")
        if not col_name or col_name not in df.columns:
            col_name = f"__missing_{key}"
            df[col_name] = ""
            COLS[key] = col_name

    df["__funding_bucket"] = df[COLS["FUNDING"]].apply(funding_bucket)

    days_list, date_list = [], []
    for val in df[COLS["LAST_CHECKED"]].tolist():
        d, ds = days_since(val)
        days_list.append(d)
        date_list.append(ds or "")
    df["__fresh_days"] = days_list
    df["__fresh_date"] = date_list

    if df[COLS["KEY"]].isna().any():
        df[COLS["KEY"]] = (
            df[COLS["PROGRAM_NAME"]]
            .fillna("")
            .astype(str)
            .str.slice(0, 80)
            + "-"
            + df.index.astype(str)
        )

    def parse_tags_field_clean(val) -> List[str]:
        if not isinstance(val, str):
            return []
        s = sanitize_text_keep_smart(val)
        if not s:
            return []
        parts = re.split(r"[;,/]", s)
        out = []
        for p in parts:
            p = p.strip()
            if not p or URL_LIKE.search(p):
                continue
            out.append(p)
        return out

    df["__region_set"] = df[COLS["REGION"]].apply(parse_tags_field_clean)
    df["__audience_set"] = df[COLS["AUDIENCE"]].apply(parse_tags_field_clean)
    df["__stage_set"] = df[COLS["STAGE"]].apply(parse_tags_field_clean)
    df["__support_set"] = df[COLS["SUPPORT_TYPE"]].apply(parse_tags_field_clean)

    def derive_funding_types_from_tags(tags: List[str]) -> set:
        types = set()
        for tag in tags:
            t = tag.lower()
            if "grant" in t:
                types.add("Grant")
            if any(x in t for x in ["loan", "micro-loan", "micro loan", "lending", "financing"]):
                types.add("Loan")
            if "tax credit" in t:
                types.add("Tax credit")
            if "voucher" in t or "rebate" in t:
                types.add("Voucher or rebate")
            if "equity" in t or "investment" in t:
                types.add("Equity or investment")
        return types

    ft_col = None
    for c in df.columns:
        lc = c.lower()
        if "fund" in lc and "type" in lc:
            ft_col = c
            break

    if ft_col:
        df["__fund_type_set"] = df[ft_col].apply(parse_tags_field_clean)
    else:
        meta_col = COLS.get("META_TAGS", "")
        if meta_col and meta_col in df.columns:
            df["__meta_tags_list"] = df[meta_col].apply(parse_tags_field_clean)
            df["__fund_type_set"] = df["__meta_tags_list"].apply(derive_funding_types_from_tags)
        else:
            df["__fund_type_set"] = [set() for _ in range(len(df))]

    return df, COLS


def fuzzy_mask(df: pd.DataFrame, query: str, threshold: int = FUZZY_THR) -> pd.Series:
    if not query:
        return pd.Series(True, index=df.index)
    q = sanitize_text_keep_smart(query).lower()
    if not q:
        return pd.Series(True, index=df.index)

    fields = [
        COLS["PROGRAM_NAME"],
        COLS["ORGANIZATION"],
        COLS["DESCRIPTION"],
        COLS["AUDIENCE"],
        COLS["STAGE"],
        COLS["SUPPORT_TYPE"],
    ]
    scores = []
    for col in fields:
        col_vals = df[col].fillna("").astype(str).str.lower().tolist()
        col_scores = [fuzz.partial_ratio(q, v) for v in col_vals]
        scores.append(col_scores)

    arr = np.array(scores)
    best = arr.max(axis=0)
    return pd.Series(best >= threshold, index=df.index)


def apply_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, List[str]]]:
    q = st.session_state.get("search_q", "")
    mask = fuzzy_mask(df, q, threshold=FUZZY_THR)

    active_filters: Dict[str, List[str]] = {}

    def multi_select_filter(session_key: str, data_field: str):
        vals = st.session_state.get(session_key, [])
        if vals:
            active_filters[session_key] = vals

            def fn(row):
                row_tags = row.get(data_field, [])
                return any(v in row_tags for v in vals)

            return df.apply(fn, axis=1)
        return pd.Series(True, index=df.index)

    mask_support = multi_select_filter("filter_support", "__support_set")
    mask_stage = multi_select_filter("filter_stage", "__stage_set")
    mask_audience = multi_select_filter("filter_audience", "__audience_set")
    mask_region = multi_select_filter("filter_region", "__region_set")

    funding_vals = st.session_state.get("filter_funding_bucket", [])
    if funding_vals:
        active_filters["filter_funding_bucket"] = funding_vals
        mask_funding = df["__funding_bucket"].isin(funding_vals)
    else:
        mask_funding = pd.Series(True, index=df.index)

    fund_type_vals = st.session_state.get("filter_funding_type", [])
    if fund_type_vals:
        active_filters["filter_funding_type"] = fund_type_vals

        def ftype(row):
            tags = row.get("__fund_type_set", set())
            return any(v in tags for v in fund_type_vals)

        mask_ftype = df.apply(ftype, axis=1)
    else:
        mask_ftype = pd.Series(True, index=df.index)

    overall = mask & mask_support & mask_stage & mask_audience & mask_region & mask_funding & mask_ftype
    return df[overall].copy(), active_filters


def clear_all_filters():
    for key in [
        "filter_support",
        "filter_funding_type",
        "filter_funding_bucket",
        "filter_stage",
        "filter_audience",
        "filter_region",
    ]:
        st.session_state[key] = []


def render_filter_pills(
    label: str,
    help_text: str,
    options: List[str],
    session_key: str,
):
    with st.container():
        st.markdown(
            f"<div class='sidebar-section'><h3>{label}</h3><small>{help_text}</small></div>",
            unsafe_allow_html=True,
        )
        if session_key not in st.session_state:
            st.session_state[session_key] = []
        selected = set(st.session_state[session_key])

        cols = st.columns(2)
        for i, opt in enumerate(options):
            col = cols[i % 2]
            with col:
                is_on = opt in selected
                if st.button(opt, key=f"{session_key}_{opt}"):
                    if is_on:
                        selected.remove(opt)
                    else:
                        selected.add(opt)
                    st.session_state[session_key] = sorted(selected)
                    st.experimental_rerun()

        if selected:
            if st.button("Clear", key=f"clear_{session_key}"):
                st.session_state[session_key] = []
                st.experimental_rerun()


def render_funding_type_pills(options: List[str]):
    render_filter_pills(
        label="What kind of funding are you looking for?",
        help_text="For example, grants, loans, tax credits, or advisory support tied to funding.",
        options=options,
        session_key="filter_funding_type",
    )


def render_chips(active_filters: Dict[str, List[str]]):
    if not active_filters:
        return
    st.markdown("<div class='chips-row'>", unsafe_allow_html=True)
    for key, vals in active_filters.items():
        for val in vals:
            if key == "filter_support":
                prefix = "Support:"
            elif key == "filter_funding_type":
                prefix = "Funding type:"
            elif key == "filter_funding_bucket":
                prefix = "Funding amount:"
            elif key == "filter_stage":
                prefix = "Stage:"
            elif key == "filter_audience":
                prefix = "Audience:"
            elif key == "filter_region":
                prefix = "Region:"
            else:
                prefix = ""
            label = f"{prefix} {val}" if prefix else val

            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"<span class='chip'>{label}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("x", key=f"chip_{key}_{val}"):
                    cur = set(st.session_state.get(key, []))
                    if val in cur:
                        cur.remove(val)
                        st.session_state[key] = sorted(cur)
                        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Small Business Supports Finder", layout="wide")
    embed_css()
    embed_logo_html()

    data_path = "Pathfinding_Master.xlsx"
    df, _cols = load_data(data_path)

    st.title("Search programs and supports")
    st.markdown(
        """
Use this internal prototype to explore programs, services, and funding for Alberta small businesses and entrepreneurs.

1. Use the search box for keywords (for example, "restaurant", "startup", "Indigenous").
2. Apply filters on the left to refine by support type, funding, stage, audience, and region.
3. Open program cards for details, eligibility highlights, and contact options.
        """
    )

    if "favorites" not in st.session_state:
        st.session_state.favorites = set()

    col_search, col_sort, col_page = st.columns([3, 1, 1])
    with col_search:
        st.text_input(
            "Search programs",
            key="search_q",
            placeholder="Search by keyword, program name, organization, or description",
        )
    with col_sort:
        sort_by = st.selectbox(
            "Sort results by",
            ["Relevance", "Program name A to Z", "Most recently checked"],
            index=0,
        )
    with col_page:
        per_page = st.selectbox("Results per page", [10, 25, 50], index=1)

    st.markdown(
        "<p class='results-summary'>Tip: Search also matches similar terms and common spellings, not just exact words.</p>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Filter programs")
        if st.button("Clear all filters"):
            clear_all_filters()
            st.experimental_rerun()

        support_options = sorted(
            {
                "Advisory and coaching",
                "Training and workshops",
                "Networking and mentorship",
                "Export and market access",
                "Innovation and technology",
            }
        )
        render_filter_pills(
            "What type of business support do you need?",
            "You can select more than one.",
            support_options,
            "filter_support",
        )

        funding_type_opts = sorted(
            {
                "Grant",
                "Loan",
                "Tax credit",
                "Voucher or rebate",
                "Equity or investment",
            }
        )
        render_funding_type_pills(funding_type_opts)

        funding_bucket_opts = [
            "Under 5K",
            "5K to 25K",
            "25K to 100K",
            "100K to 500K",
            "Over 500K",
            UNKNOWN,
        ]
        render_filter_pills(
            "How much funding are you looking for?",
            "These bands are estimates based on program information.",
            funding_bucket_opts,
            "filter_funding_bucket",
        )

        stage_opts = sorted(
            {"Idea or pre-revenue", "Startup or early stage", "Growing or scaling", "Mature business"}
        )
        render_filter_pills(
            "What stage is your business at?",
            "",
            stage_opts,
            "filter_stage",
        )

        audience_opts = sorted(
            {"Women", "Indigenous", "Youth", "Newcomers", "Rural or northern", "All small businesses"}
        )
        render_filter_pills(
            "Who is this support for?",
            "",
            audience_opts,
            "filter_audience",
        )

        region_opts = sorted(
            {"Province-wide", "Calgary region", "Edmonton region", "Other regions"}
        )
        render_filter_pills(
            "Where is your business located?",
            "",
            region_opts,
            "filter_region",
        )

    filtered, active_filters = apply_filters(df)
    total = len(filtered)
    if total == 0:
        st.info(
            "No programs match your current filters. Try clearing filters or broadening your search."
        )
        close_shell()
        return

    if sort_by == "Program name A to Z":
        filtered = filtered.sort_values(COLS["PROGRAM_NAME"].fillna(""))
    elif sort_by == "Most recently checked":
        filtered = filtered.sort_values("__fresh_days", ascending=True)

    page = st.session_state.get("page", 1)
    max_page = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, max_page))
    start = (page - 1) * per_page
    end = start + per_page

    st.markdown(
        f"<p class='results-summary'>{total} programs found. Showing {start+1}-{min(end, total)} of {total}.</p>",
        unsafe_allow_html=True,
    )

    render_chips(active_filters)

    subset = filtered.iloc[start:end].copy()
    for i, (_, row) in enumerate(subset.iterrows(), 1):
        name = str(row[COLS["PROGRAM_NAME"]] or "")
        org = str(row[COLS["ORGANIZATION"]] or "")
        desc_full = str(row[COLS["DESCRIPTION"]] or "")
        status = str(row[COLS["STATUS"]] or "")
        fund_bucket_val = str(row.get("__funding_bucket") or "")
        fund_type_set = row.get("__fund_type_set", set())
        fresh_days = row.get("__fresh_days")
        fresh_date = str(row.get("__fresh_date") or "")
        fresh_label = freshness_label(fresh_days)

        website = str(row.get(COLS["WEBSITE"]) or "").strip()
        email_raw = str(row.get(COLS["EMAIL"]) or "").strip()
        phone_raw = str(row.get(COLS["PHONE"]) or "").strip()

        if (
            "not publicly listed" in phone_raw.lower()
            and "contact page" in phone_raw.lower()
        ):
            phone_raw = ""
        phone_display_multi = format_phone_multi(phone_raw)
        key = str(row.get(COLS["KEY"], f"k{i}"))

        st.markdown("<div class='pf-card-marker'>", unsafe_allow_html=True)

        badge_cls = "badge-open"
        badge_label = "Operational"
        if "closed" in status.lower():
            badge_cls = "badge-closed"
            badge_label = "Closed"
        elif "paused" in status.lower():
            badge_cls = "badge-paused"
            badge_label = "Paused"

        st.markdown(
            f"""
            <span class='badge {badge_cls}'>{badge_label}</span>
            <span class='meta'>Last checked: {fresh_date if fresh_date else "Not available"} - {fresh_label}</span>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(f"<h3 class='program-title'>{name}</h3>", unsafe_allow_html=True)
        if org:
            st.markdown(f"<div class='program-org'>{org}</div>", unsafe_allow_html=True)

        render_description(desc_full, key)

        fund_raw = sanitize_text_keep_smart(str(row.get(COLS["FUNDING"]) or "").strip())
        fund_label = ""
        if fund_raw and "$" in fund_raw:
            fund_label = fund_raw
        elif fund_bucket_val and fund_bucket_val.strip().lower() != UNKNOWN:
            fund_label = add_dollar_signs(fund_bucket_val)

        fund_type_label = ""
        if isinstance(fund_type_set, set) and fund_type_set:
            fund_type_label = ", ".join(sorted(fund_type_set))

        fund_line = (
            f'<span class="kv"><strong>Funding available:</strong> {fund_label}</span>'
            if fund_label
            else ""
        )
        fund_type_line = (
            f'<span class="kv"><strong>Funding type:</strong> {fund_type_label}</span>'
            if fund_type_label
            else ""
        )

        elig_text = drop_url_like(
            sanitize_text_keep_smart(str(row.get(COLS["ELIGIBILITY"]) or ""))
        )
        elig_line = (
            f'<span class="kv"><strong>Eligibility highlights:</strong> {elig_text}</span>'
            if (
                elig_text
                and "description pending" not in elig_text.lower()
                and "see website" not in elig_text.lower()
            )
            else ""
        )

        meta_html_parts = [p for p in [fund_line, fund_type_line, elig_line] if p]
        if meta_html_parts:
            inner = " ".join(meta_html_parts)
            meta_html = f'<div class="meta-strip">{inner}</div>'
        else:
            meta_html = '<p class="placeholder">Funding, funding type, or eligibility details are not available in this view.</p>'

        st.markdown(meta_html, unsafe_allow_html=True)

        st.markdown("<div class='actions-row'>", unsafe_allow_html=True)
        cols_actions = st.columns(4)
        call_clicked = False
        fav_clicked = False

        with cols_actions[0]:
            if website:
                url = website if website.startswith(("http://", "https://")) else f"https://{website}"
                st.markdown(f"[Website]({url})", unsafe_allow_html=True)

        with cols_actions[1]:
            email_label, email_href = parse_email_field(email_raw)
            if email_label:
                if email_href:
                    st.markdown(f"[{email_label}]({email_href})", unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<span class='placeholder'>{email_label}</span>",
                        unsafe_allow_html=True,
                    )

        with cols_actions[2]:
            if phone_display_multi:
                call_clicked = st.button("Show phone number", key=f"call_{key}")

        with cols_actions[3]:
            fav_on = key in st.session_state.favorites
            fav_label = "★ Favourite" if fav_on else "☆ Favourite"
            fav_clicked = st.button(fav_label, key=f"fav_{key}")

        st.markdown("</div>", unsafe_allow_html=True)

        if phone_display_multi:
            call_state_key = f"show_call_{key}"
            if call_clicked:
                st.session_state[call_state_key] = not st.session_state.get(
                    call_state_key, False
                )
            if st.session_state.get(call_state_key, False):
                st.markdown(
                    f"<small class='pf-phone-line'><strong>Phone:</strong> {phone_display_multi}</small>",
                    unsafe_allow_html=True,
                )

        if fav_clicked:
            if fav_on:
                st.session_state.favorites.remove(key)
            else:
                st.session_state.favorites.add(key)
            st.experimental_rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    close_shell()


if __name__ == "__main__":
    main()
