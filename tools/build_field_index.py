#!/usr/bin/env python3
"""Build the slim spatial index the LINE field worker looks places up in.

The atlas's own catalogue is 7 MB and full of things a lookup does not need. The
field layer needs exactly enough to answer one question — *what catalogued
places are within a couple of hundred metres of here, and do any of them still
have no hours?* — so this strips it to id, position, category, and whether hours
are already known.

It also applies the **exclusion list** at build time rather than at request
time. A place that should never be logged against simply is not in the index,
so there is no code path in the worker that could record one by mistake.

    python3.13 tools/build_field_index.py [--out worker/field-index.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SRC = HERE.parent / "mot-dang" / "data" / "canonical"

# Never logged against, on any path, by anybody. Places of worship, care,
# education and residence are not street furniture for a game to check in at,
# and a crowd of players loitering outside one to log its hours is a harm the
# atlas does not need and the places themselves certainly do not.
EXCLUDED_CATS = {"wat", "medical", "learn", "realestate"}
EXCLUDED_SUBS = {"hospital", "clinic", "school", "university", "kindergarten",
                 "condo", "apartment", "house", "dormitory", "temple",
                 "church", "mosque", "shrine", "police", "embassy"}

# Categories where a passer-by observation is genuinely useful and harmless.
INCLUDED_CATS = {"food", "shopping", "essentials", "beauty", "massage",
                 "repair", "transport", "sights", "parks"}


def excluded(rec: dict) -> str | None:
    """Why this place is not in the index, or None if it belongs."""
    cats = set(rec.get("cat") or [])
    subs = set(rec.get("sub") or [])
    if cats & EXCLUDED_CATS:
        return f"category {sorted(cats & EXCLUDED_CATS)[0]}"
    if subs & EXCLUDED_SUBS:
        return f"sub {sorted(subs & EXCLUDED_SUBS)[0]}"
    if not (cats & INCLUDED_CATS):
        return "category not on the allow-list"
    if rec.get("lat") is None or rec.get("lng") is None:
        return "no position"
    return None


def build(src: pathlib.Path) -> dict:
    entries, dropped = [], {}
    total = 0
    for prov in ("cm", "cr"):
        f = src / f"{prov}.json"
        if not f.exists():
            continue
        for rec in json.loads(f.read_text()):
            total += 1
            why = excluded(rec)
            if why:
                dropped[why] = dropped.get(why, 0) + 1
                continue
            entries.append({
                "id": rec["id"],
                # Rounded to ~11 m. Enough to find what you are standing in
                # front of, not enough to be a survey of anything.
                "y": round(float(rec["lat"]), 4),
                "x": round(float(rec["lng"]), 4),
                "c": (rec.get("cat") or ["shopping"])[0],
                # 1 == the atlas already knows the hours; those are lower value
                # but still worth confirming, so they stay in with a flag.
                "h": 1 if rec.get("hours") else 0,
            })
    return {
        "kind": "field_index",
        "note": ("Slim lookup index for the LINE field layer. Excluded "
                 "categories are absent by construction — there is no request "
                 "path that can record against them."),
        # This is a derived database of an ODbL source and is published as
        # such. The obligation travels with the file, not just with the README.
        "attribution": ("Place data © OpenStreetMap contributors, ODbL 1.0, "
                        "via Mot Dang (motdang.net)."),
        "licence": "https://opendatacommons.org/licenses/odbl/1-0/",
        "excluded_categories": sorted(EXCLUDED_CATS),
        "excluded_subs": sorted(EXCLUDED_SUBS),
        "total_in_atlas": total,
        "count": len(entries),
        "missing_hours": sum(1 for e in entries if not e["h"]),
        "places": entries,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=pathlib.Path, default=DEFAULT_SRC)
    ap.add_argument("--out", type=pathlib.Path,
                    default=HERE / "worker" / "field-index.json")
    a = ap.parse_args()
    doc = build(a.src)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    kb = a.out.stat().st_size / 1024
    print(f"wrote {a.out}  ({kb:,.0f} KB)")
    print(f"  {doc['count']:,} loggable places out of {doc['total_in_atlas']:,} "
          f"in the atlas")
    print(f"  {doc['missing_hours']:,} of them have no hours — the whole point")
    print(f"  excluded: {doc['total_in_atlas'] - doc['count']:,} "
          f"(worship, care, education, residence, and anything unpositioned)")


if __name__ == "__main__":
    main()
