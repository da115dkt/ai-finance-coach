"""Shared constants and helper functions for bank statement PDF parsing."""

from __future__ import annotations

import re

from coach.ingest.imports.base import ParseError, Row, parse_amount

MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PDF_PAGES = 50

_TX_TABLE_HEADER_RE = re.compile(
    r"\b("
    # Dutch
    r"datum\s+omschrijving|boekdatum|valutadatum|vorig\s+saldo|nieuw\s+saldo|af\s+bij|bij\s+af|"
    # German
    r"buchungstag|alter\s+kontostand|neuer\s+kontostand|wertstellung|vorgang/verwendungszweck|"
    # French
    r"date\s+op[ée]ration|ancien\s+solde|nouveau\s+solde|solde\s+au|date\s+de\s+valeur|"
    # English
    r"date\s+description|booking\s+date|value\s+date|previous\s+balance|new\s+balance|debit\s+credit|credit\s+debit"
    r")\b",
    re.I,
)

_TX_ROW_PATTERN = re.compile(
    r"^\s*\d{2}[./-]\d{2}(?:[./-]\d{2,4})?\s+.*[+-]?\d+[\.,]\d{2}[+-]?\s*$"
)


def extract_statement_header(text: str, max_lines: int = 40) -> str:
    """Extract the header portion of a statement before transaction rows begin.

    Inspects lines from the start of the text and stops before the transaction
    table starts or when a transaction row is encountered.
    """
    lines = (text or "").splitlines()
    header_lines: list[str] = []
    for line in lines[:max_lines]:
        if _TX_TABLE_HEADER_RE.search(line) or _TX_ROW_PATTERN.search(line):
            break
        header_lines.append(line)
    return "\n".join(header_lines)


def parse_signed_amount(
    amt_str: str,
    decimal: str = ",",
    thousands: str | None = None,
    allow_unsigned: bool = False,
) -> float:
    """Parse an amount string requiring or allowing an explicit sign (+ or -)."""
    cleaned = re.sub(r"[€$£\s  ]|EUR|USD|GBP|CHF", "", (amt_str or "").strip(), flags=re.I)
    has_sign = cleaned.startswith(("+", "-")) or cleaned.endswith(("+", "-"))
    if not has_sign and not allow_unsigned:
        raise ValueError(f"missing explicit sign (+ or -): {amt_str!r}")
    return parse_amount(cleaned, decimal=decimal, thousands=thousands or "")


def year_rollover(stmt_year: int, stmt_month: int, tx_month: int) -> int:
    """Calculate transaction year accounting for year rollover at year-end boundaries.

    E.g., if statement is in January and transaction month is December, the transaction year is stmt_year - 1.
    """
    return stmt_year - 1 if tx_month == 12 and stmt_month == 1 else stmt_year


def reconcile_balances(
    old_bal: float | None,
    new_bal: float | None,
    rows: list[Row],
    warnings: list[str],
    force: bool,
) -> None:
    """Reconcile the sum of transactions against start and end balances."""
    if old_bal is not None and new_bal is not None and rows:
        actual_sum = round(sum(r.amount for r in rows), 2)
        diff = round(old_bal + actual_sum - new_bal, 2)
        if abs(diff) >= 0.01:
            msg = (
                f"checksum mismatch: old balance {old_bal:.2f} + sum {actual_sum:.2f} != "
                f"new balance {new_bal:.2f} (diff: {diff:+.2f})"
            )
            if not force:
                raise ParseError(msg)
            warnings.append(msg)


# Backwards-compatible alias
_reconcile_balances = reconcile_balances


__all__ = [
    "MAX_PDF_PAGES",
    "MAX_PDF_SIZE_BYTES",
    "_reconcile_balances",
    "extract_statement_header",
    "parse_signed_amount",
    "reconcile_balances",
    "year_rollover",
]
