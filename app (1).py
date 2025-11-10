import os, re, math, uuid, time, hashlib
from pathlib import Path
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

# ---------- App Setup ----------
st.set_page_config(page_title="Pathfinding Repository", layout="wide")

# ---------- Session & Analytics ----------
if "sid" not in st.session_state:
    st.session_state.sid = str(uuid.uuid4())
if "t0" not in st.session_state:
    st.session_state.t0 = time.time()

def log_event(event, **kv):
    row = {
        "ts": pd.Timestamp.utcnow().isoformat(),
        "session": st.session_state.sid,
        "event": event,
        **kv,
        "elapsed_s": int(time.time() - st.session_state.t0),
    }
    try:
        import pandas as _pd
        from pathlib import Path as _Path
        old = _pd.read_csv("analytics_events.csv") if _Path("analytics_events.csv").exists() else _pd.DataFrame()
        new = _pd.concat([old, _pd.DataFrame([row])], ignore_index=True)
        new.to_csv("analytics_events.csv", index=False)
    except Exception:
        pass

# ---------- Config ----------
DATA_FILE = "Pathfinding_Master.xlsx"
INTAKE_FILE = "Intake_Submissions.xlsx"
ADMIN_PASS = st.secrets.get("APP_ADMIN_PASS", os.environ.get("APP_ADMIN_PASS", ""))

COLS = {
    "PROGRAM_NAME": "Program Name",
    "ORG_NAME": "Organization Name",
    "ELIG": "Eligibility Description",
    "DESC": "Program Description",
    "TAGS": "Meta Tags",
    "REGION": "Geographic Region",
    "STATUS": "Operational Status",
    "LAST_CHECKED": "Last Checked (MT)",
    "WEBSITE": "Program Website",
    "EMAIL": "Email Address",
    "PHONE": "Phone Number",
    "FUNDING": "Funding Amount",
    "SOURCES": "Sources",
    "NOTES": "Notes",
    "KEY": "_key_norm",
    "CONTACT_DERIVED": "Contact Page (Derived)",
}

# Open status keywords (broadened)
def is_open(status):
    s = str(status).strip().lower()
    keywords = {"open", "active", "ongoing", "accepting", "currently accepting", "rolling"}
    return any(k in s for k in keywords)

# ---------- Visual Theme ----------
PALETTE = {
    "--bg": "#F7F8FA",
    "--surface": "#FFFFFF",
    "--text": "#0B0C0C",
    "--muted": "#5F6B7A",
    "--primary": "#003366",
    "--primary-contrast": "#FFFFFF",
    "--interactive": "#00B6ED",
    "--accent": "#FFC836",
    "--border": "#E3E7ED",
    "--badge-open": "#E6F4EA",
    "--badge-open-text": "#0F5132",
    "--badge-closed": "#FDECEE",
    "--badge-closed-text": "#842029",
    "--band-blue": "#F0F6FB",
    "--band-gold": "#FFF6D8",
}

# Synonym pack
SYNONYMS = {
    "women": {"women", "women-led", "female", "women owned", "women entrepreneurs"},
    "indigenous": {"indigenous", "first nations", "metis", "inuit", "aboriginal"},
    "startup": {"startup", "start up", "early stage", "new business"},
    "growth": {"growth", "scale", "scaling"},
    "grant": {"grant", "non-repayable", "contribution"},
    "loan": {"loan", "financing", "debt"},
    "advisory": {"advisory", "advice", "coaching", "mentorship", "mentors", "advisement"},
    "training": {"training", "workshop", "course", "learning"},
    "tax": {"tax", "credit", "rebate"},
    "voucher": {"voucher", "coupon"},
    "tech": {"tech", "technology", "ict", "digital"},
    "agri": {"agri", "agriculture", "farming"},
    "cleantech": {"cleantech", "clean tech", "clean technology", "emissions"},
    "tourism": {"tourism", "visitor economy"},
    "energy": {"energy", "oil and gas", "o&g"},
    "rural": {"rural", "remote"},
    "newcomer": {"newcomer", "immigrant", "immigration"},
    "youth": {"youth", "young entrepreneurs", "students"},
    "veteran": {"veteran", "ex-military", "military"},
    "disabled": {"disabled", "disability", "accessibility"},
    "export": {"export", "exporting", "trade"},
    "succession": {"succession", "acquisition", "buy a business", "exit"},
}

def canon_tag(s: str) -> str:
    t = s.strip().lower()
    for canon, al in SYNONYMS.items():
        if t in al:
            return canon
    return t

def parse_tags_field(s: str):
    parts = re.split(r"[;,/|]+", str(s))
    cleaned = [p.strip() for p in parts if p and p.strip()]
    return [canon_tag(t) for t in cleaned]

def expand_query_terms(q: str):
    terms = [w.strip().lower() for w in re.split(r"[,\s]+", q) if w.strip()]
    expanded = set()
    for w in terms:
        expanded.add(w)
        for canon, al in SYNONYMS.items():
            if w in al or w == canon:
                expanded.update(al)
                expanded.add(canon)
    return expanded

FUNDING_BUCKETS = [
    ("Under $5K",           0,      5_000),
    ("$5K–$25K",            5_000,  25_000),
    ("$25K–$100K",          25_000, 100_000),
    ("$100K–$500K",         100_000, 500_000),
    ("$500K+",              500_000, math.inf),
    ("Unknown / Not stated", None,  None),
]

# ---------- Utilities ----------
def ensure_cols(df):
    for col in COLS.values():
        if col not in df.columns:
            df[col] = ""
    return df

def all_regions(df):
    values = df[COLS["REGION"]].dropna().astype(str).map(str.strip)
    return sorted([v for v in values.unique().tolist() if v])

def all_tags(df):
    bag = set()
    for s in df[COLS["TAGS"]].fillna("").astype(str).tolist():
        for t in parse_tags_field(s):
            bag.add(t)
    return sorted(bag, key=lambda x: x.lower())

def fuzzy_mask(df, q, threshold=70):
    if not q:
        return pd.Series([True]*len(df), index=df.index)
    q_terms = expand_query_terms(q)
    cols = [COLS["PROGRAM_NAME"], COLS["ORG_NAME"], COLS["ELIG"], COLS["DESC"], COLS["TAGS"]]
    mask = []
    for _, row in df[cols].fillna("").astype(str).iterrows():
        blob = " ".join([row[c] for c in cols]).lower()
        score = max(fuzz.partial_ratio(term, blob) for term in q_terms) if q_terms else 0
        mask.append(score >= threshold)
    return pd.Series(mask, index=df.index)

def days_since(date_str):
    try:
        d = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(d):
            return None
        return (pd.Timestamp.utcnow().normalize() - d.normalize()).days
    except:
        return None

def freshness_label(days):
    if days is None:
        return "—"
    if days <= 30:
        return f"{days}d ago"
    if days <= 180:
        return f"{days//30}mo ago"
    return f"{days//365}y ago"

def key_for_row(row):
    raw = f"{str(row.get(COLS['PROGRAM_NAME'],'')).strip()}|{str(row.get(COLS['ORG_NAME'],'')).strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

# ---------- Data ----------
if not Path(DATA_FILE).exists():
    st.warning(f"Upload your Excel file named **{DATA_FILE}** to run the app.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel(DATA_FILE)
    df = ensure_cols(df)
    df["__funding_num"] = df[COLS["FUNDING"]].apply(lambda s: _parse_amount(str(s)))
    df["__funding_bucket"] = df["__funding_num"].apply(_funding_bucket_label)
    df["__fresh_days"] = df[COLS["LAST_CHECKED"]].apply(days_since)
    df["__tags_norm"] = df[COLS["TAGS"]].fillna("").astype(str).apply(lambda s: ";".join(sorted(set(parse_tags_field(s)))))
    if COLS["KEY"] not in df.columns or df[COLS["KEY"]].eq("").any():
        df[COLS["KEY"]] = df.apply(key_for_row, axis=1)
    return df

_money_pattern = re.compile(r"(\$?\s*\d[\d,]*\.?\d*)", re.IGNORECASE)
def _parse_amount(s: str):
    if not s:
        return None
    tokens = _money_pattern.findall(s.replace("\u2013","-"))
    vals = []
    for tok in tokens:
        tok = tok.replace("$","").replace(",","").strip()
        try:
            v = float(tok); 
            if v>0: vals.append(v)
        except: pass
    return max(vals) if vals else None

def _funding_bucket_label(amount: float):
    if amount is None:
        return "Unknown / Not stated"
    for label, lo, hi in FUNDING_BUCKETS:
        if lo is None and hi is None: 
            continue
        if lo <= amount < hi:
            return label
    return "Unknown / Not stated"

df = load_data()

# ---------- Styles ----------
css_vars = "".join([f"{k}:{v};" for k,v in PALETTE.items()])
st.markdown("<style>:root {" + css_vars + "}" + """
html, body { background: var(--bg); }
.band { padding: 12px 16px; border-radius: 8px; margin: 8px 0 16px 0; display:flex; gap:12px; align-items:center; }
.band .content a { color: var(--interactive); text-decoration: none; margin-right: 12px; }
.band.blue { background: var(--band-blue); }
.band.gold { background: var(--band-gold); }
.pills { margin: 8px 4px 8px 4px; }
.pill { display:inline-block; padding:6px 12px; margin: 4px 6px 0 0; border:1px solid var(--primary); border-radius:999px; color: var(--primary); background: #fff; font-size: 13px; text-decoration:none; }
.pill.active { background: var(--primary); color: var(--primary-contrast); }
.stTextInput > div > div > input { border: 1px solid var(--border) !important; border-radius: 10px; }
.stButton > button { background: var(--primary); color: var(--primary-contrast); border:none; border-radius: 12px; }
.card { background: var(--surface); border:1px solid var(--border); border-radius:16px; padding:16px 16px 12px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin-bottom:16px; }
.card h3 { margin:0 0 6px 0; color:var(--text); font-weight:600; }
.card .org { color:var(--muted); margin-bottom:8px; }
.badge { display:inline-block; font-size:12px; padding:4px 8px; border-radius:999px; margin-bottom:8px; }
.badge.open { background: var(--badge-open); color: var(--badge-open-text); }
.badge.closed { background: var(--badge-closed); color: var(--badge-closed-text); }
.tags { color: var(--muted); font-size: 13px; margin-top:6px; }
.links a { text-decoration:none; margin-right:10px; color: var(--interactive); }
.chips { margin: 10px 0 0 0; }
.chip { display:inline-block; background:#fff; border:1px solid var(--border); border-radius:999px; padding:3px 10px; margin:4px 6px 0 0; font-size:12px; color: var(--muted);}
.pager { color: var(--muted); }
/* link buttons beside contacts */
.linkbtn { display:inline-block; padding:6px 12px; border:1px solid var(--primary); border-radius:999px; text-decoration:none; margin-right:8px; color:var(--primary); background:#fff; }
.linkbtn:hover { background: var(--band-blue); }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown(
    '<div class="band blue"><strong>Pathfinding Programs</strong> — Find funding, advisory, and training supports for Alberta businesses. '
    '<a href="#how-to-use">How to use</a>'
    '<a href="#suggest-program">Suggest a program</a>'
    '<a href="mailto:smallbusiness@gov.ab.ca">Contact Small Business Team</a>'
    '</div>',
    unsafe_allow_html=True
)

# ---------- Tabs ----------
tab_browse, tab_favs, tab_suggest, tab_admin = st.tabs(["Browse", "Favorites", "Suggest a Program", "Admin"])

# track tab view
log_event("tab_view", tab="Browse")

# ---------- Browse ----------
with tab_browse:
    qp = st.experimental_get_query_params()
    def qp_get(name, default=""):
        return qp.get(name, [default])[0]

    # Favorites init from URL
    if "favorites" not in st.session_state:
        fav_init = set(qp.get("fav", [""])[0].split("|")) if "fav" in qp and qp["fav"][0] else set()
        st.session_state.favorites = {f for f in fav_init if f}

    c1, c2, c3, c4 = st.columns([5,2,2,2])
    q = c1.text_input("Search", value=qp_get("q"), placeholder="Search by program, organization, eligibility, tags", label_visibility="collapsed")
    include_closed = c2.checkbox("Include Closed / Paused", value=(qp_get("closed","0")=="1"))
    sort_choice = c3.selectbox("Sort by", ["Relevance", "Program Name (A–Z)", "Last Checked (Newest)"], index=["Relevance","Program Name (A–Z)","Last Checked (Newest)"].index(qp_get("sort","Relevance")))
    layout_choice = c4.radio("Layout", options=["Auto", "Compact"], index=["Auto","Compact"].index(qp_get("layout","Auto")), horizontal=True)

    # Region pills: top popular + Other(N)
    region_counts = df[COLS["REGION"]].fillna("").astype(str).str.strip().value_counts()
    top_pills = [r for r in region_counts.index if r][:7]
    other_regions = [r for r in region_counts.index if r not in top_pills]
    regions_all = ["All Regions"] + top_pills + ([f"Other ({len(other_regions)})"] if other_regions else [])

    if "pill_region" not in st.session_state or st.session_state.pill_region not in regions_all:
        st.session_state.pill_region = qp_get("pill","All Regions") if qp_get("pill","All Regions") in regions_all else "All Regions"

    pill_html = '<div class="pills">'
    for reg in regions_all:
        cls = "pill active" if reg == st.session_state.pill_region else "pill"
        pill_html += f'<span class="{cls}">{reg}</span>'
    pill_html += "</div>"
    if layout_choice == "Auto":
        st.markdown(pill_html, unsafe_allow_html=True)

    pill_choice = st.selectbox("Choose region", regions_all, index=regions_all.index(st.session_state.pill_region))
    st.session_state.pill_region = pill_choice

    picked_other = None
    if st.session_state.pill_region.startswith("Other"):
        region_query = st.text_input("Search regions", key="region_search")
        options = [r for r in other_regions if region_query.lower() in r.lower()] if region_query else other_regions
        picked_other = st.selectbox("Choose region (Other)", ["—"] + options)

    st.sidebar.header("Page Options")
    default_ps = int(qp_get("ps","12"))
    if default_ps not in [9,12,15,18,24]: default_ps = 12
    page_size = st.sidebar.selectbox("Cards per page", [9, 12, 15, 18, 24], index=[9,12,15,18,24].index(default_ps))

    st.sidebar.header("Filters")

    def base_after_text_and_status(df_in):
        out = df_in.copy()
        if not include_closed:
            out = out[out[COLS["STATUS"]].apply(is_open)]
        if q:
            out = out[fuzzy_mask(out, q, threshold=70)]
        return out

    df_base = base_after_text_and_status(df)

    # Contextual counts
    def contextual_counts(base_df):
        reg_counts = base_df[COLS["REGION"]].fillna("").value_counts().to_dict()
        tag_counts = {}
        for s in base_df[COLS["TAGS"]].fillna("").astype(str):
            for t in parse_tags_field(s):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        return reg_counts, tag_counts

    _, tag_counts_ctx = contextual_counts(df_base)
    tags_all = sorted(all_tags(df), key=lambda t: -tag_counts_ctx.get(t, 0))
    featured_tags = tags_all[:12]
    long_tail = tags_all[12:]

    st.sidebar.markdown("**Featured Tags**")
    _chip_cols = st.sidebar.columns(3)
    if "chip_tag_on" not in st.session_state:
        st.session_state.chip_tag_on = {t: False for t in featured_tags}
    for i, t in enumerate(featured_tags):
        with _chip_cols[i % 3]:
            st.session_state.chip_tag_on[t] = st.checkbox(f"{t} ({tag_counts_ctx.get(t,0)})", value=st.session_state.chip_tag_on[t], key=f"chip_{t}")
    selected_featured = [t for t, on in st.session_state.chip_tag_on.items() if on]

    with st.sidebar.expander("More Tags", expanded=False):
        tag_search = st.text_input("Search tags", key="tag_search")
        lt_options = [t for t in long_tail if tag_search.lower() in t.lower()] if tag_search else long_tail
        sel_more = st.multiselect("Add more tags (AND)", lt_options, default=[])

    sel_tags = selected_featured + sel_more

    # Funding buckets
    labels = [b[0] for b in [
        ("Under $5K",           0,      5_000),
        ("$5K–$25K",            5_000,  25_000),
        ("$25K–$100K",          25_000, 100_000),
        ("$100K–$500K",         100_000, 500_000),
        ("$500K+",              500_000, math.inf),
        ("Unknown / Not stated", None,  None),
    ]]
    with st.sidebar.expander("Funding Amount", expanded=False):
        if "fund_checks" not in st.session_state:
            pre = set(qp_get("fund","").split("|")) if qp_get("fund","") else set()
            st.session_state.fund_checks = {label: (label in pre) for label in labels}
        for label in labels:
            st.session_state.fund_checks[label] = st.checkbox(label, value=st.session_state.fund_checks[label], key=f"fund_{label}")
        sel_funding = [lab for lab, on in st.session_state.fund_checks.items() if on]

    # Region left filter
    st.sidebar.markdown("**Geographic Region**")
    reg_counts_ctx, _ = contextual_counts(df_base)
    regions_list = all_regions(df)
    if "reg_checks" not in st.session_state:
        pre = set(qp_get("regions","").split("|")) if qp_get("regions","") else set()
        st.session_state.reg_checks = {opt: (opt in pre) for opt in regions_list}
    reg_cols = st.sidebar.columns(2)
    for i, opt in enumerate(sorted(regions_list)):
        with reg_cols[i % 2]:
            lbl = f"{opt} ({reg_counts_ctx.get(opt,0)})"
            st.session_state.reg_checks[opt] = st.checkbox(lbl, value=st.session_state.reg_checks[opt], key=f"reg_{opt}")
    sel_regions = [opt for opt, checked in st.session_state.reg_checks.items() if checked]

    if st.sidebar.button("Reset all filters"):
        st.session_state.reg_checks = {opt: False for opt in regions_list}
        st.session_state.chip_tag_on = {t: False for t in featured_tags}
        if 'tag_search' in st.session_state: del st.session_state['tag_search']
        st.session_state.fund_checks = {label: False for label in labels}
        st.session_state.pill_region = "All Regions"
        st.session_state.page = 1
        st.experimental_rerun()

    chip_html = '<div class="chips">'
    if q: chip_html += f'<span class="chip">Search: {q}</span>'
    if st.session_state.pill_region and st.session_state.pill_region != "All Regions":
        chip_html += f'<span class="chip">{st.session_state.pill_region}</span>'
    if picked_other and picked_other != "—": chip_html += f'<span class="chip">{picked_other}</span>'
    for r in sel_regions: chip_html += f'<span class="chip">{r}</span>'
    for t in sel_tags: chip_html += f'<span class="chip">{t}</span>'
    for f_lab in sel_funding: chip_html += f'<span class="chip">{f_lab}</span>'
    chip_html += "</div>"
    st.markdown(chip_html, unsafe_allow_html=True)

    def apply_filters(df_in):
        out = df_in.copy()
        if not include_closed:
            out = out[out[COLS["STATUS"]].apply(is_open)]
        if st.session_state.pill_region and st.session_state.pill_region != "All Regions" and not st.session_state.pill_region.startswith("Other"):
            out = out[out[COLS["REGION"]].astype(str) == st.session_state.pill_region]
        if picked_other and picked_other != "—":
            out = out[out[COLS["REGION"]].astype(str) == picked_other]
        if sel_regions:
            out = out[out[COLS["REGION"]].isin(sel_regions)]
        if sel_tags:
            out = out[out[COLS["TAGS"]].fillna("").apply(lambda s: all(t in parse_tags_field(s) for t in sel_tags))]
        if sel_funding:
            out = out[out["__funding_bucket"].isin(sel_funding)]
        if q:
            out = out[fuzzy_mask(out, q, threshold=70)]
        return out

    fdf = apply_filters(df)
    log_event("filters", q=q, include_closed=include_closed, regions="|".join(sel_regions), tags="|".join(sel_tags), fund="|".join(sel_funding))

    if sort_choice == "Program Name (A–Z)":
        fdf = fdf.sort_values(COLS["PROGRAM_NAME"], na_position="last", kind="stable")
    elif sort_choice == "Last Checked (Newest)":
        fdf["__dt"] = pd.to_datetime(fdf[COLS["LAST_CHECKED"]], errors="coerce")
        fdf = fdf.sort_values("__dt", ascending=False, kind="stable")

    total = len(fdf)
    if "page" not in st.session_state: st.session_state.page = int(qp_get("pg","1") or 1)
    total_pages = max(1, (total + page_size - 1) // page_size)
    st.session_state.page = min(max(1, st.session_state.page), total_pages)

    pcol1, pcol2, pcol3, pcol4 = st.columns([1,2,1,2])
    with pcol1:
        if st.button("Prev", disabled=st.session_state.page <= 1, use_container_width=True):
            st.session_state.page -= 1
    with pcol2:
        goto = st.number_input("Page", min_value=1, max_value=total_pages, value=st.session_state.page)
        if goto != st.session_state.page:
            st.session_state.page = int(goto)
    with pcol3:
        if st.button("Next", disabled=st.session_state.page >= total_pages, use_container_width=True):
            st.session_state.page += 1
    with pcol4:
        csv = fdf.drop(columns=[c for c in fdf.columns if str(c).startswith("__")], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name="pathfinding_results.csv", mime="text/csv", use_container_width=True)
        log_event("download_button_rendered")

    fav_param = "|".join(sorted(st.session_state.favorites))
    st.experimental_set_query_params(
        q=q or "",
        closed="1" if include_closed else "0",
        sort=sort_choice,
        layout=layout_choice,
        pill=st.session_state.pill_region,
        regions="|".join(sel_regions),
        tags="|".join(sel_tags),
        fund="|".join(sel_funding),
        ps=str(page_size),
        pg=str(st.session_state.page),
        fav=fav_param,
    )

    start = (st.session_state.page - 1) * page_size
    end = start + page_size
    page_df = fdf.iloc[start:end].copy()

    if page_df.empty:
        st.info("No programs match your filters. Try clearing one or two filters.")
    else:
        cols_per_row = 3 if layout_choice == "Auto" else 2
        cols = st.columns(cols_per_row)
        for i, (_, row) in enumerate(page_df.iterrows()):
            with cols[i % cols_per_row]:
                name = str(row[COLS["PROGRAM_NAME"]]); org = str(row[COLS["ORG_NAME"]])
                keynorm = str(row[COLS["KEY"]])
                status_val = str(row[COLS["STATUS"]]).strip().lower()
                status_class = "open" if is_open(status_val) else "closed"
                status_label = row[COLS["STATUS"]]
                desc = (str(row[COLS["DESC"]]) or "").strip()
                desc = (desc[:240] + "…") if len(desc) > 240 else desc
                elig = (str(row[COLS["ELIG"]]) or "").strip()
                funding_label = row["__funding_bucket"]
                fresh_txt = freshness_label(row.get("__fresh_days"))

                website = row.get(COLS["WEBSITE"]); email = row.get(COLS["EMAIL"]); phone = row.get(COLS["PHONE"]); contact = row.get(COLS["CONTACT_DERIVED"])

                st.markdown(
                    f"<div class='card'>"
                    f"<span class='badge {status_class}'>{status_label}</span> "
                    f"<span class='tags'>Last checked: {fresh_txt}</span>"
                    f"<h3>{name}</h3><div class='org'>{org}</div>"
                    f"<p>{desc or 'No description provided.'}</p>"
                    + (f\"<div class='tags'><strong>Eligibility:</strong> {elig}</div>\" if elig else "")
                    + (f\"<div class='tags'><strong>Funding:</strong> {funding_label}</div>\" if funding_label else "")
                    f"</div>",
                    unsafe_allow_html=True
                )

                link_bits = []
                if website: link_bits.append(f\"<a class='linkbtn' href='{website}' target='_blank'>Website</a>\")
                if email:   link_bits.append(f\"<a class='linkbtn' href='mailto:{email}' target='_blank'>Email</a>\")
                if phone:   link_bits.append(f\"<a class='linkbtn' href='tel:{phone}' target='_blank'>Call</a>\")
                if contact: link_bits.append(f\"<a class='linkbtn' href='{contact}' target='_blank'>Contact</a>\")
                links_html = \"\".join(link_bits) if link_bits else \"<span class='tags'>No links available</span>\"

                row_links, row_fav = st.columns([5, 2])
                with row_links:
                    st.markdown(links_html, unsafe_allow_html=True)
                with row_fav:
                    fav_on = keynorm in st.session_state.favorites
                    fav_label = "★ Remove favorite" if fav_on else "☆ Add to favorites"
                    if st.button(fav_label, key=f"fav_{keynorm}", use_container_width=True):
                        if fav_on:
                            st.session_state.favorites.remove(keynorm)
                        else:
                            st.session_state.favorites.add(keynorm)
                        log_event("favorite_toggle", key=keynorm, added=(not fav_on))
                        st.experimental_rerun()

                log_event("card_render", key=keynorm)

# ---------- Favorites ----------
with tab_favs:
    log_event("tab_view", tab="Favorites")
    st.subheader("Your Favorites")
    if "favorites" not in st.session_state or not st.session_state.favorites:
        st.info("No favorites yet. Use 'Add to favorites' on a program card.")
    else:
        fav_df = df[df[COLS["KEY"]].isin(st.session_state.favorites)].copy()
        st.write(f"Total favorites: {len(fav_df)}")
        csv = fav_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Favorites CSV", csv, file_name="favorites.csv", mime="text/csv")

# ---------- Suggest a Program ----------
with tab_suggest:
    log_event("tab_view", tab="Suggest")
    st.subheader("Suggest a Program")
    with st.form("suggest_form", clear_on_submit=True):
        s_name = st.text_input("Program Name *")
        s_org = st.text_input("Organization Name *")
        s_url = st.text_input("Program Website")
        s_region = st.text_input("Geographic Region")
        s_tags = st.text_input("Meta Tags (semicolon, slash or comma separated)")
        s_desc = st.text_area("Short Description")
        s_contact_email = st.text_input("Contact Email")
        s_contact_phone = st.text_input("Contact Phone")
        s_submit = st.form_submit_button("Submit")
        if s_submit:
            sub = {
                "Submitted At (UTC)": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "Program Name": s_name, "Organization Name": s_org,
                "Program Website": s_url, "Geographic Region": s_region,
                "Meta Tags": s_tags, "Program Description": s_desc,
                "Email Address": s_contact_email, "Phone Number": s_contact_phone,
            }
            try:
                if Path(INTAKE_FILE).exists():
                    old = pd.read_excel(INTAKE_FILE)
                else:
                    old = pd.DataFrame()
                new = pd.concat([old, pd.DataFrame([sub])], ignore_index=True)
                with pd.ExcelWriter(INTAKE_FILE, engine="openpyxl", mode="w") as writer:
                    new.to_excel(writer, index=False)
                st.success("Thanks! Your suggestion was recorded for review.")
                log_event("suggest_submit")
            except Exception as e:
                st.error(f"Could not write to intake file: {e}")

# ---------- Admin Panel ----------
with tab_admin:
    log_event("tab_view", tab="Admin")
    st.subheader("Admin")
    pw = st.text_input("Enter admin password", type="password")
    if not ADMIN_PASS:
        st.info("Add APP_ADMIN_PASS to Secrets (or env var) to enable admin access.")
    if pw and ADMIN_PASS:
        if pw == ADMIN_PASS:
            st.success("Admin access granted.")
            if Path("Intake_Submissions.xlsx").exists():
                try:
                    intake_df = pd.read_excel("Intake_Submissions.xlsx")
                    st.markdown("### Intake submissions")
                    st.dataframe(intake_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Unable to read intake file: {e}")
            else:
                st.info("No intake submissions yet.")
            st.markdown("### Data quality checks")
            q_missing = df[(df[COLS["WEBSITE"]].fillna("")=="") & (df[COLS["EMAIL"]].fillna("")=="") & (df[COLS["PHONE"]].fillna("")=="")][[COLS["PROGRAM_NAME"], COLS["ORG_NAME"]]]
            q_stale = df[df["__fresh_days"].apply(lambda d: d is not None and d > 180)][[COLS["PROGRAM_NAME"], COLS["ORG_NAME"], COLS["LAST_CHECKED"]]]
            norm = lambda s: re.sub(r"[^a-z0-9]+","", str(s).lower())
            df["__dup_key"] = df.apply(lambda r: norm(r[COLS["PROGRAM_NAME"]]) + "|" + norm(r[COLS["ORG_NAME"]]), axis=1)
            dups = df[df["__dup_key"].duplicated(keep=False)].sort_values("__dup_key")[[COLS["PROGRAM_NAME"], COLS["ORG_NAME"]]]
            st.write("Missing all contacts:", len(q_missing)); st.dataframe(q_missing, use_container_width=True)
            st.write("Stale 'Last Checked' (> 180 days):", len(q_stale)); st.dataframe(q_stale, use_container_width=True)
            st.write("Possible duplicates:", len(dups)); st.dataframe(dups, use_container_width=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if not q_missing.empty:
                    st.download_button("Download Missing Contacts CSV", q_missing.to_csv(index=False).encode("utf-8"), file_name="qc_missing_contacts.csv", mime="text/csv")
            with c2:
                if not q_stale.empty:
                    st.download_button("Download Stale Rows CSV", q_stale.to_csv(index=False).encode("utf-8"), file_name="qc_stale_rows.csv", mime="text/csv")
            with c3:
                if not dups.empty:
                    st.download_button("Download Duplicates CSV", dups.to_csv(index=False).encode("utf-8"), file_name="qc_duplicates.csv", mime="text/csv")
        else:
            st.error("Incorrect password.")

# ---------- Footer ----------
st.markdown('<div class="band gold">Need help? See How to use, Suggest a program, or Contact us.</div>', unsafe_allow_html=True)
