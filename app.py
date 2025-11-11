import os, re, math
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

st.set_page_config(
    page_title="Alberta Pathfinding Tool – Small Business Supports",
    layout="wide"
)
st.markdown("<style>div.block-container {padding-top: 0rem;}</style>", unsafe_allow_html=True)

# ---- Styles (GoA look) ----
st.markdown("""
<style>
:root {
  --bg:#F7F8FA; --surface:#FFFFFF; --text:#0B0C0C; --muted:#5F6B7A;
  --primary:#002D72; --primary-contrast:#FFFFFF; --border:#E3E7ED;
  --font-body: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
}
html, body { background: var(--bg); }
body, p, div, span {
  font-family: var(--font-body) !important;
  color: var(--text);
}

/* safe top padding so header isn't clipped */
[data-testid="stAppViewContainer"] .main .block-container { padding-top: 1rem !important; }

.header {
  display:flex; align-items:center; gap:14px;
  background:#F6F8FA; border-bottom:2px solid #006FCF;
  padding:12px 20px; border-radius:8px; margin:8px 0 16px 0;
}
.header h2 { margin:0; padding:0; color:#002D72; font-weight:700; }
.header p  { margin:0; color:#333; font-size:15px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius:16px;
  padding:16px;
  box-shadow:0 1px 2px rgba(0,0,0,0.04);
  margin-bottom:16px;
}

.meta-line { color: var(--muted); font-size: 14px; margin-top: 2px; }
.org { color:var(--muted); margin-bottom:8px; }

/* eligibility/funding block */
.ef { color: var(--text); font-size: 16px; margin: 6px 0 2px 0; }
.ef strong { font-weight:700; }

/* bottom link row with tighter spacing */
.link-row {
  display:flex; align-items:center; gap: 18px;  /* tighter than default */
  margin-top: 10px;
}
.link-row a {
  color: #005AA0;
  text-decoration: underline;
  font-size: 16px;
}
</style>
""", unsafe_allow_html=True)


# ---- Header ----
st.markdown("""
<div class="header">
  <img src="assets/GoA-logo.png" alt="Government of Alberta" style="height:48px;">
  <div>
    <h2>Alberta Pathfinding Tool</h2>
    <p>Small Business Supports & Funding Repository</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ================= Secrets & Admin =================
ADMIN_PASS = st.secrets.get("APP_ADMIN_PASS", os.environ.get("APP_ADMIN_PASS", ""))

# ================= Data =================
DATA_FILE = st.secrets.get("DATA_FILE", "Pathfinding_Master.xlsx")
if not Path(DATA_FILE).exists():
    st.warning("Upload your **Pathfinding_Master.xlsx** to this folder and rerun.")
    st.stop()

def ensure_cols(df, need):
    for c in need:
        if c not in df.columns:
            df[c] = ""
    return df

df = pd.read_excel(DATA_FILE)
df.columns = [c.strip() for c in df.columns]

def _find(name):
    # find a column by fuzzy containment
    for c in df.columns:
        if name.lower() in c.lower():
            return c
    return None

COLS = {
    "PROGRAM_NAME": _find("Program Name") or "Program Name",
    "ORG_NAME": _find("Organization Name") or "Organization Name",
    "DESC": _find("Program Description") or "Program Description",
    "ELIG": _find("Eligibility") or "Eligibility Description",
    "EMAIL": _find("Email") or "Email Address",
    "PHONE": _find("Phone") or "Phone Number",
    "WEBSITE": _find("Website") or "Program Website",
    "REGION": _find("Geographic Region") or "Geographic Region",
    "TAGS": _find("Meta Tags") or "Meta Tags",
    "FUNDING": _find("Funding Amount") or "Funding Amount",
    "STATUS": _find("Operational Status") or "Operational Status",
    "CONTACT": _find("Contact Page") or "Contact Page (Derived)",
    "LAST_CHECKED": _find("Last Checked") or "Last Checked (MT)",
    "KEY": _find("_key_norm") or "_key_norm",
}

df = ensure_cols(df, list(COLS.values()))

# ---- helpers ----
def parse_tags_field(s):
    if not isinstance(s, str): return []
    parts = re.split(r"[;,/|]", s)
    return [p.strip().lower() for p in parts if p.strip()]

def funding_bucket(amount):
    s = str(amount or "").replace(",", "")
    m = re.findall(r"\d+\.?\d*", s)
    if not m: return "Unknown / Not stated"
    try:
        v = float(m[-1])
    except:
        return "Unknown / Not stated"
    if v < 5000: return "Under $5K"
    if v < 25000: return "$5K–$25K"
    if v < 100000: return "$25K–$100K"
    if v < 500000: return "$100K–$500K"
    return "$500K+"

df["__funding_bucket"] = df[COLS["FUNDING"]].apply(funding_bucket)

def is_open(status):
    s = str(status).lower().strip()
    return any(k in s for k in ["open", "active", "ongoing", "accepting", "rolling"])

def days_since(date_str):
    try:
        d = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(d): return None
        return (pd.Timestamp.utcnow().normalize() - d.normalize()).days
    except: return None

def freshness_label(days):
    if days is None: return "—"
    if days <= 30: return f"{days}d ago"
    if days <= 180: return f"{days//30}mo ago"
    return f"{days//365}y ago"

df["__fresh_days"] = df[COLS["LAST_CHECKED"]].apply(days_since)
if df[COLS["KEY"]].isna().any() or (COLS["KEY"] not in df.columns):
    df[COLS["KEY"]] = (df[COLS["PROGRAM_NAME"]].fillna("").astype(str).str.lower().str.replace(r"[^a-z0-9]+","",regex=True)
                       + "|" +
                       df[COLS["ORG_NAME"]].fillna("").astype(str).str.lower().str.replace(r"[^a-z0-9]+","",regex=True))

# ================= Tag categorization =================
TAG_CATEGORY_MAP = {
    # FundingType
    "grant":"FundingType","loan":"FundingType","financing":"FundingType",
    "subsidy":"FundingType","tax":"FundingType","credit":"FundingType",
    # Group / Audience
    "women":"Group","youth":"Group","indigenous":"Group","black":"Group","newcomer":"Group",
    "immigrant":"Group","veteran":"Group","disability":"Group","disabled":"Group",
    "bipoc":"Group","minority":"Group","racialized":"Group","lgbtq":"Group","lgbtq2s":"Group",
    "rural":"Group","remote":"Group","social":"Group","cooperative":"Group","co-op":"Group",
    "nonprofit":"Group","non-profit":"Group",
    # Sector
    "agriculture":"Sector","agri":"Sector","agtech":"Sector","farming":"Sector","ranching":"Sector",
    "energy":"Sector","oil and gas":"Sector","o&g":"Sector","petrochemicals":"Sector",
    "cleantech":"Sector","clean tech":"Sector","renewable":"Sector","hydrogen":"Sector","solar":"Sector","wind":"Sector",
    "ict":"Sector","technology":"Sector","tech":"Sector","software":"Sector","ai":"Sector","cybersecurity":"Sector","saas":"Sector","digital":"Sector",
    "manufacturing":"Sector","advanced manufacturing":"Sector","fabrication":"Sector","machining":"Sector","additive":"Sector",
    "food processing":"Sector","food & beverage":"Sector","brewery":"Sector","distillery":"Sector",
    "construction":"Sector","trades":"Sector","hvac":"Sector","electrical":"Sector","plumbing":"Sector",
    "transportation":"Sector","logistics":"Sector","trucking":"Sector","warehousing":"Sector","supply chain":"Sector",
    "tourism":"Sector","hospitality":"Sector","events":"Sector","visitor economy":"Sector",
    "life sciences":"Sector","biotech":"Sector","medtech":"Sector","pharma":"Sector","health":"Sector",
    "forestry":"Sector","wood products":"Sector","lumber":"Sector","pulp":"Sector",
    "mining":"Sector","minerals":"Sector","critical minerals":"Sector",
    "creative":"Sector","film":"Sector","television":"Sector","gaming":"Sector","game dev":"Sector","music":"Sector","design":"Sector",
    "retail":"Sector","ecommerce":"Sector","e-commerce":"Sector","marketplace":"Sector","dtc":"Sector",
    "aerospace":"Sector","defence":"Sector","defense":"Sector","mro":"Sector",
    # Stage
    "startup":"Stage","scaleup":"Stage","innovation":"Stage","export":"Stage","research":"Stage","training":"Stage",
    # Supports
    "mentorship":"Supports","advisory":"Supports","coaching":"Supports","accelerator":"Supports",
    "workshop":"Supports","networking":"Supports",
}
CATEGORIES_ORDER = ["Region","FundingType","FundingAmount","Group","Sector","Stage","Supports"]
def category_for_tag(tag: str):
    return TAG_CATEGORY_MAP.get(tag.strip().lower())

# ================= Session & analytics =================
if "favorites" not in st.session_state: st.session_state.favorites = set()
if "filters" not in st.session_state:
    st.session_state.filters = {k:set() for k in CATEGORIES_ORDER}

def log_event(event, **kv):
    row = {"ts": datetime.now().isoformat(timespec="seconds"), "event": event, **kv}
    try:
        import pandas as _pd
        a = Path("analytics_events.csv")
        _pd.DataFrame([row]).to_csv(a, mode="a", index=False, header=not a.exists())
    except Exception:
        pass

# ================= Sidebar filters =================
st.sidebar.header("Filters")
REGION_CHOICES = ["Calgary","Edmonton","Rural Alberta","Canada"]
FUND_AMOUNT_CHOICES = ["Under $5K","$5K–$25K","$25K–$100K","$100K–$500K","$500K+","Unknown / Not stated"]

def toggle(cat,opt,on):
    s = st.session_state.filters[cat]
    if on: s.add(opt)
    else: s.discard(opt)

with st.sidebar.expander("Region", expanded=False):
    for r in REGION_CHOICES:
        cur = r in st.session_state.filters["Region"]
        val = st.checkbox(r, value=cur, key=f"region_{r}")
        if val != cur: log_event("filter_toggle", category="Region", value=r, on=val)
        toggle("Region", r, val)

with st.sidebar.expander("Funding (Type)", expanded=False):
    opts = ["Grant","Loan","Financing","Subsidy","Tax Credit","Credit"]
    for t in opts:
        key = t.lower()
        cur = key in st.session_state.filters["FundingType"]
        val = st.checkbox(t, value=cur, key=f"ft_{t}")
        if val != cur: log_event("filter_toggle", category="FundingType", value=t, on=val)
        toggle("FundingType", key, val)

with st.sidebar.expander("Funding (Amount)", expanded=False):
    for f in FUND_AMOUNT_CHOICES:
        cur = f in st.session_state.filters["FundingAmount"]
        val = st.checkbox(f, value=cur, key=f"fa_{f}")
        if val != cur: log_event("filter_toggle", category="FundingAmount", value=f, on=val)
        toggle("FundingAmount", f, val)

# Build tag options for remaining categories from dataset
def tags_by_category(df, cat):
    s = set()
    for row in df[COLS["TAGS"]].dropna().astype(str):
        for t in parse_tags_field(row):
            if category_for_tag(t) == cat:
                s.add(t)
    return sorted(s)

for cat in ["Group","Sector","Stage","Supports"]:
    with st.sidebar.expander(cat, expanded=False):
        for t in tags_by_category(df, cat):
            label = t.title()
            cur = t in st.session_state.filters[cat]
            val = st.checkbox(label, value=cur, key=f"{cat}_{t}")
            if val != cur: log_event("filter_toggle", category=cat, value=t, on=val)
            toggle(cat, t, val)

if st.sidebar.button("Reset all filters"):
    for k in st.session_state.filters: st.session_state.filters[k] = set()
    st.experimental_rerun()

# ================= Search + chips =================
q = st.text_input("🔍 Search programs", "")
if q != st.session_state.get("_prev_q",""):
    log_event("search_changed", q=q)
    st.session_state["_prev_q"] = q

active = [(cat,v) for cat,vals in st.session_state.filters.items() for v in sorted(vals)]
if active:
    st.markdown('<div class="chipbtn">', unsafe_allow_html=True)
    cols = st.columns(min(6, len(active)))
    for i,(cat,v) in enumerate(active):
        with cols[i % len(cols)]:
            if st.button(f"{v.title()} ✕", key=f"chip_{cat}_{v}"):
                st.session_state.filters[cat].discard(v)
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= Filtering logic =================
def fuzzy_mask(df, q, threshold=70):
    if not q: return pd.Series([True]*len(df), index=df.index)
    cols = [COLS["PROGRAM_NAME"], COLS["ORG_NAME"], COLS["DESC"], COLS["ELIG"], COLS["TAGS"]]
    m = []
    for _, row in df[cols].fillna("").astype(str).iterrows():
        blob = " ".join([row[c] for c in cols]).lower()
        m.append(fuzz.partial_ratio(q.lower(), blob) >= threshold)
    return pd.Series(m, index=df.index)

def region_match(value: str, selected_region: str) -> bool:
    if not selected_region or selected_region == "All Regions": return True
    if not isinstance(value, str): return False
    v = value.lower()
    table = {
        "Calgary": ["calgary", "southern alberta"],
        "Edmonton": ["edmonton", "central alberta"],
        "Rural Alberta": ["rural", "northern alberta", "southern alberta", "central alberta"],
        "Canada": ["canada", "national", "federal", "international"],
    }
    return any(w in v for w in table.get(selected_region, []))

def apply_filters(df_in):
    out = df_in.copy()
    include_closed = st.checkbox("Include Closed / Paused", value=False)
    if not include_closed:
        out = out[out[COLS["STATUS"]].apply(is_open)]
    out = out[fuzzy_mask(out, q, threshold=70)]
    f = st.session_state.filters
    if f["Region"]:
        out = out[out[COLS["REGION"]].apply(lambda v: any(region_match(v, r) for r in f["Region"]))]
    if f["FundingAmount"]:
        out = out[out["__funding_bucket"].isin(f["FundingAmount"])]
    def any_tag(s, choices):
        if not choices: return True
        tags = set(parse_tags_field(s))
        return any(c in tags for c in choices)
    for cat in ["FundingType","Group","Sector","Stage","Supports"]:
        if f[cat]:
            out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: any_tag(s, f[cat]))]
    return out

filtered = apply_filters(df)

# ================= Results & cards =================
st.markdown(f"### {len(filtered)} Programs Found")

for i, (_, row) in enumerate(filtered.iterrows(), 1):
    name = str(row[COLS["PROGRAM_NAME"]] or "")
    org = str(row[COLS["ORG_NAME"]] or "")
    status_val = str(row[COLS["STATUS"]] or "").strip().lower()
    status_cls = "open" if is_open(status_val) else "closed"
    desc_full = str(row[COLS["DESC"]] or "").strip()
    desc = (desc_full[:240] + "…") if len(desc_full) > 240 else desc_full
    elig = str(row[COLS["ELIG"]] or "").strip()
    fund = row.get("__funding_bucket") or ""
    fresh = freshness_label(row.get("__fresh_days"))
    website = row.get(COLS["WEBSITE"]); email = row.get(COLS["EMAIL"]); phone = row.get(COLS["PHONE"]); contact = row.get(COLS["CONTACT"])
    key = str(row.get(COLS["KEY"], f"k{i}"))

    st.markdown(
        f"<div class='card'>"
        f"<span class='badge {status_cls}'>{row[COLS['STATUS']]}</span> "
        f"<span class='tags'>Last checked: {fresh}</span>"
        f"<h3 style='margin:4px 0 6px 0'>{name}</h3>"
        f"<div class='org'>{org}</div>"
        f"<p>{desc or '<span class=\"placeholder\">No description provided.</span>'}</p>",
        unsafe_allow_html=True
    )

    el = f"**Eligibility:** {elig}" if elig else "<span class='placeholder'>Eligibility not provided.</span>"
    fu = f"**Funding:** {fund}" if fund else "<span class='placeholder'>Funding information not provided.</span>"
    st.markdown("<div class='tags'>" + el + " &nbsp;&nbsp; " + fu + "</div>", unsafe_allow_html=True)

    if len(desc_full) > 240 or not elig or not fund:
        with st.expander("More details"):
            st.markdown(f"**Full description:** {desc_full}" if desc_full else "_No description available._")
            st.markdown(f"**Eligibility:** {elig}" if elig else "_No eligibility details available._")
            st.markdown(f"**Funding:** {fund}" if fund else "_No funding information available._")

    left, right = st.columns([6,1])
    with left:
        clicked = False
        if website:
            try:
                clicked = st.link_button("Visit Website", website, type="primary", use_container_width=False)
            except Exception:
                st.markdown(f"<a class='btn-primary' href='{website}' target='_blank'>Visit Website</a>", unsafe_allow_html=True)
        small = []
        if email: small.append(f"<a href='mailto:{email}' target='_blank'>Email</a>")
        if phone: small.append(f"<a href='tel:{phone}' target='_blank'>Call</a>")
        if contact: small.append(f"<a href='{contact}' target='_blank'>Contact</a>")
        if small:
            st.markdown("<div class='small-links'>" + " · ".join(small) + "</div>", unsafe_allow_html=True)
        if clicked: 
            from pathlib import Path as _P
            st.session_state["__clicked"] = True

    with right:
        if "favorites" not in st.session_state: st.session_state.favorites = set()
        fav_on = key in st.session_state.favorites
        label = "★" if fav_on else "☆"
        if st.button(label, key=f"fav_{key}", help="Add/Remove favorite"):
            if fav_on: st.session_state.favorites.remove(key)
            else: st.session_state.favorites.add(key)
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ================= Admin (gated) =================
st.markdown("## Admin Insights")

def admin_gate():
    if not ADMIN_PASS:
        st.info("Admin password not configured. Set APP_ADMIN_PASS in .streamlit/secrets.toml")
        return False
    k = "__admin_ok"
    if st.session_state.get(k): 
        return True
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
    from pathlib import Path as _P
    if _P("analytics_events.csv").exists():
        a = pd.read_csv("analytics_events.csv")
        top_search = (a[a["event"]=="search_changed"]["q"]
                      .dropna().astype(str).str.lower().value_counts().head(10) if "q" in a.columns else pd.Series(dtype=int))
        filt = a[a["event"]=="filter_toggle"] if "category" in a.columns else pd.DataFrame()
        if not filt.empty:
            filt["pair"] = filt["category"].astype(str) + ": " + filt["value"].astype(str)
            top_filters = filt["pair"].value_counts().head(10)
        else:
            top_filters = pd.Series(dtype=int)
        fav = a[a["event"]=="favorite_toggle"]["key"].value_counts().head(10) if "key" in a.columns else pd.Series(dtype=int)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Top search terms**")
            st.write(top_search)
        with c2:
            st.markdown("**Most used filters**")
            st.write(top_filters)
        with c3:
            st.markdown("**Most favorited programs**")
            st.write(fav)

        st.download_button("Download analytics CSV", a.to_csv(index=False).encode("utf-8"),
                           file_name="analytics_events.csv", mime="text/csv")
    else:
        st.info("No analytics yet — data will appear as users interact.")
