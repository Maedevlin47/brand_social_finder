# Brand Handle Finder

A Claude Code-native tool that finds and verifies the official Instagram and X (Twitter) handles for a list of brands. Research is performed entirely through Claude Code's built-in web search — no API key or external services required.

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed and authenticated
- Python 3.10+ (for the CSV utility helpers in `main.py` and `formatter.py`)

```bash
pip install -r requirements.txt
```

---

## How it works

All brand research is done by two Claude Code slash commands:

| Command | What it does |
|---|---|
| `/find-brand-handle <brand name>` | Looks up a single brand and returns one result row |
| `/process-brands-csv` | Reads `to-process.csv`, processes every brand sequentially, writes results to `results.csv`, and removes each row from the input file as it goes |

Claude Code uses web search to find each brand's official website, cross-reference Instagram and X handles across sources, and score confidence from 0–100 based on verification signals.

---

## Batch usage (recommended)

**1. Prepare your input file.**

Create `to-process.csv` with a header row and one brand per line:

```csv
Name,List,Location
Biti's,Vietnamese Footwear Brands,Vietnam
Bata,Global Footwear,Czechia
Muji,Japanese Retail Brands,Japan
```

| Column | Required | Description |
|---|---|---|
| `Name` | Yes | Brand name to look up |
| `List` / `Source` / `Source List` | No | Name of the source list this brand came from (header is case-insensitive) |
| `Location` | Yes | Country or region the brand is from |

**2. Run the batch command inside Claude Code:**

```
/process-brands-csv
```

Claude Code will log progress to the terminal as it runs:

```
Processing 1/3: Biti's (Vietnam)…
✓ 1/3: Biti's — instagram: bitisshoes, x: -, confidence: 55
Processing 2/3: Bata (Czechia)…
✓ 2/3: Bata — instagram: bata, x: -, confidence: 45
...
Done. 3 brand(s) processed. Results written to results.csv.
```

**Resumability:** each brand is removed from `to-process.csv` immediately after its result is written to `results.csv`. If the run is interrupted, simply re-run `/process-brands-csv` to continue from where it left off.

---

## Single brand lookup

To look up one brand interactively:

```
/find-brand-handle Nike
/find-brand-handle "Biti's"
```

Returns a single result row with handles, confidence score, and notes.

---

## Output format

Results are written to `results.csv` with these columns:

| Column | Description |
|---|---|
| `brand_name` | Brand name (from input) |
| `source_name` | Source list name (from input) |
| `country` | Country/region (from input) |
| `website` | Brand's official website URL |
| `instagram_handle` | Official Instagram handle without `@`, or `-` if not found |
| `x_handle` | Official X handle without `@`, or `-` if not found |
| `manual_review` | `true` if the tool could not confidently determine a handle |
| `confidence_score` | Integer 0–100 |
| `confidence_signals` | Semicolon-separated signals that contributed to the score |
| `notes` | Where each handle was found, plus any caveats |

---

## Confidence score

| Score | Meaning |
|---|---|
| 80–100 | High confidence — safe to use without manual review |
| 50–79 | Moderate confidence — spot-check recommended |
| 0–49 | Low confidence — manually verify before using |

Points are added for signals like a verified badge (+30), handle linked from the official website (+25), confirmed across multiple sources (+20), name match (+15), and active account (+10). Deductions apply for ambiguity, unverifiable follower counts, and regional variants.
