# Source ID Finder

A Python tool that uses Claude (with web search) to find official Instagram and Twitter/X handles for brands. Available as both a **web UI** and a **command-line tool**.

## Setup

**1. Clone the repository.**

**2. Install dependencies** (Python 3.10+ required):

```bash
pip install -r requirements.txt
```

**3. Add your API key:**

```bash
cp .env.example .env
# Then edit .env and replace `your_key_here` with your real Anthropic API key.
```

You can get an API key at <https://console.anthropic.com/>.

---

## Web UI

The easiest way to use the tool. Run:

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The web UI has two tabs:

### Search tab
- **Single Brand Lookup** — enter a brand name, source list, and location, then click Search. Results appear in a table with a confidence score.
- **Batch CSV Upload** — upload a CSV file to process multiple brands at once. Results stream in row by row as they complete. A Download CSV button appears when results are ready.

### Confidence Calculator tab
Explains how the confidence score is calculated and what each score range means, so you know whether to manually verify a result.

---

## Command-line usage

### Single-brand mode

```bash
python main.py --brand "Biti's" --source "Vietnamese Footwear Brands" --country "Vietnam"
python main.py --brand "Nike" --source "Global Footwear" --country "USA"
```

| Flag | Required | Description |
|------|----------|-------------|
| `--brand` | Yes | Brand name to look up |
| `--source` | No | Name of the source list this brand comes from |
| `--country` | Yes | Country or region the brand is from |

### Batch mode

```bash
python main.py --file brands.csv --output results.csv
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--file` | Yes | — | Input CSV file |
| `--output` | No | `results.csv` | Output CSV file |

**Resumability:** if the output file already exists, any brand already in it will be skipped. Re-run the same command to continue after an interruption.

---

## Input CSV format

The input CSV must have these three columns (header row required):

```csv
Name,List,Location
Biti's,Vietnamese Footwear Brands,Vietnam
Bata,Global Footwear,Czechia
Muji,Japanese Retail Brands,Japan
```

| Column | Description |
|--------|-------------|
| `Name` | The brand to look up |
| `List` | Name of the list this brand was sourced from |
| `Location` | Country or region the brand is from (indicates where the brand is from, not which regional account to prefer) |

---

## Output CSV format

| Column | Description |
|--------|-------------|
| `brand_name` | Brand name (from input) |
| `source_name` | Source list name (from input) |
| `country` | Country/region (from input) |
| `instagram_handle` | Best official Instagram handle without `@`, or empty |
| `twitter_handle` | Best official Twitter/X handle without `@`, or empty |
| `confidence` | Confidence score 0–100 |
| `confidence_signals` | Semicolon-separated list of signals that contributed to the score |
| `notes` | Anything worth flagging, including "MANUAL REVIEW NEEDED" if the tool could not confidently choose a handle |

---

## How it works

For each brand the tool:

1. Searches for the brand's official website and checks it for linked Instagram and Twitter/X URLs.
2. Selects the best handle using this priority order:
   - **Website link first** — if a handle is linked directly from the brand's official website, that handle is used.
   - **Highest follower count** — if multiple accounts exist and none is linked from the official website, the account with the most followers is selected, whether global or regional.
   - **Other signals** — if follower counts are unavailable, verified badges, bio links, and cross-source confirmation are used to decide.
   - **Manual review flag** — if the tool cannot confidently choose, it flags the result in the notes column.
3. Prefers Instagram; only records a Twitter/X handle if no Instagram handle is found.
4. Returns handles without `@` and leaves cells empty when a handle isn't found.
5. Scores confidence from 0–100 based on how many verification signals were confirmed.

## Confidence score

| Score | Meaning |
|-------|---------|
| 80–100 | High confidence — safe to use without manual review in most cases |
| 60–79 | Moderate confidence — spot-check recommended |
| 0–59 | Low confidence — manually verify before using |

See the **Confidence Calculator** tab in the web UI for a full breakdown of how points are added and subtracted.
