# Brand Handle Finder

## Purpose

This tool finds and verifies the official Instagram and X (Twitter) handles for a list of brands. For each brand it:

1. Searches for the brand's official website and checks it for linked social media accounts.
2. Searches independently for candidate Instagram handles and candidate X handles across the web.
3. Selects the best handle for each platform using a priority order: website link > follower count > other signals (verified badge, bio link, cross-source confirmation).
4. Scores confidence from 0–100 based on how many verification signals were confirmed.
5. Flags results for manual review when a confident choice cannot be made.

## How to run

All processing is done through two Claude Code slash commands — there is no script to run directly.

| Command | Usage |
|---|---|
| `/find-brand-handle <brand name>` | Look up a single brand interactively |
| `/process-brands-csv` | Process all brands in `to-process.csv` and write results to `results.csv` |

Both commands are defined in `.claude/commands/` and use Claude Code's built-in web search.

## Claude Code-native version

This is the **Claude Code-native** implementation. All web research must be performed using **Claude Code's built-in web search** — not the Anthropic API's `web_search` tool and not external HTTP calls. Do not add or use `BrandSearcher`, `anthropic` SDK calls, or any server-side agentic loop. Claude Code itself is the research agent.

## Input format

A CSV file with a header row and the following columns:

| Column | Description |
|--------|-------------|
| `Name` | Brand name to look up |
| `List` / `Source` / `Source List` | Name of the source list the brand came from (optional; column header is case-insensitive) |
| `Location` | Country or region the brand is from |

Example:
```csv
Name,List,Location
Biti's,Vietnamese Footwear Brands,Vietnam
Bata,Global Footwear,Czechia
Muji,Japanese Retail Brands,Japan
```

## Output format

A CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `brand_name` | Brand name (from input) |
| `source_name` | Source list name (from input) |
| `country` | Country/region (from input) |
| `website` | Brand's official website URL |
| `instagram_handle` | Official Instagram handle without `@`, or empty if not found |
| `x_handle` | Official X handle without `@`, or empty if not found |
| `manual_review` | `true` if the tool could not confidently choose a handle |
| `confidence_score` | Integer 0–100 indicating confidence in the result |
| `confidence_signals` | Semicolon-separated list of signals that contributed to the score |
| `notes` | Where the handle was found and any relevant context or caveats |
