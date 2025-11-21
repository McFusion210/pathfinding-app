# app.py - Alberta Pathfinding Tool (Streamlit)
# Government of Alberta - Small Business Supports & Funding Repository

import re
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz


# ---------------------------- Page config ----------------------------
st.set_page_config(
    page_title="Alberta Small Business Supports Pathfinding Tool",
    page_icon="📊",
    layout="wide",
)


# ---------------------------- Data loading helpers ----------------------------
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    return df


DATA_PATH = "Pathfinding_Master.xlsx"
df = load_data(DATA_PATH)


# ---------------------------- Column mapping ----------------------------
COLS = {
    "PROGRAM_NAME": "Program Name",
    "ORG_NAME": "Organization Name",
    "DESCRIPTION": "Program Description",
    "WEBSITE": "Website",
    "PHONE": "Phone Number",
    "EMAIL": "Contact Email",
    "REGION": "Region",
    "STATUS": "Operational Status",
    "LAST_CHECKED": "Last Validated",
    "FUNDING_AMOUNT": "Funding Amount",
    "FUNDING_TYPE": "Funding Type",
    "PROGRAM_STAGE": "Business Stage",
    "ACTIVITY_TAGS": "Business Supports (tags)",
    "AUDIENCE_TAGS": "Audience (tags)",
}


# ---------------------------- Normalization helpers ----------------------------
def normalize_tag_list(val):
    if pd.isna(val):
        return set()
    if isinstance(val, (list, set, tuple)):
        items = val
    else:
        s = str(val)
        if not s.strip():
            return set()
        if ";" in s:
            items = [p.strip() for p in s.split(";")]
        elif "," in s:
            items = [p.strip() for p in s.split(",")]
        else:
            items = [s.strip()]
    out = set()
    for item in items:
        if not item:
            continue
        clean = re.sub(r"\s+", " ", str(item)).strip()
        if clean:
            out.add(clean)
    return out


def canon_stage(stage: str) -> str | None:
    if not stage:
        return None
    s = stage.lower()
    if any(k in s for k in ["start", "pre-revenue", "early"]):
        return "Startup / Early Stage"
    if any(k in s for k in ["growth", "scale", "expansion"]):
        return "Growth / Scale"
    if any(k in s for k in ["mature", "established", "succession"]):
        return "Mature / Established"
    return None


def add_dollar_signs(text: str) -> str:
    if not text:
        return text
    if "unknown" in text.lower():
        return text
    return re.sub(r"(?<!\$)(\d[\d,\.]*\s*[KkMm]?)", r"$\1", text)


def funding_bucket(amount):
    """Map raw funding text into standard funding bands."""
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


def days_since(date_str):
    try:
        d = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(d):
            return
        delta = pd.Timestamp.today().normalize() - d.normalize()
        return delta.days
    except Exception:
        return


# ---------------------------- Derived columns ----------------------------
df["__funding_bucket"] = df[COLS["FUNDING_AMOUNT"]].apply(funding_bucket)
df["__funding_amount_fmt"] = df[COLS["FUNDING_AMOUNT"]].apply(add_dollar_signs)

df["__fund_type_set"] = df[COLS["FUNDING_TYPE"]].apply(normalize_tag_list)
df["__activity_norm_set"] = df[COLS["ACTIVITY_TAGS"]].apply(normalize_tag_list)
df["__audience_norm_set"] = df[COLS["AUDIENCE_TAGS"]].apply(normalize_tag_list)

df["__stage_norm_set"] = df[COLS["PROGRAM_STAGE"]].apply(
    lambda v: {canon_stage(v)} if canon_stage(v) else set()
)


# ---------------------------- Sidebar filters intro ----------------------------
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
    "Equity",
    "Guarantee",
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

FUZZY_THR = 70

REGION_MATCH_TABLE = {
    "Calgary": ["calgary", "southern alberta", "foothills"],
    "Edmonton": ["edmonton", "capital region", "central alberta"],
    "Rural Alberta": [
        "rural",
        "north",
        "northern alberta",
        "east central",
        "south central",
        "foothills",
        "parkland",
    ],
    "Canada": ["canada", "national", "pan-canadian"],
}


def region_match(region_text: str, choice: str) -> bool:
    s = str(region_text).lower()
    for token in REGION_MATCH_TABLE.get(choice, []):
        if token in s:
            return True
    return False


def count_by_option(series_of_sets):
    counts = {}
    for S in series_of_sets:
        for v in S:
            counts[v] = counts.get(v, 0) + 1
    return counts


# ---------------------------- Fuzzy search mask ----------------------------
def fuzzy_mask(df_in: pd.DataFrame, query: str, threshold: int = 70) -> pd.Series:
    if not query:
        return pd.Series(True, index=df_in.index)

    q = query.lower().strip()
    cols_to_search = [
        COLS["PROGRAM_NAME"],
        COLS["DESCRIPTION"],
        COLS["ORG_NAME"],
    ]

    def row_match(row):
        for col in cols_to_search:
            val = str(row.get(col, "") or "").lower()
            if not val:
                continue
            score = fuzz.partial_ratio(q, val)
            if score >= threshold:
                return True
        return False

    return df_in.apply(row_match, axis=1)


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
<a href="#main-content" class="skip-link">Skip to main content</a>
<div class="header goa-header">
  <div>
    <h2>Small Business Supports Pathfinding Tool</h2>
    <p>Find funding, advice and programs for Alberta small businesses and entrepreneurs.</p>
  </div>
</div>
<div class="header-spacer" id="main-content"></div>
""",
    unsafe_allow_html=True,
)


# ---------------------------- Search & gather ----------------------------
q = st.text_input(
    "Search programs",
    "",
    key="q",
    placeholder="Try 'grant', 'mentorship', or 'startup'...",
)
st.caption(
    "Tip: Search matches similar terms (for example, typing mentor will also find mentorship)."
)

all_activity_norm = sorted({v for S in df["__activity_norm_set"] for v in S})
raw_stage_norm = {v for S in df["__stage_norm_set"] for v in S}
all_stage_norm = sorted(raw_stage_norm)
stage_options = all_stage_norm

all_audience_norm = sorted({v for S in df["__audience_norm_set"] for v in S})


# ---------------------------- Build counts for filters ----------------------------
df_except_funding = df.copy()
df_except_activity = df.copy()
df_except_stage = df.copy()
df_except_audience = df.copy()

df_except_funding["__funding_bucket"] = df_except_funding["__funding_bucket"]
df_except_activity["__activity_norm_set"] = df_except_activity["__activity_norm_set"]
df_except_stage["__stage_norm_set"] = df_except_stage["__stage_norm_set"]
df_except_audience["__audience_norm_set"] = df_except_audience["__audience_norm_set"]

funding_counts = df_except_funding["__funding_bucket"].value_counts().to_dict()
activity_counts = count_by_option(df_except_activity["__activity_norm_set"])
stage_counts = count_by_option(df_except_stage["__stage_norm_set"])
audience_counts = count_by_option(df_except_audience["__audience_norm_set"])

region_counts = {}
for region in REGION_CHOICES:
    mask = df[COLS["REGION"]].astype(str).apply(lambda v, r=region: region_match(v, r))
    region_counts[region] = int(mask.sum())


# ---------------------------- Pill filter helper ----------------------------
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

        if active:
            picked.add(opt)

    return picked


# ---------------------------- Sidebar filter groups ----------------------------
selected_famts = render_filter_pills(
    "How much funding are you looking for?",
    FUND_AMOUNT_CHOICES,
    funding_counts,
    "famt",
)

selected_stage = render_filter_pills(
    "What stage is your business at?",
    stage_options,
    stage_counts,
    "stage",
)

selected_audience = render_filter_pills(
    "Who is this support for?",
    all_audience_norm,
    audience_counts,
    "audience",
)

selected_activity = render_filter_pills(
    "What kind of business supports are you looking for?",
    all_activity_norm,
    activity_counts,
    "activity",
)

selected_regions = render_filter_pills(
    "Where is your business located?",
    REGION_CHOICES,
    region_counts,
    "region",
)

selected_ftypes = render_filter_pills(
    "What type of funding are you interested in?",
    FUNDING_TYPE_CHOICES,
    funding_counts,
    "ftype",
)


def clear_all_filters():
    for key in list(st.session_state.keys()):
        if any(
            key.startswith(prefix)
            for prefix in ("famt_", "stage_", "audience_", "activity_", "region_", "ftype_")
        ):
            st.session_state[key] = False
    st.session_state["q"] = ""


st.sidebar.markdown("---")
if st.sidebar.button("Clear all filters", key="clear_all_top"):
    clear_all_filters()
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
        out = out[out["__activity_norm_set"].apply(lambda s: bool(s & selected_activity))]
    if selected_audience:
        out = out[out["__audience_norm_set"].apply(lambda s: bool(s & selected_audience))]
    return out


# ---------------------------- Chips (pill buttons with x) ----------------------------
def render_chips():
    """
    Show active filters as pill-style buttons.
    Clicking a pill clears only that specific filter.
    """
    any_chip = False

    # Marker so CSS can target this container's buttons
    st.markdown("<div class='chip-row-marker'></div>", unsafe_allow_html=True)

    def chip(label: str, key_suffix: str, clear_fn):
        nonlocal any_chip
        any_chip = True
        clicked = st.button(
            label + " x",
            key=f"chip_{key_suffix}",
        )
        if clicked:
            clear_fn()
            st.session_state["page_idx"] = 0
            st.rerun()

    if q:
        chip("Search: " + q, "search", lambda: st.session_state.update({"q": ""}))

    for f in sorted(selected_ftypes):
        chip(
            f"Funding Type: {f}",
            f"ftype_{f}",
            lambda f=f: st.session_state.update({f"ftype_{f}": False}),
        )

    for b in sorted(selected_famts):
        chip(
            f"Amount: {b}",
            f"famt_{b}",
            lambda b=b: st.session_state.update({f"famt_{b}": False}),
        )

    for au in sorted(selected_audience):
        chip(
            f"Audience: {au}",
            f"audience_{au}",
            lambda au=au: st.session_state.update({f"audience_{au}": False}),
        )

    for s in sorted(selected_stage):
        chip(
            f"Stage: {s}",
            f"stage_{s}",
            lambda s=s: st.session_state.update({f"stage_{s}": False}),
        )

    for a in sorted(selected_activity):
        chip(
            f"Business Supports: {a}",
            f"activity_{a}",
            lambda a=a: st.session_state.update({f"activity_{a}": False}),
        )

    for r in sorted(selected_regions):
        chip(
            f"Region: {r}",
            f"region_{r}",
            lambda r=r: st.session_state.update({f"region_{r}": False}),
        )

    if any_chip:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)


filtered = apply_filters(df)

render_chips()


# ---------------------------- Sort controls and page size ----------------------------
sort_col, page_col = st.columns([0.6, 0.4])
with sort_col:
    sort_mode = st.selectbox(
        "Sort results by",
        ["Relevance", "Program Name (A to Z)", "Last Checked (newest)"],
        index=0,
        help="Relevance uses fuzzy keyword matching across program name, description and tags.",
    )
with page_col:
    page_size = st.selectbox(
        "Results per page",
        [10, 25, 50],
        index=1,
        help="Change how many programs appear on each page of results.",
    )


def sort_df(dfin: pd.DataFrame) -> pd.DataFrame:
    if sort_mode == "Program Name (A to Z)":
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


# ---------------------------- Export ----------------------------
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download results (CSV)",
    csv_bytes,
    file_name="pathfinding_results.csv",
    mime="text/csv",
)

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)


# ---------------------------- Pagination ----------------------------
if "page_idx" not in st.session_state:
    st.session_state["page_idx"] = 0

total = len(filtered)
page_size = int(page_size)
max_page = max((total - 1) // page_size, 0)
page_idx = min(max(st.session_state["page_idx"], 0), max_page)
start_idx = page_idx * page_size
end_idx = min(start_idx + page_size, total)

if total == 0:
    st.info("No programs match your search and filters. Try clearing some filters or broadening your search.")
else:
    st.caption(f"Showing programs {start_idx + 1} to {end_idx} of {total}.")


# ---------------------------- Render program cards ----------------------------
def make_tel_link(phone: str) -> str | None:
    if not phone or pd.isna(phone):
        return None
    digits = re.sub(r"[^\d+]", "", str(phone))
    if not digits:
        return None
    return f"tel:{digits}"


def make_mailto(email: str) -> str | None:
    if not email or pd.isna(email):
        return None
    e = str(email).strip()
    if not e:
        return None
    return f"mailto:{e}"


for _, row in filtered.iloc[start_idx:end_idx].iterrows():
    st.markdown("<div class='pf-card-marker'></div>", unsafe_allow_html=True)

    title = row.get(COLS["PROGRAM_NAME"], "(No program name)")
    org = row.get(COLS["ORG_NAME"], "(No organization)")
    desc = row.get(COLS["DESCRIPTION"], "(No description provided)")
    website = row.get(COLS["WEBSITE"])
    email = row.get(COLS["EMAIL"])
    phone = row.get(COLS["PHONE"])
    region = row.get(COLS["REGION"])
    status = row.get(COLS["STATUS"])
    last_checked = row.get(COLS["LAST_CHECKED"])
    fund_amt = row.get("__funding_amount_fmt")
    fund_bucket = row.get("__funding_bucket")

    stage_set = row.get("__stage_norm_set", set()) or set()
    activity_set = row.get("__activity_norm_set", set()) or set()
    audience_set = row.get("__audience_norm_set", set()) or set()

    tel_link = make_tel_link(phone)
    mailto_link = make_mailto(email)

    status_badge = ""
    if isinstance(status, str) and status.strip():
        s = status.lower()
        if "open" in s:
            status_badge = '<span class="badge open">Open</span>'
        elif "closed" in s:
            status_badge = '<span class="badge closed">Closed</span>'
        elif "operational" in s:
            status_badge = '<span class="badge operational">Operational</span>'

    heading_html = f"""
<div class="title">{title}</div>
<div class="org">{org}</div>
"""
    st.markdown(heading_html, unsafe_allow_html=True)

    if isinstance(desc, str) and desc.strip():
        st.write(desc)
    else:
        st.markdown('<p class="placeholder">No description available.</p>', unsafe_allow_html=True)

    meta_bits = []
    if fund_bucket:
        meta_bits.append(f"<span><strong>Funding band:</strong> {fund_bucket}</span>")
    if region:
        meta_bits.append(f"<span><strong>Region:</strong> {region}</span>")
    if stage_set:
        meta_bits.append(f"<span><strong>Stage:</strong> {', '.join(sorted(stage_set))}</span>")
    if audience_set:
        meta_bits.append(f"<span><strong>Audience:</strong> {', '.join(sorted(audience_set))}</span>")

    meta_html = ""
    if meta_bits or status_badge:
        meta_html = "<div class='meta-info'>"
        if status_badge:
            meta_html += status_badge
        if meta_bits:
            meta_html += "<span class='kv'>" + " | ".join(meta_bits) + "</span>"
        meta_html += "</div>"

    st.markdown(meta_html, unsafe_allow_html=True)

    st.markdown('<div class="actions-row"><div class="actions-links">', unsafe_allow_html=True)

    if isinstance(website, str) and website.strip():
        st.markdown(f'<a href="{website}" target="_blank">Website</a>', unsafe_allow_html=True)
    if mailto_link:
        st.markdown(f'<a href="{mailto_link}">Email</a>', unsafe_allow_html=True)
    if tel_link:
        st.markdown(f'<a href="{tel_link}">Call</a>', unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("---")


# ---------------------------- Pagination controls ----------------------------
prev_col, next_col = st.columns([0.5, 0.5])
with prev_col:
    if st.button("Previous page", disabled=page_idx <= 0):
        st.session_state["page_idx"] = max(page_idx - 1, 0)
        st.rerun()
with next_col:
    if st.button("Next page", disabled=page_idx >= max_page):
        st.session_state["page_idx"] = min(page_idx + 1, max_page)
        st.rerun()
