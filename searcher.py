"""
Brand handle searcher using Claude API with web search tool.
"""

import json
import re

from anthropic import Anthropic

SYSTEM_PROMPT = (
    "You are a research assistant specializing in finding official social media handles for brands. "
    "You have access to web search. Always verify information carefully and only report handles "
    "you are confident are the brand's official accounts."
)


def _build_prompt(brand_name: str, source_name: str, country: str) -> str:
    return f"""Find the best official Instagram and Twitter/X social media handles for this brand:

Brand: {brand_name}
Source list: {source_name}
Country/Region: {country}

Note: the Country/Region field indicates where the brand is FROM — not which regional account to prefer.

--- STEP 1: Find the official website ---
Search: "{brand_name} official site {country}"
Identify the brand's official website URL. Record the full URL (e.g. https://www.nike.com).
Check the website footer, header, and about/contact pages for linked Instagram or Twitter/X URLs.

--- STEP 2: Find all candidate handles ---
If handles are not found on the official website, run these searches:
  - "{brand_name} official Instagram {country}"
  - "{brand_name} Instagram"
  - "{brand_name} official Twitter {country}"
  - "{brand_name} X account"
Identify ALL candidate accounts (global, regional variants, sub-brands) for both platforms.

--- STEP 3: Choose the best Instagram handle ---
Follow this priority order:

PRIORITY 1 — Website link: If exactly one Instagram account is linked directly from the brand's
official website, use that handle.

PRIORITY 2 — Global handle with website link AND higher followers: If both a global and a regional
account exist, prefer the GLOBAL handle only if BOTH of these are true:
  (a) it is linked to or from the brand's official website in some form, AND
  (b) it has a higher follower count than the regional variant.
If the global handle does not meet BOTH conditions, select by follower count instead (Priority 3).

PRIORITY 3 — Highest follower count: If no handle is linked from the official website, or if the
global handle does not meet Priority 2 conditions, select the account with the HIGHEST follower
count among all candidates — whether global or regional.

PRIORITY 4 — Other signals (use only if follower counts are unavailable):
  a) Profile bio links back to the brand's official website
  b) Handle confirmed across multiple independent sources (Wikipedia, press, directories)
  c) Handle name closely matches the brand name
  d) Profile has a verified/blue checkmark badge

PRIORITY 5 — Flag for review: If you still cannot confidently choose, set "manual_review": true
and report the most likely handle.

--- STEP 4: X handle fallback ---
If NO Instagram handle is found after completing Steps 1–3, repeat the exact same process
(same priority order, same source verification, same scoring) to find the brand's X handle.
Only populate "twitter_handle" if no Instagram handle was found.

--- STEP 5: Regional variant rule ---
Only apply the "regional_variant" signal (and its score penalty) if BOTH of the following are true:
  - A global/brand-wide account exists alongside the regional one
  - The regional account was selected despite the global one being available
If the regional account is the ONLY account found, do NOT apply the regional_variant signal or penalty.

--- STEP 6: Score your confidence (0–100) ---
Start at 0. Add and subtract points based on what you found. Cap the result between 0 and 100.

  POSITIVE (add points):
  +50  handle is directly linked from the brand's official website
  +30  profile bio links back to the brand's official website
  +25  handle confirmed across multiple independent sources
  +20  follower count is high and consistent with an established brand
  +18  handle name closely matches the brand name
  +15  profile has a verified/blue checkmark badge

  NEGATIVE (subtract points):
  -10  handle found only via web search, not linked from official website
  -15  multiple competing accounts found and ambiguity remains
  -10  follower count could not be verified
  -5   selected handle is a regional variant AND a global account also exists

--- STEP 7: List which signals fired ---
Return only the keys that apply:
  "linked_from_website"   — handle linked directly from official website
  "bio_links_website"     — profile bio links back to official website
  "multiple_sources"      — confirmed across multiple independent sources
  "high_follower_count"   — follower count high and consistent with brand size
  "most_followers"        — selected because it had the most followers among candidates
  "handle_matches_brand"  — handle name closely matches brand name
  "verified_badge"        — profile has verified/blue checkmark
  "search_only"           — found via web search only, not on official website
  "ambiguous_accounts"    — multiple competing accounts found
  "no_follower_data"      — follower count could not be verified
  "regional_variant"      — regional account selected and a global account also exists

--- STEP 8: Notes ---
The notes field MUST begin by stating exactly where the handle was found. Be specific.
Examples: "Found via brand website footer.", "Found via Google search.", "Found on brand's LinkedIn page."
Then add any other relevant context. Keep the total to one or two sentences.

Important:
- Do NOT include the @ symbol in handles
- Use an empty string "" if a handle is not found
- Set "manual_review" to true only when you cannot confidently choose between candidates

Respond with ONLY a JSON object in this exact format — no markdown, no extra text:
{{
  "instagram_handle": "",
  "twitter_handle": "",
  "website": "",
  "manual_review": false,
  "confidence": 0,
  "confidence_signals": [],
  "notes": ""
}}"""


class BrandSearcher:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.tools = [{"type": "web_search_20250305", "name": "web_search"}]

    def search(self, brand_name: str, source_name: str, country: str) -> dict:
        """Search for official Instagram/Twitter handles for a brand."""
        messages = [
            {"role": "user", "content": _build_prompt(brand_name, source_name, country)}
        ]

        for _ in range(20):  # safety cap on agentic loop turns
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                return self._parse_response(text, brand_name)

            if response.stop_reason == "tool_use":
                # Add the full assistant response (includes tool_use and any
                # server-provided web_search result blocks) to the conversation.
                messages.append({"role": "assistant", "content": response.content})

                # Check which tool_use blocks still need a client-side result.
                # For web_search_20250305 the API executes the search server-side
                # and may embed result blocks directly in response.content.
                result_ids = {
                    getattr(b, "tool_use_id", None)
                    for b in response.content
                    if hasattr(b, "tool_use_id")
                }

                pending = [
                    b
                    for b in response.content
                    if getattr(b, "type", None) == "tool_use"
                    and b.id not in result_ids
                ]

                if pending:
                    # Standard tool-use loop: echo back tool_results so the model
                    # can continue.  (Reached only when results aren't embedded.)
                    tool_results = [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Search executed. Please analyse the results and return the JSON response.",
                        }
                        for block in pending
                    ]
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # Results already embedded in the assistant turn; ask Claude
                    # to produce the final JSON answer.
                    messages.append(
                        {
                            "role": "user",
                            "content": "Based on the search results above, please provide the final JSON response.",
                        }
                    )
            else:
                # Unexpected stop_reason — extract any text and bail out.
                text = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                if text:
                    return self._parse_response(text, brand_name)
                break

        return {
            "instagram_handle": "",
            "twitter_handle": "",
            "website": "",
            "manual_review": True,
            "confidence": 0,
            "confidence_signals": [],
            "notes": "Search loop exhausted without a result.",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, text: str, brand_name: str) -> dict:
        """Extract handle data from Claude's text output."""
        # Primary: find the outermost JSON object (handles nested arrays).
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                instagram = (data.get("instagram_handle") or "").strip().lstrip("@")
                twitter = (data.get("twitter_handle") or "").strip().lstrip("@")
                website = (data.get("website") or "").strip()
                manual_review = bool(data.get("manual_review", False))
                confidence = int(data.get("confidence") or 0)
                confidence = max(0, min(100, confidence))
                signals = data.get("confidence_signals") or []
                if not isinstance(signals, list):
                    signals = []
                notes = (data.get("notes") or "").strip()
                if not notes and not instagram and not twitter:
                    notes = "No handles found."
                return {
                    "instagram_handle": instagram,
                    "twitter_handle": twitter,
                    "website": website,
                    "manual_review": manual_review,
                    "confidence": confidence,
                    "confidence_signals": signals,
                    "notes": notes,
                }
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: regex scan for handle patterns in the raw text.
        ig_match = re.search(
            r"instagram[^:]*[:\s]+@?([A-Za-z0-9._]{1,30})", text, re.IGNORECASE
        )
        tw_match = re.search(
            r"(?:twitter|x\.com)[^:]*[:\s]+@?([A-Za-z0-9._]{1,50})", text, re.IGNORECASE
        )
        return {
            "instagram_handle": ig_match.group(1).lstrip("@") if ig_match else "",
            "twitter_handle": tw_match.group(1).lstrip("@") if tw_match else "",
            "website": "",
            "manual_review": True,
            "confidence": 0,
            "confidence_signals": [],
            "notes": "Parsed from unstructured response — verify manually.",
        }
