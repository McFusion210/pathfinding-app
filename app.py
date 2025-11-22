import os
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple, Set

import numpy as np
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

UNKNOWN = "Unknown, not stated"
FUZZY_THR = 60

# Global column map, filled in main()
COLS: Dict[str, str] = {}


# ---------------------- STYLING / CHROME ----------------------


def embed_css() -> None:
    st.markdown(
        """
<style>
:root{
  --bg:#FFFFFF; --surface:#FFFFFF; --text:#0A0A0A; --muted:#4B5563;
  --primary:#003366; --primary-2:#007FA3; --border:#D9DEE7; --link:#007FA3;
  --fs-title:24px; --fs-body:15px; --fs-meta:13px;
}

/* Global text and layout */
html, body, p, div, span{
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Segoe UI Emoji";
  color:var(--text);
}
p{ margin:4px 0 4px 0; }
small{ font-size:var(--fs-meta); }

/* Search box */
div[data-testid="stTextInput"] > div > div {
  border-radius: 999px;
  border: 2px solid #C3D0E6;
  background: #F3F4F6;
  padding: 4px 10px;
}
div[data-testid="stTextInput"] input{
  border:none !important;
  box-shadow:none !important;
  background:transparent !important;
}
div[data-testid="stTextInput"] input::placeholder{
  color:#6B7280;
  opacity:1;
}

/* Header */
.goa-header{
  background:#003366;
  color:#FFFFFF;
  padding:16px 32px;
  display:flex;
  align-items:center;
  gap:16px;
  position:sticky;
  top:0;
  z-index:50;
}
.goa-header-logo{
  width:140px;
  height:auto;
}
.goa-header-text h1{
  font-size:22px;
  margin:0;
  font-weight:600;
}
.goa-header-text p{
  margin:2px 0 0 0;
  font-size:14px;
  opacity:.9;
}

/* App shell */
.app-shell{
  padding:18px 32px 32px 32px;
  background:#F3F4F6;
}
.block-container{
  padding-top:0 !important;
}

/* Program cards */
.pf-card-marker{
  border-radius:12px;
  border:1px solid var(--border);
  padding:16px 16px 14px 16px;
  background:var(--surface);
  margin-bottom:12px;
  box-shadow:0 1px 2px rgba(15,23,42,0.04);
}
.pf-card-marker:hover{
  box-sha
