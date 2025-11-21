import streamlit as st
import pandas as pd
import base64
from pathlib import Path

# ------------------------ Config ------------------------
st.set_page_config(page_title="Small Business Supports Finder", layout="wide")

# ------------------------ Load CSS ------------------------
def load_css():
    css_files = [
        "assets/style.css",
        "assets/goa-components.css",
        "assets/goa-application-layouts.css",
        "assets/goa-application-layout.print.css",
    ]
    for file in css_files:
        path = Path(file)
        if path.exists():
            st.markdown(f"<style>{path.read_text()}</style>", unsafe_allow_html=True)

load_css()

# ------------------------ Load Logo ------------------------
def embed_logo():
    svg = Path("assets/GoA-logo.svg")
    png = Path("assets/GoA-logo.png")
    if svg.exists():
        b64 = base64.b64encode(svg.read_bytes()).decode()
        return f'<img src="data:image/svg+xml;base64,{b64}" alt="Government of Alberta" style="height:44px;">'
    elif png.exists():
        b64 = base64.b64encode(png.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="Government of Alberta" style="height:44px;">'
    return '<div style="font-weight:700;font-size:18px">Government of Alberta</div>'

# ------------------------ Header ------------------------
st.markdown('<a class="skip-link" href="#results">Skip to results</a>', unsafe_allow_html=True)
st.markdown(
    '<div class="header goa-header goa-app-header">'
    f'{embed_logo()}'
    '<div>'
    '<h2>Small Business Supports Finder</h2>'
    '<p>Helping Alberta entrepreneurs and small businesses find programs, funding, and services quickly.</p>'
    '</div>'
    '</div>'
    '<div class="header-spacer"></div>',
    unsafe_allow_html=True
)

# ------------------------ Load Data ------------------------
DATA_FILE = "Pathfinding_Master.xlsx"
data_path = Path(DATA_FILE)
if not data_path.exists():
    st.error("❌ Pathfinding_Master.xlsx not found.")
    st.stop()

df = pd.read_excel(data_path)

# ------------------------ Display Filters ------------------------
st.sidebar.header("Filter results")
funding = st.sidebar.multiselect("Funding type", df["Funding"].dropna().unique())
region = st.sidebar.multiselect("Region", df["Region"].dropna().unique())
audience = st.sidebar.multiselect("Audience", df["Audience"].dropna().unique())

filtered_df = df.copy()
if funding:
    filtered_df = filtered_df[filtered_df["Funding"].isin(funding)]
if region:
    filtered_df = filtered_df[filtered_df["Region"].isin(region)]
if audience:
    filtered_df = filtered_df[filtered_df["Audience"].isin(audience)]

# ------------------------ Display Results ------------------------
st.markdown('<div id="results"></div>', unsafe_allow_html=True)
st.markdown(f"### {len(filtered_df)} Matching Supports")

for _, row in filtered_df.iterrows():
    st.markdown(f"""
<div class="pf-card-marker">
  <h4>{row.get("Program Name", "No title")}</h4>
  <p>{row.get("Description", "No description")}</p>
  <div class="actions-row actions-links">
    <a href="{row.get("Website", "#")}" target="_blank">Website</a>
    <a href="mailto:{row.get("Email", "")}">Email</a>
    <a href="tel:{row.get("Phone", "")}">Call</a>
    <a href="#">Favourite</a>
  </div>
</div>
""", unsafe_allow_html=True)