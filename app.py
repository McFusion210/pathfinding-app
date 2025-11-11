# app.py — Alberta Pathfinding Tool (Streamlit)
# Implements: EF inside cards, inline links + favourite, split Stage/Activity, no closed/paused filter,
# last-checked in card, green "Operational" badge, resilient column mapping.

import os, re
from pathlib import Path
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# ---------------------------- Page & Styles ----------------------------
st.set_page_config(page_title="Alberta Pathfinding Tool – Small Business Supports", layout="wide")

st.markdown("""
<style>
:root {
  --bg:#F7F8FA; --surface:#FFFFFF; --text:#0B0C0C; --muted:#5F6B7A;
  --primary:#002D72; --border:#E3E7ED; --link:#005AA0;
  --fs-title:24px; --fs-body:16px; --fs-meta:14px;
}
[data-testid="stAppViewContainer"] .main .block-container { padding-top: 1rem !important; }
html, body, p, div, span { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Segoe UI Emoji"; color: var(--text); }

.header {
  display:flex; align-items:center; gap:14px;
  background:#F6F8FA; border-bottom:2px solid #006FCF;
  padding:12px 20px; border-radius:8px; margin:8px 0 16px 0;
}
.header h2 { margin:0; color:#002D72; font-weight:800; font-size:28px; }
.header p  { margin:0; color:#333; font-size:15px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius:16px;
  padding:16px;
  box-shadow:0 1px 2px rgba(0,0,0,0.04);
  margin-bottom:16px;
}
.title { margin:4px 0 6px 0; font-weight:800; color:#002D72; font-size: var(--fs-title); }
.org, .meta { color:var(--muted); font-size: var(--fs-meta); }
.meta { margin-left:8px; }
.placeholder { color:#8893a0; font-style:italic; }

/* Status badges */
.badge { display:inline-block; font-size:12px; padding:4px 10px; border-radius:999px; margin-right:6px; }
.badge.operational { background:#E6F4EA; color:#0F5132; border:1px solid #B7E1C4; }  /* green */
.badge.open        { background:#EAF2FF; color:#003B95; border:1px solid #CFE1FF; }
.badge.closed      { background:#FDECEE; color:#842029; border:1px solid #F5C2C7; }

/* Info row right under the description */
.info-row{
  display:flex; align-items:center; gap:16px; flex-wrap:wrap;
  margin-top:10px; padding-top:10px; border-top:1px solid var(--border);
}
.info-left{ display:flex; align-items:center; gap:18px; font-size: var(--fs-body); }
.kv strong{ font-weight:700; }

.info-right{ margin-left:auto; display:flex; align-items:center; gap:14px; }
.links a{ color: var(--link); text-decoration: underline; font-size: var(--fs-body); }
.links a + a{ margin-left:12px; }

.info-right .stButton>button{
  padding:6px 10px; border:1px solid var(--border);
  border-radius:12px; background:#fff; font-size: var(--fs-body);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
  <img src="assets/GoA-logo.png" alt="Government of Alberta" style="height:48px;">
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

# ---------------------------- Load Data (resilient) ----------------------------
df = pd.read_excel(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

def map_col(name_hint: str, fallbacks: list[str]) -> str | None:
    for c in df.columns:
        if name_hint.lower() in str(c).lower():
            return c
    for fb in fallbacks:
        if fb in df.columns:
            return fb
    return None

COLS = {
    "PROGRAM_NAME": map_col("program name", ["Program Name"]),
    "ORG_NAME":     map_col("organization name", ["Organization Name"]),
    "DESC":         map_col("program description", ["Program Description"]),
    "ELIG":         map_col("eligibility", ["Eligibility Description", "Eligibility"]),
    "EMAIL":        map_col("email", ["Email Address"]),
    "PHONE":        map_col("phone", ["Phone Number"]),
    "WEBSITE":      map_col("website", ["Program Website","Website"]),
    "REGION":       map_col("region", ["Geographic Region","Region"]),
    "TAGS":         map_col("meta", ["Meta Tags","Tags"]),
    "FUNDING":      map_col("funding amount", ["Funding Amount","Funding"]),
    "STATUS":       map_col("operational status", ["Operational Status","Status"]),
    "LAST_CHECKED": map_col("last checked", ["Last Checked (MT)","Last Checked"]),
    "KEY":          map_col("_key_norm", ["_key_norm","Key"]),
}

# Ensure referenced columns exist to avoid KeyErrors
for k, v in COLS.items():
    if v is None or v not in df.columns:
        new_name = f"__missing_{k}"
        df[new_name] = ""
        COLS[k] = new_name

def parse_tags_field(s):
    if not isinstance(s, str): return []
    parts = re.split(r"[;,/|]", s)
    return [p.strip().lower() for p in parts if p.strip()]

def funding_bucket(amount):
    s = str(amount or "").replace(",", "")
    nums = re.findall(r"\d+\.?\d*", s)
    if not nums: return "Unknown / Not stated"
    try:
        val = float(nums[-1])
    except ValueError:
        return "Unknown / Not stated"
    if val < 5000: return "Under $5K"
    if val < 25000: return "$5K–$25K"
    if val < 100000: return "$25K–$100K"
    if val < 500000: return "$100K–$500K"
    return "$500K+"

df["__funding_bucket"] = df[COLS["FUNDING"]].apply(funding_bucket)

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

df["__fresh_days"] = df[COLS["LAST_CHECKED"]].apply(days_since)

# Fallback for missing keys
if df[COLS["KEY"]].isna().any():
    df[COLS["KEY"]] = (
        df[COLS["PROGRAM_NAME"]].fillna("").astype(str).str.lower().str.replace(r"[^a-z0-9]+","",regex=True)
        + "|" +
        df[COLS["ORG_NAME"]].fillna("").astype(str).str.lower().str.replace(r"[^a-z0-9]+","",regex=True)
    )

# ---------------------------- Sidebar Filters ----------------------------
st.sidebar.header("Filters")

REGION_CHOICES = ["Calgary","Edmonton","Rural Alberta","Canada"]
FUNDING_TYPE_CHOICES = ["Grant","Loan","Financing","Subsidy","Tax Credit","Credit"]
FUND_AMOUNT_CHOICES = ["Under $5K","$5K–$25K","$25K–$100K","$100K–$500K","$500K+","Unknown / Not stated"]

def sb_multi(label, options, key_prefix):
    picked = set()
    with st.sidebar.expander(label, expanded=False):
        for opt in options:
            v = st.checkbox(opt, key=f"{key_prefix}_{opt}")
            if v: picked.add(opt)
    return picked

sel_regions = sb_multi("Region", REGION_CHOICES, "region")
sel_ftypes  = sb_multi("Funding (Type)", FUNDING_TYPE_CHOICES, "ftype")
sel_famts   = sb_multi("Funding (Amount)", FUND_AMOUNT_CHOICES, "famt")

# Split Stage vs Activity from tags
def tags_by_category(df_in, cat_keywords):
    result = set()
    for s in df_in[COLS["TAGS"]].dropna().astype(str):
        tlist = parse_tags_field(s)
        for t in tlist:
            if any(k in t for k in cat_keywords):
                result.add(t)
    return sorted(result)

stage_tags    = tags_by_category(df, ["startup","scale","scaleup"])
activity_tags = tags_by_category(df, ["export","research","training","innovation","cohort","workshop","mentorship","mentor","accelerator","advis","advisory","coaching","network"])

sel_stage    = sb_multi("Business Stage", [t.title() for t in stage_tags], "stage")
sel_activity = sb_multi("Activity",       [t.title() for t in activity_tags], "activity")

q = st.text_input("🔍 Search programs", "")

# ---------------------------- Filter Logic ----------------------------
def fuzzy_mask(df_in, q_text, threshold=70):
    if not q_text: return pd.Series([True]*len(df_in), index=df_in.index)
    cols = [COLS["PROGRAM_NAME"], COLS["ORG_NAME"], COLS["DESC"], COLS["ELIG"], COLS["TAGS"]]
    out = []
    for _, row in df_in[cols].fillna("").astype(str).iterrows():
        blob = " ".join([row[c] for c in cols]).lower()
        out.append(fuzz.partial_ratio(q_text.lower(), blob) >= threshold)
    return pd.Series(out, index=df_in.index)

def region_match(region_value: str, selected: str) -> bool:
    if not selected or selected == "All Regions": return True
    if not isinstance(region_value, str): return False
    v = region_value.lower()
    table = {
        "Calgary": ["calgary", "southern alberta"],
        "Edmonton": ["edmonton", "central alberta"],
        "Rural Alberta": ["rural", "northern alberta", "southern alberta", "central alberta"],
        "Canada": ["canada", "national", "federal", "international"],
    }
    return any(word in v for word in table.get(selected, []))

def has_any_tag(s, choices_lower: set[str]) -> bool:
    if not choices_lower: return True
    tags = set(parse_tags_field(s))
    return bool(tags & choices_lower)

def apply_filters(df_in: pd.DataFrame) -> pd.DataFrame:
    out = df_in.copy()

    # No status filter (always populate)

    # Search
    out = out[fuzzy_mask(out, q, threshold=70)]

    # Region (guarded)
    if sel_regions and COLS["REGION"] in out.columns:
        col = out[COLS["REGION"]].astype(str)
        out = out[col.apply(lambda v: any(region_match(v, r) for r in sel_regions))]

    # Funding amount
    if sel_famts:
        out = out[out["__funding_bucket"].isin(sel_famts)]

    # Funding type (from tags)
    if sel_ftypes:
        ft_lower = {t.lower() for t in sel_ftypes}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, ft_lower))]

    # Stage and Activity (separate)
    if sel_stage:
        stg_lower = {t.lower() for t in sel_stage}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, stg_lower))]
    if sel_activity:
        act_lower = {t.lower() for t in sel_activity}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, act_lower))]

    return out

filtered = apply_filters(df)

# ---------------------------- Results ----------------------------
st.markdown(f"### {len(filtered)} Programs Found")

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

for i, (_, row) in enumerate(filtered.iterrows(), 1):
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
    email   = str(row.get(COLS["EMAIL"]) or "").strip()
    phone   = str(row.get(COLS["PHONE"]) or "").strip()
    key     = str(row.get(COLS["KEY"], f"k{i}"))

    # Card header & description
    st.markdown(
        f"<div class='card'>"
        f"<span class='badge {badge_cls}'>{badge_label}</span>"
        f"<span class='meta'>Last checked: {fresh}</span>"
        f"<div class='title'>{name}</div>"
        f"<div class='org'>{org}</div>"
        f"<p>{desc or '<span class=\"placeholder\">No description provided.</span>'}</p>",
        unsafe_allow_html=True
    )

    # Build Funding + Eligibility (omit if empty/unknown)
    fund_line = ""
    elig_line = ""
    if fund_bucket and fund_bucket.strip().lower() != UNKNOWN:
        fund_line = f'<span class="kv"><strong>Funding:</strong> {fund_bucket}</span>'
    if elig and elig.strip().lower() != UNKNOWN:
        elig_line = f'<span class="kv"><strong>Eligibility:</strong> {elig}</span>'
    left_html = " ".join(x for x in [fund_line, elig_line] if x) or "<span class='placeholder'>No additional details</span>"

    # Right side links
    link_parts = []
    if website: link_parts.append(f'<a href="{website}" target="_blank" rel="noopener">Website</a>')
    if email:   link_parts.append(f'<a href="mailto:{email}">Email</a>')
    if phone:   link_parts.append(f'<a href="tel:{phone}">Call</a>')
    links_html = f'<div class="links">{" ".join(link_parts)}</div>' if link_parts else ""

    # Single info row: left (fund/elig) · right (links + favourite)
    col_left, col_right = st.columns([0.68, 0.32], gap="small")
    with col_left:
        st.markdown(f'<div class="info-row"><div class="info-left">{left_html}</div>', unsafe_allow_html=True)
    with col_right:
        st.markdown(f'<div class="info-right">{links_html}', unsafe_allow_html=True)
        fav_on = key in st.session_state.favorites
        fav_label = "★ Favourite" if fav_on else "☆ Favourite"
        clicked = st.button(fav_label, key=f"fav_{key}")
        st.markdown("</div>", unsafe_allow_html=True)  # close .info-right
        if clicked:
            if fav_on:
                st.session_state.favorites.remove(key)
            else:
                st.session_state.favorites.add(key)
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)      # close .info-row
    st.markdown("</div>", unsafe_allow_html=True)      # close .card

    # Optional expander if long description
    if len(desc_full) > 240:
        with st.expander("More details"):
            st.markdown(f"**Full description:** {desc_full}")
