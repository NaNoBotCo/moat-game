"""The smuggler's vocabulary — the trade's own words, and what knowing them buys.

Built from wichaa.net's glossary (`tools/import_wichaa.py`), so every term, every
gloss and every count is sourced rather than invented. Each word carries how many
catalogued manuscripts and how many market listings actually use it, and that is
what grades it: a word carried by 1,198 listings is what anyone at a stall says;
a word carried by three is what marks you as someone who has read the old hand.

You learn words by using them — appraising, communing, being taught. The
vocabulary you hold is a second, quieter skill sheet: it decides whether a dealer
treats you as a mark or a colleague.
"""

from __future__ import annotations

import json
import pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "dictionary.json"

# What each tier of word is worth when you use it in front of someone who knows.
RARITY_WEIGHT = {"common": 0, "trade": 1, "deep": 2, "rare": 3}
RARITY_NOTE = {
    "common": "everyone in the trade says this",
    "trade": "you sound like a dealer",
    "deep": "you sound like someone's student",
    "rare": "you sound like you read the old hand",
}

_CACHE: dict | None = None


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        if DATA.exists():
            _CACHE = json.loads(DATA.read_text())
        else:
            _CACHE = {"words": [], "count": 0, "attribution": ""}
    return _CACHE


def all_words() -> list[dict]:
    return _load().get("words", [])


def by_term(term: str) -> dict | None:
    t = term.strip().lower()
    for w in all_words():
        if w["term"] == term or w["roman"].lower() == t:
            return w
    return None


def in_domain(domain: str) -> list[dict]:
    return [w for w in all_words() if w["domain"] == domain]


def domains() -> list[tuple[str, str, int]]:
    """(key, label, count) for each domain present, commonest first."""
    seen: dict[str, tuple[str, int]] = {}
    for w in all_words():
        label, n = seen.get(w["domain"], (w["domain_label"], 0))
        seen[w["domain"]] = (label, n + 1)
    return sorted(((k, l, n) for k, (l, n) in seen.items()), key=lambda x: -x[2])


def learn(pc, term: str) -> bool:
    """Add a word to the smuggler's vocabulary. True if it was new."""
    if term in pc.words:
        return False
    pc.words = [*pc.words, term]
    return True


def known(pc) -> list[dict]:
    return [w for w in all_words() if w["term"] in pc.words]


def fluency(pc) -> int:
    """A single number for how the trade hears you: 0..5-ish, weighted by rarity."""
    score = sum(RARITY_WEIGHT.get(w["rarity"], 0) for w in known(pc))
    score += len(known(pc)) // 4
    return min(5, score // 3)


def fluency_note(pc) -> str:
    f = fluency(pc)
    return {
        0: "You speak like a tourist with money.",
        1: "You know enough words to buy without being laughed at.",
        2: "You can hold a stall conversation without giving yourself away.",
        3: "Dealers start quoting you the second price, not the first.",
        4: "You are taken for someone's student, and treated accordingly.",
        5: "You are spoken to as a peer, which is its own kind of danger.",
    }[f]


def attribution() -> str:
    return _load().get("attribution", "")
