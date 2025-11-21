import streamlit as st
from pathlib import Path
import base64
import pandas as pd
import re

# ---------------------------- Streamlit config ----------------------------
st.set_page_config(
    page_title="Small Business Supports Finder",
    layout="wide",
)

# ---------------------------- Load external CSS ----------------------------
def load_local_css(file_path: str):
    path = Path(file_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load your style.css
load_local_css("assets/style.css")

# Optionally load GoA styles (if present)
for fname in [
    "goa-application-layouts.css",
    "goa-application-layout.print.css",
    "goa-components.css",
]:
    fpath = Path(f"assets/{fname}")
    if fpath.exists():
        load_local_css(str(fpath))

# ---------------------------- Header ----------------------------
def embed_logo_html():
    svg_path = Path("assets/GoA-logo.svg")
    png_path = Path("assets/GoA-logo.png")
    if svg_path.exists():
        b64 = base64.b64encode(svg_path.read_bytes()).decode()
        return f'<img src="data:image/svg+xml;base64,{b64}" alt="Government of Alberta" style="height:44px;">'
    elif png_path.exists():
        b64 = base64.b64encode(png_path.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="Government of Alberta" style="height:44px;">'
    return '<div style="font-weight:700;font-size:18px">Government of Alberta</div>'

st.markdown('<a class="skip-link" href="#results-main">Skip to results</a>', unsafe_allow_html=True)
st.markdown(f"""
<div class="header goa-header goa-app-header">
  {embed_logo_html()}
  <div>
    <h2>Small Business Supports Finder</h2>
    <p>Helping Alberta entrepreneurs and small businesses find programs, funding, and services quickly.</p>
  </div>
</div>
<div class="header-spacer"></div>
""", unsafe_allow_html=True)

# ---------------------------- Upload Data (Example) ----------------------------
st.markdown("### Upload your program data")
data_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if data_file:
    df = pd.read_excel(data_file)
    st.success(f"Loaded {len(df)} records.")
    st.dataframe(df.head())
else:
    st.info("Please upload a file to begin.")
