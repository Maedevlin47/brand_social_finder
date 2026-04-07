Find the official Instagram and X (Twitter) handles for a brand using web search, then return a single result row with a confidence score.

## Input

The brand name is provided as the argument to this command: $ARGUMENTS

If no brand name is given, ask the user to provide one before proceeding.

## Steps

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

**Step 6 — Write the notes field**
Begin with exactly where each handle was found (e.g. "Instagram handle found in website footer. X handle found via web search."). Then add any caveats, ambiguities, or flags worth reviewing. Keep to one or two sentences.

## Output

Return exactly one result in this format — a plain text block followed by a markdown table:

```
brand_name        | instagram_handle | x_handle | confidence_score | notes
------------------|------------------|----------|------------------|------
$ARGUMENTS        | <handle or ->    | <handle or -> | <0-100>     | <notes>
```

Rules:
- Do not include the `@` symbol in handles
- Use `-` (not empty) when a handle is not found
- The notes field must state where each handle was found before any other context
