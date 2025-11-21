import re
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# ---------------------------- Page config ----------------------------
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

/* Search input styling - make box more visible */
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

/* Card marker and container styling */
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

/* Funding and eligibility strip */
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
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) a,
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button{
  color:var(--link) !important;
  text-decoration:underline !important;
  font-size:var(--fs-body);
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) a:hover,
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button:hover{
  opacity:.85;
  text-decoration:underline;
}
div[data-testid="stVerticalBlock"]:has(.pf-card-marker) .stButton > button{
  background:none !important;
  border:none !important;
  padding:0;
  margin:0;
  cursor:pointer;
  box-shadow:none !important;
  border-radius:0 !important;
}

/* Global primary and secondary buttons */
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

/* Active filter pills under search bar */
div[data-testid="stVerticalBlock"]:has(.chip-row-marker) button{
  border-radius:999px;
  border:1px solid var(--border);
  background:#E6F2F8;
  color:var(--primary);
  font-size:13px;
  padding:4px 12px;
  margin:4px 6px 4px 0;
  cursor:pointer;
  text-decoration:none !important;
}
div[data-testid="stVerticalBlock"]:has(.chip-row-marker) button:hover{
  background:#D3E5F5;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------- Header ----------------------------
st.markdown(
    """
<a class="skip-link" href="#results-main">Skip to results</a>
<div class="header goa-header">
  <div>
    <h2>Small Business Supports Finder</h2>
    <p>Helping Alberta entrepreneurs and small businesses find programs, funding, and services quickly.</p>
  </div>
</div>
<div class="header-spacer"></div>
""",
    unsafe_allow_html=True,
)

# ---------------------------- Data loading ----------------------------
DATA_FILE = "Pathfinding_Master.xlsx"

if not Path(DATA_FILE).exists():
    st.error("Pathfinding_Master.xlsx not found in app folder.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_df(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

df = load_df(DATA_FILE)

# Column mapping based on your actual file
COLS = {
    "PROGRAM_NAME": "Program Name",
    "ORG_NAME": "Organization Name",
    "DESC": "Program Description",
    "ELIG": "Eligibility Description",
    "WEBSITE": "Program Website",
    "EMAIL": "Email Address",
    "PHONE": "Phone Number",
    "REGION": "Geographic Region",
    "TAGS": "Meta Tags",
    "LAST_CHECKED": "Last Checked (MT)",
    "STATUS": "Operational Status",
    "FUNDING": "Funding Amount",
    "KEY": "_key_norm",
}

# ---------------------------- Tag parsing & normalization ----------------------------
def parse_tags_field_clean(s):
    if not isinstance(s, str):
        return []
    parts = re.split(r"[;,/|]", s)
    out = []
    for p in parts:
        t = (p or "").strip()
        if t:
            out.append(t)
    return out

ACTIVITY_NORMALIZATION_MAP = {
    "mentor": "Mentorship",
    "mentorship": "Mentorship",
    "advis": "Advisory / Consulting",
    "coaching": "Coaching",
    "accelerator": "Accelerator / Incubator",
    "incubator": "Accelerator / Incubator",
    "innovation": "Innovation / R and D",
    "research": "Innovation / R and D",
    "export": "Export Readiness",
    "network": "Networking / Peer Support",
    "workshop": "Workshops / Training",
    "training": "Workshops / Training",
    "cohort": "Cohort / Program Participation",
    "program": "Cohort / Program Participation",
}

STAGE_NORMALIZATION_MAP = {
    "startup": "Startup / Early Stage",
    "start-up": "Startup / Early Stage",
    "early": "Startup / Early Stage",
    "pre-revenue": "Startup / Early Stage",
    "ideation": "Startup / Early Stage",
    "seed": "Startup / Early Stage",
    "scaleup": "Growth / Scale",
    "scale-up": "Growth / Scale",
    "growth": "Growth / Scale",
    "expand": "Growth / Scale",
    "mature": "Mature / Established",
    "established": "Mature / Established",
    "existing": "Mature / Established",
}

AUDIENCE_NORMALIZATION_MAP = {
    "women": "Women",
    "woman": "Women",
    "female": "Women",
    "indigenous": "Indigenous",
    "first nation": "Indigenous",
    "metis": "Indigenous",
    "inuit": "Indigenous",
    "black": "Black entrepreneurs",
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
    "digital": "Technology / Digital",
    "tourism": "Tourism and Hospitality",
    "agri": "Agriculture and Agri-food",
    "energy": "Energy",
    "cleantech": "Clean Technology",
    "manufactur": "Manufacturing",
    "film": "Creative Industries",
    "creative": "Creative Industries",
}

FUNDING_TYPE_KEYWORDS = {
    "grant": "Grant",
    "non-repayable": "Grant",
    "loan": "Loan",
    "microloan": "Loan",
    "guarantee": "Guarantee",
    "credit": "Credit",
    "line of credit": "Credit",
    "financing": "Financing",
    "subsidy": "Subsidy",
    "tax credit": "Tax Credit",
    "rebate": "Rebate",
    "equity": "Equity Investment",
    "venture capital": "Equity Investment",
    "in-kind": "In-kind",
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

def detect_funding_types_from_meta(val):
    text = str(val or "").lower()
    hits = set()
    for needle, canon in FUNDING_TYPE_KEYWORDS.items():
        if needle in text:
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

# ---------------------------- Funding buckets & dates ----------------------------
def funding_bucket(amount):
    s = str(amount or "").replace(",", "")
    nums = re.findall(r"\d+\.?\d*", s)
    if not nums:
        return "Unknown / Not stated"
    try:
        val = float(nums[-1])
    except ValueError:
        return "Unknown / Not stated"
    if val < 10000:
        return "Micro (<10K)"
    if val < 50000:
        return "Small (10K-50K)"
    if val < 250000:
        return "Medium (50K-250K)"
    if val < 1000000:
        return "Large (250K-1M)"
    return "Major (1M+)"

def add_dollar_signs(text: str) -> str:
    if not text:
        return text
    if "unknown" in str(text).lower():
        return text
    return re.sub(r"(?<!\$)(\d[\d,\.]*\s*[KkMm]?)", r"$\1", str(text))

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

# ---------------------------- Derive columns ----------------------------
df["__funding_bucket"] = df[COLS["FUNDING"]].apply(funding_bucket)
df["__funding_amount_fmt"] = df[COLS["FUNDING"]].apply(add_dollar_signs)
df["__fund_type_set"] = df[COLS["TAGS"]].apply(detect_funding_types_from_meta)
df["__activity_norm_set"] = df[COLS["TAGS"]].apply(row_activity_norm_set)
df["__stage_norm_set"] = df[COLS["TAGS"]].apply(row_stage_norm_set)
df["__audience_norm_set"] = df[COLS["TAGS"]].apply(row_audience_norm_set)

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

# ---------------------------- Search bar ----------------------------
st.markdown("### Find programs and supports for your Alberta business")

q = st.text_input(
    "Search programs",
    "",
    key="q",
    placeholder="Try grant, mentorship, or startup...",
)
st.caption(
    "Tip: Search matches similar terms. For example, typing mentor will also find mentorship."
)

# ---------------------------- Fuzzy search ----------------------------
FUZZY_THR = 70

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
    "Guarantee",
    "Equity Investment",
    "In-kind",
]
FUND_AMOUNT_CHOICES = [
    "Micro (<10K)",
    "Small (10K-50K)",
    "Medium (50K-250K)",
    "Large (250K-1M)",
    "Major (1M+)",
    "Unknown / Not stated",
]

def region_match(region_value: str, selected: str) -> bool:
    if not isinstance(region_value, str):
        return False
    v = region_value.lower()
    table = {
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
        ],
        "Canada": ["canada", "national", "pan-canadian", "federal"],
    }
    return any(word in v for word in table.get(selected, []))

def count_by_option(series_of_sets: pd.Series):
    freq: dict[str, int] = {}
    for S in series_of_sets:
        for v in S:
            freq[v] = freq.get(v, 0) + 1
    return freq

# Simple global counts (keeps logic lighter)
region_counts = {}
for r in REGION_CHOICES:
    region_counts[r] = int(
        df[COLS["REGION"]]
        .astype(str)
        .apply(lambda v, rr=r: region_match(v, rr))
        .sum()
    )

ftype_counts = count_by_option(df["__fund_type_set"])
famt_counts = df["__funding_bucket"].value_counts().to_dict()
stage_counts = count_by_option(df["__stage_norm_set"])
activity_counts = count_by_option(df["__activity_norm_set"])
audience_counts = count_by_option(df["__audience_norm_set"])

all_activity_norm = sorted({v for S in df["__activity_norm_set"] for v in S})
all_stage_norm = sorted({v for S in df["__stage_norm_set"] for v in S})
all_audience_norm = sorted({v for S in df["__audience_norm_set"] for v in S})

def render_filter_pills(label, options, counts, state_prefix):
    picked = set()
    st.sidebar.markdown(f"### {label}")
    if st.sidebar.button("Clear", key=f"clear_{state_prefix}"):
        for opt in options:
            st.session_state[f"{state_prefix}_{opt}"] = False
    for opt in options:
        c = counts.get(opt, 0)
        disabled = c == 0
        state_key = f"{state_prefix}_{opt}"
        active = st.session_state.get(state_key, False)
        btn_type = "primary" if active and not disabled else "secondary"
        label_text = f"{opt} ({c})"
        clicked = st.sidebar.button(
            label_text,
            key=f"pill_{state_prefix}_{opt}",
            disabled=disabled,
            type=btn_type,
        )
        if clicked and not disabled:
            st.session_state[state_key] = not active
            active = st.session_state[state_key]
        if active and not disabled:
            picked.add(opt)
    return picked

def clear_all_filters():
    for k in list(st.session_state.keys()):
        if any(
            k.startswith(prefix)
            for prefix in ("region_","ftype_","famt_","stage_","activity_","audience_")
        ):
            st.session_state[k] = False
    st.session_state["q"] = ""

if st.sidebar.button("Clear all filters", key="clear_all_top"):
    clear_all_filters()
    st.rerun()

sel_activity = render_filter_pills(
    "What type of business support do you need?",
    all_activity_norm,
    activity_counts,
    "activity",
)
sel_ftypes = render_filter_pills(
    "What kind of funding are you looking for?",
    FUNDING_TYPE_CHOICES,
    ftype_counts,
    "ftype",
)
sel_famts = render_filter_pills(
    "How much funding are you looking for?",
    FUND_AMOUNT_CHOICES,
    famt_counts,
    "famt",
)
sel_stage = render_filter_pills(
    "What stage is your business at?",
    all_stage_norm,
    stage_counts,
    "stage",
)
sel_audience = render_filter_pills(
    "Who is this support for?",
    all_audience_norm,
    audience_counts,
    "audience",
)
sel_regions = render_filter_pills(
    "Where is your business located?",
    REGION_CHOICES,
    region_counts,
    "region",
)

selected_regions = sel_regions
selected_ftypes = sel_ftypes
selected_famts = sel_famts
selected_stage = sel_stage
selected_activity = sel_activity
selected_audience = sel_audience

if st.sidebar.button("Clear all filters", key="clear_all_bottom"):
    clear_all_filters()
    st.rerun()

# ---------------------------- Active chips under search ----------------------------
def render_chips():
    any_chip = False
    st.markdown("<div class='chip-row-marker'></div>", unsafe_allow_html=True)

    def chip(label: str, key_suffix: str, clear_fn):
        nonlocal any_chip
        any_chip = True
        clicked = st.button(label + " x", key=f"chip_{key_suffix}")
        if clicked:
            clear_fn()
            st.rerun()

    if q:
        chip(f"Search: {q}", "search", lambda: st.session_state.update({"q": ""}))
    for f in sorted(selected_ftypes):
        chip(f"Funding Type: {f}", f"ftype_{f}", lambda f=f: st.session_state.update({f"ftype_{f}": False}))
    for b in sorted(selected_famts):
        chip(f"Amount: {b}", f"famt_{b}", lambda b=b: st.session_state.update({f"famt_{b}": False}))
    for s in sorted(selected_stage):
        chip(f"Stage: {s}", f"stage_{s}", lambda s=s: st.session_state.update({f"stage_{s}": False}))
    for a in sorted(selected_activity):
        chip(f"Support: {a}", f"activity_{a}", lambda a=a: st.session_state.update({f"activity_{a}": False}))
    for au in sorted(selected_audience):
        chip(f"Audience: {au}", f"audience_{au}", lambda au=au: st.session_state.update({f"audience_{au}": False}))
    for r in sorted(selected_regions):
        chip(f"Region: {r}", f"region_{r}", lambda r=r: st.session_state.update({f"region_{r}": False}))

    if any_chip:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

# ---------------------------- Apply filters ----------------------------
def apply_filters(df_in: pd.DataFrame) -> pd.DataFrame:
    out = df_in.copy()
    out = out[fuzzy_mask(out, q, threshold=FUZZY_THR)]
    if selected_regions:
        col = out[COLS["REGION"]].astype(str)
        out = out[col.apply(lambda v: any(region_match(v, r) for r in selected_regions))]
    if selected_famts:
        out = out[out["__funding_bucket"].isin(selected_famts)]
    if selected_ftypes:
        out = out[out["__fund_type_set"].apply(lambda s: bool(s & selected_ftypes))]
    if selected_stage:
        out = out[out["__stage_norm_set"].apply(lambda s: bool(s & selected_stage))]
    if selected_activity:
        out = out[out["__activity_norm_set"].apply(lambda s: bool(s & selected_activity))]
    if selected_audience:
        out = out[out["__audience_norm_set"].apply(lambda s: bool(s & selected_audience))]
    return out

filtered = apply_filters(df)
render_chips()

# ---------------------------- Sort & page size ----------------------------
sort_col, page_col = st.columns([0.6, 0.4])
with sort_col:
    sort_mode = st.selectbox(
        "Sort results by",
        ["Relevance", "Program Name (A to Z)", "Last Checked (newest)"],
        index=0,
    )
with page_col:
    page_size = st.selectbox(
        "Results per page",
        [10, 25, 50],
        index=1,
    )

def sort_df(dfin: pd.DataFrame) -> pd.DataFrame:
    if sort_mode == "Program Name (A to Z)":
        return dfin.sort_values(COLS["PROGRAM_NAME"], na_position="last", kind="mergesort")
    if sort_mode == "Last Checked (newest)":
        tmp = dfin.copy()
        tmp["__dt"] = pd.to_datetime(tmp[COLS["LAST_CHECKED"]], errors="coerce")
        tmp = tmp.sort_values("__dt", ascending=False, na_position="last", kind="mergesort")
        return tmp.drop(columns="__dt")
    return dfin

filtered = sort_df(filtered)

st.markdown(f"### {len(filtered)} Programs Found")

# ---------------------------- Export ----------------------------
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download results (CSV)",
    csv_bytes,
    file_name="pathfinding_results.csv",
    mime="text/csv",
)

# ---------------------------- Pagination ----------------------------
if "page_idx" not in st.session_state:
    st.session_state["page_idx"] = 0

total = len(filtered)
page_size_int = int(page_size)
max_page = max(0, (total - 1) // page_size_int)
page = min(st.session_state["page_idx"], max_page)
start = page * page_size_int
end = min(start + page_size_int, total)

if total > 0:
    st.caption(f"Showing {start+1}-{end} of {total}")
else:
    st.info("No programs match your current filters. Try clearing filters or broadening your search.")

prev_col, next_col = st.columns([0.5, 0.5])
with prev_col:
    if st.button("Prev", disabled=page == 0):
        st.session_state["page_idx"] = max(0, page - 1)
        st.rerun()
with next_col:
    if st.button("Next", disabled=page >= max_page):
        st.session_state["page_idx"] = min(max_page, page + 1)
        st.rerun()

st.markdown(
    '<div id="results-main" role="main"></div>',
    unsafe_allow_html=True,
)

# ---------------------------- Render cards ----------------------------
for _, row in filtered.iloc[start:end].iterrows():
    with st.container():
        st.markdown("<div class='pf-card-marker'></div>", unsafe_allow_html=True)

        name = str(row[COLS["PROGRAM_NAME"]] or "")
        org = str(row[COLS["ORG_NAME"]] or "")
        status_raw = str(row[COLS["STATUS"]] or "")
        s_low = status_raw.lower()

        badge_cls = (
            "operational"
            if "operational" in s_low
            else ("open" if "open" in s_low else "closed")
        )
        badge_label = status_raw or (
            "Operational" if badge_cls == "operational" else ("Open" if badge_cls == "open" else "Closed or Paused")
        )

        desc = str(row[COLS["DESC"]] or "").strip()
        elig = str(row[COLS["ELIG"]] or "").strip()
        fund_bucket_val = str(row.get("__funding_bucket") or "")
        fund_amount_fmt = str(row.get("__funding_amount_fmt") or "")
        fund_type_set = row.get("__fund_type_set", set())
        fresh_days = row.get("__fresh_days")
        fresh_date = str(row.get("__fresh_date") or "")
        fresh_label = freshness_label(fresh_days)

        website = str(row.get(COLS["WEBSITE"]) or "").strip()
        email = str(row.get(COLS["EMAIL"]) or "").strip()
        phone = str(row.get(COLS["PHONE"]) or "").strip()

        st.markdown(
            f"""
            <span class='badge {badge_cls}'>{badge_label}</span>
            <span class='meta'>Last checked: {fresh_date if fresh_date else "—"} {f"({fresh_label})" if fresh_label != "—" else ""}</span>
            <div class='title'>{name}</div>
            <div class='org'>{org}</div>
            """,
            unsafe_allow_html=True,
        )

        if desc:
            st.write(desc)
        else:
            st.markdown('<p class="placeholder">No description provided.</p>', unsafe_allow_html=True)

        parts = []
        if fund_bucket_val:
            parts.append(f"<span class='kv'><strong>Funding band:</strong> {fund_bucket_val}</span>")
        if fund_amount_fmt:
            parts.append(f"<span class='kv'><strong>Funding amount:</strong> {fund_amount_fmt}</span>")
        if fund_type_set:
            parts.append(f"<span class='kv'><strong>Funding type:</strong> {', '.join(sorted(fund_type_set))}</span>")
        if elig:
            parts.append(f"<span class='kv'><strong>Eligibility highlights:</strong> {elig}</span>")

        meta_html = " ".join(parts) if parts else "<span class='placeholder'>No additional details.</span>"
        st.markdown(f"<div class='meta-info'>{meta_html}</div>", unsafe_allow_html=True)

        st.markdown('<div class="actions-row"><div class="actions-links">', unsafe_allow_html=True)
        if website:
            url = website if website.startswith(("http://","https://")) else f"https://{website}"
            st.markdown(f'<a href="{url}" target="_blank">Website</a>', unsafe_allow_html=True)
        if email:
            st.markdown(f'<a href="mailto:{email}">Email</a>', unsafe_allow_html=True)
        if phone:
            st.markdown(f'<a href="tel:{phone}">Call</a>', unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
