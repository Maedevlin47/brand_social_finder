"""
Rich table formatting for brand handle results.
"""

from rich.console import Console
from rich.table import Table

console = Console()

COLUMNS = [
    ("Brand", "cyan", 24),
    ("Source", "magenta", 22),
    ("Country", "yellow", 12),
    ("Website", "white", 28),
    ("Instagram", "green", 22),
    ("X Handle", "blue", 20),
    ("Review?", "red", 8),
    ("Confidence", "white", 10),
    ("Notes", "white", 36),
]


def _make_table(title: str = "") -> Table:
    table = Table(title=title, show_lines=False, highlight=True, expand=False)
    for name, style, width in COLUMNS:
        table.add_column(name, style=style, max_width=width, no_wrap=False)
    return table


def _row_values(row: dict) -> tuple:
    confidence = row.get("confidence_score", "")
    confidence_str = f"{confidence}/100" if confidence != "" else ""
    manual_review = row.get("manual_review", False)
    review_str = "Yes" if manual_review and str(manual_review).lower() not in ("false", "0", "") else ""
    return (
        row.get("brand_name", ""),
        row.get("source_name", ""),
        row.get("country", ""),
        row.get("website", "") or "",
        row.get("instagram_handle", "") or "",
        row.get("x_handle", "") or "",
        review_str,
        confidence_str,
        row.get("notes", "") or "",
    )


def print_single_result(row: dict) -> None:
    """Print a single-brand result as a one-row Rich table."""
    table = _make_table("Brand Handle Lookup")
    table.add_row(*_row_values(row))
    console.print(table)


def build_batch_table(rows: list[dict], title: str = "Brand Handle Results") -> Table:
    """Build a Rich table from a list of result dicts (for Live rendering)."""
    table = _make_table(title)
    for row in rows:
        table.add_row(*_row_values(row))
    return table
