#!/usr/bin/env python3
"""Import wichaa.net's glossary into the game as the smuggler's dictionary.

wichaa.net publishes a curated glossary of the tradition's own words — each term
in Thai, romanised, and glossed in English and 中文, with counts of how many
catalogued manuscripts and how many market listings actually carry it. That is
exactly the vocabulary an amulet smuggler would live inside, and it is already
sourced, which is why the game reads it rather than inventing Thai.

The counts come across too: a word carried by 1,198 listings is common trade
talk, one carried by 3 is the sort of word that marks you as someone who knows.
That rarity is what the game grades you on.

    python3.13 tools/import_wichaa.py [--api PATH] [--out data/dictionary.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_API = HERE.parent / "nanobotco-lanna" / "docs" / "api"


def rarity(entry: dict) -> str:
    """How much knowing this word says about you."""
    listings = entry.get("listings", 0) or 0
    mss = entry.get("manuscripts", 0) or 0
    if listings >= 300:
        return "common"        # anyone in the trade says this
    if listings >= 40 or mss >= 10:
        return "trade"         # you sound like a dealer
    if listings >= 5 or mss >= 2:
        return "deep"          # you sound like someone's student
    return "rare"              # you sound like you read the old hand


def build(api: pathlib.Path) -> dict:
    src = json.loads((api / "glossary.json").read_text())
    words = []
    for e in src.get("entries", []):
        g = e.get("glosses", {}) or {}
        words.append({
            "term": e["term"],
            "roman": e.get("roman", ""),
            "domain": e.get("domain", ""),
            "domain_label": e.get("domainLabel", ""),
            "en": g.get("en", ""),
            "zh": g.get("zh", ""),
            "th": g.get("th", ""),
            "manuscripts": e.get("manuscripts", 0),
            "listings": e.get("listings", 0),
            "rarity": rarity(e),
        })
    words.sort(key=lambda w: (w["domain"], -w["listings"]))
    return {
        "kind": "dictionary",
        "source": "wichaa.net /glossary",
        "note": src.get("note", ""),
        "attribution": "Glossary and counts from wichaa.net (NaNoBotCo).",
        "languages": src.get("languages", []),
        "count": len(words),
        "words": words,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=str(DEFAULT_API), type=pathlib.Path)
    ap.add_argument("--out", default=str(HERE / "data" / "dictionary.json"),
                    type=pathlib.Path)
    a = ap.parse_args()
    data = build(a.api)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    by = {}
    for w in data["words"]:
        by[w["rarity"]] = by.get(w["rarity"], 0) + 1
    print(f"wrote {a.out}  —  {data['count']} words "
          + ", ".join(f"{n} {k}" for k, n in by.items()))


if __name__ == "__main__":
    main()
