import os
from typing import List, Optional

import numpy as np
import pandas as pd
import streamlit as st

# ------------------------- Constants & config -------------------------

ALBERTA_DARK_BLUE = "#002c4e"
ALBERTA_LINK_BLUE = "#0077cd"
ALBERTA_TEXT = "#333333"

UNKNOWN = "Unknown, not stated"

st.set_page_config(
    page_title="Small Business Supports Finder",
    page_icon="✅",
    layout="wide",
)

# ------------------------- CSS & layout helpers -------------------------


def embed_css() -> None:
    """Inject Alberta.ca-style colours, typography and pill / chip styling."""
    st.markdown(
        f"""
<style>
html, body, [class*="block-container"] {{
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  color: {ALBERTA_TEXT};
}}

h1, h2, h3, h4 {{
  font-weight: 600;
  color: {ALBERTA_TEXT};
}}

a {{
  color: {ALBERTA_LINK_BLUE};
}}

.header-hero {{
  width: 100%;
  background: {ALBERTA_DARK_BLUE};
  color: white;
  padding: 18px 0 24px 0;
}}

.header-inner {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}}

.hero-title {{
  font-size: 2rem;
  font-weight: 600;
  margin: 4px 0 0 0;
}}

.hero-subtitle {{
  font-size: 0.95rem;
  opacity: 0.9;
  margin-top: 4px;
}}

.section-divider {{
  border-top: 1px solid #e5e7eb;
  margin: 16px 0 24px 0;
}}

.callout {{
  background: #e5f3ff;
  border-left: 4px solid {ALBERTA_LINK_BLUE};
  padding: 12px 14px;
  border-radius: 6px;
  font-size: 0.9rem;
  margin-bottom: 12px;
}}

.question-heading {{
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
}}

.helper-text {{
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 8px;
}}

/* Pill / chip style for multiselect tags */
.css-1n76uvr, .css-1w1xk2l, [data-baseweb="tag"] {{
  border-radius: 999px !important;
  border: 1px solid #d1d5db !important;
  background-color: #ffffff !important;
  color: {ALBERTA_TEXT} !important;
  padding-top: 2px !important;
  padding-bottom: 2px !important;
  font-size: 0.85rem !important;
}}

[data-baseweb="tag"] span {{
  font-size: 0.85rem !important;
}}

/* Selected options in multiselect dropdown */
.stMultiSelect [aria-selected="true"] {{
  background-color: {ALBERTA_LINK_BLUE} !important;
  color: white !important;
}}

/* Buttons – Alberta link-blue */
.stButton>button {{
  background-color: {ALBERTA_LINK_BLUE};
  color: white;
  border-radius: 999px;
  border: none;
  padding: 0.45rem 1.1rem;
  font-size: 0.9rem;
}}

.stButton>button:hover {{
  background-color: #0061a4;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Alberta.ca-style hero header."""
    st.markdown(
        f"""
<div class="header-hero">
  <div class="header-inner">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
      <span style="font-size:1.1rem; font-weight:600;">Government of Alberta</span>
    </div>
    <div class="hero-title">Find programs and supports for your Alberta business</div>
    <div class="hero-subtitle">
      Helping Alberta entrepreneurs and small businesses find programs, funding and services quickly.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ------------------------- Data loading -------------------------


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    """Load the repository data. Update `path` for your environment."""
    ext = os.path.splitext(path)[1].lower()
    if ext in [".csv"]:
        df = pd.read_csv(path)
    elif ext in [".xlsx", ".xlsm", ".xls"]:
        df = pd.read_excel(path)
    elif ext in [".parquet"]:
        df = pd.read_parquet(path)
    else:
        st.error(f"Unsupported data file type: {ext}")
        return pd.DataFrame()

    return df


def pick_column(df: pd.DataFrame, options: List[str]) -> Optional[str]:
    """Return the first column name from `options` that exists in df."""
    for name in options:
        if name in df.columns:
            return name
    return None


# ------------------------- Filter UI & logic -------------------------


def build_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render filter controls and return filtered dataframe."""

    # Column mappings – adjust here if your names differ
    col_support_type = pick_column(df, ["Type of support", "Type of Support", "Support type"])
    col_audience = pick_column(df, ["Target Audience(s)", "Who the program is for", "Audience"])
    col_funding_type = pick_column(df, ["Funding type", "Funding Type", "Type of funding"])
    col_owned_by = pick_column(df, ["Owned by", "Priority audiences", "Owned By"])
    col_region = pick_column(df, ["Service region", "Service Region", "Region"])
    col_delivery = pick_column(df, ["Delivery method", "Delivery", "Support delivery"])
    col_title = pick_column(df, ["Program name", "Program", "Title"])
    col_org = pick_column(df, ["Organization", "Organisation", "Program owner"])

    # Defaults if missing
    if col_title is None:
        col_title = df.columns[0]
    if col_org is None:
        col_org = df.columns[1]

    # Left column = filters, right = content
    col_filters, col_main = st.columns([0.32, 0.68])

    with col_filters:
        st.markdown("### Filter programs")

        # 1. What type of support do you need?
        if col_support_type:
            st.markdown('<div class="question-heading">What type of support do you need?</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="helper-text">You can select one or more support types.</div>',
                unsafe_allow_html=True,
            )
            support_options = sorted(df[col_support_type].fillna(UNKNOWN).unique())
            selected_support = st.multiselect(
                "Support type",
                options=support_options,
                default=[],
                label_visibility="collapsed",
            )
        else:
            selected_support = []

        # 2. Who is this program meant for?
        if col_audience:
            st.markdown('<div class="question-heading">Who is this program meant for?</div>', unsafe_allow_html=True)
            audience_options = sorted(df[col_audience].fillna(UNKNOWN).unique())
            selected_audience = st.multiselect(
                "Who the program is for",
                options=audience_options,
                default=[],
                label_visibility="collapsed",
            )
        else:
            selected_audience = []

        # 3. Are you looking for funding?
        st.markdown('<div class="question-heading">Are you looking for funding?</div>', unsafe_allow_html=True)
        funding_choice = st.radio(
            "Funding?",
            options=["Show all programs", "Funding only", "Non-funding supports only"],
            index=0,
            label_visibility="collapsed",
        )

        # 4. What kind of funding are you looking for?
        if col_funding_type and funding_choice in ("Show all programs", "Funding only"):
            st.markdown('<div class="question-heading">What kind of funding are you looking for?</div>', unsafe_allow_html=True)
            funding_options = sorted(df[col_funding_type].fillna(UNKNOWN).unique())
            selected_funding_types = st.multiselect(
                "Funding type",
                options=funding_options,
                default=[],
                label_visibility="collapsed",
            )
        else:
            selected_funding_types = []

        # 5. Are you part of a priority group?
        if col_owned_by:
            st.markdown('<div class="question-heading">Are you part of a priority group?</div>', unsafe_allow_html=True)
            audience_options2 = sorted(df[col_owned_by].fillna(UNKNOWN).unique())
            selected_priority = st.multiselect(
                "Priority audiences",
                options=audience_options2,
                default=[],
                label_visibility="collapsed",
            )
        else:
            selected_priority = []

        # 6. Where is your business located?
        if col_region:
            st.markdown('<div class="question-heading">Where is your business located?</div>', unsafe_allow_html=True)
            region_options = ["All regions"] + sorted(
                [r for r in df[col_region].dropna().unique() if str(r).strip()]
            )
            region_choice = st.selectbox(
                "Region",
                options=region_options,
                index=0,
                label_visibility="collapsed",
            )
        else:
            region_choice = "All regions"

        # 7. How do you prefer to access the support?
        if col_delivery:
            st.markdown('<div class="question-heading">How do you prefer to access the support?</div>', unsafe_allow_html=True)
            delivery_options = sorted(df[col_delivery].fillna(UNKNOWN).unique())
            selected_delivery = st.multiselect(
                "Delivery method",
                options=delivery_options,
                default=[],
                label_visibility="collapsed",
            )
        else:
            selected_delivery = []

    # ----------------- Apply filters -----------------

    filt = df.copy()

    # Support type
    if selected_support and col_support_type:
        filt = filt[filt[col_support_type].fillna(UNKNOWN).isin(selected_support)]

    # Audience
    if selected_audience and col_audience:
        filt = filt[filt[col_audience].fillna(UNKNOWN).isin(selected_audience)]

    # Funding yes/no
    if funding_choice != "Show all programs" and col_funding_type:
        is_funding = filt[col_funding_type].notna() & (filt[col_funding_type].str.strip() != "")
        if funding_choice == "Funding only":
            filt = filt[is_funding]
        else:
            filt = filt[~is_funding]

    # Funding types
    if selected_funding_types and col_funding_type:
        filt = filt[filt[col_funding_type].fillna(UNKNOWN).isin(selected_funding_types)]

    # Priority audiences (simple contains match – adjust if you use booleans)
    if selected_priority and col_owned_by:
        mask = np.zeros(len(filt), dtype=bool)
        owned_series = filt[col_owned_by].fillna("").astype(str)
        for val in selected_priority:
            mask |= owned_series.str.contains(str(val), case=False, na=False)
        filt = filt[mask]

    # Region
    if region_choice != "All regions" and col_region:
        filt = filt[filt[col_region].fillna("").astype(str) == str(region_choice)]

    # Delivery
    if selected_delivery and col_delivery:
        filt = filt[filt[col_delivery].fillna(UNKNOWN).isin(selected_delivery)]

    # ----------------- Main content -----------------

    with col_main:
        st.markdown("### Browse matching programs")

        search_query = st.text_input(
            "Search programs by keyword, program name or organization",
            "",
            help="Search also matches similar terms and common spellings.",
        )

        sort_choice = st.selectbox(
            "Sort results by",
            ["Relevance", "Program name (A–Z)"],
            index=0,
        )

        # Simple keyword filter (title + org)
        if search_query.strip():
            q = search_query.strip().lower()
            mask = (
                filt[col_title].fillna("").str.lower().str.contains(q)
                | filt[col_org].fillna("").str.lower().str.contains(q)
            )
            filt = filt[mask]

        # Simple sort
        if sort_choice == "Program name (A–Z)":
            filt = filt.sort_values(by=col_title)

        st.caption(f"{len(filt):,} programs found.")

        # Render cards
        for _, row in filt.iterrows():
            st.markdown("---")
            st.markdown(f"#### {row.get(col_title, '')}")
            st.markdown(f"*{row.get(col_org, '')}*")
            # Short description if available
            desc_col = pick_column(df, ["Program description", "Description", "Short description"])
            if desc_col:
                st.write(row.get(desc_col, ""))

    return filt


# ------------------------- Main app -------------------------


def main() -> None:
    embed_css()
    render_header()

    # Divider between hero and tool body
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Questionnaire callout
    st.markdown(
        """
<div class="callout">
  <strong>We’re looking for feedback to make this tool better.</strong><br>
  Please take a short questionnaire to share your thoughts.
</div>
""",
        unsafe_allow_html=True,
    )
    st.button("Take the questionnaire")

    data_path = os.getenv("SB_TOOL_DATA_PATH", "data/programs.xlsx")
    df = load_data(data_path)
    if df.empty:
        st.warning("Data could not be loaded. Please update `data_path` in app.py.")
        return

    _ = build_filters(df)

    # Contact and Support block (from PPT)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### Contact and Support")
    st.write(
        "Biz Connect provides supports to help Alberta entrepreneurs and small "
        "businesses start, grow and succeed."
    )
    st.write(
        "For questions on this tool or additional support, contact "
        "[bizconnect@gov.ab.ca](mailto:bizconnect@gov.ab.ca)."
    )
    st.write(
        "More resources for small businesses are available at "
        "[alberta.ca/small-business-resources](https://www.alberta.ca/small-business-resources)."
    )
    st.write(
        "If you are an investor, find investment-related data and resources at "
        "[investmenthub.alberta.ca](https://investmenthub.alberta.ca)."
    )


if __name__ == "__main__":
    main()
