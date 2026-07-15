"""Consistent page heading."""

import streamlit as st

from utils.formatting import text


def page_title(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="cv-page-head"><h1>{text(title)}</h1><p>{text(subtitle)}</p></div>', unsafe_allow_html=True)
