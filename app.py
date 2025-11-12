import math
import re
from typing import List, Optional

import pandas as pd
import streamlit as st

# =========================
# ---- APP CONFIG / CSS ----
# =========================
st.set_page_config(
    page_title="Alberta Pathfinding Tool",
    page_icon="✅",
    layout="wide",
)

GOA_PRIMARY = "#003A70"  # deep navy
CARD_BORDER = "#E6EAF0"

st.markdown(
    f"""
    <style>
        /* Sticky global header */
        .goa-sticky {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: {GOA_PRIMARY};
            color: white;
            padding: 14px 18px;
            border-bottom: 1px solid rgba(255,255,255,0.15);
        }}
        .goa-title {{ font-weight: 700; font-size: 20px; letter-spacing: .2px; }}
        .goa-subtitle {{ font-size: 12.5px; opacity: .9; margin-top: 2px; }}

        /* Cards */
        .program-card {{
            background: #fff;
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
            padding: 16px 18px;
            transition: transform .06s ease, box-shadow .06s ease, border-color .06s ease;
        }}
        .program-card:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 22px rgba(0,0,0,.06);
            border-color: #d7dfea;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radi
