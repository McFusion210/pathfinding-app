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

# Page config
st.set_page_config(
    page_title="Small Business Supports Finder",
    page_icon="✅",
    layout="wide",
)


# ---------------------- STYLING / CHROME ----------------------


def embed_css() -> None:
    st.markdown(
        """
<style>
:root{
  --bg:#FFFFFF; --surface:#FFFFFF; --text:#0A0A0A; --muted:#4B5563;
  --primary:#003366; --primary-2:#007FA3; --border:#D9DEE7; --link:#007FA3;
  --fs-title:24px; --fs-body:15px; --fs-meta:13px;
}

/* Global text and layout */
html, body, p, div, span{
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Segoe UI Emoji";
  color:var(--text);
}
body{
  background:#F3F4F6;
}
p{ margin:4px 0 4px 0; }
small{ font-size:var(--fs-meta); }

/* Normalise link colours so visited links do not go purple */
a:link, a:visited{
  color:var(--link);
}

/* Header */
.goa-header{
  background:#003366;
  color:#FFFFFF !important;
  padding:16px 32px;
  display:flex;
  align-items:center;
  gap:16px;
  position:sticky;
  top:0;
  z-index:50;
}
.goa-header *{
  color:#FFFFFF !important;
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

/* App shell */
.app-shell{
  padding:18px 32px 32px 32px;
  background:#F3F4F6;
}
.block-container{
  padding-top:0 !important;
}

/* Program cards (GoA blue box) */
.pf-card-marker{
  border-radius:12px;
  border:1px solid #003366;
  padding:16px 16px 14px 16px;
  background:#E6EFF7; /* light Alberta blue */
  margin:10px 0 14px 0;
  box-shadow:0 1px 3px rgba(15,23,42,0.10);
}
.pf-card-marker:hover{
  box-shadow:0 4px 10px rgba(15,23,42,0.18);
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
  color:#111827;
}
h3.program-title{
  font-size:18px;
  margin:6px 0 2px 0;
}
.program-org{
  font-size:var(--fs-body);
  color:#1F2933;
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
  color:#111827;
}
.placeholder{
  font-size:var(--fs-meta);
  color:#6B7280;
  font-style:italic;
}
.actions-row{
  margin-top:10px;
}
.pf-phone-line{
  display:block;
  margin-top:4px;
  font-size:var(--fs-body);
}
.pf-phone-line strong{
  font-weight:600;
}
.results-summary{
  font-size:var(--fs-meta);
  color:#4B5563;
}

/* Accessibility skip link */
.skip-link {
  position:absolute; left:-9999px; top:auto; width:1px; height:1px; overflow:hidden;
}
.skip-link:focus {
  position:fixed; left:16px; top:12px; width:auto; height:auto; padding:8px 10px;
  background:#fff; color:#000; border:2px solid #000; z-index:9999;
}

/* Sidebar sections and pills */
.sidebar-section{
  margin-top:6px;
}
.sidebar-section h3{
  font-size:12px;           /* swapped: smaller heading */
  font-weight:600;
  margin:0 0 4px 0;
}
.sidebar-section small{
  color:#6B7280;
  font-size:12px;
}

/* Base button font reset */
.stButton > button{
  font-size:14px;
}

/* Sidebar filter pills (single-column) */
div[data-testid="stSidebar"] .stButton > button{
  font-size:15px !important;  /* swapped: larger pill text */
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
.chips-row{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin-top:4px;
}
.chips-row .stButton > button{
  font-size:11px;
  padding:4px 12px;
  margin:2px 4px 0 0;
  border-radius:999px;
  border:1px solid #D1D5DB;
  background:#E5E7EB;
  color:#1D4ED8;  /* blue-ish to distinguish */
  text-align:left;
}
.chips-row .stButton > button:hover{
  background:#D1D5DB;
}

/* Links inside cards */
.pf-card-marker a{
  color:#007FA3 !important;
  text-decoration:underline;
}
.pf-card-marker a:hover{
  opacity:.85;
}

/* Buttons inside cards treated as text links (Call, Favourite) */
.pf-card-marker .stButton > button{
  background:none !important;
  border:none !important;
  padding:0;
  margin:0 16px 0 0;
  color:#007FA3 !important;
  text-decoration:underline;
  font-size:var(--fs-body);
  cursor:pointer;
  box-shadow:none !important;
  border-radius:0 !important;
}
.pf-card-marker .stButton > button:hover{
  opacity:.85;
}

/* Search bar border a bit darker */
div[data-baseweb="input"] > div{
  border-color:#9CA3AF !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def embed_logo_html() -> None:
    # Use repo assets / official GoA logo if available; fall back to remote
    local_logo = "assets/GoA-logo.svg"
    if os.path.exists(local_logo):
        logo_src = local_logo
    else:
        logo_src = (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/"
            "Alberta_Government_Logo.svg/320px-Alberta_Government_Logo.svg.png"
        )

    st.markdown(
        f"""
<a href="#main" class="skip-link">Skip to main content</a>
<div class="goa-header">
  <img src="{logo_src}" alt="Government of Alberta" class="goa-header-logo" />
  <div class="goa-header-text">
    <h1>Small Business Supports Finder</h1>
    <p>Helping Alberta entrepreneurs and small businesses find programs, funding, and services quickly.</p>
  </div>
</div>
<div id="main" class="app-shell">
""",
        unsafe_allow_html=True,
    )


def close_shell() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------- TEXT UTILITIES ----------------------


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


def parse_tags_field_clean(val) -> List[str]:
    """Split Meta Tags into tokens, dropping web addresses."""
    if not isinstance(val, str):
        return []
    s = re.sub(r"[\n\r]+", " ", val)
    parts = [p.strip() for p in s.split(";")]
    out: List[str] = []
    for p in parts:
        if not p:
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
    return int(delta), d.date().isoformat()


def freshness_label(days: Optional[int]) -> str:
    if days is None:
        return "Last checked date not available"
    if days <= 90:
        return f"{days} days ago (recent)"
    if days <= 365:
        return f"{days} days ago"
    return f"{days} days ago (may be out of date)"


# ---------------------- FUNDING & CONTACT LOGIC ----------------------


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


def normalize_phone(phone: str) -> Tuple[str, str]:
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


def parse_email_field(raw: str) -> Tuple[str, str]:
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


# ---------------------- DISPLAY HELPERS ----------------------


def render_description(desc_full: str, key: str) -> None:
    desc_full = sanitize_text_keep_smart(desc_full or "")
    if not desc_full:
        st.markdown(
            "<p class='placeholder'>No description available.</p>",
            unsafe_allow_html=True,
        )
        return
    short = desc_full
    limit = 260
    if len(desc_full) > limit:
        short = desc_full[:limit].rsplit(" ", 1)[0] + "..."
    state_key = f"show_more_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = False
    if st.session_state[state_key]:
        st.markdown(
            f"<p class='program-desc'>{desc_full}</p>", unsafe_allow_html=True
        )
        if st.button("Show less", key=f"less_{key}"):
            st.session_state[state_key] = False
            st.rerun()
    else:
        st.markdown(
            f"<p class='program-desc'>{short}</p>", unsafe_allow_html=True
        )
        if len(desc_full) > limit:
            if st.button("Show more", key=f"more_{key}"):
                st.session_state[state_key] = True
                st.rerun()


# ---------------------- COLUMN INFERENCE ----------------------


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
        "ORGANIZATION": map_col(
            df, ["Organization Name", "Organization", "Provider", "Delivery partner"]
        ),
        "DESCRIPTION": map_col(df, ["Program Description", "Description", "Summary"]),
        "ELIGIBILITY": map_col(
            df, ["Eligibility Description", "Eligibility", "Eligibility highlights"]
        ),
        "WEBSITE": map_col(df, ["Program Website", "Website", "URL", "Link"]),
        "EMAIL": map_col(df, ["Email Address", "Email", "E-mail", "Contact email"]),
        "PHONE": map_col(df, ["Phone Number", "Phone", "Telephone", "Contact phone"]),
        "REGION": map_col(df, ["Geographic Region", "Region", "Location", "Geography"]),
        "FUNDING": map_col(
            df, ["Funding Amount", "Funding amount", "Funding", "Max funding"]
        ),
        "STATUS": map_col(df, ["Operational Status", "Status", "Program status"]),
        "LAST_CHECKED": map_col(
            df, ["Last Checked (MT)", "Last checked", "Validated on", "Last updated"]
        ),
        "META_TAGS": map_col(df, ["Meta Tags", "Tags", "Keywords"]),
        "KEY": map_col(df, ["_key_norm", "Key", "Unique id", "Program key"]),
    }
    return cfg


# ---------------------- CATEGORY CLASSIFIERS ----------------------


def classify_support(tags: List[str], funding_amount) -> List[str]:
    """High level support categories derived from Meta Tags and funding info."""
    lower = "; ".join(tags).lower()
    cats: Set[str] = set()

    has_funding_text = any(
        k in lower
        for k in [
            "grant",
            "loan",
            "flexloan",
            "microloan",
            "micro-loan",
            "fund",
            "financing",
            "capital",
            "tax",
            "credit",
            "equity",
            "voucher",
            "rebate",
        ]
    )
    has_funding_amount = isinstance(funding_amount, str) and funding_amount.strip()

    if has_funding_text or has_funding_amount:
        cats.add("Funding and Financial Supports")

    if any(
        k in lower
        for k in ["advisory", "consulting", "coaching", "mentor", "mentorship"]
    ):
        cats.add("Advisory, Coaching, and Mentorship")

    if any(
        k in lower
        for k in [
            "training",
            "workshop",
            "workshops",
            "course",
            "bootcamp",
            "learning",
            "education",
        ]
    ):
        cats.add("Training and Workshops")

    if any(
        k in lower
        for k in ["networking", "community", "peer", "association", "event"]
    ):
        cats.add("Networking and Peer Support")

    if any(k in lower for k in ["accelerator", "incubator", "pre-accelerator", "cohort"]):
        cats.add("Accelerators, Incubators, and Cohorts")

    if any(k in lower for k in ["export", "market", "canexport", "international"]):
        cats.add("Export and Market Access")

    if any(k in lower for k in ["innovation", "r&d", "research", "technology", "ip"]):
        cats.add("Innovation, R&D, and Technology")

    if not cats:
        cats.add("General Business Supports")

    return sorted(cats)


def classify_audience(tags: List[str]) -> List[str]:
    lower = "; ".join(tags).lower()
    cats: Set[str] = set()

    if any(k in lower for k in ["women", "woman", "female", "women-owned"]):
        cats.add("Women and Women Led Businesses")
    if "indigenous" in lower or "first nation" in lower or "metis" in lower or "inuit" in lower:
        cats.add("Indigenous Entrepreneurs")
    if "youth" in lower or "student" in lower:
        cats.add("Youth and Students")
    if "newcomer" in lower or "immigrant" in lower or "refugee" in lower:
        cats.add("Newcomers and Immigrants")
    if "rural" in lower or "northern" in lower:
        cats.add("Rural and Northern Businesses")
    if "black" in lower:
        cats.add("Black Entrepreneurs")
    if "francophone" in lower:
        cats.add("Francophone Entrepreneurs")

    if not cats:
        cats.add("All Small Businesses")

    return sorted(cats)


def classify_stage(tags: List[str]) -> List[str]:
    """Business stage categories, derived from meta tags."""
    lower = "; ".join(tags).lower()
    cats: Set[str] = set()

    if any(k in lower for k in ["idea stage", "idea-stage", "pre-start", "pre start", "pre-startup", "prestartup"]):
        cats.add("Idea or Pre Startup")

    if any(k in lower for k in ["early stage", "start-up", "startup", "new business", "first three years", "0-3 years", "0 to 3 years"]):
        cats.add("Startup – Operating Less Than 3 Years")

    if any(k in lower for k in ["established", "mature", "3+ years", "three or more years", "5+ years"]):
        cats.add("Established – 3 or More Years in Business")

    if any(k in lower for k in ["scale up", "scale-up", "scaling", "growth stage", "expansion"]):
        cats.add("Growing or Scaling")

    if not cats:
        cats.add("Open to All Stages")

    return sorted(cats)


def classify_region(raw) -> List[str]:
    """Region categories for sidebar pills with GoA-friendly labels."""
    if not isinstance(raw, str):
        return ["Location Not Specified"]
    s = raw.lower().strip()
    cats: Set[str] = set()

    # Canada (including export & international)
    if "canada" in s:
        cats.add("Canada")

    # City-specific
    if "calgary" in s:
        cats.add("Calgary")
    if "edmonton" in s:
        cats.add("Edmonton")

    # Rural and Siksika
    is_rural = "rural" in s or "siksika" in s

    # Simple markers for north / central / south
    northern_markers = [
        "fort mcmurray",
        "fort mcmurray wood buffalo",
        "wood buffalo",
        "grand prairie",
        "grande prairie",
        "peace river",
        "high level",
        "slave lake",
        "northern",
    ]
    central_markers = [
        "red deer",
        "central",
        "rocky mountain house",
        "camrose",
        "wetaskiwin",
    ]
    southern_markers = [
        "lethbridge",
        "medicine hat",
        "brooks",
        "taber",
        "cardston",
        "southern",
        "siksika",
    ]

    if any(m in s for m in northern_markers):
        cats.add("Northern Alberta")
    if any(m in s for m in central_markers):
        cats.add("Central Alberta")
    if any(m in s for m in southern_markers):
        cats.add("Southern Alberta")

    if is_rural:
        cats.add("Rural Alberta")

    # Alberta-wide
    if s == "alberta" or "alberta-wide" in s:
        cats.add("Alberta-wide")

    # If nothing matched but Alberta is mentioned, default to Alberta-wide
    if not cats and "alberta" in s:
        cats.add("Alberta-wide")

    # Fallback to original text if absolutely nothing matched
    if not cats:
        cats.add(raw)

    return sorted(cats)


def derive_funding_types_from_tags(tags: List[str]) -> Set[str]:
    types: Set[str] = set()
    for tag in tags:
        t = tag.lower()
        if "grant" in t:
            types.add("Grant")
        if any(x in t for x in ["loan", "microloan", "micro-loan", "flexloan"]):
            types.add("Loan")
        if "tax credit" in t or (("tax" in t) and ("credit" in t)):
            types.add("Tax Credit")
        if "voucher" in t or "rebate" in t:
            types.add("Voucher or Rebate")
        if "equity" in t or "investment" in t:
            types.add("Equity or Investment")
        if "financing" in t and not types:
            types.add("Other Financing")
    return types


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

    # Derived funding bucket
    df["__funding_bucket"] = df[col_map["FUNDING"]].apply(funding_bucket)

    # Last checked metrics
    days_list, date_list = [], []
    for val in df[col_map["LAST_CHECKED"]].tolist():
        d, ds = days_since(val)
        days_list.append(d)
        date_list.append(ds or "")
    df["__fresh_days"] = days_list
    df["__fresh_date"] = date_list

    # Stable key
    if df[col_map["KEY"]].isna().any():
        df[col_map["KEY"]] = (
            df[col_map["PROGRAM_NAME"]]
            .fillna("")
            .astype(str)
            .str.slice(0, 80)
            + "-"
            + df.index.astype(str)
        )

    # Meta tags list
    df["__tags_list"] = df[col_map["META_TAGS"]].apply(parse_tags_field_clean)

    # High level support categories, audience, region, and stage
    df["__support_cats"] = [
        classify_support(tags, fa)
        for tags, fa in zip(df["__tags_list"], df[col_map["FUNDING"]])
    ]
    df["__audience_cats"] = df["__tags_list"].apply(classify_audience)
    df["__region_cats"] = df[col_map["REGION"]].apply(classify_region)
    df["__stage_cats"] = df["__tags_list"].apply(classify_stage)

    # Funding type set
    df["__fund_type_set"] = df["__tags_list"].apply(derive_funding_types_from_tags)

    return df, col_map


# ---------------------- SEARCH & FILTER LOGIC ----------------------


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
        COLS["ELIGIBILITY"],
    ]
    scores = []
    for col in fields:
        col_vals = df[col].fillna("").astype(str).str.lower().tolist()
        col_scores = [fuzz.partial_ratio(q, v) for v in col_vals]
        scores.append(col_scores)

    arr = np.array(scores)
    best = arr.max(axis=0)
    return pd.Series(best >= threshold, index=df.index)


def apply_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
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

    mask_support = multi_select_filter("filter_support", "__support_cats")
    mask_audience = multi_select_filter("filter_audience", "__audience_cats")
    mask_region = multi_select_filter("filter_region", "__region_cats")
    mask_stage = multi_select_filter("filter_stage", "__stage_cats")

    # Funding amount buckets
    funding_vals = st.session_state.get("filter_funding_bucket", [])
    if funding_vals:
        active_filters["filter_funding_bucket"] = funding_vals
        mask_funding = df["__funding_bucket"].isin(funding_vals)
    else:
        mask_funding = pd.Series(True, index=df.index)

    # Funding types (grants, loans, etc.)
    fund_type_vals = st.session_state.get("filter_funding_type", [])
    if fund_type_vals:
        active_filters["filter_funding_type"] = fund_type_vals

        def ftype(row):
            tags = row.get("__fund_type_set", set())
            return any(v in tags for v in fund_type_vals)

        mask_ftype = df.apply(ftype, axis=1)
    else:
        mask_ftype = pd.Series(True, index=df.index)

    overall = (
        mask
        & mask_support
        & mask_audience
        & mask_region
        & mask_stage
        & mask_funding
        & mask_ftype
    )
    return df[overall].copy(), active_filters


def clear_all_filters():
    for key in [
        "filter_support",
        "filter_funding_type",
        "filter_funding_bucket",
        "filter_audience",
        "filter_region",
        "filter_stage",
    ]:
        st.session_state[key] = []


def render_filter_pills(
    label: str,
    help_text: str,
    options: List[Tuple[str, str]],
    session_key: str,
):
    """Pill style filters that store clean values but display labels with counts."""
    with st.container():
        st.markdown(
            f"<div class='sidebar-section'><h3>{label}</h3><small>{help_text}</small></div>",
            unsafe_allow_html=True,
        )
        if session_key not in st.session_state:
            st.session_state[session_key] = []
        selected = set(st.session_state[session_key])

        # Single-column layout: each button on its own row
        for value, label_text in options:
            is_on = value in selected
            btn_label = label_text
            if st.button(btn_label, key=f"{session_key}_{value}"):
                if is_on:
                    selected.remove(value)
                else:
                    selected.add(value)
                st.session_state[session_key] = sorted(selected)
                st.rerun()

        if selected:
            if st.button("Clear", key=f"clear_{session_key}"):
                st.session_state[session_key] = []
                st.rerun()


def render_funding_type_pills(options: List[Tuple[str, str]]):
    # Sleeker helper text: short intro + small bullet list of definitions
    help_text = """
Choose the type of financial support that best fits what you need.
<ul style='margin-top:4px; padding-left:18px;'>
  <li><strong>Grant</strong> – non repayable funding.</li>
  <li><strong>Loan</strong> – repayable financing with interest.</li>
  <li><strong>Tax Credit</strong> – reduces taxes based on eligible expenses.</li>
  <li><strong>Voucher or Rebate</strong> – discounts or partial refunds.</li>
  <li><strong>Equity or Investment</strong> – capital in exchange for ownership.</li>
  <li><strong>Other Financing</strong> – other financial products.</li>
</ul>
"""
    render_filter_pills(
        label="What kind of funding are you looking for?",
        help_text=help_text,
        options=options,
        session_key="filter_funding_type",
    )


def render_chips(active_filters: Dict[str, List[str]]):
    if not active_filters:
        return

    flat: List[Tuple[str, str, str]] = []
    for key, vals in active_filters.items():
        for val in vals:
            if key == "filter_support":
                prefix = "Support:"
            elif key == "filter_funding_type":
                prefix = "Funding type:"
            elif key == "filter_funding_bucket":
                prefix = "Funding amount:"
            elif key == "filter_audience":
                prefix = "Audience:"
            elif key == "filter_region":
                prefix = "Region:"
            elif key == "filter_stage":
                prefix = "Stage:"
            else:
                prefix = ""
            label = f"{prefix} {val}" if prefix else val
            flat.append((key, val, label))

    if not flat:
        return

    st.markdown("<div class='chips-row'>", unsafe_allow_html=True)
    num_cols = min(4, len(flat))
    cols = st.columns(num_cols)

    for i, (key, val, label) in enumerate(flat):
        col = cols[i % num_cols]
        with col:
            if st.button(f"{label} ✕", key=f"chip_{key}_{val}"):
                cur = set(st.session_state.get(key, []))
                if val in cur:
                    cur.remove(val)
                    st.session_state[key] = sorted(cur)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------- MAIN APP ----------------------


def main():
    global COLS

    embed_css()
    embed_logo_html()

    data_path = "Pathfinding_Master.xlsx"
    df, col_map = load_data(data_path)
    COLS = col_map

    # Hero section
    st.markdown("## Find programs and supports for your Alberta business")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """1. **Choose filters**  
Pick your location, support type, audience, funding needs, and more."""
        )
    with col2:
        st.markdown(
            """2. **Browse matching programs**  
Scroll through cards that match your selections."""
        )
    with col3:
        st.markdown(
            """3. **Take action**  
Use the website, email, phone, and favourite options to connect or save programs."""
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

    # Build option lists with counts from the actual data
    support_counts = Counter()
    for cats in df["__support_cats"]:
        support_counts.update(cats)
    support_options = [
        (name, f"{name} ({support_counts[name]})")
        for name in sorted(support_counts.keys())
    ]

    audience_counts = Counter()
    for cats in df["__audience_cats"]:
        audience_counts.update(cats)
    audience_options = [
        (name, f"{name} ({audience_counts[name]})")
        for name in sorted(audience_counts.keys())
    ]

    region_counts = Counter()
    for cats in df["__region_cats"]:
        region_counts.update(cats)
    region_options = [
        (name, f"{name} ({region_counts[name]})")
        for name in sorted(region_counts.keys())
    ]

    stage_counts = Counter()
    for cats in df["__stage_cats"]:
        stage_counts.update(cats)
    stage_options = [
        (name, f"{name} ({stage_counts[name]})")
        for name in sorted(stage_counts.keys())
    ]

    bucket_counts = Counter(df["__funding_bucket"].tolist())
    funding_bucket_values = [
        "Under 5K",
        "5K to 25K",
        "25K to 100K",
        "100K to 500K",
        "Over 500K",
        UNKNOWN,
    ]
    funding_bucket_options = [
        (
            b,
            f"{add_dollar_signs(b) if b != UNKNOWN else 'Unknown / not stated'} ({bucket_counts.get(b, 0)})",
        )
        for b in funding_bucket_values
        if bucket_counts.get(b, 0) > 0
    ]

    fund_type_counts = Counter()
    for s in df["__fund_type_set"]:
        fund_type_counts.update(s)
    funding_type_values = [
        "Grant",
        "Loan",
        "Tax Credit",
        "Voucher or Rebate",
        "Equity or Investment",
        "Other Financing",
    ]
    funding_type_options = [
        (t, f"{t} ({fund_type_counts.get(t, 0)})")
        for t in funding_type_values
        if fund_type_counts.get(t, 0) > 0
    ]

    with st.sidebar:
        st.header("Filter programs")
        if st.button("Clear all filters"):
            clear_all_filters()
            st.rerun()

        # 1. Stage
        render_filter_pills(
            "Where is your business in its journey?",
            "Some programs are tailored to certain stages of business.",
            stage_options,
            "filter_stage",
        )

        # 2. Support type
        render_filter_pills(
            "What type of business support do you need?",
            "High level categories of support. You can select more than one.",
            support_options,
            "filter_support",
        )

        # 3. Location (left at the bottom of the stack of “core” filters)
        render_filter_pills(
            "Where is your business located?",
            "",
            region_options,
            "filter_region",
        )

        # 4. Funding type (with definitions)
        if funding_type_options:
            render_funding_type_pills(funding_type_options)

        # 5. Funding amount
        if funding_bucket_options:
            render_filter_pills(
                "How much funding are you looking for?",
                "These bands are based on the maximum funding available per program.",
                funding_bucket_options,
                "filter_funding_bucket",
            )

        # 6. Audience
        render_filter_pills(
            "Who is this support for?",
            "",
            audience_options,
            "filter_audience",
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
        name_col = COLS["PROGRAM_NAME"]
        filtered = filtered.sort_values(by=name_col, na_position="last")
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
        phone_raw_original = str(row.get(COLS["PHONE"]) or "").strip()

        # Phone handling: detect "not publicly listed" but allow a Call click to reveal that
        phone_note_hidden = False
        if "not publicly listed" in phone_raw_original.lower():
            phone_note_hidden = True
            phone_raw = ""
        else:
            phone_raw = phone_raw_original

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
            st.markdown(
                f"<div class='program-org'>{org}</div>", unsafe_allow_html=True
            )

        render_description(desc_full, key)

        # Funding amount display logic
        fund_raw = sanitize_text_keep_smart(
            str(row.get(COLS["FUNDING"]) or "").strip()
        )
        fund_label = ""
        if fund_raw and "$" in fund_raw:
            fund_label = fund_raw
        elif fund_bucket_val and fund_bucket_val.strip().lower() != UNKNOWN.lower():
            fund_label = add_dollar_signs(fund_bucket_val)

        fund_type_label = ""
        if isinstance(fund_type_set, set) and fund_type_set:
            fund_type_label = ", ".join(sorted(fund_type_set))

        if fund_label:
            fund_line = f'<span class="kv"><strong>Funding available:</strong> {fund_label}</span>'
        else:
            fund_line = ""

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
            meta_html = (
                '<p class="placeholder">Funding or eligibility details are not available in this view.</p>'
            )

        st.markdown(meta_html, unsafe_allow_html=True)

        # Actions row
        st.markdown("<div class='actions-row'>", unsafe_allow_html=True)
        cols_actions = st.columns(4)
        call_clicked = False
        fav_clicked = False

        with cols_actions[0]:
            if website:
                url = (
                    website
                    if website.startswith(("http://", "https://"))
                    else f"https://{website}"
                )
                st.markdown(f"[Website]({url})", unsafe_allow_html=True)

        with cols_actions[1]:
            email_label, email_href = parse_email_field(email_raw)
            # Only show Email when we actually have a clickable address
            if email_href:
                st.markdown(
                    f"[{email_label}]({email_href})", unsafe_allow_html=True
                )

        with cols_actions[2]:
            show_call_button = bool(phone_display_multi or phone_note_hidden)
            if show_call_button:
                call_clicked = st.button("Call", key=f"call_{key}")

        with cols_actions[3]:
            fav_on = key in st.session_state.favorites
            fav_label = "★ Favourite" if fav_on else "☆ Favourite"
            fav_clicked = st.button(fav_label, key=f"fav_{key}")

        st.markdown("</div>", unsafe_allow_html=True)

        # Call reveal: show numbers or "no phone number listed"
        if phone_display_multi or phone_note_hidden:
            call_state_key = f"show_call_{key}"
            if call_clicked:
                st.session_state[call_state_key] = not st.session_state.get(
                    call_state_key, False
                )
            if st.session_state.get(call_state_key, False):
                if phone_display_multi:
                    st.markdown(
                        f"<small class='pf-phone-line'><strong>Phone:</strong> {phone_display_multi}</small>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<small class='pf-phone-line'><strong>Phone:</strong> No phone number listed. Visit the program website for contact options.</small>",
                        unsafe_allow_html=True,
                    )

        if fav_clicked:
            if fav_on:
                st.session_state.favorites.remove(key)
            else:
                st.session_state.favorites.add(key)
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    close_shell()


if __name__ == "__main__":
    main()
