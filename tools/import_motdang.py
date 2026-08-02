#!/usr/bin/env python3
"""Import the Mot Dang city catalogue into the game's venue layer.

Mot Dang holds ~9,000 real Chiang Mai places (OSM-derived, with real names,
phones and addresses). The game needs the *shape* of that city — how dense the
food is on which lane, what hours things actually keep, how many wats sit inside
the moat — without shipping a real shop's identity into a game about smuggling.

So this importer keeps the mechanism and drops the identity:

  KEPT      category & sub mix, per-district density, opening-hours archetypes,
            whether a place keeps a narrow window, rough spatial distribution
  DROPPED   name, phone, address, website, OSM id, exact coordinates
  MADE UP   a plain English descriptor ("the corner noodle shop"). We do not
            invent Thai names — Thai writers name these, or a real business
            lends its name under `consent`.

**Consent.** Every venue carries a consent block. Default is `none`, which means
the venue is a fictional composite and is free to be a front, a fence, or a
drop. A venue with `status: "granted"` is a real, named, permissioned business —
and those may only ever be depicted doing their actual trade. See
`game/venues.py`, which enforces that split at load time.

    python3.13 tools/import_motdang.py [--motdang PATH] [--out data/venues.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import re

HERE = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MOTDANG = (HERE.parent / "mot-dang" / "data" / "canonical")

# Approximate real centroids, used only to bin a place into a game district.
# The moat square is the real one; everything outside snaps to the nearest hub.
MOAT = {"lat": (18.7795, 18.7965), "lng": (98.9770, 98.9945)}
CENTROIDS = {
    "old_city":        (18.7880, 98.9857),
    "tha_phae":        (18.7877, 98.9932),
    "chang_phuak":     (18.7960, 98.9860),
    "suan_dok":        (18.7880, 98.9770),
    "chiang_mai_gate": (18.7800, 98.9880),
    "suan_prung":      (18.7810, 98.9820),
    "kad_chang_phuak": (18.8010, 98.9860),
    "warorot":         (18.7890, 98.9985),
    "wualai":          (18.7760, 98.9860),
    "nimman":          (18.7960, 98.9670),
    "ping_river":      (18.7880, 99.0035),
    "night_bazaar":    (18.7830, 98.9990),
    "doi_suthep":      (18.8050, 98.9210),
}
GATES = {"tha_phae", "chang_phuak", "suan_dok", "chiang_mai_gate", "suan_prung"}

# Plain descriptors, by sub-category. Deliberately English and generic: a Thai
# writer replaces these, or a real business lends its name under consent.
DESCRIPTORS = {
    "thai": ["a rice-and-curry shop", "a noodle counter", "a khao soi shop",
             "a somtam stall", "a one-wok kitchen"],
    "street-food": ["a cart under a tarp", "a charcoal grill on the kerb",
                    "a night stall with four stools"],
    "cafe": ["a coffee window", "a cafe with a blue awning",
             "a slow cafe full of students"],
    "bar-pub": ["a bar with the shutter half down", "a beer shop with plastic chairs"],
    "convenience": ["a bright 24-hour shop", "a corner shop with a cold case"],
    "bank": ["a branch with a single teller", "a bank office above a shopfront"],
    "wat": ["a small wat behind a wall", "a temple compound with a working bell"],
    "massage": ["a massage shop with curtained beds", "a two-chair foot massage"],
    "beauty": ["a glass-fronted beauty shop", "a salon with one dryer"],
    "medical": ["a chemist's with a blue cross", "a two-room clinic"],
    "repair": ["a scooter repair with the bike on the pavement",
               "a workshop that fixes anything with a motor"],
    "fuel": ["a two-pump filling station"],
    "hotel-full": ["a hotel with a lit sign"],
    "guesthouse": ["a guesthouse behind a gate"],
    "hostel": ["a hostel with bicycles outside"],
    "condo": ["a condominium block"],
    "international": ["a restaurant with a printed menu"],
}
GENERIC = {
    "food": ["an eating place"], "hotel": ["a place to stay"],
    "essentials": ["a shop for daily things"], "shopping": ["a shop"],
    "wat": ["a temple"], "massage": ["a massage shop"],
    "medical": ["a place for medicine"], "beauty": ["a beauty shop"],
    "transport": ["a transport stop"], "learn": ["a place of learning"],
    "parks": ["an open green space"], "sights": ["a place people come to see"],
    "repair": ["a repair shop"], "realestate": ["a letting office"],
}

_HOURS = re.compile(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})")


def parse_window(hours: str | None) -> tuple[int, int] | None:
    """'Mo-Su 07:00-20:00' -> (420, 1200) minutes. None if unparseable."""
    if not hours:
        return None
    if "24/7" in hours:
        return (0, 1440)
    m = _HOURS.search(hours)
    if not m:
        return None
    o = int(m.group(1)) * 60 + int(m.group(2))
    c = int(m.group(3)) * 60 + int(m.group(4))
    if c <= o:
        c += 24 * 60          # closes after midnight
    return (o, c)


def district_of(lat: float, lng: float) -> str:
    """Bin a real coordinate into a game district."""
    if (MOAT["lat"][0] <= lat <= MOAT["lat"][1]
            and MOAT["lng"][0] <= lng <= MOAT["lng"][1]):
        return "old_city"
    best, best_d = "old_city", 1e9
    for key, (clat, clng) in CENTROIDS.items():
        if key in GATES or key == "old_city":
            continue          # gates are checkpoints, not places to shop
        d = (lat - clat) ** 2 + (lng - clng) ** 2
        if d < best_d:
            best, best_d = key, d
    return best


def descriptor(rng: random.Random, cat: str, sub: str) -> str:
    pool = DESCRIPTORS.get(sub) or GENERIC.get(cat) or ["a shopfront"]
    return rng.choice(pool)


def build(src: pathlib.Path, seed: int = 1296) -> dict:
    rng = random.Random(seed)
    recs = json.loads((src / "cm.json").read_text())
    venues, stats = [], {}
    for i, r in enumerate(recs):
        lat, lng = r.get("lat"), r.get("lng")
        if lat is None or lng is None:
            continue
        cat = (r.get("cat") or ["shopping"])[0]
        sub = (r.get("sub") or [cat])[0]
        dist = district_of(lat, lng)
        window = parse_window(r.get("hours"))
        stats.setdefault(dist, {}).setdefault(cat, 0)
        stats[dist][cat] += 1
        v = {
            "key": f"v{i:05d}",
            "district": dist,
            "cat": cat,
            "sub": sub,
            # A plain descriptor stands in until a writer names it, or a real
            # business lends its name through consent.
            "descriptor": descriptor(rng, cat, sub),
            "open": window[0] if window else None,
            "close": window[1] if window else None,
            # A narrow window is the scheduling primitive the smuggler learns.
            "narrow": bool(window and (window[1] - window[0]) <= 240),
            # Consent is a dead-man's switch: it expires on its own and has to
            # be re-asked. Silence lapses the permission instead of extending
            # it, so losing touch with an owner un-names them automatically.
            "consent": {
                "status": "none",     # none|pending|granted|withdrawn|lapsed
                "real_name": None,    # used ONLY while consent is live
                "granted_on": None,
                "expires_on": None,   # hard stop; past this it is lapsed
                "term_days": 180,
                "renewals": 0,
                "last_asked": None,
                "scope": None,        # what the owner actually agreed to
                "contact": None,
            },
        }
        venues.append(v)
    return {
        "kind": "venues",
        "source": "mot-dang canonical CM catalogue (OSM-derived, ODbL)",
        "note": ("Identities are stripped by construction. A venue is a "
                 "fictional composite unless consent.status == 'granted', in "
                 "which case it is a real permissioned business and may only be "
                 "depicted doing its actual trade."),
        "attribution": "Place data © OpenStreetMap contributors, ODbL, via Mot Dang.",
        "count": len(venues),
        "density": stats,
        "venues": venues,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motdang", default=str(DEFAULT_MOTDANG), type=pathlib.Path)
    ap.add_argument("--out", default=str(HERE / "data" / "venues.json"),
                    type=pathlib.Path)
    a = ap.parse_args()
    data = build(a.motdang)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    narrow = sum(1 for v in data["venues"] if v["narrow"])
    timed = sum(1 for v in data["venues"] if v["open"] is not None)
    print(f"wrote {a.out}  —  {data['count']:,} venues, {timed:,} with real "
          f"hours, {narrow:,} keeping a narrow window")
    for d, cats in sorted(data["density"].items(),
                          key=lambda kv: -sum(kv[1].values())):
        print(f"  {d:<17}{sum(cats.values()):>5}   "
              + ", ".join(f"{c} {n}" for c, n in
                          sorted(cats.items(), key=lambda kv: -kv[1])[:4]))


if __name__ == "__main__":
    main()
