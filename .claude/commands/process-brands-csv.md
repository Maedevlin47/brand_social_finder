Process every brand in `to-process.csv` sequentially, writing results to `results.csv` and removing each row from `to-process.csv` after it is successfully written. This gives full resumability: if the command is interrupted, re-running it continues from where it left off.

## Input and output files

- **Input:** `to-process.csv` — columns: `Name`, `List` / `Source` / `Source List` (case-insensitive), `Location`
- **Output:** `results.csv` — columns: `brand_name`, `source_name`, `country`, `website`, `instagram_handle`, `x_handle`, `manual_review`, `confidence_score`, `confidence_signals`, `notes`

An optional argument can override the input filename: $ARGUMENTS (if provided, treat it as the path to the input CSV instead of `to-process.csv`).

## Token efficiency rules

Follow these rules on every run to keep token usage lean:

- **Do not fetch pages directly.** Use only web search results (titles, snippets, URLs). Do not use WebFetch or load any URLs. Search snippet data is sufficient to identify handles.
- **Stop searching once confident.** If the first search returns a clear, unambiguous handle, do not run additional searches for that platform.
- **Skip already-processed brands.** Before starting the loop, check `results.csv`. If a brand already has a row there, skip it entirely — do not re-research or re-append it.

## Setup steps (do these once before the loop)

1. Read the input CSV. Count the total number of rows — you will need this for progress logging.
2. Check whether `results.csv` exists. If it does not, create it now with just the header row:
   `brand_name,source_name,country,website,instagram_handle,x_handle,manual_review,confidence_score,confidence_signals,notes`
3. If `results.csv` already exists but has no header, prepend the header row before continuing.

## Processing loop

Repeat the following steps for each row in the input CSV, in order from top to bottom.

### Step 1 — Log progress
Print to the terminal:
```
Processing <N>/<total>: <Name> (<Location>)…
```
where N is the 1-based index of the current row.

### Step 2 — Research the brand
Use web search to find the official Instagram and X handles for this brand. Follow the same research logic as the `/find-brand-handle` command, substituting `<Name>` and `<Location>` for the current row.

### Step 3 — Score confidence (0–100)
Follow the same scoring rules as the `/find-brand-handle` command.

Set `manual_review` to `true` if confidence is below 50 or if meaningful ambiguity remains.

### Step 4 — Build the result row
Construct a single CSV row with these fields:

| Field | Value |
|---|---|
| `brand_name` | `Name` from input |
| `source_name` | Value from the `List`, `Source`, or `Source List` column (case-insensitive); empty string if none present |
| `country` | `Location` from input |
| `website` | Official website URL found, or empty |
| `instagram_handle` | Handle without `@`, or `-` if not found |
| `x_handle` | Handle without `@`, or `-` if not found |
| `manual_review` | `true` or `false` |
| `confidence_score` | Integer 0–100 |
| `confidence_signals` | Signals joined with `; ` (e.g. `multiple_sources; handle_matches_brand`) |
| `notes` | Start with where each handle was found, then any caveats. One or two sentences. |

Escape any commas or double-quotes in field values per RFC 4180 (wrap field in double-quotes, escape internal double-quotes as `""`).

### Step 5 — Append to results.csv
Append the result row as a new line at the end of `results.csv`. Do not rewrite the whole file — append only. Confirm the row was written before moving to Step 6.

### Step 6 — Remove the processed row from the input CSV
Remove **only** the row just processed from the input CSV, leaving the header and all remaining rows intact. Rewrite the file with that one data row removed. This ensures that if the command is interrupted, re-running it resumes from the next unprocessed brand.

### Step 7 — Log completion
Print to the terminal:
```
✓ <N>/<total>: <Name> — instagram: <handle or "-">, x: <handle or "-">, confidence: <score>
```
Then continue to the next row.

## After the loop

When all rows have been processed (the input CSV contains only the header row), print:
```
Done. <total> brand(s) processed. Results written to results.csv.
```
