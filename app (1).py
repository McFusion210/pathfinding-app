
# app.py — Alberta Pathfinding Tool (Streamlit) — GoA Theme + Fixed Fuzziness + Detailed Funding Checkboxes
# - Government of Alberta colour palette
# - Fuzziness fixed to 70 (no slider), with helper note
# - Clickable chips, normalization, counts, disable-zero, CSV export, sorting, pagination
# - NEW: Detailed Funding Amount checkboxes (CAD) with robust numeric parsing (K/M)
#        If any detailed ranges are selected, they OVERRIDE the coarse buckets.
#        Also includes "Only programs with numeric funding" toggle and a custom amount range.

import re
from pathlib import Path
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# ---------------------------- Page & Styles ----------------------------
st.set_page_config(page_title="Alberta Pathfinding Tool – Small Business Supports", layout="wide")

st.markdown("""
<style>
:root {
  /* Government of Alberta palette */
  --bg:#FFFFFF; 
  --surface:#FFFFFF; 
  --text:#0A0A0A; 
  --muted:#4B5563;
  --primary:#003366;           /* GoA navy */
  --primary-2:#007FA3;         /* GoA teal/sky */
  --border:#D9DEE7; 
  --link:#007FA3;
  --fs-title:24px; --fs-body:16px; --fs-meta:14px;
}

[data-testid="stAppViewContainer"] .main .block-container { padding-top: 1rem !important; }
html, body, p, div, span { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Segoe UI Emoji"; color: var(--text); }

.header {
  display:flex; align-items:center; gap:14px;
  background:var(--primary);
  padding:14px 20px; border-radius:8px; margin:8px 0 16px 0; color:#fff;
  border-bottom:2px solid #00294F;
}
.header h2 { margin:0; color:#fff; font-weight:800; font-size:28px; letter-spacing:.2px;}
.header p  { margin:0; color:#E6F2F8; font-size:15px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius:16px;
  padding:16px;
  box-shadow:0 1px 2px rgba(0,0,0,0.05);
  margin-bottom:16px;
}
.title { margin:4px 0 6px 0; font-weight:800; color:var(--primary); font-size: var(--fs-title); }
.org, .meta { color:var(--muted); font-size: var(--fs-meta); }
.meta { margin-left:8px; }
.placeholder { color:#7C8796; font-style:italic; }

/* Status badges */
.badge { display:inline-block; font-size:12px; padding:4px 10px; border-radius:999px; margin-right:6px; }
.badge.operational { background:#DFF3E6; color:#0B3D2E; border:1px solid #A6D9BE; }  /* green */
.badge.open        { background:#E0EAFF; color:#062F6E; border:1px solid #B7CBFF; }
.badge.closed      { background:#FBE5E8; color:#6D1B26; border:1px solid #F2BAC1; }

/* Info row inside card (under description) */
.info-row{
  display:flex; align-items:center; gap:16px; flex-wrap:wrap;
  margin-top:10px; padding-top:10px; border-top:1px solid var(--border);
}
.info-left{ display:flex; align-items:center; gap:18px; font-size: var(--fs-body); }
.kv strong{ font-weight:700; }

.info-right{ margin-left:auto; display:flex; align-items:center; gap:14px; }
.links a{ color: var(--link); text-decoration: underline; font-size: var(--fs-body); }
.links a + a{ margin-left:12px; }

/* favourite button small & inline */
.info-right .stButton>button{
  padding:6px 10px; border:1px solid var(--border);
  border-radius:12px; background:#fff; font-size: var(--fs-body);
}

/* Filter chips (clickable) */
.chips{ display:flex; gap:8px; flex-wrap:wrap; margin:8px 0 16px 0; }
.chip{
  display:inline-flex; align-items:center; gap:8px;
  padding:4px 10px; border:1px solid var(--primary-2); border-radius:999px;
  background:#E7F6FB; font-size:13px; color:var(--primary);
}
.chip .x{
  border:none; background:#F3F4F6; color:#111827;
  padding:2px 6px; border-radius:999px; cursor:pointer; font-weight:700;
}
.count{ color:#4A5565; font-size:12px; margin-left:6px; }
.disabled{ opacity:0.45; }

/* Sidebar panel look */
section[data-testid="stSidebar"] .block-container { background:#F5F7F9; border-right:1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
  <img src="assets/GoA-logo.svg" alt="Government of Alberta" style="height:48px;">
  <div>
    <h2>Alberta Pathfinding Tool</h2>
    <p>Small Business Supports & Funding Repository</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------- Data Config ----------------------------
DATA_FILE = st.secrets.get("DATA_FILE", "Pathfinding_Master.xlsx")
if not Path(DATA_FILE).exists():
    st.info("Upload **Pathfinding_Master.xlsx** to the repository root and rerun.")
    st.stop()

# ---------------------------- Caching ----------------------------
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
    "WEBSITE":      map_col(df, "website", ["Program Website","Website"]),
    "REGION":       map_col(df, "region", ["Geographic Region","Region"]),
    "TAGS":         map_col(df, "meta", ["Meta Tags","Tags"]),
    "FUNDING":      map_col(df, "funding amount", ["Funding Amount","Funding"]),
    "STATUS":       map_col(df, "operational status", ["Operational Status","Status"]),
    "LAST_CHECKED": map_col(df, "last checked", ["Last Checked (MT)","Last Checked"]),
    "KEY":          map_col(df, "_key_norm", ["_key_norm","Key"]),
}
for k, v in COLS.items():
    if v is None or v not in df.columns:
        new_name = f"__missing_{k}"
        df[new_name] = ""
        COLS[k] = new_name

# ---------------------------- Utilities ----------------------------
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
    if not text: return text
    if "unknown" in text.lower(): return text
    return re.sub(r'(?<!\$)(\d[\d,\.]*\s*[KkMm]?)', r'$\1', text)

def funding_bucket(amount):
    s = str(amount or "").replace(",", "")
    nums = re.findall(r"\d+\.?\d*", s)
    if not nums: return "Unknown / Not stated"
    try:
        val = float(nums[-1])
    except ValueError:
        return "Unknown / Not stated"
    if val < 5000: return "Under 5K"
    if val < 25000: return "5K–25K"
    if val < 100000: return "25K–100K"
    if val < 500000: return "100K–500K"
    return "500K+"

def parse_amounts(text: str):
    """Return list of numeric amounts in dollars, interpreting K/M suffixes."""
    if not isinstance(text, str) or not text.strip():
        return []
    amounts = []
    for m in re.finditer(r'(\d[\d,\.]*)\s*([KkMm]?)', text):
        num = m.group(1).replace(',', '')
        suf = (m.group(2) or '').lower()
        try:
            val = float(num)
        except:
            continue
        if suf == 'k':
            val *= 1000.0
        elif suf == 'm':
            val *= 1_000_000.0
        amounts.append(val)
    return amounts

def amount_min_max(text: str):
    vals = parse_amounts(text)
    if not vals:
        return (None, None)
    return (min(vals), max(vals))

def days_since(date_str):
    try:
        d = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(d): return None
        return (pd.Timestamp.utcnow().normalize() - d.normalize()).days
    except Exception:
        return None

def freshness_label(days):
    if days is None: return "—"
    if days <= 30:  return f"{days}d ago"
    if days <= 180: return f"{days//30}mo ago"
    return f"{days//365}y ago"

# ---------------------------- Normalization Maps ----------------------------
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
    "loan": "Loan",
    "microloan": "Loan",
    "financ": "Financing",
    "capital": "Financing",
    "subsid": "Subsidy",
    "tax credit": "Tax Credit",
    "taxcredit": "Tax Credit",
    "credit": "Credit",
    "line of credit": "Credit",
}

def normalize_activity_tag(tag: str) -> str:
    t = (tag or "").strip().lower()
    if not t:
        return ""
    for needle, canon in ACTIVITY_NORMALIZATION_MAP.items():
        if needle in t:
            return canon
    return ""

def normalize_stage_tag(tag: str) -> str:
    t = (tag or "").strip().lower()
    if not t:
        return ""
    for needle, canon in STAGE_NORMALIZATION_MAP.items():
        if needle in t:
            return canon
    return ""

def detect_funding_types_from_tags(s: str) -> set[str]:
    tags = parse_tags_field_clean(s)
    hits = set()
    for t in tags:
        tl = t.lower()
        for needle, canon in FUNDING_TYPE_MAP.items():
            if needle in tl:
                hits.add(canon)
    return hits

def row_activity_norm_set(raw_tag_field: str) -> set[str]:
    raw_tags = parse_tags_field_clean(raw_tag_field)
    return { normalize_activity_tag(rt) for rt in raw_tags if normalize_activity_tag(rt) }

def row_stage_norm_set(raw_tag_field: str) -> set[str]:
    raw_tags = parse_tags_field_clean(raw_tag_field)
    return { normalize_stage_tag(rt) for rt in raw_tags if normalize_stage_tag(rt) }

# ---------------------------- Derived Columns ----------------------------
df["__funding_bucket"] = df[COLS["FUNDING"]].apply(funding_bucket)
df["__fresh_days"]     = df[COLS["LAST_CHECKED"]].apply(days_since)

# Numeric amounts parsed
mins, maxs = [], []
for txt in df[COLS["FUNDING"]].astype(str).tolist():
    mn, mx = amount_min_max(txt)
    mins.append(mn)
    maxs.append(mx)
df["__amt_min"] = mins
df["__amt_max"] = maxs

if df[COLS["KEY"]].isna().any():
    df[COLS["KEY"]] = (
        df[COLS["PROGRAM_NAME"]].fillna("").astype(str).str.lower().str.replace(r"[^a-z0-9]+","",regex=True)
        + "|" +
        df[COLS["ORG_NAME"]].fillna("").astype(str).str.lower().str.replace(r"[^a-z0-9]+","",regex=True)
    )

df["__activity_norm_set"] = df[COLS["TAGS"]].fillna("").astype(str).apply(row_activity_norm_set)
df["__stage_norm_set"]    = df[COLS["TAGS"]].fillna("").astype(str).apply(row_stage_norm_set)
df["__fund_type_set"]     = df[COLS["TAGS"]].fillna("").astype(str).apply(detect_funding_types_from_tags)

# ---------------------------- Sidebar Filters ----------------------------
st.sidebar.header("Filters")

REGION_CHOICES = ["Calgary","Edmonton","Rural Alberta","Canada"]
FUNDING_TYPE_CHOICES = ["Grant","Loan","Financing","Subsidy","Tax Credit","Credit"]
FUND_AMOUNT_CHOICES = ["Under 5K","5K–25K","25K–100K","100K–500K","500K+","Unknown / Not stated"]

# NEW: Detailed ranges (checkboxes) — dollars
DETAILED_AMOUNT_CHOICES = [
    ("< $5K", (0, 5_000)),
    ("$5K–$10K", (5_000, 10_000)),
    ("$10K–$25K", (10_000, 25_000)),
    ("$25K–$50K", (25_000, 50_000)),
    ("$50K–$100K", (50_000, 100_000)),
    ("$100K–$250K", (100_000, 250_000)),
    ("$250K–$500K", (250_000, 500_000)),
    (">$500K", (500_000, float("inf"))),
]

# Controls (Fixed fuzziness)
FUZZY_THR = 70

sort_mode = st.sidebar.selectbox("Sort results by", ["Relevance","Program Name (A–Z)","Last Checked (newest)"], index=0)
page_size = st.sidebar.selectbox("Results per page", [10, 25, 50], index=1)

# REGION matching
REGION_MATCH_TABLE = {
    "Calgary": ["calgary", "southern alberta", "foothills"],
    "Edmonton": ["edmonton", "capital region", "central alberta"],
    "Rural Alberta": ["rural", "north", "northern alberta", "east central", "south", "southern alberta", "central alberta", "mountain view", "parkland"],
    "Canada": ["canada", "national", "federal", "pan-canadian", "international"],
}

def region_match(region_value: str, selected: str) -> bool:
    if not selected or selected == "All Regions": return True
    if not isinstance(region_value, str): return False
    v = region_value.lower()
    return any(word in v for word in REGION_MATCH_TABLE.get(selected, []))

# ---------------------------- Faceted counts & rendering ----------------------------
def count_by_option(series_of_sets: pd.Series):
    freq = {}
    for S in series_of_sets:
        for v in S:
            freq[v] = freq.get(v, 0) + 1
    return freq

def fuzzy_mask(df_in, q_text, threshold=70):
    if not q_text: return pd.Series([True]*len(df_in), index=df_in.index)
    cols = [COLS["PROGRAM_NAME"], COLS["ORG_NAME"], COLS["DESC"], COLS["ELIG"], COLS["TAGS"]]
    blobs = (df_in[cols].fillna("").astype(str).agg(" ".join, axis=1).str.lower())
    return blobs.apply(lambda blob: fuzz.partial_ratio(q_text.lower(), blob) >= threshold)

def filtered_except(df_in, q_text, selected_regions, selected_ftypes, selected_famts, selected_stage, selected_activity, selected_detailed_ranges, *, except_dim):
    out = df_in.copy()
    # search
    if q_text:
        mask = fuzzy_mask(out, q_text, threshold=FUZZY_THR)
        out = out[mask]

    if except_dim != "region":
        if selected_regions:
            col = out[COLS["REGION"]].astype(str)
            out = out[col.apply(lambda v: any(region_match(v, r) for r in selected_regions))]

    # Apply either detailed ranges or buckets
    if except_dim != "famt":
        if selected_detailed_ranges:
            def overlaps_any(row):
                mn, mx = row["__amt_min"], row["__amt_max"]
                if mn is None and mx is None:
                    return False
                for (lo, hi) in selected_detailed_ranges:
                    # overlap if any intersection
                    if (mn is not None and hi >= mn) and (mx is not None and lo <= mx):
                        return True
                return False
            out = out[out.apply(overlaps_any, axis=1)]
        else:
            if selected_famts:
                out = out[out["__funding_bucket"].isin(selected_famts)]

    if except_dim != "ftype":
        if selected_ftypes:
            out = out[out["__fund_type_set"].apply(lambda s: bool(s & selected_ftypes))]

    if except_dim != "stage":
        if selected_stage:
            out = out[out["__stage_norm_set"].apply(lambda s: bool(s & selected_stage))]

    if except_dim != "activity":
        if selected_activity:
            out = out[out["__activity_norm_set"].apply(lambda s: bool(s & selected_activity))]

    return out

# ---------------------------- Search & Gather ----------------------------
q = st.text_input("🔍 Search programs", "", key="q", placeholder="Try 'grant', 'mentorship', or 'startup'…")
st.caption("Tip: Search matches similar terms (e.g., typing **mentor** finds **mentorship**).")

# Option lists (present ones)
all_activity_norm = sorted({ v for S in df["__activity_norm_set"] for v in S })
all_stage_norm    = sorted({ v for S in df["__stage_norm_set"] for v in S })

# Pull current selections from session
selected_regions  = {opt for opt in REGION_CHOICES if st.session_state.get(f"region_{opt}")}
selected_ftypes   = {opt for opt in FUNDING_TYPE_CHOICES if st.session_state.get(f"ftype_{opt}")}
selected_famts    = {opt for opt in FUND_AMOUNT_CHOICES if st.session_state.get(f"famt_{opt}")}
selected_stage    = {opt for opt in all_stage_norm if st.session_state.get(f"stage_{opt}")}
selected_activity = {opt for opt in all_activity_norm if st.session_state.get(f"activity_{opt}")}

# Detailed ranges UI
st.sidebar.markdown("**Funding (Detailed Amounts)**")
selected_detailed_ranges = []
# toggle: only records with numeric amounts
only_numeric = st.sidebar.checkbox("Only show programs with a numeric amount", value=False)
for label, (lo, hi) in DETAILED_AMOUNT_CHOICES:
    if st.sidebar.checkbox(label, key=f"damount_{label}"):
        selected_detailed_ranges.append((lo, hi))

# Optional custom range if no checkboxes used
with st.sidebar.expander("Custom amount range (CAD)", expanded=False):
    # Determine dataset min/max for guidance
    global_min = int(pd.Series([v for v in df["__amt_min"].dropna()]).min()) if pd.notna(df["__amt_min"]).any() else 0
    global_max = int(pd.Series([v for v in df["__amt_max"].dropna()]).max()) if pd.notna(df["__amt_max"]).any() else 1_000_000
    min_in = st.number_input("Min", min_value=0, value=max(0, global_min//1000*1000), step=1000)
    max_in = st.number_input("Max", min_value=min_in, value=min(global_max//1000*1000, 1_000_000), step=1000)
    if st.button("Apply custom amount range"):
        selected_detailed_ranges.append((float(min_in), float(max_in)))

# Faceted datasets (for counts) — pass detailed ranges
df_except_region   = filtered_except(df, q, selected_regions, selected_ftypes, selected_famts, selected_stage, selected_activity, selected_detailed_ranges, except_dim="region")
df_except_ftype    = filtered_except(df, q, selected_regions, selected_ftypes, selected_famts, selected_stage, selected_activity, selected_detailed_ranges, except_dim="ftype")
df_except_famt     = filtered_except(df, q, selected_regions, selected_ftypes, selected_famts, selected_stage, selected_activity, selected_detailed_ranges, except_dim="famt")
df_except_stage    = filtered_except(df, q, selected_regions, selected_ftypes, selected_famts, selected_stage, selected_activity, selected_detailed_ranges, except_dim="stage")
df_except_activity = filtered_except(df, q, selected_regions, selected_ftypes, selected_famts, selected_stage, selected_activity, selected_detailed_ranges, except_dim="activity")

region_counts = {}
for r in REGION_CHOICES:
    col = df_except_region[COLS["REGION"]].astype(str)
    region_counts[r] = int(col.apply(lambda v: region_match(v, r)).sum())

ftype_counts = {}
for f in FUNDING_TYPE_CHOICES:
    ftype_counts[f] = int(df_except_ftype["__fund_type_set"].apply(lambda s, f=f: f in s).sum())

famt_counts = df_except_famt["__funding_bucket"].value_counts().to_dict()
stage_counts = count_by_option(df_except_stage["__stage_norm_set"])
activity_counts = count_by_option(df_except_activity["__activity_norm_set"])

def render_filter_checklist(label, options, counts, state_prefix):
    picked = set()
    with st.sidebar.expander(label, expanded=False):
        if st.button("Clear", key=f"clear_{state_prefix}"):
            for opt in options:
                st.session_state[f"{state_prefix}_{opt}"] = False
        for opt in options:
            c = counts.get(opt, 0)
            disabled = c == 0
            val = st.checkbox(f"{opt} ({c})", key=f"{state_prefix}_{opt}", disabled=disabled)
            if val and not disabled:
                picked.add(opt)
    return picked

# Render filters
sel_regions  = render_filter_checklist("Region", REGION_CHOICES, region_counts, "region")
sel_ftypes   = render_filter_checklist("Funding (Type)", FUNDING_TYPE_CHOICES, ftype_counts, "ftype")
sel_famts    = render_filter_checklist("Funding (Amount – Buckets)", FUND_AMOUNT_CHOICES, famt_counts, "famt")
sel_stage    = render_filter_checklist("Business Stage", all_stage_norm, stage_counts, "stage")
sel_activity = render_filter_checklist("Activity", all_activity_norm, activity_counts, "activity")

# Update selected sets
selected_regions, selected_ftypes, selected_famts = sel_regions, sel_ftypes, sel_famts
selected_stage, selected_activity = sel_stage, sel_activity

# Global clear-all
if st.sidebar.button("Clear all filters"):
    for k in list(st.session_state.keys()):
        if any(k.startswith(prefix) for prefix in ("region_","ftype_","famt_","stage_","activity_","damount_")):
            st.session_state[k] = False
    st.session_state["q"] = ""
    st.experimental_rerun()

# ---------------------------- Apply Filters ----------------------------
def apply_filters(df_in: pd.DataFrame) -> pd.DataFrame:
    out = df_in.copy()
    out = out[fuzzy_mask(out, q, threshold=FUZZY_THR)]
    if selected_regions and COLS["REGION"] in out.columns:
        col = out[COLS["REGION"]].astype(str)
        out = out[col.apply(lambda v: any(region_match(v, r) for r in selected_regions))]
    # Amounts: detailed overrides buckets if any selected
    if selected_detailed_ranges:
        def overlaps_any(row):
            mn, mx = row["__amt_min"], row["__amt_max"]
            if only_numeric and (mn is None and mx is None):
                return False
            if mn is None and mx is None:
                return False
            for (lo, hi) in selected_detailed_ranges:
                if (mn is not None and hi >= mn) and (mx is not None and lo <= mx):
                    return True
            return False
        out = out[out.apply(overlaps_any, axis=1)]
    else:
        if selected_famts:
            out = out[out["__funding_bucket"].isin(selected_famts)]
        if only_numeric:
            out = out[out["__amt_min"].notna() | out["__amt_max"].notna()]
    # Funding type (normalized)
    if selected_ftypes:
        out = out[out["__fund_type_set"].apply(lambda s: bool(s & selected_ftypes))]
    # Stage (normalized)
    if selected_stage:
        out = out[out["__stage_norm_set"].apply(lambda s: bool(s & selected_stage))]
    # Activity (normalized)
    if selected_activity:
        out = out[out["__activity_norm_set"].apply(lambda s: bool(s & selected_activity))]
    return out

filtered = apply_filters(df)

# ---------------------------- Sort & Pagination ----------------------------
def sort_df(dfin: pd.DataFrame) -> pd.DataFrame:
    if sort_mode == "Program Name (A–Z)":
        return dfin.sort_values(COLS["PROGRAM_NAME"].replace("\\\\",""), na_position="last", kind="mergesort")
    if sort_mode == "Last Checked (newest)":
        tmp = dfin.copy()
        tmp["__dt"] = pd.to_datetime(tmp[COLS["LAST_CHECKED"]], errors="coerce")
        return tmp.sort_values("__dt", ascending=False, na_position="last", kind="mergesort").drop(columns="__dt")
    return dfin

filtered = sort_df(filtered)

st.markdown(f"### {len(filtered)} Programs Found")

# ---------------------------- Clickable Chips ----------------------------
def render_chips():
    chips = []
    if q: chips.append(("Search", q, "search", None))
    for r in sorted(selected_regions): chips.append(("Region", r, "region", r))
    for f in sorted(selected_ftypes): chips.append(("Funding Type", f, "ftype", f))
    for a in sorted(selected_activity): chips.append(("Activity", a, "activity", a))
    for s in sorted(selected_stage): chips.append(("Stage", s, "stage", s))
    for b in sorted(selected_famts): chips.append(("Amount", b, "famt", b))
    if selected_detailed_ranges:
        chips.append(("Amount (detailed)", f"{len(selected_detailed_ranges)} selected", "damount", "any"))
    if only_numeric:
        chips.append(("Amount", "Numeric only", "numeric_only", "1"))

    if not chips:
        return

    st.write("")
    row_cols = 5
    idx = 0
    while idx < len(chips):
        cols = st.columns(row_cols)
        for c in range(row_cols):
            if idx >= len(chips): break
            (k, v, prefix, opt) = chips[idx]
            label = f"{k}: {v}  ✕"
            if cols[c].button(label, key=f"chip_{prefix}_{opt or 'q'}"):
                if prefix == "search":
                    st.session_state["q"] = ""
                elif prefix in ("region","ftype","famt","stage","activity"):
                    if opt is not None:
                        st.session_state[f"{prefix}_{opt}"] = False
                elif prefix == "damount":
                    # clear all detailed range checkboxes
                    for (lab, _) in DETAILED_AMOUNT_CHOICES:
                        st.session_state[f"damount_{lab}"] = False
                elif prefix == "numeric_only":
                    # toggle off numeric only
                    st.session_state["Amount_Numeric_Only_tmp"] = False  # a no-op visual
                st.experimental_rerun()
            idx += 1

render_chips()

# Export current view
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download results (CSV)", csv_bytes, file_name="pathfinding_results.csv", mime="text/csv")

# Pagination
total = len(filtered)
if "page_idx" not in st.session_state:
    st.session_state.page_idx = 0
max_page = max(0, (total - 1) // page_size)
page = min(st.session_state.page_idx, max_page)
start = page * page_size
end = min(start + page_size, total)
if total > 0:
    st.caption(f"Showing {start+1}-{end} of {total}")

prev_col, mid_col, next_col = st.columns([0.1,0.8,0.1])
with prev_col:
    if st.button("◀ Prev", disabled=page==0):
        st.session_state.page_idx = max(0, page - 1)
        st.experimental_rerun()
with next_col:
    if st.button("Next ▶", disabled=page>=max_page):
        st.session_state.page_idx = min(max_page, page + 1)
        st.experimental_rerun()

# ---------------------------- Results ----------------------------
if "favorites" not in st.session_state:
    st.session_state.favorites = set()

def status_class_and_label(s: str):
    s_low = (s or "").lower()
    if "operational" in s_low:
        return "operational", s or "Operational"
    if any(k in s_low for k in ["open","active","ongoing","accepting","rolling"]):
        return "open", s or "Open"
    return "closed", s or "Closed / Paused"

UNKNOWN = "unknown / not stated"

subset = filtered.iloc[start:end].copy()
for i, (_, row) in enumerate(subset.iterrows(), 1):
    name   = str(row[COLS["PROGRAM_NAME"]] or "")
    org    = str(row[COLS["ORG_NAME"]] or "")
    status_raw = str(row[COLS["STATUS"]] or "")
    badge_cls, badge_label = status_class_and_label(status_raw)
    desc_full = str(row[COLS["DESC"]] or "").strip()
    desc = (desc_full[:240] + "…") if len(desc_full) > 240 else desc_full
    elig = str(row[COLS["ELIG"]] or "").strip()
    fund_bucket = str(row.get("__funding_bucket") or "")
    fresh = freshness_label(row.get("__fresh_days"))

    website = str(row.get(COLS["WEBSITE"]) or "").strip()
    email   = str(row.get(COLS["EMAIL"]) or "").strip().lower()
    phone   = str(row.get(COLS["PHONE"]) or "").strip()
    key     = str(row.get(COLS["KEY"], f"k{i}"))

    st.markdown(
        f"<div class='card'>"
        f"<span class='badge {badge_cls}'>{badge_label}</span>"
        f"<span class='meta'>Last checked: {fresh}</span>"
        f"<div class='title'>{name}</div>"
        f"<div class='org'>{org}</div>"
        f"<p>{desc or '<span class=\"placeholder\">No description provided.</span>'}</p>",
        unsafe_allow_html=True
    )

    fund_label = ""
    if fund_bucket and fund_bucket.strip().lower() != UNKNOWN:
        fund_label = add_dollar_signs(fund_bucket)
    fund_line = f'<span class="kv"><strong>Funding:</strong> {fund_label}</span>' if fund_label else ""

    elig_line = ""
    if elig and elig.strip().lower() != UNKNOWN and len(elig.strip()) > 2 and elig.strip().lower() not in {"n/a","na"}:
        elig_line = f'<span class="kv"><strong>Eligibility:</strong> {elig}</span>'

    left_html = " ".join(x for x in [fund_line, elig_line] if x) or "<span class='placeholder'>No additional details</span>"

    link_parts = []
    if website:
        url = website if website.startswith(("http://","https://")) else f"https://{website}"
        link_parts.append(f'<a href="{url}" target="_blank" rel="noopener">Website</a>')
    if email:
        link_parts.append(f'<a href="mailto:{email}">Email</a>')
    if phone:
        link_parts.append(f'<a href="tel:{phone}">Call</a>')
    links_html = f'<div class="links">{" ".join(link_parts)}</div>' if link_parts else ""

    st.markdown(f"<div class='info-row'><div class='info-left'>{left_html}</div><div class='info-right'>", unsafe_allow_html=True)
    if links_html:
        st.markdown(links_html, unsafe_allow_html=True)

    fav_on = key in st.session_state.favorites
    fav_label = "★ Favourite" if fav_on else "☆ Favourite"
    clicked = st.button(fav_label, key=f"fav_{key}")
    st.markdown("</div></div>", unsafe_allow_html=True)

    if clicked:
        if fav_on:
            st.session_state.favorites.remove(key)
        else:
            st.session_state.favorites.add(key)
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if len(desc_full) > 240:
        with st.expander("More details"):
            st.markdown(f"**Full description:** {desc_full}")
