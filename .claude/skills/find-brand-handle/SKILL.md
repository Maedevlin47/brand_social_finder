Find the official Instagram and X (Twitter) handles for a brand using web search. Supports two modes:

- **CSV batch mode** (primary): `$ARGUMENTS` ends in `.csv` — process every brand in the file
- **Single-brand mode** (secondary): `$ARGUMENTS` is a brand name — look up one brand interactively

---

## Mode 1: CSV Batch Mode

Triggered when `$ARGUMENTS` ends in `.csv`.

### Setup (do once before the loop)

1. Read the input CSV. The required column is `brand_name`. Any additional columns (`source_name`, `country`, etc.) are carried through to output unchanged. Count the total rows for progress logging.
2. Check whether `results.csv` exists. If it does not, create it with this header row:
   `brand_name,instagram_handle,x_handle,confidence_score,manual_review_needed,confidence_signals,notes`
3. If `results.csv` exists, read all `brand_name` values already present — these are **already-processed brands** and must be skipped.

### Processing loop

Repeat for each row in the input CSV, top to bottom. Skip any row whose `brand_name` is already in `results.csv`.

**Step 1 — Log progress**
Print:
```
Processing <N>/<total>: <brand_name>…
```

**Steps 2–7 — Research the brand**
Follow the 6-step research flow described in Mode 2 below, substituting the current row's `brand_name` for `$ARGUMENTS`.

**Step 8 — Build the result row**

| Field | Value |
|---|---|
| `brand_name` | From input row |
| `instagram_handle` | Handle without `@`, or `-` if not found |
| `x_handle` | Handle without `@`, or `-` if not found |
| `confidence_score` | Integer 0–100 |
| `manual_review_needed` | `TRUE` if confidence < 50, no handle found for either platform, or meaningful ambiguity remains; otherwise `FALSE` |
| `confidence_signals` | Signals joined with `; ` (e.g. `verified_badge; handle_matches_brand`) |
| `notes` | Where each handle was found, then any caveats. One or two sentences. |

Escape any commas or double-quotes per RFC 4180 (wrap field in double-quotes; escape internal double-quotes as `""`).

**Step 9 — Append to results.csv**
Append the result row as a new line. Do not rewrite the whole file.

**Step 10 — Log completion**
Print:
```
✓ <N>/<total>: <brand_name> — instagram: <handle or "-">, x: <handle or "-">, confidence: <score>, review: <TRUE/FALSE>
```

### After the loop

Print:
```
Done. <total_processed> brand(s) processed, <total_skipped> skipped (already in results.csv). Results written to results.csv.
```

---

## Mode 2: Single-Brand Mode

Triggered when `$ARGUMENTS` does not end in `.csv`.

If no argument is given, ask the user to provide a brand name before proceeding.

Work through these steps in order. Use web search for each one.

**Step 1 — Find the official website**
Search: `"$ARGUMENTS" official site`
Identify the brand's official website URL. Then check the website's footer, header, and contact/about pages for any linked Instagram or X (Twitter) URLs. Record any handles found here — these are the highest-confidence signals.

**Step 2 — Find the Instagram handle**
Search: `"$ARGUMENTS" Instagram official`
Also try: `site:instagram.com "$ARGUMENTS"`
Identify all candidate Instagram accounts (global, regional, sub-brand). Note follower counts, verified badge status, and whether the bio links back to the official website.

**Step 3 — Find the X handle**
Search: `"$ARGUMENTS" Twitter X official`
Also try: `site:x.com "$ARGUMENTS"`
Identify all candidate X accounts. Note follower counts, verified badge status, and whether the bio links back to the official website.

**Step 4 — Cross-reference and select the best handle**
For each platform, select the best handle using this priority order:
1. Handle linked directly from the brand's official website
2. Handle whose bio links back to the official website AND has the highest follower count
3. Handle with the highest follower count among all candidates
4. Handle confirmed across multiple independent sources (press, Wikipedia, directories)

If no handle can be identified with reasonable confidence, use `-` for that field.

**Step 5 — Score confidence (0–100)**
Start at 0. Apply the following, then cap the result between 0 and 100.

Positive signals (add points):
- +30 — verified badge found on the selected account
- +25 — handle linked directly from the brand's official website
- +20 — handle confirmed across multiple independent sources
- +15 — handle name or branding clearly matches the brand
- +10 — account appears active (recent posts visible)

Deductions (subtract points):
- −15 — multiple competing accounts found with no clear winner
- −10 — handle found via search only, not on official website
- −10 — follower count could not be verified
- −5 — selected account is a regional variant and a global account also exists

**Step 6 — Determine manual_review_needed**
Set to `TRUE` if any of the following apply:
- Confidence score is below 50
- No handle was found for either platform (`-` in both fields)
- Meaningful ambiguity remains (e.g. multiple plausible accounts with similar follower counts)

Otherwise set to `FALSE`.

**Step 7 — Write the notes field**
Begin with exactly where each handle was found (e.g. "Instagram handle found in website footer. X handle found via web search."). Then add any caveats, ambiguities, or flags worth reviewing. Keep to one or two sentences.

### Output

Return exactly one result as a markdown table:

```
brand_name  | instagram_handle | x_handle     | confidence_score | manual_review_needed | notes
------------|------------------|--------------|------------------|----------------------|------
$ARGUMENTS  | <handle or ->    | <handle or-> | <0-100>          | TRUE/FALSE           | <notes>
```

Rules:
- Do not include the `@` symbol in handles
- Use `-` (not empty) when a handle is not found
- The notes field must state where each handle was found before any other context
