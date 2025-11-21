# app.py — Alberta Pathfinding Tool (Streamlit)
# Government of Alberta – Small Business Supports & Funding Repository

import re
import base64
import html
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# ---------------------------- Page ----------------------------
st.set_page_config(
    page_title="Small Business Supports Finder",
    layout="wide",
)

# ---------------------------- Styles ----------------------------
st.markdown(
    """
<style>
:root{
  --bg:#FFFFFF; --surface:#FFFFFF; --text:#0A0A0A; --muted:#4B5563;
  --primary:#003366; --primary-2:#007FA3; --border:#D9DEE7; --link:#007FA3;
  --fs-title:24px; --fs-body:15px; --fs-meta:13px;
}

/* Search input styling – make box more visible */
div[data-testid="stTextInput"] > div > div {
  border-radius: 999px;
  border: 2px solid #C3D0E6;
  background: #F3F4F6;
  padding: 4px 10px;
}

/* Remove default input border so only the outer pill shows */
div[data-testid="stTextInput"] input {
  border: none;
  background: transparent;
}

/* main spacing */
[data-testid="stAppViewContainer"] .main .block-container{
  padding-top:0 !important;
  max-width: 1100px;
}

/* base typography */
html, body, p, div, span{
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Segoe UI Emoji";
  color:var(--text);
}
p{ margin:4px 0 4px 0; }
small{ font-size:var(--fs-meta); }

/* Skip link (keyboard users) */
.skip-link {
  position:absolute; left:-9999px; top:auto; width:1px; height:1px; overflow:hidden;
}
.skip-link:focus {
  position:fixed; left:16px; top:12px; width:auto; height:auto; padding:8px 10px;
  background:#fff; color:#000; border:2px solid #feba35; border-radius:6px; z-index:10000;
}

/* Sticky header (GoA band) */
.header.goa-header{
  position:sticky; top:0; z-index:9999;
  display:flex; align-items:center; gap:14px;
  background:var(--primary); color:#fff;
  padding:10px 20px;
  border-radius:0; margin:0 -1.5rem 0 -1.5rem;
  border-bottom:2px solid #00294F;
  box-shadow:0 2px 8px rgba(0,0,0,.08);
}
.header.goa-header h2{
  margin:0;
  color:#fff;
  font-weight:800;
  font-size:26px;
  letter-spacing:.2px;
}
.header.goa-header p{
  margin:2px 0 0 0;
  color:#E6F2F8;
  font-size:14px;
}

/* Spacer so content never sits beneath header */
.header-spacer{ height:10px; }

/* Card marker + container styling */
.pf-card-marker{
  display:none;
}

/* Style card container based on marker */
div[data-testid="stVerticalBlock"]:has(.pf-card-marker){
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:16px;
  padding:12px 16px 12px 16px;
  box-shadow:0 1px 2px rgba(0,0,0,0.04);
  margin:8px 0 12px 0;
  transition:box-shadow .15s ease, border-color .15s ease, transform .15s ease;
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker):hover{
  box-shadow:0 4px 14px rgba(0,0,0,0.08);
  border-color:#C3D0E6;
  transform:translateY(-1px);
}

.title{
  margin:4px 0 2px 0;
  font-weight:800;
  color:var(--primary);
  font-size:var(--fs-title);
}
.org,.meta{
  color:var(--muted);
  font-size:var(--fs-meta);
}
.meta{ margin-left:8px; }
.placeholder{ color:#7C8796; font-style:italic; }

/* Status badges */
.badge{
  display:inline-block;
  font-size:12px;
  padding:3px 9px;
  border-radius:999px;
  margin-right:6px;
}
.badge.operational{
  background:#DFF3E6;
  color:#0B3D2E;
  border:1px solid #A6D9BE;
}
.badge.open{
  background:#E0EAFF;
  color:#062F6E;
  border:1px solid #B7CBFF;
}
.badge.closed{
  background:#FBE5E8;
  color:#6D1B26;
  border:1px solid #F2BAC1;
}

/* Funding + Eligibility strip */
.meta-info{
  display:flex;
  gap:16px;
  flex-wrap:wrap;
  margin:6px 0 0 0;
  padding:6px 0 0 0;
  border-top:none;
  border-bottom:none;
}
.kv strong{ font-weight:700; }

/* Actions row wrapper */
.actions-row{
  margin-top:6px;
}

/* Inline link-style anchors */
.actions-links{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
}
.actions-links a{
  color:var(--link);
  text-decoration:underline;
  font-size:var(--fs-body);
  transition:opacity .15s ease, text-decoration-color .15s ease;
}
.actions-links a:hover{
  opacity:.85;
  text-decoration:underline;
}
.actions-links a:focus{
  outline:3px solid #feba35;
  outline-offset:2px;
  border-radius:4px;
}

/* Ensure all links inside program cards share the same link colour */
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) a{
  color:var(--link) !important;
  text-decoration:underline;
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) a:hover{
  opacity:.85;
}

/* Make Call / Favourite buttons inside cards look like text links */
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button{
  background:none !important;
  border:none !important;
  padding:0;
  margin:0;
  color:var(--link) !important;
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
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button:focus{
  outline:3px solid #feba35;
  outline-offset:2px;
}

/* Make info buttons smaller */
button[aria-label="ℹ️"]{
  font-size:12px !important;
  padding:0 6px !important;
}

/* Global primary/secondary buttons */
button[kind="primary"]{
  background:var(--primary);
  color:#fff;
  border-radius:8px;
  border:1px solid #00294F;
}
button[kind="primary"]:hover{
  background:#00294F;
}
button[kind="secondary"]{
  background:#FFFFFF;
  color:var(--text);
  border-radius:8px;
  border:1px solid var(--border);
}

/* Pill-style sidebar filter buttons (full-width) */
section[data-testid="stSidebar"] div.stButton > button{
  border-radius:999px;
  width:100% !important;
  display:flex;
  justify-content:flex-start;
  margin-bottom:4px;
}

/* Sticky sidebar content (desktop-ish) */
section[data-testid="stSidebar"] > div{
  position:sticky;
  top:80px;
  max-height:calc(100vh - 96px);
  overflow-y:auto;
}

/* Download button styling */
div[data-testid="stDownloadButton"] > button{
  border-radius:8px;
  border:1px solid var(--border);
  background:#F3F4F6;
}

/* Pagination buttons spacing */
div[data-testid="stHorizontalBlock"] button{
  margin-top:4px;
}

/* Chip / active filter pills */
.chip-row-marker{
  display:none;
}

/* All buttons inside the chip row container become pill chips */
div[data-testid="stVerticalBlock"]:has(.chip-row-marker) button{
  border-radius:999px;
  border:1px solid #D1D5DB;
  background:#F9FAFB;
  font-size:13px;
  padding:4px 10px;
  margin:4px 6px 4px 0;
  cursor:pointer;
}
div[data-testid="stVerticalBlock"]:has(.chip-row-marker) button:hover{
  background:#E5E7EB;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------- Optional: inline GoA CSS if present ----------------------------
def inline_gov_css():
    for fname in (
        "goa-application-layouts.css",
        "goa-application-layout.print.css",
        "goa-components.css",
    ):
        p = Path(fname)
        if p.exists():
            try:
                st.markdown(
                    f"<style>{p.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True,
                )
            except Exception:
                pass


inline_gov_css()

# ---------------------------- Header / Logo ----------------------------
def embed_logo_html():
    """Embed GoA logo; prefers SVG, then PNG, else text fallback."""
    svg_path = Path("assets/GoA-logo.svg")
    png_path = Path("assets/GoA-logo.png")
    if svg_path.exists():
        b64 = base64.b64encode(svg_path.read_bytes()).decode()
        return (
            f'<img src="data:image/svg+xml;base64,{b64}" '
            f'alt="Government of Alberta" style="height:44px;">'
        )
    if png_path.exists():
        b64 = base64.b64encode(png_path.read_bytes()).decode()
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'alt="Government of Alberta" style="height:44px;">'
        )
    return '<div style="font-weight:700;font-size:18px">Government of Alberta</div>'


st.markdown(
    '<a class="skip-link" href="#results-main">Skip to results</a>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="header goa-header goa-app-header">
  {embed_logo_html()}
  <div>
    <h2>Small Business Supports Finder</h2>
    <p>Helping Alberta entrepreneurs and small businesses find programs, funding, and services quickly.</p>
  </div>
</div>
<div class="header-spacer"></div>
""",
    unsafe_allow_html=True,
)

# ---------------------------- Promise + How it works ----------------------------
st.markdown(
    """
### Find programs and supports for your Alberta business

This tool helps entrepreneurs and small businesses quickly find funding and business supports that match their stage, location,
and needs.
"""
)

st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

with st.container():
    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            "**1. Choose filters**  \n"
            "Pick your region, business stage, audience, funding type and the supports you're looking for."
        )
    with cols[1]:
        st.markdown(
            "**2. Browse matching programs**  \n"
            "Scroll through program cards that match your selections and compare options."
        )
    with cols[2]:
        st.markdown(
            "**3. Take action**  \n"
            "Use the Website, Email, Call and Favourite options to connect with programs or save them for later."
        )

st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

# ---------------------------- Data ----------------------------
DATA_FILE = st.secrets.get("DATA_FILE", "Pathfinding_Master.xlsx")
if not Path(DATA_FILE).exists():
    st.info("Upload **Pathfinding_Master.xlsx** to the project root and rerun.")
    st.stop()


@st.cache_data(show_spinner=False)
def load_df(path):
    df_loaded = pd.read_excel(path)
    df_loaded.columns = [str(c).strip() for c in df_loaded.columns]
    return df_loaded


df = load_df(DATA_FILE)


def map_col(df_in, name_hint: str, fallbacks: list[str]) -> str | None:
    for c in df_in.columns:
        if name_hint.lower() in str(c).lower():
            return c
    for fb in fallbacks:
        if fb in df_in.columns:
            return fb
    return None


COLS = {
    "PROGRAM_NAME": map_col(df, "program name", ["Program Name"]),
    "ORG_NAME": map_col(df, "organization name", ["Organization Name"]),
    "DESC": map_col(df, "program description", ["Program Description"]),
    "ELIG": map_col(df, "eligibility", ["Eligibility Description", "Eligibility"]),
    "EMAIL": map_col(df, "email", ["Email Address"]),
    "PHONE": map_col(df, "phone", ["Phone Number"]),
    "WEBSITE": map_col(df, "website", ["Program Website", "Website"]),
    "REGION": map_col(df, "region", ["Geographic Region", "Region"]),
    "TAGS": map_col(df, "meta", ["Meta Tags", "Tags"]),
    "FUNDING": map_col(df, "funding amount", ["Funding Amount", "Funding"]),
    "STATUS": map_col(df, "operational status", ["Operational Status", "Status"]),
    "LAST_CHECKED": map_col(df, "last checked", ["Last Checked (MT)", "Last Checked"]),
    "KEY": map_col(df, "_key_norm", ["_key_norm", "Key"]),
}

for k, v in COLS.items():
    if v is None or v not in df.columns:
        new_name = f"__missing_{k}"
        df[new_name] = ""
        COLS[k] = new_name

# ---------------------------- Text utilities ----------------------------
def fix_mojibake(s: str) -> str:
    if not isinstance(s, str):
        return ""
    repl = {
        "â€™": "’",
        "â€œ": "“",
        "â€\x9d": "”",
        "â€“": "–",
        "â€”": "—",
        "Â": "",
        "â€": "”",
        "â€˜": "‘",
        "â€\x94": "—",
        "�": "",
    }
    for bad, good in repl.items():
        s = s.replace(bad, good)
    return s


def sanitize_text_keep_smart(s: str) -> str:
    s = fix_mojibake(s or "")
    for b in ["•", "●", "○", "▪", "▫", "■", "□", "–·", "‣"]:
        s = s.replace(b, " ")
    s = re.sub(r"[\U0001F300-\U0001FAFF]", " ", s)
    s = re.sub(r"[\u2600-\u26FF]", " ", s)
    s = re.sub(r"[\u2700-\u27BF]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


URL_LIKE = re.compile(r"https?://|www\.|\.ca\b|\.com\b|\.org\b|\.net\b", re.I)
NUMERICY = re.compile(r"^\d{1,4}$")


def parse_tags_field_clean(s):
    if not isinstance(s, str):
        return []
    parts = re.split(r"[;,/|]", s)
    out = []
    for p in parts:
        t = (p or "").strip().lower()
        if not t:
            continue
        if URL_LIKE.search(t):
            continue
        if NUMERICY.match(t):
            continue
        out.append(t)
    return out


def add_dollar_signs(text: str) -> str:
    if not text:
        return text
    if "unknown" in text.lower():
        return text
    return re.sub(r"(?<!\$)(\d[\d,\.]*\s*[KkMm]?)", r"$\1", text)


def funding_bucket(amount):
    s = str(amount or "").replace(",", "")
    nums = re.findall(r"\d+\.?\d*", s)
    if not nums:
        return "Unknown / Not stated"
    try:
        val = float(nums[-1])
    except ValueError:
        return "Unknown / Not stated"
    if val < 5000:
        return "Under 5K"
    if val < 25000:
        return "5K–25K"
    if val < 100000:
        return "25K–100K"
    if val < 500000:
        return "100K–500K"
    return "500K+"


def days_since(date_str):
    try:
        d = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(d):
            return None, None
        delta = (pd.Timestamp.utcnow().normalize() - d.normalize()).days
        return delta, d.strftime("%Y-%m-%d")
    except Exception:
        return None, None


def normalize_phone(phone: str) -> tuple[str, str]:
    """
    Normalize a phone number to:
      - display looks like 403-555-1234
      - tel looks like +14035551234
    """
    if not phone:
        return "", ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):  # North America 1 + 10 digits
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


def render_description(desc_full: str, program_key: str, max_chars: int = 260):
    """Show description with Show more / Show less controls."""
    desc_full = desc_full or ""
    if not desc_full.strip():
        st.markdown(
            '<p><span class="placeholder">No description provided.</span></p>',
            unsafe_allow_html=True,
        )
        return

    if len(desc_full) <= max_chars:
        st.markdown(f"<p>{html.escape(desc_full)}</p>", unsafe_allow_html=True)
        return

    state_key = f"show_full_desc_{program_key}"
    show_full = st.session_state.get(state_key, False)

    if show_full:
        st.markdown(f"<p>{html.escape(desc_full)}</p>", unsafe_allow_html=True)
        if st.button("Show less", key=f"{state_key}_less"):
            st.session_state[state_key] = False
            st.rerun()
    else:
        short = desc_full[:max_chars]
        if " " in short:
            short = short.rsplit(" ", 1)[0]
        short = short + "..."
        st.markdown(f"<p>{html.escape(short)}</p>", unsafe_allow_html=True)
        if st.button("Show more", key=f"{state_key}_more"):
            st.session_state[state_key] = True
            st.rerun()

# ---------------------------- Normalization ----------------------------
ACTIVITY_NORMALIZATION_MAP = {
    "mentor": "Mentorship",
    "mentorship": "Mentorship",
    "mentoring": "Mentorship",
    "advis": "Advisory / Consulting",
    "advisory": "Advisory / Consulting",
    "advising": "Advisory / Consulting",
    "advice": "Advisory / Consulting",
    "coaching": "Coaching",
    "accelerator": "Accelerator / Incubator",
    "acceleration": "Accelerator / Incubator",
    "incubator": "Accelerator / Incubator",
    "innovation": "Innovation / R&D",
    "research": "Innovation / R&D",
    "r&d": "Innovation / R&D",
    "export": "Export Readiness",
    "network": "Networking / Peer Support",
    "networking": "Networking / Peer Support",
    "peer": "Networking / Peer Support",
    "workshop": "Workshops / Training",
    "workshops": "Workshops / Training",
    "training": "Workshops / Training",
    "cohort": "Cohort / Program Participation",
    "program": "Cohort / Program Participation",
}

STAGE_NORMALIZATION_MAP = {
    "startup": "Startup / Early Stage",
    "start-up": "Startup / Early Stage",
    "early": "Startup / Early Stage",
    "pre-revenue": "Startup / Early Stage",
    "pre revenue": "Startup / Early Stage",
    "ideation": "Startup / Early Stage",
    "prototype": "Startup / Early Stage",
    "preseed": "Startup / Early Stage",
    "pre-seed": "Startup / Early Stage",
    "seed": "Startup / Early Stage",
    "scaleup": "Growth / Scale",
    "scale-up": "Growth / Scale",
    "scale": "Growth / Scale",
    "growth": "Growth / Scale",
    "expand": "Growth / Scale",
    "expansion": "Growth / Scale",
    "commercializ": "Growth / Scale",
    "market-entry": "Growth / Scale",
    "market entry": "Growth / Scale",
    "mature": "Mature / Established",
    "established": "Mature / Established",
    "existing": "Mature / Established",
}

FUNDING_TYPE_MAP = {
    "grant": "Grant",
    "non-repayable": "Grant",
    "nonrepayable": "Grant",
    "contribution": "Grant",
    "rebate": "Rebate",
    "tax credit": "Tax Credit",
    "tax incentive": "Tax Credit",
    "tax deduction": "Tax Credit",
    "tax break": "Tax Credit",
    "tax credit": "Tax Credit",
    "loan": "Loan",
    "loans": "Loan",
    "microloan": "Loan",
    "micro loan": "Loan",
    "micro-loan": "Loan",
    "financing": "Financing",
    "finance": "Financing",
    "line of credit": "Credit",
    "credit": "Credit",
    "guarantee": "Financing",
    "guarantees": "Financing",
    "wage subsidy": "Subsidy",
    "wage grant": "Subsidy",
    "subsidy": "Subsidy",
    "subsidies": "Subsidy",
    "training subsidy": "Subsidy",
    "training grant": "Subsidy",
    "tuition grant": "Subsidy",
    "tuition subsidy": "Subsidy",
    "stipend": "Subsidy",
    "stipends": "Subsidy",
    "equity": "Equity Investment",
    "equity investment": "Equity Investment",
    "equity financing": "Equity Investment",
    "equity funding": "Equity Investment",
    "equity finance": "Equity Investment",
    "equity-capital": "Equity Investment",
    "equity capital": "Equity Investment",
    "seed funding": "Equity Investment",
    "seed investing": "Equity Investment",
    "seed investment": "Equity Investment",
    "equity-based": "Equity Investment",
    "equity based": "Equity Investment",
    "equity stake": "Equity Investment",
    "invest": "Equity Investment",
    "investment": "Equity Investment",
    "investor": "Equity Investment",
    "angel investment": "Equity Investment",
    "angel investing": "Equity Investment",
    "angel investors": "Equity Investment",
    "angel investor": "Equity Investment",
    "venture capital": "Equity Investment",
    "vc": "Equity Investment",
    "angel": "Equity Investment",
    "co-invest": "Equity Investment",
    "co invest": "Equity Investment",
}

FUNDING_TYPE_DESCRIPTIONS = {
    "Grant": "Non-repayable funding that supports eligible activities when program conditions are met.",
    "Loan": "Funding that must be repaid, usually with interest and defined repayment terms.",
    "Financing": "Access to capital such as facilities or blended products that may combine different tools.",
    "Subsidy": "Support that offsets specific costs, for example wages, training, or program fees.",
    "Tax Credit": "A credit that reduces taxes payable based on eligible spending or investment.",
    "Rebate": "Funding paid after you incur eligible costs and submit proof of spending.",
    "Credit": "A revolving credit limit or line of credit that you can draw from as needed.",
    "Equity Investment": "Investment where the funder receives an ownership stake in the business.",
}

AUDIENCE_NORMALIZATION_MAP = {
    "women": "Women",
    "woman": "Women",
    "female": "Women",
    "indigenous": "Indigenous",
    "first nation": "Indigenous",
    "first nations": "Indigenous",
    "aboriginal": "Indigenous",
    "metis": "Indigenous",
    "inuit": "Indigenous",
    "black": "Black entrepreneurs",
    "afro": "Black entrepreneurs",
    "immigrant": "Immigrants / Newcomers",
    "newcomer": "Immigrants / Newcomers",
    "refugee": "Immigrants / Newcomers",
    "youth": "Youth",
    "student": "Students",
    "rural": "Rural",
    "veteran": "Veterans",
    "disabil": "Persons with disabilities",
    "lgbt": "2SLGBTQ+",
    "2slgbt": "2SLGBTQ+",
    "queer": "2SLGBTQ+",
    "tech": "Technology / Digital",
    "technology": "Technology / Digital",
    "digital": "Technology / Digital",
    "ict": "Technology / Digital",
    "software": "Technology / Digital",
    "saas": "Technology / Digital",
    "tourism": "Tourism & Hospitality",
    "hospitality": "Tourism & Hospitality",
    "hotel": "Tourism & Hospitality",
    "visitor": "Tourism & Hospitality",
    "agri": "Agriculture & Agri-food",
    "agriculture": "Agriculture & Agri-food",
    "farm": "Agriculture & Agri-food",
    "farmer": "Agriculture & Agri-food",
    "agri-food": "Agriculture & Agri-food",
    "agri food": "Agriculture & Agri-food",
    "energy": "Energy",
    "oil": "Energy",
    "gas": "Energy",
    "oilsands": "Energy",
    "oil sands": "Energy",
    "petro": "Energy",
    "cleantech": "Clean Technology",
    "clean tech": "Clean Technology",
    "net-zero": "Clean Technology",
    "net zero": "Clean Technology",
    "low-carbon": "Clean Technology",
    "low carbon": "Clean Technology",
    "manufactur": "Manufacturing",
    "industrial": "Manufacturing",
    "film": "Creative Industries",
    "screen": "Creative Industries",
    "tv": "Creative Industries",
    "television": "Creative Industries",
    "creative": "Creative Industries",
    "culture": "Creative Industries",
    "arts": "Creative Industries",
}


def normalize_activity_tag(tag: str) -> str:
    t = (tag or "").strip().lower()
    for needle, canon in ACTIVITY_NORMALIZATION_MAP.items():
        if needle in t:
            return canon
    return ""


def normalize_stage_tag(tag: str) -> str:
    t = (tag or "").strip().lower()
    for needle, canon in STAGE_NORMALIZATION_MAP.items():
        if needle in t:
            return canon
    return ""


def normalize_audience_tag(tag: str) -> str:
    t = (tag or "").strip().lower()
    for needle, canon in AUDIENCE_NORMALIZATION_MAP.items():
        if needle in t:
            return canon
    return ""


def detect_funding_types_from_tags(s: str) -> set[str]:
    tags = parse_tags_field_clean(s)
    hits: set[str] = set()
    for t in tags:
        tl = t.lower()
        for needle, canon in FUNDING_TYPE_MAP.items():
            if needle in tl:
                hits.add(canon)
    return hits


def row_activity_norm_set(raw_tag_field: str) -> set[str]:
    return {
        normalize_activity_tag(rt)
        for rt in parse_tags_field_clean(raw_tag_field)
        if normalize_activity_tag(rt)
    }


def row_stage_norm_set(raw_tag_field: str) -> set[str]:
    return {
        normalize_stage_tag(rt)
        for rt in parse_tags_field_clean(raw_tag_field)
        if normalize_stage_tag(rt)
    }


def row_audience_norm_set(raw_tag_field: str) -> set[str]:
    return {
        normalize_audience_tag(rt)
        for rt in parse_tags_field_clean(raw_tag_field)
        if normalize_audience_tag(rt)
    }


def calc_stages(row):
    raw = str(row.get(COLS["TAGS"], "") or "")
    return row_stage_norm_set(raw)


def calc_audiences(row):
    raw = str(row.get(COLS["TAGS"], "") or "")
    return row_audience_norm_set(raw)


def calc_activities(row):
    raw = str(row.get(COLS["TAGS"], "") or "")
    return row_activity_norm_set(raw)


def calc_funding_bucket(row):
    raw = str(row.get(COLS["FUNDING"], "") or "")
    return funding_bucket(raw)


def calc_funding_type(row):
    raw_tags = str(row.get(COLS["TAGS"], "") or "")
    raw_name = str(row.get(COLS["PROGRAM_NAME"], "") or "")
    raw_desc = str(row.get(COLS["DESC"], "") or "")
    tags_hits = detect_funding_types_from_tags(raw_tags)
    name_hits = detect_funding_types_from_tags(raw_name)
    desc_hits = detect_funding_types_from_tags(raw_desc)
    hits = tags_hits.union(name_hits).union(desc_hits)
    return hits if hits else {UNKNOWN}


def freshness(row):
    days, formatted_date = days_since(row.get(COLS["LAST_CHECKED"], ""))
    return days, formatted_date


df["__activities"] = df.apply(calc_activities, axis=1)
df["__stages"] = df.apply(calc_stages, axis=1)
df["__audiences"] = df.apply(calc_audiences, axis=1)
df["__funding_bucket"] = df.apply(calc_funding_bucket, axis=1)
df["__fund_type_set"] = df.apply(calc_funding_type, axis=1)
df["__fresh_days"], df["__fresh_date"] = zip(*df.apply(freshness, axis=1))

# ---------------------------- Search / Filters ----------------------------
REGION_OPTIONS = sorted(
    {r for r in df[COLS["REGION"]].dropna().astype(str).unique() if r.strip()}
)
ACTIVITY_OPTIONS = sorted(
    {
        v
        for tags_set in df["__activities"]
        for v in tags_set
        if v and v != UNKNOWN
    }
)
STAGE_OPTIONS = sorted(
    {v for tags_set in df["__stages"] for v in tags_set if v and v != UNKNOWN}
)
AUDIENCE_OPTIONS = sorted(
    {v for tags_set in df["__audiences"] for v in tags_set if v and v != UNKNOWN}
)
FUNDING_BUCKET_OPTIONS = [
    "Under 5K",
    "5K–25K",
    "25K–100K",
    "100K–500K",
    "500K+",
    "Unknown / Not stated",
]
FUNDING_TYPE_OPTIONS = sorted(
    {v for tags_set in df["__fund_type_set"] for v in tags_set if v}
)

UNKNOWN = "Unknown / Not stated"

# Audience tips popover text
AUDIENCE_TIPS = """
- Choose one or more audiences to see programs that explicitly serve those groups.
- If no audience is selected, results will include general programs open to all.
"""

# ---------------------------- Helpers ----------------------------
def ensure_session_state():
    defaults = {
        "query": "",
        "region": [],
        "activity": [],
        "stage": [],
        "audience": [],
        "funding_bucket": [],
        "funding_type": [],
        "favorites": set(),
        "page_idx": 0,
        "show_filters": False,
        "include_unknown_funding": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_pagination():
    st.session_state.page_idx = 0


def toggle_filters():
    st.session_state.show_filters = not st.session_state.show_filters


ensure_session_state()

# ---------------------------- Sidebar (filters) ----------------------------
with st.sidebar:
    st.subheader("Filters")
    st.button(
        "Toggle filters",
        key="toggle_filters",
        on_click=toggle_filters,
        help="Show or hide filter controls",
    )

    if st.session_state.show_filters:
        st.markdown("### Region")
        region = st.multiselect(
            "Select region(s)",
            options=REGION_OPTIONS,
            default=st.session_state.region,
            help="Choose one or more geographic regions",
            on_change=reset_pagination,
        )
        st.session_state.region = region

        st.markdown("### Funding type")
        funding_type = st.multiselect(
            "Select funding type(s)",
            options=FUNDING_TYPE_OPTIONS,
            default=st.session_state.funding_type,
            on_change=reset_pagination,
        )
        st.session_state.funding_type = funding_type

        st.markdown("### Funding amount")
        funding_bucket = st.multiselect(
            "Select funding amount",
            options=FUNDING_BUCKET_OPTIONS,
            default=st.session_state.funding_bucket,
            on_change=reset_pagination,
        )
        st.session_state.funding_bucket = funding_bucket

        st.markdown("### Business stage")
        stage = st.multiselect(
            "Select stage(s)",
            options=STAGE_OPTIONS,
            default=st.session_state.stage,
            on_change=reset_pagination,
        )
        st.session_state.stage = stage

        st.markdown("### Activity / support type")
        activity = st.multiselect(
            "Select activities",
            options=ACTIVITY_OPTIONS,
            default=st.session_state.activity,
            on_change=reset_pagination,
        )
        st.session_state.activity = activity

        st.markdown("### Target audiences")
        with st.expander("Who is this program for? (Optional)"):
            st.info(AUDIENCE_TIPS.strip())
            audience = st.multiselect(
                "Select audiences",
                options=AUDIENCE_OPTIONS,
                default=st.session_state.audience,
                on_change=reset_pagination,
            )
            st.session_state.audience = audience

        st.checkbox(
            "Include programs where funding amount is unknown / not stated",
            value=st.session_state.include_unknown_funding,
            key="include_unknown_funding",
            on_change=reset_pagination,
        )

        st.markdown("### Favorites")
        st.caption("View programs you've starred (☆/★).")
        if st.button("Show only favorites", key="filter_favorites"):
            st.session_state.favorites_only = True
            st.rerun()

# ---------------------------- Search input ----------------------------
search_query = st.text_input(
    "Search programs",
    value=st.session_state.query,
    placeholder="Search by keyword, topic, organization, or program name",
)
if search_query != st.session_state.query:
    st.session_state.query = search_query
    reset_pagination()

# ---------------------------- Filter logic ----------------------------
def text_match_score(row, query):
    if not query:
        return 0
    haystack = " ".join(
        [
            str(row.get(COLS["PROGRAM_NAME"], "")),
            str(row.get(COLS["DESC"], "")),
            str(row.get(COLS["ORG_NAME"], "")),
            str(row.get(COLS["TAGS"], "")),
            str(row.get(COLS["ELIG"], "")),
        ]
    )
    return fuzz.token_set_ratio(query.lower(), haystack.lower())


def filter_df(df_in, query):
    df_work = df_in.copy()

    def matches_filters(row):
        # Region
        if st.session_state.region:
            if row.get(COLS["REGION"], "") not in st.session_state.region:
                return False

        # Funding type
        if st.session_state.funding_type:
            if not (
                row.get("__fund_type_set", set()) & set(st.session_state.funding_type)
            ):
                return False

        # Funding bucket
        if st.session_state.funding_bucket:
            bucket = row.get("__funding_bucket", UNKNOWN)
            if bucket not in st.session_state.funding_bucket:
                return False

        # Activity
        if st.session_state.activity:
            if not (row.get("__activities", set()) & set(st.session_state.activity)):
                return False

        # Stage
        if st.session_state.stage:
            if not (row.get("__stages", set()) & set(st.session_state.stage)):
                return False

        # Audience
        if st.session_state.audience:
            if not (row.get("__audiences", set()) & set(st.session_state.audience)):
                return False

        # Include unknown funding?
        if not st.session_state.include_unknown_funding:
            bucket = row.get("__funding_bucket", UNKNOWN)
            if bucket == UNKNOWN:
                return False

        return True

    df_work["__matches_filters"] = df_work.apply(matches_filters, axis=1)

    # Favorites filter
    if st.session_state.get("favorites_only"):
        df_work = df_work[df_work.get(COLS["KEY"]).isin(st.session_state.favorites)]

    if query:
        df_work["__text_score"] = df_work.apply(text_match_score, axis=1, query=query)
        df_work = df_work[df_work["__text_score"] > 0]
        df_work = df_work.sort_values(
            "__text_score", ascending=False
        )  # Highest score first
    else:
        df_work["__text_score"] = 0

    df_filtered = df_work[df_work["__matches_filters"]]

    return df_filtered.drop(columns=["__matches_filters"])


filtered_df = filter_df(df, search_query)

# ---------------------------- Results / Pagination ----------------------------
PAGE_SIZE = 12
total = len(filtered_df)
max_page = (total - 1) // PAGE_SIZE if total else 0
page = st.session_state.page_idx
page = max(0, min(page, max_page))
st.session_state.page_idx = page

start = page * PAGE_SIZE
end = start + PAGE_SIZE

with st.container():
    st.markdown("<div class='chip-row-marker'></div>", unsafe_allow_html=True)
    st.markdown("### Active filters")
    active_filters = []

    if search_query:
        active_filters.append(f"Search: \"{search_query}\"")
    if st.session_state.region:
        active_filters.extend(st.session_state.region)
    if st.session_state.funding_type:
        active_filters.extend(st.session_state.funding_type)
    if st.session_state.funding_bucket:
        active_filters.extend(st.session_state.funding_bucket)
    if st.session_state.activity:
        active_filters.extend(st.session_state.activity)
    if st.session_state.stage:
        active_filters.extend(st.session_state.stage)
    if st.session_state.audience:
        active_filters.extend(st.session_state.audience)
    if st.session_state.include_unknown_funding:
        active_filters.append("Include unknown funding")

    if st.session_state.get("favorites_only"):
        active_filters.append("Favorites only")

    cols_chips = st.columns(3)
    with cols_chips[0]:
        st.button("Clear all filters", on_click=reset_pagination, key="clear_filters")
    with cols_chips[1]:
        st.button("Show favorites", key="show_favorites", on_click=lambda: st.session_state.setdefault("favorites_only", True) or st.rerun())
    with cols_chips[2]:
        st.button("Show all programs", key="show_all", on_click=lambda: st.session_state.pop("favorites_only", None) or st.rerun())

    if active_filters:
        st.write(", ".join(active_filters))
    else:
        st.write("No active filters.")

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    st.write(f"Showing {start + 1}–{min(end, total)} of {total} programs")

    # Pagination controls
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("Previous", disabled=page <= 0):
            st.session_state.page_idx = max(0, page - 1)
            st.rerun()
    with col_page:
        st.write(f"Page {page + 1} of {max_page + 1}")
    with col_next:
        if st.button("Next", disabled=page >= max_page):
            st.session_state.page_idx = min(max_page, page + 1)
            st.rerun()

st.markdown(
    '<div id="results-main" role="main" class="goa-searchresults"></div>',
    unsafe_allow_html=True,
)

if total == 0:
    st.info(
        "No programs match your current filters. Try clearing filters or broadening your search."
    )
else:
    subset = filtered_df.iloc[start:end].copy()
    for i, (_, row) in enumerate(subset.iterrows(), 1):
        name = str(row[COLS["PROGRAM_NAME"]] or "")
        org = str(row[COLS["ORG_NAME"]] or "")
        status_raw = str(row[COLS["STATUS"]] or "")
        s_low = (status_raw or "").lower()

        badge_cls = (
            "operational"
            if "operational" in s_low
            else (
                "open"
                if any(
                    k in s_low
                    for k in ["open", "active", "ongoing", "accepting", "rolling"]
                )
                else "closed"
            )
        )
        badge_label = status_raw or (
            "Operational"
            if badge_cls == "operational"
            else ("Open" if badge_cls == "open" else "Closed / Paused")
        )
        badge_label_safe = html.escape(badge_label)

        name_safe = html.escape(name)
        org_safe = html.escape(org)

        # Description (strip placeholder text)
        raw_desc = str(row[COLS["DESC"]] or "").strip()
        if (
            raw_desc.strip().lower()
            == "description pending verification from program website."
        ):
            raw_desc = ""
        desc_full = sanitize_text_keep_smart(raw_desc)

        elig = sanitize_text_keep_smart(str(row[COLS["ELIG"]] or "").strip())
        fund_bucket_val = str(row.get("__funding_bucket") or "")
        fund_type_set = row.get("__fund_type_set", set())
        fresh_days = row.get("__fresh_days")
        fresh_date = str(row.get("__fresh_date") or "")
        fresh_label = freshness_label(fresh_days)

        website = str(row.get(COLS["WEBSITE"]) or "").strip()
        email = str(row.get(COLS["EMAIL"]) or "").strip().lower()
        phone_raw = str(row.get(COLS["PHONE"]) or "").strip()

        # Hide call when phone is missing or "not publicly listed – use contact page"
        if (
            "not publicly listed" in phone_raw.lower()
            and "contact page" in phone_raw.lower()
        ):
            phone_raw = ""

        phone_display_multi = format_phone_multi(phone_raw)
        key = str(row.get(COLS["KEY"], f"k{i}"))

        with st.container():
            st.markdown("<div class='pf-card-marker'></div>", unsafe_allow_html=True)

            # Header: badge + freshness + title + org
            st.markdown(
                f"""
                <span class='badge {badge_cls}'>{badge_label_safe}</span>
                <span class='meta'>Last checked: {html.escape(fresh_date) if fresh_date else '—'}
                {f"({html.escape(fresh_label)})" if fresh_label != "—" else ""}</span>
                <div class='title'>{name_safe}</div>
                <div class='org'>{org_safe}</div>
                """,
                unsafe_allow_html=True,
            )

            # Description with Show more / Show less
            render_description(desc_full, key)

            # Funding + Eligibility strip
            fund_label = ""
            if fund_bucket_val and fund_bucket_val.strip().lower() != UNKNOWN:
                fund_label = add_dollar_signs(fund_bucket_val)

            fund_type_label = ""
            if isinstance(fund_type_set, set) and fund_type_set:
                fund_type_label = ", ".join(sorted(fund_type_set))

            fund_line = (
                f'<span class="kv"><strong>Funding available:</strong> {html.escape(fund_label)}</span>'
                if fund_label
                else ""
            )
            fund_type_line = (
                f'<span class="kv"><strong>Funding type:</strong> {html.escape(fund_type_label)}</span>'
                if fund_type_label
                else ""
            )

            elig_line = (
                f'<span class="kv"><strong>Eligibility highlights:</strong> {html.escape(elig)}</span>'
                if (
                    elig
                    and elig.strip().lower()
                    not in {"", "unknown / not stated", "n/a", "na"}
                )
                else ""
            )

            meta_html_parts = [x for x in [fund_line, fund_type_line, elig_line] if x]
            meta_html = (
                " ".join(meta_html_parts)
                or "<span class='placeholder'>No additional details</span>"
            )

            st.markdown(
                f"<div class='meta-info'>{meta_html}</div>",
                unsafe_allow_html=True,
            )

            # Actions row: Website · Email · Call · ☆/★ Favourite (all text-link style)
            st.markdown("<div class='actions-row'>", unsafe_allow_html=True)

            cols_actions = st.columns(4)
            call_clicked = False
            fav_clicked = False

            # Website
            with cols_actions[0]:
                if website:
                    url = (
                        website
                        if website.startswith(("http://", "https://"))
                        else f"https://{website}"
                    )
                    st.markdown(f"[Website]({url})", unsafe_allow_html=False)

            # Email
            with cols_actions[1]:
                if email:
                    st.markdown(f"[Email](mailto:{email})", unsafe_allow_html=False)

            # Call (toggle numbers)
            with cols_actions[2]:
                if phone_display_multi:
                    call_clicked = st.button("Call", key=f"call_{key}")

            # Favourite
            with cols_actions[3]:
                fav_on = key in st.session_state.favorites
                fav_label = "★ Favourite" if fav_on else "☆ Favourite"
                fav_clicked = st.button(fav_label, key=f"fav_{key}")

            st.markdown("</div>", unsafe_allow_html=True)

            # Toggle phone number display
            if phone_display_multi:
                call_state_key = f"show_call_{key}"
                if call_clicked:
                    st.session_state[call_state_key] = not st.session_state.get(
                        call_state_key, False
                    )
                if st.session_state.get(call_state_key, False):
                    st.markdown(
                        f"<small><strong>Call:</strong> {html.escape(phone_display_multi)}</small>",
                        unsafe_allow_html=True,
                    )

            # Toggle favourites
            if fav_clicked:
                if fav_on:
                    st.session_state.favorites.remove(key)
                else:
                    st.session_state.favorites.add(key)
                st.rerun()
