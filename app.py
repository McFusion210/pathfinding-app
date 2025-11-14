# app.py — Alberta Pathfinding Tool (Streamlit)
# Government of Alberta – Small Business Supports & Funding Repository

import re
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# ---------------------------- Page ----------------------------
st.set_page_config(
    page_title="Alberta Pathfinding Tool – Small Business Supports",
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
  padding:14px 20px; border-radius:0; margin:0 -1.5rem 0 -1.5rem;
  border-bottom:2px solid #00294F;
  box-shadow:0 2px 8px rgba(0,0,0,.08);
}
.header.goa-header h2{
  margin:0;
  color:#fff;
  font-weight:800;
  font-size:28px;
  letter-spacing:.2px;
}
.header.goa-header p{
  margin:2px 0 0 0;
  color:#E6F2F8;
  font-size:15px;
}

/* Spacer so content never sits beneath header */
.header-spacer{ height:12px; }

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

/* Make secondary buttons (Call / Favourite / chips) look like text links */
button[data-testid="baseButton-secondary"]{
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
button[data-testid="baseButton-secondary"]:hover{
  opacity:.85;
  text-decoration:underline;
}
button[data-testid="baseButton-secondary"]:focus{
  outline:3px solid #feba35;
  outline-offset:2px;
}

/* Keep primary buttons (filters, pagination) slightly rounded */
button[kind="primary"]{ border-radius:8px; }
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
            f'alt="Government of Alberta" style="height:48px;">'
        )
    if png_path.exists():
        b64 = base64.b64encode(png_path.read_bytes()).decode()
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'alt="Government of Alberta" style="height:48px;">'
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
    <h2>Alberta Pathfinding Tool</h2>
    <p>Small Business Supports &amp; Funding Repository</p>
  </div>
</div>
<div class="header-spacer"></div>
""",
    unsafe_allow_html=True,
)

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


def freshness_label(days):
    if days is None:
        return "—"
    if days <= 30:
        return f"{days}d ago"
    if days <= 180:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


# Phone helpers
def normalize_phone(phone: str):
    """Return (display, tel) where display is XXX-XXX-XXXX and tel is +1XXXXXXXXXX."""
    if not phone:
        return "", ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        country = "1"
        digits = digits[1:]
    elif len(digits) == 10:
        country = "1"
    else:
        # Fallback: show original, use raw digits for tel if present
        return phone, (digits or phone)
    display = f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    tel = f"+{country}{digits}"
    return display, tel


def format_phone_multi(phone: str) -> str:
    """
    Split multiple phone numbers and format them as 'xxx-xxx-xxxx | yyy-yyy-yyyy'.
    Falls back to the original chunk if normalize_phone can't format it.
    """
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

# Funding types
FUNDING_TYPE_MAP = {
    "grant": "Grant",
    "non-repayable": "Grant",
    "nonrepayable": "Grant",
    "contribution": "Grant",
    "loan": "Loan",
    "microloan": "Loan",
    "micro loan": "Loan",
    "financ": "Financing",
    "capital": "Financing",
    "facility": "Financing",
    "subsid": "Subsidy",
    "wage subsidy": "Subsidy",
    "salary subsidy": "Subsidy",
    "tax credit": "Tax Credit",
    "taxcredit": "Tax Credit",
    "rebate": "Rebate",
    "cash rebate": "Rebate",
    "credit": "Credit",
    "line of credit": "Credit",
    "equity": "Equity Investment",
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
    # Demographic / group audiences
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
    # Industry / sector audiences
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


# ---------------------------- Derived columns ----------------------------
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
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "", regex=True)
        + "|"
        + df[COLS["ORG_NAME"]]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "", regex=True)
    )

df["__activity_norm_set"] = (
    df[COLS["TAGS"]].fillna("").astype(str).apply(row_activity_norm_set)
)
df["__stage_norm_set"] = (
    df[COLS["TAGS"]].fillna("").astype(str).apply(row_stage_norm_set)
)
df["__fund_type_set"] = (
    df[COLS["TAGS"]].fillna("").astype(str).apply(detect_funding_types_from_tags)
)
df["__audience_norm_set"] = (
    df[COLS["TAGS"]].fillna("").astype(str).apply(row_audience_norm_set)
)

STAGE_CANON_CHOICES = [
    "Startup / Early Stage",
    "Growth / Scale",
    "Mature / Established",
]

# ---------------------------- Sidebar filters ----------------------------
st.sidebar.header("Filters")
st.sidebar.caption(
    "Use these filters to narrow down programs by funding, audience, stage, business supports and region."
)

REGION_CHOICES = ["Calgary", "Edmonton", "Rural Alberta", "Canada"]
FUNDING_TYPE_CHOICES = [
    "Grant",
    "Loan",
    "Financing",
    "Subsidy",
    "Tax Credit",
    "Rebate",
    "Credit",
    "Equity Investment",
]
FUND_AMOUNT_CHOICES = [
    "Under 5K",
    "5K–25K",
    "25K–100K",
    "100K–500K",
    "500K+",
    "Unknown / Not stated",
]

FUZZY_THR = 70

sort_mode = st.sidebar.selectbox(
    "Sort results by",
    ["Relevance", "Program Name (A–Z)", "Last Checked (newest)"],
    index=0,
    help="Relevance uses fuzzy keyword matching across program name, description and tags.",
)
page_size = st.sidebar.selectbox(
    "Results per page",
    [10, 25, 50],
    index=1,
    help="Change how many programs appear on each page of results.",
)

REGION_MATCH_TABLE = {
    "Calgary": ["calgary", "southern alberta", "foothills"],
    "Edmonton": ["edmonton", "capital region", "central alberta"],
    "Rural Alberta": [
        "rural",
        "north",
        "northern alberta",
        "east central",
        "south",
        "southern alberta",
        "central alberta",
        "mountain view",
        "parkland",
    ],
    "Canada": ["canada", "national", "federal", "pan-canadian", "international"],
}


def region_match(region_value: str, selected: str) -> bool:
    if not selected or selected == "All Regions":
        return True
    if not isinstance(region_value, str):
        return False
    v = region_value.lower()
    return any(word in v for word in REGION_MATCH_TABLE.get(selected, []))


def count_by_option(series_of_sets: pd.Series):
    freq: dict[str, int] = {}
    for S in series_of_sets:
        for v in S:
            freq[v] = freq.get(v, 0) + 1
    return freq


def fuzzy_mask(df_in, q_text, threshold=70):
    if not q_text:
        return pd.Series([True] * len(df_in), index=df_in.index)
    cols = [
        COLS["PROGRAM_NAME"],
        COLS["ORG_NAME"],
        COLS["DESC"],
        COLS["ELIG"],
        COLS["TAGS"],
    ]
    blobs = df_in[cols].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return blobs.apply(lambda blob: fuzz.partial_ratio(q_text.lower(), blob) >= threshold)


def filtered_except(
    df_in,
    q_text,
    selected_regions,
    selected_ftypes,
    selected_famts,
    selected_stage,
    selected_activity,
    selected_audience,
    *,
    except_dim,
):
    out = df_in.copy()
    if q_text:
        out = out[fuzzy_mask(out, q_text, threshold=FUZZY_THR)]
    if except_dim != "region" and selected_regions:
        col = out[COLS["REGION"]].astype(str)
        out = out[col.apply(lambda v: any(region_match(v, r) for r in selected_regions))]
    if except_dim != "famt" and selected_famts:
        out = out[out["__funding_bucket"].isin(selected_famts)]
    if except_dim != "ftype" and selected_ftypes:
        out = out[out["__fund_type_set"].apply(lambda s: bool(s & selected_ftypes))]
    if except_dim != "stage" and selected_stage:
        out = out[out["__stage_norm_set"].apply(lambda s: bool(s & selected_stage))]
    if except_dim != "activity" and selected_activity:
        out = out[out["__activity_norm_set"].apply(lambda s: bool(s & selected_activity))]
    if except_dim != "audience" and selected_audience:
        out = out[out["__audience_norm_set"].apply(lambda s: bool(s & selected_audience))]
    return out


# ---------------------------- Search & gather ----------------------------
q = st.text_input(
    "🔍 Search programs",
    "",
    key="q",
    placeholder="Try 'grant', 'mentorship', or 'startup'…",
)
st.caption(
    "Tip: Search matches similar terms (e.g., typing **mentor** finds **mentorship**)."
)

all_activity_norm = sorted({v for S in df["__activity_norm_set"] for v in S})
raw_stage_norm = {v for S in df["__stage_norm_set"] for v in S}
all_stage_norm = sorted(raw_stage_norm)
stage_options = sorted(set(all_stage_norm) | set(STAGE_CANON_CHOICES))
all_audience_norm = sorted({v for S in df["__audience_norm_set"] for v in S})

selected_regions = {
    opt for opt in REGION_CHOICES if st.session_state.get(f"region_{opt}")
}
selected_ftypes = {
    opt for opt in FUNDING_TYPE_CHOICES if st.session_state.get(f"ftype_{opt}")
}
selected_famts = {
    opt for opt in FUND_AMOUNT_CHOICES if st.session_state.get(f"famt_{opt}")
}
selected_stage = {
    opt for opt in stage_options if st.session_state.get(f"stage_{opt}")
}
selected_activity = {
    opt for opt in all_activity_norm if st.session_state.get(f"activity_{opt}")
}
selected_audience = {
    opt for opt in all_audience_norm if st.session_state.get(f"audience_{opt}")
}

df_except_region = filtered_except(
    df,
    q,
    selected_regions,
    selected_ftypes,
    selected_famts,
    selected_stage,
    selected_activity,
    selected_audience,
    except_dim="region",
)
df_except_ftype = filtered_except(
    df,
    q,
    selected_regions,
    selected_ftypes,
    selected_famts,
    selected_stage,
    selected_activity,
    selected_audience,
    except_dim="ftype",
)
df_except_famt = filtered_except(
    df,
    q,
    selected_regions,
    selected_ftypes,
    selected_famts,
    selected_stage,
    selected_activity,
    selected_audience,
    except_dim="famt",
)
df_except_stage = filtered_except(
    df,
    q,
    selected_regions,
    selected_ftypes,
    selected_famts,
    selected_stage,
    selected_activity,
    selected_audience,
    except_dim="stage",
)
df_except_activity = filtered_except(
    df,
    q,
    selected_regions,
    selected_ftypes,
    selected_famts,
    selected_stage,
    selected_activity,
    selected_audience,
    except_dim="activity",
)
df_except_audience = filtered_except(
    df,
    q,
    selected_regions,
    selected_ftypes,
    selected_famts,
    selected_stage,
    selected_activity,
    selected_audience,
    except_dim="audience",
)

region_counts = {
    r: int(
        df_except_region[COLS["REGION"]]
        .astype(str)
        .apply(lambda v, r=r: region_match(v, r))
        .sum()
    )
    for r in REGION_CHOICES
}
ftype_counts = {
    f: int(df_except_ftype["__fund_type_set"].apply(lambda s, f=f: f in s).sum())
    for f in FUNDING_TYPE_CHOICES
}
famt_counts = df_except_famt["__funding_bucket"].value_counts().to_dict()
stage_counts = count_by_option(df_except_stage["__stage_norm_set"])
activity_counts = count_by_option(df_except_activity["__activity_norm_set"])
audience_counts = count_by_option(df_except_audience["__audience_norm_set"])


def render_filter_checklist(label, options, counts, state_prefix):
    picked = set()
    with st.sidebar.expander(label, expanded=False):
        if st.button("Clear", key=f"clear_{state_prefix}"):
            for opt in options:
                st.session_state[f"{state_prefix}_{opt}"] = False
        for opt in options:
            c = counts.get(opt, 0)
            disabled = c == 0
            val = st.checkbox(
                f"{opt} ({c})",
                key=f"{state_prefix}_{opt}",
                disabled=disabled,
            )
            if val and not disabled:
                picked.add(opt)
    return picked


if "funding_type_info_states" not in st.session_state:
    st.session_state["funding_type_info_states"] = {}


def render_funding_type_filter(label, options, counts, state_prefix="ftype"):
    picked = set()
    info_states = st.session_state["funding_type_info_states"]

    with st.sidebar.expander(label, expanded=False):
        if st.button("Clear", key=f"clear_{state_prefix}"):
            for opt in options:
                st.session_state[f"{state_prefix}_{opt}"] = False
            for opt in list(info_states.keys()):
                info_states[opt] = False

        for opt in options:
            c = counts.get(opt, 0)
            disabled = c == 0

            cols = st.columns([4, 1])

            # Checkbox
            with cols[0]:
                val = st.checkbox(
                    f"{opt} ({c})",
                    key=f"{state_prefix}_{opt}",
                    disabled=disabled,
                )
                if val and not disabled:
                    picked.add(opt)

            # ℹ button + description
            show_desc = info_states.get(opt, False)
            with cols[1]:
                if st.button("ℹ️", key=f"info_btn_{state_prefix}_{opt}"):
                    show_desc = not show_desc
            info_states[opt] = show_desc

            if show_desc:
                desc = FUNDING_TYPE_DESCRIPTIONS.get(opt, "")
                if desc:
                    st.caption(desc)

    st.session_state["funding_type_info_states"] = info_states
    return picked


# Funding filters first
sel_ftypes = render_funding_type_filter(
    "Funding Type", FUNDING_TYPE_CHOICES, ftype_counts, "ftype"
)
sel_famts = render_filter_checklist(
    "Funding Amount", FUND_AMOUNT_CHOICES, famt_counts, "famt"
)
sel_audience = render_filter_checklist(
    "Audience & Industry", all_audience_norm, audience_counts, "audience"
)
sel_stage = render_filter_checklist(
    "Business Stage", stage_options, stage_counts, "stage"
)
sel_activity = render_filter_checklist(
    "Business Supports", all_activity_norm, activity_counts, "activity"
)
sel_regions = render_filter_checklist(
    "Region", REGION_CHOICES, region_counts, "region"
)

with st.sidebar.expander("About funding types", expanded=False):
    st.markdown(
        """
Use **Funding Type** to select the broad kind of financial support:

- **Grants** and **rebates** generally do not need to be repaid.
- **Loans**, **financing** and **credit** are repayable forms of capital.
- **Tax credits** and **subsidies** reduce specific costs or taxes.
- **Equity investment** provides capital in exchange for ownership.
"""
    )

selected_regions, selected_ftypes, selected_famts = (
    sel_regions,
    sel_ftypes,
    sel_famts,
)
selected_stage, selected_activity, selected_audience = (
    sel_stage,
    sel_activity,
    sel_audience,
)

if st.sidebar.button("Clear all filters"):
    for k in list(st.session_state.keys()):
        if any(
            k.startswith(prefix)
            for prefix in (
                "region_",
                "ftype_",
                "famt",
                "stage",
                "activity_",
                "audience",
            )
        ):
            st.session_state[k] = False
    st.session_state["funding_type_info_states"] = {}
    st.rerun()

# ---------------------------- Apply filters ----------------------------
def apply_filters(df_in: pd.DataFrame) -> pd.DataFrame:
    out = df_in.copy()
    out = out[fuzzy_mask(out, q, threshold=FUZZY_THR)]
    if selected_regions and COLS["REGION"] in out.columns:
        col = out[COLS["REGION"]].astype(str)
        out = out[col.apply(lambda v: any(region_match(v, r) for r in selected_regions))]
    if selected_famts:
        out = out[out["__funding_bucket"].isin(selected_famts)]
    if selected_ftypes:
        out = out[out["__fund_type_set"].apply(lambda s: bool(s & selected_ftypes))]
    if selected_stage:
        out = out[out["__stage_norm_set"].apply(lambda s: bool(s & selected_stage))]
    if selected_activity:
        out = out[
            out["__activity_norm_set"].apply(lambda s: bool(s & selected_activity))
        ]
    if selected_audience:
        out = out[
            out["__audience_norm_set"].apply(lambda s: bool(s & selected_audience))
        ]
    return out


filtered = apply_filters(df)

# ---------------------------- Sort & pagination ----------------------------
def sort_df(dfin: pd.DataFrame) -> pd.DataFrame:
    if sort_mode == "Program Name (A–Z)":
        return dfin.sort_values(
            COLS["PROGRAM_NAME"],
            na_position="last",
            kind="mergesort",
        )
    if sort_mode == "Last Checked (newest)":
        tmp = dfin.copy()
        tmp["__dt"] = pd.to_datetime(tmp[COLS["LAST_CHECKED"]], errors="coerce")
        tmp = tmp.sort_values(
            "__dt",
            ascending=False,
            na_position="last",
            kind="mergesort",
        )
        return tmp.drop(columns="__dt")
    return dfin


filtered = sort_df(filtered)

st.markdown(f"### {len(filtered)} Programs Found")

# ---------------------------- Chips (read-only) ----------------------------
def render_chips():
    """Show active filters as read-only chips (no state mutation)."""
    chips = []

    if q:
        chips.append(f"Search: {q}")

    for f in sorted(selected_ftypes):
        chips.append(f"Funding Type: {f}")
    for b in sorted(selected_famts):
        chips.append(f"Amount: {b}")
    for au in sorted(selected_audience):
        chips.append(f"Audience & Industry: {au}")
    for s in sorted(selected_stage):
        chips.append(f"Stage: {s}")
    for a in sorted(selected_activity):
        chips.append(f"Business Supports: {a}")
    for r in sorted(selected_regions):
        chips.append(f"Region: {r}")

    if not chips:
        return

    st.write("")
    chip_markup = " ".join(
        f"<span style='border-radius:999px;border:1px solid #D1D5DB;"
        f"padding:4px 10px;margin-right:6px;font-size:13px;background:#F9FAFB;'>{c}</span>"
        for c in chips
    )
    st.markdown(chip_markup, unsafe_allow_html=True)


render_chips()

# ---------------------------- Export ----------------------------
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download results (CSV)",
    csv_bytes,
    file_name="pathfinding_results.csv",
    mime="text/csv",
)

# ---------------------------- Results (role=main) ----------------------------
if "favorites" not in st.session_state:
    st.session_state.favorites = set()

UNKNOWN = "unknown / not stated"

total = len(filtered)
if "page_idx" not in st.session_state:
    st.session_state.page_idx = 0
max_page = max(0, (total - 1) // page_size)
page = min(st.session_state.page_idx, max_page)
start = page * page_size
end = min(start + page_size, total)
if total > 0:
    st.caption(f"Showing {start + 1}-{end} of {total}")

prev_col, _, next_col = st.columns([0.1, 0.8, 0.1])
with prev_col:
    if st.button("◀ Prev", disabled=page == 0):
        st.session_state.page_idx = max(0, page - 1)
        st.rerun()
with next_col:
    if st.button("Next ▶", disabled=page >= max_page):
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
    subset = filtered.iloc[start:end].copy()
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

        # Description (strip placeholder text)
        raw_desc = str(row[COLS["DESC"]] or "").strip()
        if (
            raw_desc.strip().lower()
            == "description pending verification from program website."
        ):
            raw_desc = ""
        desc_full = sanitize_text_keep_smart(raw_desc)
        desc = (desc_full[:240] + "…") if len(desc_full) > 240 else desc_full

        elig = sanitize_text_keep_smart(str(row[COLS["ELIG"]] or "").strip())
        fund_bucket = str(row.get("__funding_bucket") or "")
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

            # Header
            st.markdown(
                f"""
                <span class='badge {badge_cls}'>{badge_label}</span>
                <span class='meta'>Last checked: {fresh_date if fresh_date else '—'}
                {f"({fresh_label})" if fresh_label != "—" else ""}</span>
                <div class='title'>{name}</div>
                <div class='org'>{org}</div>
                """,
                unsafe_allow_html=True,
            )

            # Description
            st.markdown(
                f"<p>{desc or '<span class=\"placeholder\">No description provided.</span>'}</p>",
                unsafe_allow_html=True,
            )

            # Funding + Eligibility strip
            fund_label = ""
            if fund_bucket and fund_bucket.strip().lower() != UNKNOWN:
                fund_label = add_dollar_signs(fund_bucket)

            fund_line = (
                f'<span class="kv"><strong>Funding:</strong> {fund_label}</span>'
                if fund_label
                else ""
            )
            elig_line = (
                f'<span class="kv"><strong>Eligibility:</strong> {elig}</span>'
                if (
                    elig
                    and elig.strip().lower()
                    not in {"", "unknown / not stated", "n/a", "na"}
                )
                else ""
            )

            meta_html = (
                " ".join(x for x in [fund_line, elig_line] if x)
                or "<span class='placeholder'>No additional details</span>"
            )

            st.markdown(
                f"<div class='meta-info'>{meta_html}</div>", unsafe_allow_html=True
            )

            # Actions row: Website · Email · Call · ☆/★ Favourite
            st.markdown("<div class='actions-row'>", unsafe_allow_html=True)

            cols = st.columns(4)
            call_clicked = False
            fav_clicked = False

            # Website
            with cols[0]:
                if website:
                    url = (
                        website
                        if website.startswith(("http://", "https://"))
                        else f"https://{website}"
                    )
                    st.markdown(f"[Website]({url})", unsafe_allow_html=True)

            # Email
            with cols[1]:
                if email:
                    st.markdown(f"[Email](mailto:{email})", unsafe_allow_html=True)

            # Call (toggle numbers)
            with cols[2]:
                if phone_display_multi:
                    call_clicked = st.button("Call", key=f"call_{key}")

            # Favourite
            with cols[3]:
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
                        f"<small><strong>Call:</strong> {phone_display_multi}</small>",
                        unsafe_allow_html=True,
                    )

            # Toggle favourites
            if fav_clicked:
                if fav_on:
                    st.session_state.favorites.remove(key)
                else:
                    st.session_state.favorites.add(key)
                st.rerun()

            if len(desc_full) > 240:
                with st.expander("More details"):
                    st.markdown(f"**Full description:** {desc_full}")
