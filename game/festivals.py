"""The Lanna festival year — the fixed anchors the whole game is played around.

Festivals are the tentpoles of the calendar. Some recur every week (the walking
streets, the Buddhist sabbath); the great annual rites fall on a single day and
the whole city bends toward them. Mechanically they are the strongest lever the
player has: join one and every bond present there deepens at once, city heat and
personal stress drop, and the sacred rites let you spend a food offering for more
relief. So you plan your days to be in the right district on the right day.

Everything here is grounded in the real Chiang Mai up to 2007 — the Ratchadamnoen
Sunday walking street (begun ~2002), the Wualai Saturday street in the silver
quarter, Wan Phra at the temples, and Inthakhin Bucha at Wat Chedi Luang.

It is deliberately **data**: to grow the year, add festivals, not machinery.
"""

from __future__ import annotations

from dataclasses import dataclass

from .events import Event, ev

# The city's slice begins on a Wan Chan (Monday), so several weekend walking
# streets fall inside the window. Thai weekday names, Sunday-first.
WEEK = ("Wan Athit", "Wan Chan", "Wan Angkhan", "Wan Phut",
        "Wan Phruehat", "Wan Suk", "Wan Sao")
_START_INDEX = 1  # game day 1 == WEEK[1] == Wan Chan (Monday)

# The day the Inthakhin flowers are laid — the arc's whole clock runs to it.
# ~2.5 weeks of unhurried lead-in: room to wander, plan around festivals, and
# get to know people without a perfect-play race (see the "relaxing" feel goal).
INTHAKHIN_DAY = 18


def weekday(day: int) -> int:
    return (_START_INDEX + day - 1) % 7


def weekday_name(day: int) -> str:
    return WEEK[weekday(day)]


@dataclass(frozen=True)
class Festival:
    key: str
    name: str
    where: str            # district key; "" == city-wide (any temple/street)
    kind: str             # "weekly" | "annual"
    weekday: int = -1     # for weekly: 0 (Sun) .. 6 (Sat)
    day: int = 0          # for annual: the game day it falls
    span: int = 1         # how many days it lasts (annual)
    lanna: str = ""       # a true note — the culture the festival teaches
    blurb: str = ""       # what it's like to be there
    boon: str = ""        # short label of the payoff for taking part
    # --- what taking part actually does (the differentiated payoff) ---------
    heat: int = -2        # city heat cooled by giving the day to it
    stress: int = -1      # personal strain eased
    bond: int = 1         # how much each bond present here deepens
    minutes: int = 150    # how much of the day it eats
    merit: bool = False   # a sacred rite: you may make merit with an offering


# Festivals that fall within the playable window (~2.5 weeks to Inthakhin).
CALENDAR: list[Festival] = [
    Festival(
        "sunday_walk", "Ratchadamnoen Sunday Walking Street", "old_city",
        kind="weekly", weekday=0,
        lanna="Every Sunday since about 2002, Ratchadamnoen Road from Tha Phae "
              "Gate into the old city closes to traffic and fills with Lanna "
              "handicraft, buskers, and khan toke food — the city meeting itself.",
        blurb="Lantern-light, khao soi steam, a saw-sam-sai played for coins; the "
              "whole old city is out walking, and everyone's easier to reach.",
        boon="deepens your bond with every old-city contact here; drops city heat"),
    Festival(
        "saturday_walk", "Wualai Saturday Walking Street", "wualai",
        kind="weekly", weekday=6,
        lanna="Wualai Road, the old silversmith quarter south of Chiang Mai Gate, "
              "holds its own street each Saturday — repoussé silver, Shan and Hmong "
              "craft, and the ring of hammers that named the road.",
        blurb="Beaten-silver stalls glinting, sai ua on the grill, the Saturday "
              "crowd thick from the gate to the temple.",
        boon="deepens your bond with every Wualai contact here; drops city heat"),
    Festival(
        "wan_phra", "Wan Phra (the Buddhist sabbath)", "",
        kind="weekly", weekday=3,
        lanna="The Buddhist observance day, kept roughly weekly by the moon. "
              "Laypeople carry food to the monks at dawn, take the precepts, and "
              "let the temple quiet the week — merit-making, not spectacle.",
        blurb="Incense and white cloth, an old woman's whispered chant, the monks "
              "moving slow; a day when the sangha will actually see you.",
        boon="big stress relief; make merit with a food offering for more",
        heat=-1, stress=-3, bond=1, minutes=120, merit=True),
    Festival(
        "inthakhin", "Inthakhin Bucha (Sai Khan Dok)", "old_city",
        kind="annual", day=INTHAKHIN_DAY, span=1,
        lanna="At the turn into the rains, Chiang Mai gathers at Wat Chedi Luang "
              "to honour the Sao Inthakhin, the city pillar Kawila enshrined. For "
              "six to eight days the faithful lay flowers (sai khan dok) around it, "
              "renewing the vow that keeps the city's shade. It ends the day the "
              "flowers are offered.",
        blurb="The pillar's hall banked in marigold and jasmine, candle-smoke and "
              "the whole city circling — the year's holiest hinge.",
        boon="the biggest heat drop of the year; make merit for more",
        heat=-3, stress=-2, bond=1, minutes=180, merit=True),
]

# The wider turning year — annual rites outside this chapter's window. Shown for
# planning and teaching (the Lanna calendar), not yet played. Grow this into the
# CALENDAR as the game's timeline lengthens toward a full Stardew-style year.
LANNA_YEAR: list[tuple[str, str, str]] = [
    ("Songkran (Pi Mai Mueang)", "mid-April",
     "The Lanna new year — water poured over Buddha images and elders, sand "
     "chedis raised at the temples, the old city one long, drenched blessing."),
    ("Visakha Bucha", "May full moon",
     "The Buddha's birth, enlightenment, and passing on one moon; candle "
     "processions (wian tian) circle the chedis after dark."),
    ("Inthakhin Bucha", "late May–early June",
     "The city-pillar festival at Wat Chedi Luang — the anchor of this chapter."),
    ("Khao Phansa", "July full moon",
     "The start of the rains retreat; the monks stay in, and the laity carry "
     "candles and cloth to see them through the wet months."),
    ("Yi Peng & Loy Krathong", "November full moon",
     "Lanna's festival of light — khom loi lanterns loosed into the night sky "
     "and krathong set on the Ping, carrying off the year's misfortune."),
]


# --- queries the engine leans on --------------------------------------------
def _active(f: Festival, day: int) -> bool:
    if f.kind == "weekly":
        return weekday(day) == f.weekday
    return f.day - f.span < day <= f.day


def on_day(day: int) -> list[Festival]:
    """Every festival happening on this game day."""
    return [f for f in CALENDAR if _active(f, day)]


def here_now(location: str, day: int) -> list[Festival]:
    """Festivals you can actually join right here, right now."""
    return [f for f in on_day(day) if f.where in ("", location)]


def days_until(day: int, f: Festival) -> int:
    """Whole days until this festival's next occurrence (0 == today)."""
    if f.kind == "weekly":
        for d in range(8):
            if weekday(day + d) == f.weekday:
                return d
        return 7
    return f.day - day


def upcoming(day: int, within: int = 8) -> list[tuple[int, Festival]]:
    """(days_until, festival) for what's coming, soonest first; excludes today."""
    out = []
    for f in CALENDAR:
        d = days_until(day, f)
        if 0 < d <= within:
            out.append((d, f))
    out.sort(key=lambda t: t[0])
    return out


# --- taking part: mutate state, return events (never print) -----------------
def _best_offering(pc) -> str | None:
    """The offering you carry with the most merit weight, or None."""
    from .items import OFFERINGS
    best, best_w = None, 0
    for k, w in OFFERINGS.items():
        if pc.inventory.get(k, 0) > 0 and w > best_w:
            best, best_w = k, w
    return best


def celebrate(pc, location: str, day: int) -> list[Event]:
    """Give the day to a festival on here now. Each festival pays out its own
    way; the sacred ones let you make merit with a carried offering."""
    from . import relationships
    from .items import OFFERINGS, get
    present = here_now(location, day)
    if not present:
        return [ev("festival_none")]
    f = present[0]
    if pc.festivals_seen.get(f.key) == day:
        return [ev("festival_repeat", name=f.name)]
    pc.festivals_seen[f.key] = day

    warmed = []
    for c in relationships.here(pc, location):
        before = relationships.tier(relationships.bond_of(pc, c.key))
        b = relationships.adjust_bond(pc, c.key, f.bond, day)
        after = relationships.tier(b)
        warmed.append((c.name, after if after != before else ""))

    heat, stress = f.heat, f.stress
    events = [ev("festival_joined", key=f.key, name=f.name, lanna=f.lanna,
                 warmed=warmed, heat=heat, stress=stress, minutes=f.minutes)]

    if f.merit:
        off = _best_offering(pc)
        if off:
            pc.add_item(off, -1)
            extra_heat = -1
            extra_stress = -(1 + OFFERINGS[off] // 2)   # richer alms, deeper ease
            heat += extra_heat
            stress += extra_stress
            events.append(ev("festival_merit", item=get(off).name,
                             extra_heat=extra_heat, extra_stress=extra_stress))
        else:
            events.append(ev("festival_merit_none"))

    pc.add_heat(heat)
    pc.add_stress(stress)
    return events
