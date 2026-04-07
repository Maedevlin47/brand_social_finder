#!/usr/bin/env python3
"""
CSV utilities for brand handle results.

Brand research is performed via the /find-brand-handle Claude Code slash command.
This module provides helpers for reading input CSVs and writing output CSVs in the
canonical column format.
"""

import csv
from pathlib import Path

OUTPUT_FIELDNAMES = [
    "brand_name",
    "source_name",
    "country",
    "website",
    "instagram_handle",
    "x_handle",
    "manual_review",
    "confidence_score",
    "confidence_signals",
    "notes",
]


def _find_source_column(fieldnames: list[str]) -> str | None:
    """Return the first fieldname matching List/Source/Source List (case-insensitive)."""
    accepted = {"list", "source", "source list"}
    for name in fieldnames:
        if name.strip().lower() in accepted:
            return name
    return None


def load_input_csv(input_path: Path) -> list[dict]:
    """Read a brands input CSV (columns: Name, List/Source/Source List, Location) and return normalised dicts."""
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        source_col = _find_source_column(reader.fieldnames or [])
        return [
            {
                "brand_name": row["Name"].strip(),
                "source_name": (row[source_col].strip() if source_col else ""),
                "country": row["Location"].strip(),
            }
            for row in reader
        ]


def load_existing_results(output_path: Path) -> dict[str, dict]:
    """Return a dict keyed by brand_name of rows already written to the output CSV."""
    existing: dict[str, dict] = {}
    if not output_path.exists():
        return existing
    with output_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("brand_name", "").strip()
            if name:
                existing[name] = row
    return existing


def write_results(output_path: Path, rows: list[dict]) -> None:
    """Write result rows to a CSV, joining confidence_signals lists with '; '."""
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        serialized = []
        for row in rows:
            r = dict(row)
            signals = r.get("confidence_signals", [])
            if isinstance(signals, list):
                r["confidence_signals"] = "; ".join(signals)
            serialized.append(r)
        writer.writerows(serialized)
