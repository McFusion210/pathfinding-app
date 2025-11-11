# app.py — Alberta Pathfinding Tool (Streamlit)
# Clean rebuild: resilient column mapping, safe filters, tidy layout, bottom text links.

import os, re
from datetime import datetime
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
.badge { display:inline-block; font-size:12px; padding:4px 8px; border-radius:999px; margin-bottom:8px; }
.badge.open { background:#E6F4EA; color:#0F5132; }
.badge.closed { background:#FDECEE; color:#842029; }
.org { color:var(--muted); margin-bottom:8px; font-size: var(--fs-meta); }
.tags { color:var(--muted); font-size: var(--fs-meta); margin-left:8px; }
.placeholder { color:#8893a0; font-style:italic; }
.ef { font-size: var(--fs-body); margin:6px 0 2px 0; }
.ef strong { font-weight:700; }

.link-row { display:flex; align-items:center; gap: 18px; margin-top: 10px; }
.link-row a { color: var(--link); text-decoration: underline; font-size: var(--fs-body); }
.title { margin:4px 0 6px 0; font-weight:800; color:#002D72; font-size: var(--fs-title); }
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

# ---------------------------- Config & Secrets ----------------------------
ADMIN_PASS = st.secrets.get("APP_ADMIN_PASS", os.environ.get("APP_ADMIN_PASS", ""))  # optional
DATA_FILE  = st.secrets.get("DATA_FILE", "Pathfinding_Master.xlsx")

if not Path(DATA_FILE).exists():
    st.info("Upload **Pathfinding_Master.xlsx** to the repository root and rerun.")
    st.stop()

# ---------------------------- Load Data (resilient) ----------------------------
df = pd.read_excel(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

def map_col(name_hint: str, fallbacks: list[str]) -> str | None:
    """Find a column whose header contains name_hint (case-insensitive), else first fallback that exists."""
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
    "CONTACT":      map_col("contact page", ["Contact Page (Derived)","Contact"]),
    "LAST_CHECKED": map_col("last checked", ["Last Checked (MT)","Last Checked"]),
    "KEY":          map_col("_key_norm", ["_key_norm","Key"]),
}

# ensure any missing referenced columns exist (as empty strings), so no KeyErrors
for k, v in COLS.items():
    if v is None or v not in df.columns:
        new_name = f"__missing_{k}"
        df[new_name] = ""
        COLS[k] = new_name

# helpers
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

def is_open(status):
    s = str(status or "").lower()
    return any(k in s for k in ["open", "active", "ongoing", "accepting", "rolling"])

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

# keys (fallback)
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
FUND_AMOUNT_CHOICES = ["Under $5k","$5k–$25k","$25–$100k","$100K–$500K","$500K+","Unknown / Not stated"]

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

# dynamic tag filters (optional: Group/Sector/Stage/Supports) — safe even if TAGS missing/empty
def tags_by_category(df_in, cat_keywords):
    result = set()
    for s in df_in[COLS["TAGS"]].dropna().astype(str):
        tlist = parse_tags_field(s)
        for t in tlist:
            if any(k in t for k in cat_keywords):
                result.add(t)
    return sorted(result)

group_tags   = tags_by_category(df, ["women","youth","indigenous","black","newcomer","immigrant","veteran","disab","bipoc","minority","racial","lgbt"])
sector_tags  = tags_by_category(df, ["agri","energy","oil","clean","ict","tech","manufact","food","construct","transport","tourism","life","forestry","mining","creative","retail","aero"])
stage_tags   = tags_by_category(df, ["startup","scale","export","research","training","innovation"])
support_tags = tags_by_category(df, ["mentor","advis","coach","accelerator","workshop","network"])

sel_groups   = sb_multi("Audience / Priority", [t.title() for t in group_tags], "group")
sel_sectors  = sb_multi("Sector / Industry",  [t.title() for t in sector_tags], "sector")
sel_stage    = sb_multi("Business Stage / Activity", [t.title() for t in stage_tags], "stage")
sel_supports = sb_multi("Supports", [t.title() for t in support_tags], "support")

q = st.text_input("🔍 Search programs", "")

include_closed = st.checkbox("Include Closed / Paused", value=False)

# ---------------------------- Filter Logic (resilient) ----------------------------
def fuzzy_mask(df_in, q_text, threshold=70):
    if not q_text: return pd.Series([True]*len(df_in), index=df_in.index)
    cols = [COLS["PROGRAM_NAME"], COLS["ORG_NAME"], COLS["DESC"], COLS["ELIG"], COLS["TAGS"]]
    out = []
    for _, row in df_in[cols].fillna("").astype(str).iterrows():
        blob = " ".join([row[c] for c in cols]).lower()
        out.append(fuzz.partial_ratio(q_text.lower(), blob) >= threshold)
    return pd.Series(out, index=df_in.index)

def region_match(region_value: str, selected: str) -> bool:
    """Map textual region to buckets; robust to missing/unknown."""
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

    # status
    if not include_closed:
        out = out[out[COLS["STATUS"]].apply(is_open)]

    # search
    out = out[fuzzy_mask(out, q, threshold=70)]

    # region — only if the mapped column truly exists (we created a filler if not)
    # region (guarded)
if sel_regions and COLS["REGION"] in out.columns:
    col = out[COLS["REGION"]].astype(str)
    out = out[col.apply(lambda v: any(region_match(v, r) for r in sel_regions))]
# absolute safety: create an empty region column if still missing
if COLS["REGION"] not in df.columns:
    df[COLS["REGION"]] = ""


    # funding amount
    if sel_famts:
        out = out[out["__funding_bucket"].isin(sel_famts)]

    # funding type (from tags)
    if sel_ftypes:
        ft_lower = {t.lower() for t in sel_ftypes}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, ft_lower))]

    # dynamic tag buckets (these are title-cased in UI, convert back to lower for match)
    if sel_groups:
        grp_lower = {t.lower() for t in sel_groups}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, grp_lower))]
    if sel_sectors:
        sec_lower = {t.lower() for t in sel_sectors}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, sec_lower))]
    if sel_stage:
        stg_lower = {t.lower() for t in sel_stage}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, stg_lower))]
    if sel_supports:
        sup_lower = {t.lower() for t in sel_supports}
        out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: has_any_tag(s, sup_lower))]

    return out

filtered = apply_filters(df)

# ---------------------------- Chips for Active Filters ----------------------------
def render_chips():
    chosen = []
    for s in [sel_regions, sel_ftypes, sel_famts, sel_groups, sel_sectors, sel_stage, sel_supports]:
        chosen.extend(sorted(list(s)))
    if not chosen: return
    st.write("")
    cols = st.columns(min(6, len(chosen)))
    for i, label in enumerate(chosen):
        with cols[i % len(cols)]:
            st.button(f"{label} ✕", key=f"chip_{i}")

render_chips()

# ---------------------------- Results & Cards ----------------------------
st.markdown(f"### {len(filtered)} Programs Found")

if "favorites" not in st.session_state:
    st.session_state.favorites = set()

for i, (_, row) in enumerate(filtered.iterrows(), 1):
    name   = str(row[COLS["PROGRAM_NAME"]] or "")
    org    = str(row[COLS["ORG_NAME"]] or "")
    status = str(row[COLS["STATUS"]] or "")
    status_cls = "open" if is_open(status) else "closed"
    desc_full = str(row[COLS["DESC"]] or "").strip()
    desc = (desc_full[:240] + "…") if len(desc_full) > 240 else desc_full
    elig = str(row[COLS["ELIG"]] or "").strip()
    fund = str(row.get("__funding_bucket") or "")
    fresh = freshness_label(row.get("__fresh_days"))

    website = str(row.get(COLS["WEBSITE"]) or "").strip()
    email   = str(row.get(COLS["EMAIL"]) or "").strip()
    phone   = str(row.get(COLS["PHONE"]) or "").strip()
    contact = str(row.get(COLS["CONTACT"]) or "").strip()
    key     = str(row.get(COLS["KEY"], f"k{i}"))

    # Card header & summary
    st.markdown(
        f"<div class='card'>"
        f"<span class='badge {status_cls}'>{status or '—'}</span>"
        f"<span class='tags'>Last checked: {fresh}</span>"
        f"<div class='title'>{name}</div>"
        f"<div class='org'>{org}</div>"
        f"<p>{desc or '<span class=\"placeholder\">No description provided.</span>'}</p>",
        unsafe_allow_html=True
    )

    # Eligibility & Funding (text under description)
    ef_html = f"""
    <div class='ef'><strong>Eligibility:</strong> {elig if elig else '<span class="placeholder">Not provided</span>'}</div>
    <div class='ef'><strong>Funding:</strong> {fund if fund else '<span class="placeholder">Unknown / Not stated</span>'}</div>
    """
    st.markdown(ef_html, unsafe_allow_html=True)

    # Expandable details as needed
    if len(desc_full) > 240 or not elig or not fund:
        with st.expander("More details"):
            st.markdown(f"**Full description:** {desc_full}" if desc_full else "_No description available._")
            st.markdown(f"**Eligibility:** {elig}" if elig else "_No eligibility details available._")
            st.markdown(f"**Funding:** {fund}" if fund else "_No funding information available._")

    # Bottom text hyperlinks
    links = []
    if website: links.append(f'<a href="{website}" target="_blank" rel="noopener">Website</a>')
    if email:   links.append(f'<a href="mailto:{email}">Email</a>')
    if phone:   links.append(f'<a href="tel:{phone}">Call</a>')
    if contact: links.append(f'<a href="{contact}" target="_blank" rel="noopener">Contact</a>')
    if links:
        st.markdown('<div class="link-row">' + " ".join(links) + '</div>', unsafe_allow_html=True)

    # Favorites toggle (simple)
    fav_on = key in st.session_state.favorites
    label = "★" if fav_on else "☆"
    if st.button(label, key=f"fav_{key}", help="Add/Remove favorite"):
        if fav_on:
            st.session_state.favorites.remove(key)
        else:
            st.session_state.favorites.add(key)
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------- Admin (Optional) ----------------------------
st.markdown("## Admin Insights")
def admin_gate():
    if not ADMIN_PASS:
        st.info("Admin password not configured. Set APP_ADMIN_PASS in `.streamlit/secrets.toml`.")
        return False
    k = "__admin_ok"
    if st.session_state.get(k): return True
    pwd = st.text_input("Enter admin password", type="password")
    if st.button("Unlock Admin"):
        if pwd == ADMIN_PASS:
            st.session_state[k] = True
            st.success("Admin unlocked")
            return True
        else:
            st.error("Incorrect password")
    return st.session_state.get(k, False)

if admin_gate():
    st.write("🔎 Basic insights coming soon (favorites, top searches, most used filters).")
