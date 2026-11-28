"""Shared base structures, exceptions and utilities for statement imports."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from coach.ingest.imports.profiles import Profile


class ParseError(Exception):
    pass


@dataclass
class Row:
    date: str
    amount: float
    currency: str
    description: str
    value_date: str | None = None
    counterparty: str = ""
    reference: str | None = None
    raw: dict = field(default_factory=dict)
    line: int = 0


@dataclass
class Parsed:
    format: str
    rows: list[Row]
    iban: str | None = None
    currency: str | None = None
    warnings: list[str] = field(default_factory=list)


def parse_amount(text: str, decimal: str = "auto", thousands: str = "") -> float:
    t = (text or "").strip()
    if not t:
        raise ValueError("empty amount")
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1]
    t = re.sub(r"[€$£\s  ]|EUR|USD|GBP|CHF", "", t, flags=re.I)
    if t.endswith("-"):
        neg, t = True, t[:-1]
    if t.startswith("+"):
        t = t[1:]
    if t.endswith("+"):
        t = t[:-1]
    if thousands:
        t = t.replace(thousands, "")
    if decimal == "auto":
        if "," in t and "." in t:
            decimal = "," if t.rfind(",") > t.rfind(".") else "."
        elif "," in t:
            decimal = "," if re.search(r",\d{1,2}$", t) else "."  # "1,234" = thousands
        else:
            decimal = "."
    if decimal == ",":
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        raise ValueError(f"not an amount: {text!r}")
    v = float(t)
    return -v if neg else v


__all__ = [
    "ParseError",
    "Parsed",
    "Profile",
    "Row",
    "parse_amount",
]
