#!/usr/bin/env python3
"""Build the art manifest and the commission deck for Lanna artists.

Two outputs, from one source of truth:

  data/art_manifest.json   the living manifest — every asset the game needs,
                           its spec, and its status (placeholder / commissioned
                           / final). Machine-readable, so the build can check
                           coverage and code can swap an asset without changing.

  <deck>.html              one printable card per asset, for sending to an
                           artist. Each card says what the picture is *for*
                           mechanically, what must be in frame, what must never
                           be in frame, and the exact file it has to arrive as.

The briefs deliberately do **not** prescribe style. Composition and function are
the game's problem; how a thing is drawn is the artist's, and where Lanna visual
convention is concerned the artist is the authority and this document is not.
Every card carries a line saying so.

    python3.13 tools/art_cards.py [--out PATH]
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from game.items import AMULETS, POTIONS                      # noqa: E402
from game.rails import RAILS                                 # noqa: E402
from game.wealth import BANDS                                # noqa: E402
from game.works import WORKS                                 # noqa: E402
from game.world import DISTRICTS                             # noqa: E402
from game.noticing import QUARTERS                           # noqa: E402
from game import relationships as R                          # noqa: E402
from game import festivals as F                              # noqa: E402

# --- formats ---------------------------------------------------------------
# Working specs. Aspect and resolution are NaN's to change once, globally —
# every card reads its numbers from here, so one edit re-specs the whole deck.
FORMATS = {
    "key": dict(px="2560×1440", note="key art, full bleed, 16:9",
                fmt="PNG, RGBA, 300dpi print master + web export"),
    "scene": dict(px="1920×1080", note="place card, full bleed, 16:9",
                  fmt="PNG, RGBA"),
    "portrait": dict(px="1024×1280", note="character, 4:5, waist-up",
                     fmt="PNG, RGBA, transparent background"),
    "item": dict(px="512×512", note="object on transparent ground, 1:1",
                 fmt="PNG, RGBA, transparent background"),
    "icon": dict(px="256×256", note="UI icon, 1:1, legible at 64px",
                 fmt="PNG, RGBA, transparent background"),
    "object": dict(px="1536×1536", note="hero object, 1:1",
                   fmt="PNG, RGBA, transparent background"),
}

# Named palette slots. The artist chooses the actual colours; the game refers to
# them by slot so a repaint never touches code.
PALETTE_SLOTS = ("ink", "teak", "moat", "brass", "silver", "marigold",
                 "lamp", "dull")

# The rails that apply to every single card, printed on every single card.
UNIVERSAL_RAILS = [
    "No real business names, signage, logos or shopfronts. Every venue in this "
    "game is a fictional composite unless a named permission is attached, and "
    "none is attached here.",
    "No recognisable real people. Faces are invented.",
    "Chiang Mai, 2076 — fifty years on. Worn-in near-future over Lanna fabric: "
    "solar shingles on old tin, sensor arches bolted to brick. Never gleaming, "
    "never a clean slate.",
    "The animist layer is real in this world and is never winked at, ironised, "
    "or explained away. Draw it as fact, not as superstition.",
    "Where Lanna visual convention is concerned you are the authority and this "
    "brief is not. If something here is wrong, say so and we change it.",
]


def card(key, title, fmt, function, in_frame, avoid=(), refs=(), slots=(),
         group="", status="placeholder"):
    return dict(key=key, title=title, format=fmt, group=group, status=status,
                function=function, in_frame=list(in_frame), avoid=list(avoid),
                refs=list(refs), palette=list(slots) or list(PALETTE_SLOTS[:4]),
                file=f"art/{group}/{key}.png" if group else f"art/{key}.png")


def build() -> list[dict]:
    cards: list[dict] = []

    # --- the two images the whole game hangs off --------------------------
    cards.append(card(
        "key_art", "Key art — the pile", "key", group="key",
        function="The first image anyone sees, and the whole premise in one "
                 "frame: a person who owns more money than they can physically "
                 "guard, and knows it.",
        in_frame=[
            "A room — not a vault — with 208 tonnes of twenty-baht notes and "
            "coin in it: rice sacks, biscuit tins, buckets of coin, stacked to "
            "the ceiling and out of the doorway.",
            "The bottom layer visibly going soft with damp. This detail is the "
            "story.",
            "One person, small in the frame, looking at it. Not triumphant. "
            "Doing arithmetic.",
            "Somewhere in the composition, a way in that does not lock.",
        ],
        avoid=["Glamour. Nothing about this is a heist poster.",
               "Gold, gems, briefcases, banded stacks of foreign notes."],
        slots=("ink", "teak", "lamp", "dull")))

    cards.append(card(
        "coucal_clock", "The coucal clock", "object", group="key",
        function="The single authoritative time in the world, and the object "
                 "the opening quest is a search for. Everything in the city "
                 "keys off it; the player does not know it exists for hours.",
        in_frame=[
            "A case of teak and glass the height of a man, in a side hall "
            "nobody has any reason to lock.",
            "A brass coucal on a bracket — the bird that comes out at the turn "
            "of the watch and calls three times.",
            "A movement behind the case that has not been wound in a lifetime "
            "and does not appear to need it.",
            "Fifty years of dust everywhere except the bird's track.",
            "A dial divided into EIGHT, not twelve. This is the tell and it "
            "must be readable.",
        ],
        avoid=["Any clock face a viewer could read as an ordinary 12-hour "
               "clock. The eight-fold division is the point.",
               "Grandeur, altar treatment, gold. It is furniture that happens "
               "to be running the city."],
        refs=["game/coucal.py — eight watches, day begins 00:37"],
        slots=("teak", "brass", "ink", "lamp")))

    # --- the ring of water -------------------------------------------------
    gates = {k: d for k, d in DISTRICTS.items() if d.zone == "gate"}
    for key, d in gates.items():
        extra, avoid = [], []
        if key == "suan_prung":
            extra = [
                "This is the gate the dead went out by for six hundred years, "
                "and it is half-shunned. Under the arch, in the shade nobody "
                "wants to stand in, there is a market — the best prices in the "
                "city, because nobody decent will trade here.",
                "The spirit-heat alarm is switched off. Show the switch.",
                "The Silver Temple's roof visible over the wall. The remedy is "
                "two hundred metres from the harm and always has been.",
            ]
            avoid = ["Horror. It is shunned, not haunted-house. The officers "
                     "are bored, not frightened."]
        cards.append(card(
            key, d.name, "scene", group="gates",
            function="A moat gate: permanent, canonical, and a customs "
                     "checkpoint. The player will see this frame hundreds of "
                     "times over hundreds of hours and must know it instantly.",
            in_frame=[d.blurb] + extra,
            avoid=avoid or ["Military hardware. This is customs, not a border "
                            "war — bored people with a scanner."],
            slots=("moat", "teak", "ink", "lamp")))

    # --- inside the wall: the five permanent places ------------------------
    for key, (name, blurb) in QUARTERS.items():
        cards.append(card(
            f"quarter_{key}", name, "scene", group="old_city",
            function="One of five hand-authored places inside the wall. The "
                     "old city NEVER changes — these five frames are the map "
                     "the player keeps for the life of the game, and they are "
                     "where the opening triangulation happens.",
            in_frame=[blurb,
                      "A mile-square grid of teak and temple wall. Solar "
                      "shingles on old tin roofs.",
                      "Something in frame that keeps a schedule — a shutter, a "
                      "gate, a stall — because this quarter is evidence."],
            slots=("teak", "moat", "marigold", "ink")))

    # --- the outer city and the Lanna world --------------------------------
    for key, d in DISTRICTS.items():
        if d.zone in ("gate",):
            continue
        if key == "old_city":
            continue
        grp = "districts" if d.zone == "outside" else "cities"
        fn = ("An outer-city district. Everything outside the moat is mutable "
              "— this frame must be able to change under the simulation later, "
              "so compose it so a building can be gone next year."
              if d.zone == "outside" else
              "A city on the smuggling routes. Loads as a content module, so "
              "it needs to read as its own place, not as Chiang Mai again.")
        cards.append(card(
            key, d.name, "scene", group=grp, function=fn,
            in_frame=[d.blurb],
            slots=("teak", "moat", "lamp", "marigold")))

    # --- the Silver Temple, which is ours ----------------------------------
    cards.append(card(
        "silver_temple", "The Silver Temple", "scene", group="key",
        function="Where a curse comes off. Structurally the counterweight to "
                 "Suan Prung, and a visible ledger of every cursed bargain the "
                 "city has ever needed undone.",
        in_frame=[
            "A hall clad head to foot in worked silver panels, beaten on this "
            "road for generations.",
            "About one panel in twenty gone the grey of a cold sky, taking no "
            "light at all while every other surface throws the lamps back.",
            "Smiths up a ladder replacing a dull one.",
            "The fire in the compound where the work is actually done — NOT "
            "inside the hall.",
            "Behind the fire, a shed; in the shed, a rack; on the rack, fifty "
            "years of dull grey sheets nobody will melt down.",
        ],
        avoid=["This is the game's own temple and not a portrait of any real "
               "one. Do not reproduce an actual temple's identifying features.",
               "Do not make the dull panels look damaged or dirty. They are "
               "full, not spoiled."],
        slots=("silver", "dull", "lamp", "ink")))

    # --- people ------------------------------------------------------------
    for key, c in getattr(R, "CONTACTS", {}).items():
        where = getattr(c, "where", getattr(c, "district", ""))
        faction = getattr(c, "faction", "")
        unseen = faction == "unseen"
        cards.append(card(
            f"contact_{key}", getattr(c, "name", key), "portrait",
            group="people",
            function=("One of the dead, or something older. The player can "
                      "only speak to them with Spirit-speech, and they are "
                      "drawn as plainly real as anyone living — the animist "
                      "layer is fact in this world."
                      if unseen else
                      f"A contact the player builds a bond with over hundreds "
                      f"of hours ({faction}, usually found at "
                      f"{DISTRICTS[where].name if where in DISTRICTS else where})."
                      ),
            in_frame=[f"WHO: {getattr(c, 'heritage', '')}",
                      getattr(c, "bio", ""),
                      (f"They are usually out during: "
                       f"{', '.join(getattr(c, 'hours', ())) or 'any hour'}."
                       + (f" Their voice: “{getattr(c, 'greet')}”"
                          if getattr(c, "greet", "") else "")),
                      "Waist-up, working clothes, doing or holding the thing "
                      "they actually do.",
                      "A face that reads at 200px. The player will see it "
                      "beside dialogue for a very long time."],
            avoid=["Invented face, invented person. No likeness of anyone real.",
                   "No spectral clichés for the unseen — no transparency, no "
                   "glow, no chains." if unseen else
                   "No character-sheet neutrality. They are mid-something."],
            slots=("ink", "teak", "marigold", "lamp")))

    # --- objects the economy runs on ---------------------------------------
    for key, it in {**AMULETS, **POTIONS}.items():
        kind = "amulet" if key in AMULETS else "potion"
        cards.append(card(
            f"item_{key}", it.name, "item", group="items",
            function=f"A {kind} the player buys, carries, authenticates and "
                     f"smuggles. Must read at 64px in a bag list AND stand up "
                     f"to close appraisal, because forensic authentication is "
                     f"a core skill — wear, material and make have to be there.",
            in_frame=[it.note,
                      "Actual size cues. These are small objects.",
                      "Honest wear. A genuine one has a history and it shows."],
            avoid=["Do not invent a lineage or an inscription. If you need the "
                   "real form of something, ask — we have a sourced reference "
                   "corpus and will get it right rather than guess.",
                   "No glow, no aura, no particle effects. Power here is not "
                   "signalled by lighting."],
            refs=["wichaa.net — sourced amulet reference and glossary"],
            slots=("brass", "teak", "ink", "silver")))

    # --- the wallet that is a class choice ---------------------------------
    for key, rail in RAILS.items():
        cards.append(card(
            f"rail_{key}", rail.name, "icon", group="rails",
            function="One of four ways to hold a billion baht, chosen once at "
                     "the start. The icon has to carry the whole trade-off at a "
                     "glance, because the choice is made before the player "
                     "understands the game.",
            in_frame=[rail.blurb,
                      f"STRENGTH: {rail.strength}",
                      f"WEAKNESS: {rail.weakness}"],
            avoid=["No currency symbols as the whole idea. Show the *form* the "
                   "money takes and what holding it costs you."],
            slots=("ink", "brass", "silver", "dull")))

    # --- how the city reads you --------------------------------------------
    for b in BANDS:
        cards.append(card(
            f"band_{b.key}", f"Read as: {b.name}", "icon", group="wealth",
            function="How strangers treat the player at this level of "
                     "*perceived* wealth. Six of these form a ladder the player "
                     "climbs whether they want to or not.",
            in_frame=[b.read,
                      "The same person, read differently. Show it in how "
                      "others hold themselves, not in what the player wears."],
            avoid=["No money in frame. This is about being *seen*, not having."],
            slots=("ink", "marigold", "lamp", "dull")))

    # --- what a billion is actually for ------------------------------------
    for key, w in WORKS.items():
        cards.append(card(
            f"work_{key}", w.name, "scene", group="works",
            function=f"A great work, funded in instalments over months. "
                     f"Consequence: {w.effect}",
            in_frame=[w.blurb,
                      "Work in progress, not a ribbon-cutting. These take "
                      "years and are visible the whole time."],
            avoid=["No philanthropy imagery. Nobody is being thanked."],
            slots=("teak", "moat", "ink", "brass")))

    # --- the turning year --------------------------------------------------
    for f in getattr(F, "CALENDAR", []):
        where = getattr(f, "where", "")
        cards.append(card(
            f"festival_{f.key}", f.name, "scene", group="festivals",
            function="A recurring gathering the player plans around. Presence "
                     "is the cost — a festival eats most of a day and deepens "
                     "every bond in the crowd at once.",
            in_frame=[getattr(f, "blurb", "") or getattr(f, "boon", ""),
                      f"Set at {DISTRICTS[where].name}." if where in DISTRICTS
                      else "Set wherever this is properly kept.",
                      "A crowd the player is inside, not watching."],
            avoid=["No tourist framing. Never sort this into authentic vs. "
                   "for-visitors — it is simply what people do."],
            slots=("marigold", "lamp", "teak", "ink")))

    # --- UI: the lattice ---------------------------------------------------
    cards.append(card(
        "watch_glyphs", "The eight watches — glyph set", "icon", group="ui",
        function="Eight glyphs, one per watch of the coucal day, shown once "
                 "the player can read the lattice. They replace an ordinary "
                 "clock in the player's head, so they must be learnable and "
                 "never confusable with 12-hour time.",
        in_frame=["Eight distinct marks: the still, cold, opening, trading, "
                  "low, turning, lit and quiet watches.",
                  "A sequence that reads as a cycle, legible at 32px.",
                  "Delivered as one sheet plus eight separate files."],
        avoid=["Clock hands. Numerals 1–12. Anything that suggests the "
               "player's own clock still applies."],
        slots=("ink", "brass", "lamp", "dull")))

    cards.append(card(
        "curse_mark", "The curse — visual language", "icon", group="ui",
        function="What a cursed thing or person looks like at a glance, in the "
                 "bag list and on the status line. It is the same grey the "
                 "spent silver panels go.",
        in_frame=["A mark that reads as 'this has taken something in and kept "
                  "it', not as damage or dirt.",
                  "Must sit on an item icon without hiding the item."],
        avoid=["Skulls, red, cracks, rot. This is a full thing, not a broken "
               "one."],
        slots=("dull", "silver", "ink")))

    return cards


# --- rendering -------------------------------------------------------------
CSS = """
:root{--bg:#faf7f2;--fg:#1b1714;--mut:#6b5f54;--line:#d8cec1;--acc:#7a4b2a;
--card:#fff;--warn:#8a2f1d}
@media (prefers-color-scheme:dark){:root{--bg:#14110f;--fg:#f2ece4;
--mut:#a89886;--line:#332c25;--acc:#c98a5a;--card:#1d1916;--warn:#e08a72}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:17px/1.65 "Iowan Old Style",Georgia,serif;padding:2rem 1.25rem 6rem}
.wrap{max-width:60rem;margin:0 auto}
h1{font-size:2.4rem;margin:0 0 .3rem;letter-spacing:-.02em}
.sub{color:var(--mut);margin:0 0 2rem;font-size:1.05rem}
.rails{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--warn);
border-radius:.5rem;padding:1.1rem 1.4rem;margin:0 0 2.5rem}
.rails h2{font-size:1.05rem;margin:0 0 .6rem;text-transform:uppercase;
letter-spacing:.08em;color:var(--warn)}
.rails li{margin:.35rem 0}
.grp{margin:3rem 0 1rem;font-size:1.5rem;border-bottom:2px solid var(--acc);
padding-bottom:.3rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:.6rem;
padding:1.4rem 1.6rem;margin:1.1rem 0;page-break-inside:avoid}
.card h3{margin:0 0 .15rem;font-size:1.35rem}
.meta{color:var(--mut);font-size:.9rem;margin:0 0 1rem;font-family:ui-monospace,Menlo,monospace}
.lbl{font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;
color:var(--acc);margin:1rem 0 .3rem;font-weight:700}
ul{margin:.2rem 0;padding-left:1.3rem}
.no li{color:var(--warn)}
.pal span{display:inline-block;border:1px solid var(--line);border-radius:.3rem;
padding:.12rem .5rem;margin:.15rem .25rem .15rem 0;font-size:.85rem;
font-family:ui-monospace,Menlo,monospace}
.st{float:right;font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;
border:1px solid var(--line);border-radius:1rem;padding:.15rem .7rem;color:var(--mut)}
@media print{body{background:#fff;padding:0;font-size:11pt}.card{border-color:#bbb}}
"""


def render(cards: list[dict], counts: dict) -> str:
    groups: dict[str, list[dict]] = {}
    for c in cards:
        groups.setdefault(c["group"] or "other", []).append(c)
    order = ["key", "gates", "old_city", "districts", "cities", "people",
             "items", "rails", "wealth", "works", "festivals", "ui"]
    titles = {"key": "The images the game hangs off", "gates": "The ring of water",
              "old_city": "Inside the wall — permanent, never redrawn",
              "districts": "The outer city — mutable by design",
              "cities": "The Lanna world", "people": "People",
              "items": "What the economy moves", "rails": "The four rails",
              "wealth": "How the city reads you", "works": "Great works",
              "festivals": "The turning year", "ui": "The lattice & its marks"}
    e = html.escape
    out = [f"<style>{CSS}</style>", '<div class="wrap">',
           "<h1>Moat — art commission deck</h1>",
           f'<p class="sub">Chiang Mai, 2076. {len(cards)} assets across '
           f'{len(groups)} groups. Every card says what the picture is for '
           f'mechanically, what must be in frame, and what must never be. '
           f'Style is deliberately not specified — that is yours.</p>']
    out.append('<div class="rails"><h2>Applies to every card</h2><ul>')
    for r in UNIVERSAL_RAILS:
        out.append(f"<li>{e(r)}</li>")
    out.append("</ul></div>")

    for g in order + [k for k in groups if k not in order]:
        if g not in groups:
            continue
        out.append(f'<h2 class="grp">{e(titles.get(g, g.title()))} '
                   f'<span style="color:var(--mut);font-size:1rem">'
                   f'({len(groups[g])})</span></h2>')
        for c in groups[g]:
            f = FORMATS[c["format"]]
            out.append('<div class="card">')
            out.append(f'<span class="st">{e(c["status"])}</span>')
            out.append(f'<h3>{e(c["title"])}</h3>')
            out.append(f'<p class="meta">{e(c["file"])} &nbsp;·&nbsp; '
                       f'{e(f["px"])} &nbsp;·&nbsp; {e(f["note"])} '
                       f'&nbsp;·&nbsp; {e(f["fmt"])}</p>')
            out.append(f'<div class="lbl">What it is for</div><p>{e(c["function"])}</p>')
            if c["in_frame"]:
                out.append('<div class="lbl">Must be in frame</div><ul>')
                out += [f"<li>{e(x)}</li>" for x in c["in_frame"] if x]
                out.append("</ul>")
            if c["avoid"]:
                out.append('<div class="lbl">Must not be in frame</div><ul class="no">')
                out += [f"<li>{e(x)}</li>" for x in c["avoid"]]
                out.append("</ul>")
            if c["refs"]:
                out.append('<div class="lbl">Reference</div><ul>')
                out += [f"<li>{e(x)}</li>" for x in c["refs"]]
                out.append("</ul>")
            out.append('<div class="lbl">Palette slots</div><p class="pal">'
                       + "".join(f"<span>{e(s)}</span>" for s in c["palette"])
                       + " <span style='border:0;color:var(--mut)'>"
                         "— you choose the actual colours; the game refers to "
                         "them by slot so a repaint never touches code.</span></p>")
            out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path.home() / "Desktop" /
                    "Moat — Art Commission Deck.html")
    ap.add_argument("--manifest", type=pathlib.Path,
                    default=HERE / "data" / "art_manifest.json")
    a = ap.parse_args()

    cards = build()
    counts: dict[str, int] = {}
    for c in cards:
        counts[c["group"]] = counts.get(c["group"], 0) + 1

    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(
        {"kind": "art_manifest",
         "note": "Living document. Status is placeholder | commissioned | "
                 "final. Code refers to assets by `file`, so a swap needs no "
                 "code change.",
         "formats": FORMATS, "palette_slots": list(PALETTE_SLOTS),
         "universal_rails": UNIVERSAL_RAILS,
         "count": len(cards), "by_group": counts, "assets": cards},
        ensure_ascii=False, indent=1))
    a.out.write_text(render(cards, counts))
    print(f"manifest : {a.manifest}")
    print(f"deck     : {a.out}")
    print(f"{len(cards)} assets — " + ", ".join(f"{k} {v}" for k, v in
                                                sorted(counts.items())))


if __name__ == "__main__":
    main()
