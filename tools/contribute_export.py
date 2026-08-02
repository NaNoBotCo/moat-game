#!/usr/bin/env python3
"""Export what the game has observed, in the shape Mot Dang's queue accepts.

Writes a file. **It does not post anything anywhere.** Sending observations to a
live service is a publishing act and wants a human deciding to do it, so the
last step is deliberately manual: this produces the payload, somebody reads it,
somebody posts it.

The payload is bounded to what Mot Dang's own worker says a stranger may
propose — a place id and an hours observation, with no name, address or
coordinate anywhere in it, and everything routed to the moderation queue rather
than to a live write.

    python3.13 tools/contribute_export.py [--save saves/slot1.json] [--out PATH]
    python3.13 tools/contribute_export.py --demo     # shape check, no save
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from game.character import Character           # noqa: E402
from game import contribute                    # noqa: E402

ENDPOINT_NOTE = ("POST to the atlas's /suggest endpoint — the moderation queue "
                 "that a human reads. Never /claim (that is for an owner "
                 "speaking about their own business) and never a direct write.")


def demo_pc() -> Character:
    """A worked example, so the shape can be checked without a save file."""
    pc = Character.create("Demo", "trader")
    # Six passers-by see one shop over a week: open 09:40–18:10, shut outside.
    seen = [(9 * 60 + 40, True), (11 * 60, True), (14 * 60 + 15, True),
            (18 * 60 + 10, True), (7 * 60 + 30, False), (21 * 60, False)]
    for i, (m, is_open) in enumerate(seen):
        contribute.log(pc, "cm-osm-node-10008774317", m, i % 7, is_open,
                       source="field")
    # And one place nobody has seen enough of.
    contribute.log(pc, "cm-osm-node-99999999", 10 * 60, 1, True, source="field")
    # An in-game sighting, which must never reach the atlas.
    contribute.log(pc, "v00003", 11 * 60, 2, True, source="play")
    return pc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", type=pathlib.Path,
                    default=HERE / "saves" / "slot1.json")
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path.home() / "Desktop" /
                    "Moat — hours for Mot Dang.json")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    if a.demo:
        pc = demo_pc()
    elif a.save.exists():
        pc = Character.from_dict(json.loads(a.save.read_text()))
    else:
        raise SystemExit(f"no save at {a.save} (try --demo)")

    windows = contribute.ready(pc)
    payload = {
        "kind": "moat_hours_contribution",
        "target": ENDPOINT_NOTE,
        "scope": ("Hours only. No name, address, coordinate, contact detail or "
                  "ownership claim appears in this file, by construction."),
        "count": len(windows),
        "suggestions": [contribute.as_suggestion(w) for w in windows],
    }
    a.out.write_text(json.dumps(payload, ensure_ascii=False, indent=1))

    for line in contribute.summary(pc):
        print(line)
    print(f"\nwrote {a.out}")
    print(f"{len(windows)} suggestion(s) ready. Nothing has been sent.")
    for w in windows:
        print(f"  {w.place_id}  {contribute.hhmm(w.opens)}–"
              f"{contribute.hhmm(w.closes)}  "
              f"({w.observations} obs, {w.agreement:.0%} agreement)")


if __name__ == "__main__":
    main()
