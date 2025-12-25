"""Text Utilities

Shared text normalization and processing functions.

IMPORTANT: The normalize_text function must stay in sync with the frontend
version in astro-frontend/src/lib/utils/co-mentions.ts:normalizeText().
Both implementations should produce identical output for the same input.
"""
import re
import unicodedata
from typing import Optional

# Pre-compiled regex for non-alphanumeric characters (except spaces)
_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")

# Common name suffixes to filter in tokenization
NAME_SUFFIXES = frozenset({"jr", "sr", "ii", "iii", "iv", "v"})


def normalize_text(s: Optional[str]) -> str:
    """Normalize text for matching.

    Algorithm (must match frontend normalizeText):
    1. Strip accents/diacritics using Unicode NFKD normalization
    2. Convert to lowercase
    3. Remove non-alphanumeric characters (except spaces)
    4. Collapse multiple spaces
    5. Trim leading/trailing whitespace

    Args:
        s: Input string to normalize

    Returns:
        Normalized string, or empty string if input is None/empty

    Examples:
        >>> normalize_text("Kylian Mbappé")
        'kylian mbappe'
        >>> normalize_text("Patrick Mahomes II")
        'patrick mahomes ii'
        >>> normalize_text("O'Brien-Smith")
        'obrien smith'
    """
    if not s:
        return ""
    # Strip accents using Unicode NFKD normalization
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    s_lower = s_ascii.lower()
    s_clean = _NON_ALNUM.sub(" ", s_lower)
    return " ".join(s_clean.split())


def tokenize_name(name: str) -> list:
    """Tokenize a name into individual parts for matching.

    Filters out common suffixes (Jr, Sr, II, etc.) and very short tokens.
    Must match frontend tokenizeName() behavior.

    Args:
        name: Name to tokenize

    Returns:
        List of meaningful name tokens
    """
    normalized = normalize_text(name)
    tokens = normalized.split()
    return [t for t in tokens if t not in NAME_SUFFIXES and len(t) >= 2]


def strip_specials_preserve_case(s: Optional[str]) -> str:
    """Remove accents and non-alphanumeric characters while preserving case.

    Used for display names where we want clean text but original casing.

    Args:
        s: Input string

    Returns:
        Cleaned string with original case preserved
    """
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    # Keep alnum and spaces only
    out = [ch for ch in s_ascii if ch.isalnum() or ch == " "]
    s_clean = "".join(out)
    return " ".join(s_clean.split())


def first_last_only(name: Optional[str]) -> str:
    """Reduce a display name to only first and last tokens.

    Removes middle names/initials and handles common suffixes.

    Args:
        name: Full name

    Returns:
        Simplified first + last name

    Examples:
        >>> first_last_only("Kevin Wayne Durant Jr.")
        'Kevin Durant'
        >>> first_last_only("LeBron Raymone James Sr")
        'LeBron James'
    """
    if not name:
        return ""
    parts = str(name).split()
    if len(parts) <= 1:
        return parts[0] if parts else ""

    first = parts[0]
    last = parts[-1]

    # Handle suffixes - if last is a suffix, take the previous token
    if last.lower().strip(". ") in NAME_SUFFIXES and len(parts) >= 3:
        last = parts[-2]

    return f"{first} {last}".strip()
