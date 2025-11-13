# app.py — Alberta Pathfinding Tool (Streamlit)
# Features:
# • Sticky GoA header with hover/focus states
# • All info visually inside each card (using container + :has marker)
# • Actions row: Website · Email · Call · ☆/★ Favourite inline as text
# • Call control reveals phone number(s), with multiple separated by " | "
# • Hide Call when phone is missing or "not publicly listed – use contact page"
# • Smart punctuation preserved; bullets/emojis stripped; mojibake fixed
# • GoA logo embedded (SVG/PNG). Optional GoA CSS injection if files exist
# • ARIA: role="main" on results, “Skip to results” link
# • Empty-state message, chips, pagination, sorting
# • Audience & industry filter derived from Meta Tags
# • Funding-type help panel in sidebar
# • Business Supports filter (was “Activity”)
# • Per–Funding Type ℹ info buttons with definitions

import re, base64
from pathlib import Path
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# ---------------------------- Page ----------------------------
st.set_page_config(
    page_title="Alberta Pathfinding Tool – Small Business Supports",
    layout="wide"
)

# ---------------------------- Styles ----------------------------
st.markdown("""
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

.actions-dot{ color:#9CA3AF; }

/* Make card buttons (Call / Favourite) look like text links */
/* Target only buttons inside program cards so other buttons keep default styling */
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button{
  background:none !important;
  border:none !important;
  padding:0 !important;
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

/* Keep other primary buttons (filters, pagination) slightly rounded */
button[kind="primary"]{ border-radius:8px; }
</style>
""", unsafe_allow_html=True)

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
    svg_path = Path("assets/GoA-logo.svg")
    png_path = Path("assets/GoA-logo.png")
    if svg_path.exists():
        b64 = base64.b64encode(svg_path.read_bytes()).decode()
        return f'<img src="data:image/svg+xml;base64,{b64}" alt="Government of Alberta" style="height:48px;">'
    if png_path.exists():
        b64 = base64.b64encode(png_path.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="Government of Alberta" style="height:48px;">'
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
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = load_df(DATA_FILE)

def map_col(df, name_hint: str, fallbacks: list[str]) -> str | None:
    for c in df.columns:
        if name_hint.lower() in str(c).lower():
            return c
    for fb in fallbacks:
        if fb in df.columns:
            return fb
    return None

COLS = {
    "PROGRAM_NAME": map_col(df, "program name", ["Program Name"]),
    "ORG_NAME":     map_col(df, "organization name", ["Organization Name"]),
    "DESC":         map_col(df, "program description", ["Program Description"]),
    "ELIG":         map_col(df, "eligibility", ["Eligibility Description", "Eligibility"]),
    "EMAIL":        map_col(df, "email", ["Email Address"]),
    "PHONE":        map_col(df, "phone", ["Phone Number"]),
    "WEBSITE":      map_col(df, "website", ["Program Website", "Website"]),
    "REGION":       map_col(df, "region", ["Geographic Region", "Region"]),
    "TAGS":         map_col(df, "meta", ["Meta Tags", "Tags"]),
    "FUNDING":      map_col(df, "funding amount", ["Funding Amount", "Funding"]),
    "STATUS":       map_col(df, "operational status", ["Operational Status", "Status"]),
    "LAST_CHECKED": map_col(df, "last checked", ["Last Checked (MT)", "Last Checked"]),
    "KEY":          map_col(df, "_key_norm", ["_key_norm", "Key"]),
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

URL_LIKE = re.compile(r"https?://|www\\.|\\.ca\\b|\\.com\\b|\\.org\\b|\\.net\\b", re.I)
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
    return re.sub(r'(?<!\$)(\d[\d,\.]*\s*[KkMm]?)', r'$\1', text)

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
        return f"{days//30}mo ago"
    return f"{days//365}y ago"

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
    chunks = re.split(r"[,/;]|\\bor\\b", str(phone))
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
    "mentor":"Mentorship","mentorship":"Mentorship","mentoring":"Mentorship",
    "advis":"Advisory / Consulting","advisory":"Advisory / Consulting",
    "advising":"Advisory / Consulting","advice":"Advisory / Consulting",
    "coaching":"Coaching",
    "accelerator":"Accelerator / Incubator","acceleration":"Accelerator / Incubator",
    "incubator":"Accelerator / Incubator",
    "innovation":"Innovation / R&D","research":"Innovation / R&D","r&d":"Innovation / R&D",
    "export":"Export Readiness",
    "network":"Networking / Peer Support","networking":"Networking / Peer Support",
    "peer":"Networking / Peer Support",
    "workshop":"Workshops / Training","workshops":"Workshops / Training",
    "training":"Workshops / Training",
    "cohort":"Cohort / Program Participation","program":"Cohort / Program Participation",
}

STAGE_NORMALIZATION_MAP = {
    "startup":"Startup / Early Stage","start-up":"Startup / Early Stage",
    "early":"Startup / Early Stage",
    "pre-revenue":"Startup / Early Stage","pre revenue":"Startup / Early Stage",
    "ideation":"Startup / Early Stage",
    "prototype":"Startup / Early Stage","preseed":"Startup / Early Stage",
    "pre-seed":"Startup / Early Stage","seed":"Startup / Early Stage",
    "scaleup":"Growth / Scale","scale-up":"Growth / Scale",
    "scale":"Growth / Scale","growth":"Growth / Scale",
    "expand":"Growth / Scale","expansion":"Growth / Scale",
    "commercializ":"Growth / Scale","market-entry":"Growth / Scale",
    "market entry":"Growth / Scale",
    "mature":"Mature / Established","established":"Mature / Established",
    "existing":"Mature / Established",
}

# Funding types: Grant, Loan, Financing, Subsidy, Tax Credit, Rebate, Credit, Equity Investment
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

# Short, plain-language definitions for each funding type (GoA-friendly tone)
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

    # Industry / sector audiences (from Meta Tags)
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
