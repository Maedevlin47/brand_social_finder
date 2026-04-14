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

## Input / output format

See README.md for column definitions and examples.