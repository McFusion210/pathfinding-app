import os
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple, Set

import numpy as np
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

UNKNOWN = "Unknown, not stated"
FUZZY_THR = 60

# Global column map, filled in main()
COLS: Dict[str, str] = {}


# ------------------------- CSS AND LAYOUT -------------------------


def embed_css() -> None:
    st.markdown(
        """
<style>
:root{
  --bg:#FFFFFF; --surface:#FFFFFF; --text:#0A0A0A; --muted:#4B5563;
  --border:#E5E7EB; --border-subtle:#E5E7EB;
  --primary:#003366; --primary-soft:#E5EDF7;
  --accent:#0077C8; --accent-soft:#E0F2FE;
  --danger:#991B1B; --danger-soft:#FEE2E2;
  --success:#166534; --success-soft:#DCFCE7;
  --pill-bg:#F9FAFB; --pill-on:#003366; --pill-on-text:#FFFFFF;
  --shadow-sm:0 1px 2px rgba(15,23,42,0.08);
  --shadow-md:0 4px 6px rgba(15,23,42,0.08);
  --radius-lg:12px; --radius-xl:16px; --radius-pill:999px;
  --header-height:56px;
}

html, body, [data-testid="stAppViewContainer"]{
  background:var(--bg);
  color:var(--text);
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}

/* Remove default Streamlit padding */
main.block-container{
  padding-top:0.5rem;
  padding-bottom:1.5rem;
}

/* GoA style header bar */
.goa-header{
  background:#003366;
  color:#FFFFFF;
  height:var(--header-height);
  display:flex;
  align-items:center;
  padding:0 1.5rem;
  box-shadow:0 1px 2px rgba(15,23,42,0.35);
  position:sticky;
  top:0;
  z-index:999;
}
.goa-header-inner{
  display:flex;
  align-items:center;
  gap:1rem;
}
.goa-logo-wrap{
  display:flex;
  align-items:center;
  gap:0.5rem;
}
.goa-logo-text{
  font-size:0.9rem;
  letter-spacing:0.06em;
  text-transform:uppercase;
  opacity:0.9;
}
.goa-header-title-block{
  display:flex;
  flex-direction:column;
}
.goa-header-title{
  font-size:1.05rem;
  font-weight:600;
}
.goa-header-sub{
  font-size:0.8rem;
  opacity:0.9;
}

/* Top hero section */
.hero-shell{
  margin-top:1.25rem;
  margin-bottom:0.75rem;
}
.hero-steps{
  font-size:0.9rem;
  color:#111827;
}

/* Search tip */
.tip-pill{
  background:#EFF6FF;
  color:#1D4ED8;
  border-radius:var(--radius-lg);
  padding:0.6rem 0.75rem;
  font-size:0.8rem;
  border:1px solid #BFDBFE;
  margin-top:0.4rem;
}

/* Search bar */
.search-shell{
  margin:0.5rem 0 0.5rem 0;
}
.search-shell .stTextInput>div>div input{
  border-radius:999px;
  border:1px solid #CBD5E1;
  font-size:0.9rem;
  padding:0.5rem 0.85rem;
}
.search-shell .stTextInput>div>div input:focus{
  border-color:#2563EB;
  box-shadow:0 0 0 1px #2563EB;
}

/* Sort and page size row */
.meta-row{
  margin-top:0.4rem;
  margin-bottom:0.4rem;
}
.meta-row label{
  font-size:0.8rem !important;
}

/* Sidebar */
[data-testid="stSidebar"]{
  background:#F9FAFB;
  border-right:1px solid #E5E7EB;
}
[data-testid="stSidebar"]>div:first-child{
  padding-top:1rem;
}
.sidebar-section{
  padding-bottom:1.2rem;
  border-bottom:1px solid #E5E7EB;
  margin-bottom:1rem;
}
.sidebar-section h3{
  font-size:15px;
  font-weight:600;
  margin-bottom:0.25rem;
}
.sidebar-section .hint{
  font-size:0.8rem;
  color:#6B7280;
  margin-bottom:0.35rem;
}
.sidebar-section .hint-strong{
  font-size:0.8rem;
  color:#111827;
}

/* Tiny uppercase label above groups */
.sidebar-label{
  text-transform:uppercase;
  letter-spacing:0.06em;
  font-size:0.7rem;
  color:#6B7280;
  margin-bottom:0.25rem;
}

/* Base button font reset */
.stButton > button{
  font-size:14px;
}

/* Sidebar filter pills (single-column) */
div[data-testid="stSidebar"] .stButton > button{
  font-size:13px !important;
  padding:8px 10px;
  margin:4px 0 0 0;
  border-radius:12px;
  border:1px solid #D1D5DB;
  background:#F9FAFB;
  color:#111827;
  white-space:normal;
  width:100%;
  text-align:left;
  min-height:40px;
}
div[data-testid="stSidebar"] .stButton > button:hover{
  border-color:#9CA3AF;
  background:#F3F4F6;
}
div[data-testid="stSidebar"] .stButton > button:focus{
  outline:2px solid #2563EB;
}

/* Active filter chips under search bar */
.active-filters{
  display:flex;
  flex-wrap:wrap;
  gap:0.25rem;
  margin:0.2rem 0 0.5rem 0;
}
.filter-chip{
  border-radius:999px;
  padding:0.2rem 0.5rem;
  font-size:0.75rem;
  border:1px solid #CBD5E1;
  background:#EEF2FF;
  color:#111827;
}

/* Funding definitions text under pills */
.funding-defs{
  margin-top:0.4rem;
  padding:0.5rem 0.25rem 0.1rem 0.25rem;
  border-top:1px solid #E5E7EB;
}
.funding-defs dt{
  font-weight:600;
  font-size:0.8rem;
  margin-top:0.25rem;
}
.funding-defs dd{
  margin-left:0;
  font-size:0.78rem;
  color:#4B5563;
}

/* Program card shell */
.card-shell{
  margin-top:0.5rem;
}
.card-marker{
  border-radius:14px;
  border:1px solid #E5E7EB;
  box-shadow:var(--shadow-sm);
  background:#FFFFFF;
  padding:0.85rem 1rem 0.7rem 1rem;
  margin-bottom:0.8rem;
  display:flex;
  flex-direction:column;
  gap:0.35rem;
}

/* Status row */
.card-status-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:0.5rem;
  font-size:0.78rem;
  color:#6B7280;
}
.status-pill{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:0.15rem 0.6rem;
  border-radius:999px;
  font-size:0.75rem;
  font-weight:500;
}
.status-op{
  background:#DCFCE7;
  color:#166534;
}
.status-paused{
  background:#FEF3C7;
  color:#92400E;
}
.status-closed{
  background:#FEE2E2;
  color:#991B1B;
}
.fresh-chip{
  padding:0.1rem 0.45rem;
  border-radius:999px;
  background:#EFF6FF;
  color:#1D4ED8;
  font-size:0.72rem;
}

/* Program title and org */
.card-title{
  font-size:0.98rem;
  font-weight:600;
  color:#111827;
}
.card-org{
  font-size:0.83rem;
  color:#4B5563;
}

/* Description with show more */
.card-desc{
  font-size:0.85rem;
  color:#111827;
  margin-top:0.1rem;
}
.showmore-btn{
  font-size:0.78rem;
  color:#1D4ED8;
  cursor:pointer;
}

/* Meta strip under description */
.card-meta-row{
  display:flex;
  flex-wrap:wrap;
  gap:0.25rem 0.75rem;
  font-size:0.76rem;
  color:#4B5563;
  margin-top:0.1rem;
}
.meta-label{
  font-weight:600;
  color:#374151;
}

/* Tag chips */
.tag-row{
  display:flex;
  flex-wrap:wrap;
  gap:0.2rem;
  margin-top:0.15rem;
}
.tag-chip{
  border-radius:999px;
  padding:0.1rem 0.45rem;
  font-size:0.72rem;
  border:1px solid #E5E7EB;
  background:#F9FAFB;
  color:#4B5563;
}

/* Card actions row */
.card-actions{
  margin-top:0.35rem;
  padding-top:0.4rem;
  border-top:1px dashed #E5E7EB;
}
.card-actions-inner{
  display:flex;
  flex-wrap:wrap;
  gap:0.5rem;
  align-items:center;
  justify-content:flex-start;
}
.card-actions-inner .stButton>button{
  border-radius:999px;
  padding:0.25rem 0.75rem;
  font-size:0.8rem !important;
  border:1px solid #D1D5DB;
  background:#F9FAFB;
}
.card-actions-inner .stButton>button:hover{
  border-color:#9CA3AF;
  background:#EFF6FF;
}

/* Results summary row */
.results-summary{
  font-size:0.85rem;
  color:#4B5563;
  margin:0.25rem 0 0.2rem 0;
}

/* Small helper text in body */
.helper-text{
  font-size:0.8rem;
  color:#6B7280;
  margin-top:0.15rem;
}

/* Hide default header */
header[data-testid="stHeader"]{
  display:none;
}

/* Adjust sidebar width */
@media (min-width: 1024px){
  [data-testid="stSidebar"]{
    min-width:280px;
    max-width:280px;
  }
}

/* Tweak selectboxes */
.stSelectbox>div>div{
  border-radius:999px;
}

/* Footer spacing */
footer{
  margin-top:1.5rem;
}

/* Small grey text */
.small-grey{
  font-size:0.76rem;
  color:#6B7280;
}

/* Location text under sidebar */
.location-note{
  font-size:0.78rem;
  color:#6B7280;
  margin-top:0.75rem;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def embed_logo_html() -> None:
    st.markdown(
        """
<div class="goa-header">
  <div class="goa-header-inner">
    <div class="goa-logo-wrap">
      <img src="https://upload.wikimedia.org/wikipedia/commons/8/89/Alberta_Wordmark_Logo.svg"
           alt="Alberta" height="26">
      <span class="goa-logo-text">Government of Alberta</span>
    </div>
    <div class="goa-header-title-block">
      <div class="goa-header-title">Small Business Supports Finder</div>
      <div class="goa-header-sub">
        Helping Alberta entrepreneurs and small businesses find programs, funding, and services quickly.
      </div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------- COLUMN INFERENCE -------------------------


def infer_columns(df: pd.DataFrame) -> Dict[str, str]:
    cols = {c.lower(): c for c in df.columns}

    def match_one(candidates: List[str]) -> Optional[str]:
        for c in candidates:
            for k, original in cols.items():
                if c in k:
                    return original
        return None

    mapping = {
        "PROGRAM_NAME": match_one(["program name", "program", "initiative"]),
        "ORGANIZATION": match_one(["organization", "organisation", "provider"]),
        "DESCRIPTION": match_one(["description", "overview", "summary", "details"]),
        "ELIGIBILITY": match_one(["eligibility", "who is eligible", "who can apply"]),
        "WEBSITE": match_one(["website", "url", "link"]),
        "EMAIL": match_one(["email", "e-mail"]),
        "PHONE": match_one(["phone", "telephone", "tel"]),
        "REGION": match_one(["region", "location", "area", "geography"]),
        "FUNDING": match_one(["funding amount", "max funding", "amount"]),
        "STATUS": match_one(["status", "availability"]),
        "LAST_CHECKED": match_one(["last checked", "validation date", "last updated"]),
        "META_TAGS": match_one(["tags", "meta tags", "keywords", "metadata"]),
        "KEY": match_one(["stable key", "program key", "unique key", "id"]),
    }

    for k, v in mapping.items():
        if v is None:
            mapping[k] = ""

    return mapping


# ------------------------- TAG PARSING AND CLASSIFICATION -------------------------


TAG_SPLIT = re.compile(r"[;,/|]")


def parse_tags_field(value: str) -> List[str]:
    if not isinstance(value, str):
        return []
    parts = TAG_SPLIT.split(value)
    return [p.strip() for p in parts if p.strip()]


URL_LIKE = re.compile(r"https?://|www\\.", re.IGNORECASE)


def parse_tags_field_clean(value: str) -> List[str]:
    raw = parse_tags_field(value)
    out: List[str] = []
    for p in raw:
        low = p.lower()
        if len(low) <= 1:
            continue
        if low in {"n/a", "na", "none", "unknown"}:
            continue
        if URL_LIKE.search(p):
            continue
        out.append(p)
    return out


def days_since(value) -> Tuple[Optional[int], Optional[str]]:
    if not value:
        return None, None
    try:
        d = pd.to_datetime(value)
    except Exception:
        return None, None
    delta = (pd.Timestamp("today").normalize() - d.normalize()).days
    if delta < 0:
        return None, d.strftime("%Y %b %d")
    return int(delta), d.strftime("%Y %b %d")


def funding_bucket(value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Unknown"
    try:
        s = str(value)
    except Exception:
        return "Unknown"

    s_clean = s.replace(",", "").replace("$", "").strip()
    if not s_clean:
        return "Unknown"

    m = re.search(r"(\\d+(?:\\.\\d+)?)", s_clean)
    if not m:
        return "Unknown"
    try:
        num = float(m.group(1))
    except Exception:
        return "Unknown"

    if num < 5000:
        return "Under $5K"
    if num < 20000:
        return "$5K to under $20K"
    if num < 50000:
        return "$20K to under $50K"
    if num < 100000:
        return "$50K to under $100K"
    if num < 250000:
        return "$100K to under $250K"
    if num < 500000:
        return "$250K to under $500K"
    if num < 1000000:
        return "$500K to under $1M"
    return "$1M and above"


SUPPORT_CATS = {
    "grant": ["grant"],
    "loan": ["loan", "financing"],
    "tax_credit": ["tax credit", "tax benefit"],
    "voucher": ["voucher", "rebate", "coupon"],
    "equity": ["equity", "investment"],
    "other_financing": ["guarantee", "financing", "credit line"],
    "advisory": ["advisory", "coaching", "mentorship", "training", "workshop"],
}

AUDIENCE_CUES = {
    "Indigenous": ["indigenous", "first nation", "metis", "inuit"],
    "Youth": ["youth", "young", "student"],
    "Women": ["women", "woman", "female"],
    "Newcomer": ["immigrant", "newcomer"],
    "Rural": ["rural"],
    "Northern": ["north", "northern"],
    "Tech": ["technology", "innovation", "digital", "startup"],
}

REGION_CUES = {
    "Province wide": ["alberta wide", "province wide", "all regions", "alberta"],
    "Rural Alberta": ["rural"],
    "Northern Alberta": ["north", "northern"],
    "Southern Alberta": ["south", "southern"],
    "Calgary region": ["calgary"],
    "Edmonton region": ["edmonton"],
}

STAGE_CUES = {
    "Idea or planning": ["idea", "planning", "concept"],
    "Startup or early stage": ["startup", "start up", "early stage"],
    "Growing or scaling": ["growth", "scaling", "scale"],
    "Established or mature": ["mature", "established"],
}


def classify_support(tags: List[str], funding_amount_raw) -> List[str]:
    text = " ".join(tags).lower()
    matches: Set[str] = set()
    for label, cues in SUPPORT_CATS.items():
        for c in cues:
            if c in text:
                matches.add(label)
                break

    if "grant" not in matches and isinstance(funding_amount_raw, str):
        if "grant" in funding_amount_raw.lower():
            matches.add("grant")

    if not matches:
        matches.add("other_support")
    return sorted(matches)


def classify_audience(tags: List[str]) -> List[str]:
    text = " ".join(tags).lower()
    matches: Set[str] = set()
    for label, cues in AUDIENCE_CUES.items():
        for c in cues:
            if c in text:
                matches.add(label)
                break
    return sorted(matches)


def classify_region(region_value) -> List[str]:
    if isinstance(region_value, str) and region_value.strip():
        lower = region_value.lower()
        matches: Set[str] = set()
        for label, cues in REGION_CUES.items():
            for c in cues:
                if c in lower:
                    matches.add(label)
                    break
        if matches:
            return sorted(matches)
    return ["Province wide"]


def classify_stage(tags: List[str]) -> List[str]:
    text = " ".join(tags).lower()
    matches: Set[str] = set()
    for label, cues in STAGE_CUES.items():
        for c in cues:
            if c in text:
                matches.add(label)
                break
    return sorted(matches)


def derive_funding_types_from_tags(tags: List[str]) -> Set[str]:
    out: Set[str] = set()
    for t in tags:
        low = t.lower()
        if "grant" in low:
            out.add("Grant")
        if "loan" in low:
            out.add("Loan")
        if "tax" in low and "credit" in low:
            out.add("Tax Credit")
        if "voucher" in low or "rebate" in low:
            out.add("Voucher or Rebate")
        if "equity" in low or "investment" in low:
            out.add("Equity or Investment")
        if "financing" in low or "guarantee" in low:
            out.add("Other Financing")
    return out


# ---------------------- SEARCH AND FILTER LOGIC ----------------------


def fuzzy_mask(df: pd.DataFrame, query: str, threshold: int = FUZZY_THR) -> pd.Series:
    if not query:
        return pd.Series(True, index=df.index)

    query = query.strip()
    if not query:
        return pd.Series(True, index=df.index)

    target_cols = [
        COLS.get("PROGRAM_NAME", ""),
        COLS.get("ORGANIZATION", ""),
        COLS.get("DESCRIPTION", ""),
    ]
    target_cols = [c for c in target_cols if c in df.columns]

    if not target_cols:
        return pd.Series(True, index=df.index)

    mask = np.zeros(len(df), dtype=bool)
    for col in target_cols:
        series = df[col].fillna("").astype(str)
        scores = series.apply(lambda s: fuzz.partial_ratio(query, s))
        mask |= scores.values >= threshold

    return pd.Series(mask, index=df.index)


def apply_multi_filter(
    df: pd.DataFrame, col: str, selected: List[str], allow_empty: bool = True
) -> pd.DataFrame:
    if not selected:
        return df
    if col not in df.columns:
        return df

    def row_ok(values: List[str]) -> bool:
        if not isinstance(values, list):
            return False if not allow_empty else True
        if not values:
            return allow_empty
        for v in values:
            if v in selected:
                return True
        return False

    mask = df[col].apply(row_ok)
    return df[mask]


def apply_simple_filter(
    df: pd.DataFrame, col: str, selected: List[str]
) -> pd.DataFrame:
    if not selected:
        return df
    if col not in df.columns:
        return df
    return df[df[col].isin(selected)]


def build_active_filter_labels(
    funding_types: List[str],
    funding_bands: List[str],
    audiences: List[str],
    regions: List[str],
    stages: List[str],
) -> List[str]:
    out: List[str] = []

    for v in funding_types:
        out.append(f"Funding type: {v}")
    for v in funding_bands:
        out.append(f"Funding amount: {v}")
    for v in audiences:
        out.append(f"Audience: {v}")
    for v in regions:
        out.append(f"Location: {v}")
    for v in stages:
        out.append(f"Stage: {v}")

    return out


# ---------------------- PHONE AND CONTACT HANDLING ----------------------


PHONE_CLEAN = re.compile(r"[^\d]+")


def normalize_phone(raw: str) -> Optional[str]:
    if raw is None:
        return None
    if isinstance(raw, float) and np.isnan(raw):
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"nan", "n/a", "na", "none", "not listed"}:
        return None

    digits = PHONE_CLEAN.sub("", s)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return digits


def format_phone(digits: str) -> str:
    if len(digits) != 10:
        return digits
    return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"


def extract_phone_list(raw_value) -> List[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, float) and np.isnan(raw_value):
        return []
    s = str(raw_value)
    if not s.strip():
        return []

    parts = re.split(r"[;\\n/|,]", s)
    out: List[str] = []
    for p in parts:
        norm = normalize_phone(p)
        if norm:
            out.append(norm)
    seen: Set[str] = set()
    uniq: List[str] = []
    for v in out:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def format_phone_multi(raw_value) -> Tuple[str, str]:
    phones = extract_phone_list(raw_value)
    if not phones:
        return "", ""

    formatted = [format_phone(p) for p in phones]
    main = formatted[0]
    more = " | ".join(formatted)
    return main, more


def safe_email(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    s = str(value).strip()
    if not s or s.lower() in {"nan", "n/a", "na", "none"}:
        return ""
    if s.lower().startswith("mailto:"):
        s = s[7:].strip()
    return s


def safe_url(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    s = str(value).strip()
    if not s or s.lower() in {"nan", "n/a", "na", "none"}:
        return ""
    if not s.lower().startswith(("http://", "https://")):
        s = "https://" + s
    return s


# ---------------------- DATA LOADING ----------------------


def load_data(path: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    df.columns = [str(c).strip() for c in df.columns]
    col_map = infer_columns(df)

    required = [
        "PROGRAM_NAME",
        "ORGANIZATION",
        "DESCRIPTION",
        "ELIGIBILITY",
        "WEBSITE",
        "EMAIL",
        "PHONE",
        "REGION",
        "FUNDING",
        "STATUS",
        "LAST_CHECKED",
        "META_TAGS",
        "KEY",
    ]
    for key in required:
        col_name = col_map.get(key, "")
        if not col_name or col_name not in df.columns:
            col_name = f"__missing_{key}"
            df[col_name] = ""
            col_map[key] = col_name

    df["__funding_bucket"] = df[col_map["FUNDING"]].apply(funding_bucket)

    days_list, date_list = [], []
    for val in df[col_map["LAST_CHECKED"]].tolist():
        d, ds = days_since(val)
        days_list.append(d)
        date_list.append(ds or "")
    df["__fresh_days"] = days_list
    df["__fresh_date"] = date_list

    if df[col_map["KEY"]].isna().any():
        df[col_map["KEY"]] = (
            df[col_map["PROGRAM_NAME"]]
            .fillna("")
            .astype(str)
            .str.slice(0, 80)
            + "-"
            + df.index.astype(str)
        )

    df["__tags_list"] = df[col_map["META_TAGS"]].apply(parse_tags_field_clean)

    df["__support_cats"] = [
        classify_support(tags, fa)
        for tags, fa in zip(df["__tags_list"], df[col_map["FUNDING"]])
    ]
    df["__audience_cats"] = df["__tags_list"].apply(classify_audience)
    df["__region_cats"] = df[col_map["REGION"]].apply(classify_region)
    df["__stage_cats"] = df["__tags_list"].apply(classify_stage)

    df["__fund_type_set"] = df["__tags_list"].apply(derive_funding_types_from_tags)

    return df, col_map


# ---------------------- SIDEBAR FILTER RENDERING ----------------------


def render_filter_pills(
    label: str,
    hint: str,
    options: List[Tuple[str, str]],
    session_key: str,
    single_select: bool = False,
) -> List[str]:
    st.markdown(f"<div class='sidebar-section'><h3>{label}</h3>", unsafe_allow_html=True)
    if hint:
        st.markdown(
            f"<div class='hint'>{hint}</div>",
            unsafe_allow_html=True,
        )

    selected = st.session_state.get(session_key, [])

    for code, text in options:
        is_selected = code in selected
        btn_label = f"✓ {text}" if is_selected else text
        clicked = st.button(btn_label, key=f"{session_key}_{code}")
        if clicked:
            if single_select:
                selected = [code]
            else:
                if is_selected:
                    selected = [v for v in selected if v != code]
                else:
                    selected = selected + [code]
            st.session_state[session_key] = selected
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    return selected


def render_funding_type_pills(funding_type_counts: Counter) -> List[str]:
    options = [
        ("Grant", f"Grant ({funding_type_counts.get('Grant', 0)})"),
        ("Loan", f"Loan ({funding_type_counts.get('Loan', 0)})"),
        ("Tax Credit", f"Tax Credit ({funding_type_counts.get('Tax Credit', 0)})"),
        (
            "Voucher or Rebate",
            f"Voucher or Rebate ({funding_type_counts.get('Voucher or Rebate', 0)})",
        ),
        (
            "Equity or Investment",
            f"Equity or Investment ({funding_type_counts.get('Equity or Investment', 0)})",
        ),
        (
            "Other Financing",
            f"Other Financing ({funding_type_counts.get('Other Financing', 0)})",
        ),
    ]

    st.markdown(
        "<div class='sidebar-section'><h3>What kind of funding are you looking for?</h3>"
        "<div class='hint'>Select one or more funding types.</div>",
        unsafe_allow_html=True,
    )

    session_key = "filter_funding_type"
    selected = st.session_state.get(session_key, [])

    for code, text in options:
        is_selected = code in selected
        btn_label = f"✓ {text}" if is_selected else text
        clicked = st.button(btn_label, key=f"{session_key}_{code}")
        if clicked:
            if is_selected:
                selected = [v for v in selected if v != code]
            else:
                selected = selected + [code]
            st.session_state[session_key] = selected
            st.experimental_rerun()

    st.markdown(
        """
<dl class="funding-defs">
  <dt>Grant</dt>
  <dd>Non repayable funding.</dd>
  <dt>Loan</dt>
  <dd>Repayable financing with interest.</dd>
  <dt>Tax Credit</dt>
  <dd>Reduces taxes based on eligible expenses.</dd>
  <dt>Voucher or Rebate</dt>
  <dd>Discounts or partial refunds.</dd>
  <dt>Equity or Investment</dt>
  <dd>Capital in exchange for ownership.</dd>
  <dt>Other Financing</dt>
  <dd>Other financial products.</dd>
</dl>
</div>
        """,
        unsafe_allow_html=True,
    )

    return selected


# ---------------------- MAIN PAGE AND CARDS ----------------------


def render_active_filters(labels: List[str]) -> None:
    if not labels:
        return
    st.markdown('<div class="active-filters">', unsafe_allow_html=True)
    for lbl in labels:
        st.markdown(
            f'<span class="filter-chip">{lbl}</span>', unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)


def open_shell() -> None:
    st.markdown('<div class="card-shell">', unsafe_allow_html=True)


def close_shell() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_program_card(row: pd.Series) -> None:
    program_name = str(row[COLS["PROGRAM_NAME"]] or "").strip() or "Untitled program"
    org = str(row[COLS["ORGANIZATION"]] or UNKNOWN)
    desc = str(row[COLS["DESCRIPTION"]] or UNKNOWN)
    elig = str(row[COLS["ELIGIBILITY"]] or "")
    website = safe_url(row[COLS["WEBSITE"]])
    email = safe_email(row[COLS["EMAIL"]])
    raw_phone = row[COLS["PHONE"]]
    status_raw = str(row[COLS["STATUS"]] or UNKNOWN)
    fresh_days = row.get("__fresh_days")
    fresh_date = row.get("__fresh_date")
    funding_bucket_label = row.get("__funding_bucket", "Unknown")
    support_cats = row.get("__support_cats", [])
    audience_cats = row.get("__audience_cats", [])
    region_cats = row.get("__region_cats", [])
    stage_cats = row.get("__stage_cats", [])
    tags_list = row.get("__tags_list", [])
    key = row[COLS["KEY"]]

    main_phone, phone_display_multi = format_phone_multi(raw_phone)

    status_label = status_raw or "Unknown"
    status_class = "status-op"
    low = status_label.lower()
    if "pause" in low:
        status_class = "status-paused"
    elif "close" in low or "ended" in low:
        status_class = "status-closed"

    st.markdown('<div class="card-marker">', unsafe_allow_html=True)

    st.markdown('<div class="card-status-row">', unsafe_allow_html=True)
    status_html = f'<span class="status-pill {status_class}">{status_label}</span>'
    fresh_html = ""
    if isinstance(fresh_days, int):
        if fresh_days <= 60:
            freshness = "Recently checked"
            fresh_html = f'<span class="fresh-chip">{freshness}</span>'
        else:
            freshness = f"Last checked {fresh_days} days ago"
            fresh_html = f'<span class="fresh-chip">{freshness}</span>'
    elif fresh_date:
        fresh_html = f'<span class="fresh-chip">Last checked {fresh_date}</span>'

    st.markdown(
        status_html + (f"<span>{fresh_html}</span>" if fresh_html else ""),
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="card-title">{program_name}</div>', unsafe_allow_html=True
    )
    st.markdown(f'<div class="card-org">{org}</div>', unsafe_allow_html=True)

    key_desc = f"desc_{key}"
    key_more = f"more_{key}"
    show_more = st.session_state.get(key_more, False)

    if len(desc) > 320:
        short = desc[:320].rsplit(" ", 1)[0] + "..."
        st.markdown(
            f'<div class="card-desc" id="{key_desc}">{short if not show_more else desc}</div>',
            unsafe_allow_html=True,
        )
        toggled = st.button(
            "Show more" if not show_more else "Show less",
            key=f"toggle_{key}",
        )
        if toggled:
            st.session_state[key_more] = not show_more
            st.experimental_rerun()
    else:
        st.markdown(
            f'<div class="card-desc" id="{key_desc}">{desc}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="card-meta-row">', unsafe_allow_html=True)
    if funding_bucket_label and funding_bucket_label != "Unknown":
        st.markdown(
            f'<span><span class="meta-label">Funding type:</span> {funding_bucket_label}</span>',
            unsafe_allow_html=True,
        )
    if elig:
        st.markdown(
            f'<span><span class="meta-label">Eligibility highlights:</span> {elig[:140]}{"..." if len(elig) > 140 else ""}</span>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    all_tags: List[str] = []
    if support_cats:
        all_tags.extend(support_cats)
    if audience_cats:
        all_tags.extend(audience_cats)
    if region_cats:
        all_tags.extend(region_cats)
    if stage_cats:
        all_tags.extend(stage_cats)

    dedup_tags: List[str] = []
    seen_tags: Set[str] = set()
    for t in all_tags:
        if t not in seen_tags:
            seen_tags.add(t)
            dedup_tags.append(t)

    extra_tags = [t for t in tags_list if t not in seen_tags]

    if dedup_tags or extra_tags:
        st.markdown('<div class="tag-row">', unsafe_allow_html=True)
        for t in dedup_tags:
            st.markdown(
                f'<span class="tag-chip">{t}</span>',
                unsafe_allow_html=True,
            )
        for t in extra_tags[:5]:
            st.markdown(
                f'<span class="tag-chip">{t}</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="card-actions"><div class="card-actions-inner">',
        unsafe_allow_html=True,
    )

    cols_actions = st.columns(4)

    with cols_actions[0]:
        if website:
            clicked = st.button("Website", key=f"web_{key}")
            if clicked:
                st.markdown(
                    f"[Open website]({website})", unsafe_allow_html=False
                )

    with cols_actions[1]:
        if email:
            st.button("Email", key=f"email_{key}")

    with cols_actions[2]:
        if phone_display_multi:
            st.button("Call", key=f"call_{key}")

    with cols_actions[3]:
        if "favorites" not in st.session_state:
            st.session_state.favorites = set()
        fav_on = key in st.session_state.favorites
        fav_label = "★ Favourite" if fav_on else "☆ Favourite"
        fav_clicked = st.button(fav_label, key=f"fav_{key}")
        if fav_clicked:
            if fav_on:
                st.session_state.favorites.remove(key)
            else:
                st.session_state.favorites.add(key)
            st.experimental_rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

    if phone_display_multi:
        st.markdown(
            f'<div class="helper-text">Phone: {phone_display_multi}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------- MAIN APP ----------------------


def main():
    global COLS

    embed_css()
    embed_logo_html()

    data_path = "Pathfinding_Master.xlsx"
    df, col_map = load_data(data_path)
    COLS = col_map

    st.markdown("## Find programs and supports for your Alberta business")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """1. **Choose filters**  
Pick your location, support type, audience, funding needs, and more.""",
        )
    with col2:
        st.markdown(
            """2. **Browse matching programs**  
Scroll through cards that match your selections.""",
        )
    with col3:
        st.markdown(
            """3. **Take action**  
Use the website, email, phone, and favourite options to connect or save programs.""",
        )

    if "favorites" not in st.session_state:
        st.session_state.favorites = set()

    col_search, col_sort, col_page = st.columns([3, 1, 1])
    with col_search:
        st.markdown('<div class="search-shell">', unsafe_allow_html=True)
        q = st.text_input(
            "Search programs",
            "",
            help="Search also matches similar terms and common spellings, not just exact words.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with col_sort:
        sort_by = st.selectbox(
            "Sort results by",
            ["Relevance", "Program name (A to Z)", "Most recently checked"],
        )
    with col_page:
        page_size = st.selectbox("Results per page", [10, 25, 50], index=1)

    total_count = len(df)
    st.markdown(
        f'<div class="results-summary">{total_count} programs found.</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            "<div class='sidebar-label'>Filters</div>",
            unsafe_allow_html=True,
        )

        funding_type_counts = Counter()
        for s in df["__fund_type_set"]:
            for ft in s:
                funding_type_counts[ft] += 1
        selected_funding_types = render_funding_type_pills(funding_type_counts)

        band_counts = Counter(df["__funding_bucket"])
        band_options = [
            (b, f"{b} ({band_counts.get(b, 0)})")
            for b in [
                "Under $5K",
                "$5K to under $20K",
                "$20K to under $50K",
                "$50K to under $100K",
                "$100K to under $250K",
                "$250K to under $500K",
                "$500K to under $1M",
                "$1M and above",
            ]
        ]
        selected_bands = render_filter_pills(
            "How much funding are you looking for?",
            "These bands are based on the maximum funding available per program.",
            band_options,
            "filter_funding_band",
        )

        audience_counts = Counter()
        for s in df["__audience_cats"]:
            for a in s:
                audience_counts[a] += 1
        audience_options = sorted(
            ((a, f"{a} ({audience_counts.get(a, 0)})") for a in audience_counts.keys()),
            key=lambda x: x[0],
        )
        selected_audience = render_filter_pills(
            "Who is this support for?",
            "",
            audience_options,
            "filter_audience",
        )

        region_counts = Counter()
        for s in df["__region_cats"]:
            for r in s:
                region_counts[r] += 1
        region_labels = [
            "Province wide",
            "Rural Alberta",
            "Northern Alberta",
            "Southern Alberta",
            "Calgary region",
            "Edmonton region",
        ]
        region_options = [
            (r, f"{r} ({region_counts.get(r, 0)})") for r in region_labels
        ]
        selected_region = render_filter_pills(
            "Where is your business located?",
            "",
            region_options,
            "filter_region",
        )

        stage_counts = Counter()
        for s in df["__stage_cats"]:
            for a in s:
                stage_counts[a] += 1
        stage_labels = [
            "Idea or planning",
            "Startup or early stage",
            "Growing or scaling",
            "Established or mature",
        ]
        stage_options = [
            (s, f"{s} ({stage_counts.get(s, 0)})") for s in stage_labels
        ]
        selected_stage = render_filter_pills(
            "What stage is your business at?",
            "",
            stage_options,
            "filter_stage",
        )

        st.markdown(
            "<div class='location-note'>Location filters apply based on the regions listed in each program. If no specific region is listed, programs are treated as province wide.</div>",
            unsafe_allow_html=True,
        )

    active_labels = build_active_filter_labels(
        selected_funding_types,
        selected_bands,
        selected_audience,
        selected_region,
        selected_stage,
    )
    render_active_filters(active_labels)

    out = df.copy()
    out = out[fuzzy_mask(out, q, threshold=FUZZY_THR)]

    if selected_funding_types:
        mask_ft = out["__fund_type_set"].apply(
            lambda s: any(ft in s for ft in selected_funding_types)
        )
        out = out[mask_ft]

    if selected_bands:
        out = apply_simple_filter(out, "__funding_bucket", selected_bands)
    if selected_audience:
        out = apply_multi_filter(out, "__audience_cats", selected_audience)
    if selected_region:
        out = apply_multi_filter(out, "__region_cats", selected_region)
    if selected_stage:
        out = apply_multi_filter(out, "__stage_cats", selected_stage)

    if sort_by == "Program name (A to Z)":
        out = out.sort_values(COLS["PROGRAM_NAME"].strip(), kind="mergesort")
    elif sort_by == "Most recently checked":
        out = out.sort_values("__fresh_days", ascending=True, kind="mergesort")

    filtered_count = len(out)
    st.markdown(
        f'<div class="results-summary">Showing {filtered_count} programs based on your filters.</div>',
        unsafe_allow_html=True,
    )

    if filtered_count == 0:
        st.info(
            "No programs found that match your search and filters. "
            "Try removing a filter or broadening your search terms."
        )
        return

    total_pages = (filtered_count - 1) // page_size + 1
    page_num = st.number_input(
        "Page",
        min_value=1,
        max_value=int(total_pages),
        value=1,
        step=1,
        help="Use this to jump between pages of results.",
    )

    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    page_df = out.iloc[start_idx:end_idx]

    open_shell()
    for _, row in page_df.iterrows():
        render_program_card(row)
    close_shell()


if __name__ == "__main__":
    main()
