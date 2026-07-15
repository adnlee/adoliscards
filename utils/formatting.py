"""Safe display formatting shared by CardVault pages."""

from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd


def text(value: Any, fallback: str = "—") -> str:
    """Return escaped display text without leaking null-like values."""
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return fallback
    rendered = str(value).strip()
    return escape(rendered) if rendered else fallback


def money(value: Any) -> str:
    """Format a database numeric value as US currency."""
    try:
        return f"${float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def number(value: Any) -> float:
    """Convert a nullable database value to a finite float."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
