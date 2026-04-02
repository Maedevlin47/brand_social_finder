#!/usr/bin/env python3
"""
brand_handle_finder — find official Instagram and Twitter/X handles for brands.

Single mode:
    python main.py --brand "Biti's" --source "Vietnamese Footwear Brands" --country "Vietnam"

Batch mode:
    python main.py --file brands.csv --output results.csv
"""

import argparse
import csv
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from formatter import build_batch_table, console, print_single_result
from searcher import BrandSearcher

load_dotenv()

OUTPUT_FIELDNAMES = [
    "brand_name",
    "source_name",
    "country",
    "website",
    "instagram_handle",
    "twitter_handle",
    "manual_review",
    "confidence",
    "confidence_signals",
    "notes",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not set. "
            "Add it to a .env file or export it in your shell."
        )
        sys.exit(1)
    return key


def _load_existing_results(output_path: Path) -> dict[str, dict]:
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


def _write_results(output_path: Path, rows: list[dict]) -> None:
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


# ---------------------------------------------------------------------------
# Single-brand mode
# ---------------------------------------------------------------------------


def run_single(args: argparse.Namespace) -> None:
    searcher = BrandSearcher(api_key=_get_api_key())

    console.print(
        f"\nSearching for [bold cyan]{args.brand}[/bold cyan] "
        f"([dim]{args.country}[/dim]) …\n"
    )

    with Live(
        Spinner("dots", text=Text("Querying Claude with web search…", style="dim")),
        console=console,
        refresh_per_second=10,
    ):
        result = searcher.search(
            brand_name=args.brand,
            source_name=args.source,
            country=args.country,
        )

    row = {
        "brand_name": args.brand,
        "source_name": args.source,
        "country": args.country,
        **result,
    }
    print_single_result(row)


# ---------------------------------------------------------------------------
# Batch mode
# ---------------------------------------------------------------------------


def run_batch(args: argparse.Namespace) -> None:
    input_path = Path(args.file)
    output_path = Path(args.output)

    if not input_path.exists():
        console.print(f"[bold red]Error:[/bold red] Input file not found: {input_path}")
        sys.exit(1)

    # Read input CSV
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        brands = [
            {
                "brand_name": row["Name"].strip(),
                "source_name": row.get("List", "").strip(),
                "country": row["Location"].strip(),
            }
            for row in reader
        ]

    if not brands:
        console.print("[yellow]Input CSV is empty — nothing to process.[/yellow]")
        return

    # Resumability: load already-completed results
    existing = _load_existing_results(output_path)
    results: list[dict] = list(existing.values())
    skipped = len(existing)

    if skipped:
        console.print(
            f"[dim]Resuming: {skipped} brand(s) already processed, "
            f"{len(brands) - skipped} remaining.[/dim]\n"
        )

    searcher = BrandSearcher(api_key=_get_api_key())
    todo = [b for b in brands if b["brand_name"] not in existing]
    lock = threading.Lock()

    def process(brand: dict) -> dict:
        for attempt in range(5):
            try:
                result = searcher.search(
                    brand_name=brand["brand_name"],
                    source_name=brand["source_name"],
                    country=brand["country"],
                )
                return {**brand, **result}
            except Exception as exc:
                if "rate_limit" in str(exc).lower() or "429" in str(exc):
                    wait = 10 * (attempt + 1)
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError(f"Rate limit retries exhausted for {brand['brand_name']}")

    with Live(
        build_batch_table(results),
        console=console,
        refresh_per_second=4,
        vertical_overflow="visible",
    ) as live:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process, b): b for b in todo}
            for future in as_completed(futures):
                row = future.result()
                with lock:
                    results.append(row)
                    existing[row["brand_name"]] = row
                    live.update(build_batch_table(results))

    # Write final CSV
    _write_results(output_path, results)
    console.print(
        f"\n[bold green]Done.[/bold green] "
        f"{len(results)} result(s) written to [cyan]{output_path}[/cyan]"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brand_handle_finder",
        description="Find official Instagram and Twitter/X handles for brands.",
    )
    sub = parser.add_subparsers(dest="mode")

    # Allow positional-style single mode directly on the root parser
    # so both invocations work:
    #   python main.py --brand X --source Y --country Z   (single)
    #   python main.py --file f.csv --output r.csv         (batch)

    single = parser.add_argument_group("single-brand mode")
    single.add_argument("--brand", metavar="NAME", help="Brand name to look up")
    single.add_argument("--source", metavar="LIST", help="Source list name", default="")
    single.add_argument("--country", metavar="COUNTRY", help="Country/region of the brand", default="")

    batch = parser.add_argument_group("batch mode")
    batch.add_argument(
        "--file", metavar="CSV", help="Input CSV with columns: brand_name, source_name, country"
    )
    batch.add_argument("--output", metavar="CSV", default="results.csv", help="Output CSV path (default: results.csv)")
    batch.add_argument("--workers", metavar="N", type=int, default=8, help="Parallel workers (default: 8)")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.brand:
        if not args.country:
            parser.error("--country is required in single-brand mode")
        run_single(args)
    elif args.file:
        run_batch(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
