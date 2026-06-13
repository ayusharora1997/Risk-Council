"""
Robust JSON extraction from AI model responses.

Models sometimes wrap JSON in markdown fences or add prose before/after.
This module tries multiple strategies before giving up.
"""
from __future__ import annotations

import json
import re
from typing import Any


class JSONExtractionError(ValueError):
    """Raised when all JSON extraction strategies fail."""


def extract_json(text: str) -> dict[str, Any]:
    """Extract the first valid JSON object from an AI response string.

    Strategies tried in order:
    1. Parse the full trimmed response directly.
    2. Extract content inside ```json ... ``` or ``` ... ``` fences.
    3. Find the outermost { ... } span and parse it.

    Raises:
        JSONExtractionError: If no valid JSON object is found.
    """
    stripped = text.strip()

    # Strategy 1 — direct parse
    try:
        result = json.loads(stripped)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Strategy 2 — markdown code fences
    fence_pattern = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.DOTALL)
    for match in fence_pattern.finditer(stripped):
        try:
            result = json.loads(match.group(1))
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            continue

    # Strategy 3 — outermost braces (greedy scan)
    start = stripped.find("{")
    if start != -1:
        # Walk backwards from end to find the matching closing brace
        depth = 0
        for i, ch in enumerate(stripped[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = stripped[start : i + 1]
                    try:
                        result = json.loads(candidate)
                        if isinstance(result, dict):
                            return result
                    except json.JSONDecodeError:
                        break

    raise JSONExtractionError(
        f"Could not extract a valid JSON object from model response "
        f"(first 300 chars): {stripped[:300]!r}"
    )
