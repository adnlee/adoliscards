"""Dashboard metric component."""

import streamlit as st

from utils.formatting import text


def stat_card(label: str, value: str, icon: str, detail: str = "", tone: str = "blue") -> None:
    st.markdown(
        f'<div class="cv-stat {tone}"><div class="cv-stat-top"><span>{text(label)}</span><b>{icon}</b></div>'
        f'<div class="cv-stat-value">{text(value)}</div><small>{text(detail, "")}</small></div>',
        unsafe_allow_html=True,
    )
