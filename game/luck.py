"""Luck: the day's hidden tilt, read through omens nobody agrees on.

In this city luck is not a mood — it is real, and it is *actionable*. Every dawn
the world hands you a sign: your left eye jumps, a gecko drops on your shoulder,
a crow will not stop cawing at your door. What the sign MEANS, though, depends
entirely on who you ask — grandma says money, the coffee auntie says tears, and
both say it like it's obvious. That disagreement is the whole point. The day
really is tilted (``pc.luck`` is +1, 0, or -1, and it nudges the rolls that
matter — the gate scan, a hard persuasion), but the reading you're given is
contested, so you never quite know whether to press your luck today or wait for
a better one. Timing your risks around omens you can't fully trust IS the game.

The number is deliberately hidden. Omens hint; they do not tell.

It is **data**: to grow the folklore, add omens, not machinery. Grounded in
living modern-Thai belief (eye-twitch, itchy palms, jing-jok calls, the colour
of the day), not invented tropes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from . import festivals


# --- colour of the day -----------------------------------------------------
# The Thai week each has its planetary colour (worn for luck, matched to the
# King's birthday, painted on shrines). Index matches festivals.weekday():
# 0 Sun .. 6 Sat. Wednesday famously splits day (green) / night (grey); we keep
# the daytime colour, since that's when the smuggler works the streets.
WEEKDAY_COLOR = (
    "red",     # Wan Athit   — Sunday
    "yellow",  # Wan Chan    — Monday
    "pink",    # Wan Angkhan — Tuesday
    "green",   # Wan Phut    — Wednesday
    "orange",  # Wan Phruehat— Thursday
    "blue",    # Wan Suk     — Friday
    "purple",  # Wan Sao     — Saturday
)


def weekday_color(day: int) -> tuple[str, str]:
    """Return (weekday_name, lucky_colour) for a game day."""
    return festivals.weekday_name(day), WEEKDAY_COLOR[festivals.weekday(day)]


def _a(color: str) -> str:
    return "an" if color[0] in "aeiou" else "a"


# --- numbers the city trusts (data for the lottery to come) ----------------
LUCKY_DIGITS = {
    9: "kao \u2014 rhymes with 'to step up'; progress, rising",
    5: "ha \u2014 the sound of laughter (5-5-5); ease and good cheer",
    8: "Rahu's number \u2014 powerful, sought-after, double-edged",
}
UNLUCKY_DIGITS = {
    0: "sun \u2014 nothing, emptiness; a number to pad, not to trust",
}


# --- the omens -------------------------------------------------------------
@dataclass(frozen=True)
class Omen:
    key: str
    sign: str    # the portent, as it happens to you at dawn
    good: str    # a folk voice reading it well (attributed)
    bad: str     # a folk voice reading it ill (attributed) — and they disagree
    short: str   # a terse recap for the status line


OMENS: list[Omen] = [
    Omen("left_eye",
         "Your left eye twitches before you're even properly awake.",
         "Grandma's rule: left eye jumping means money is walking toward you.",
         "The coffee-cart auntie clicks her tongue \u2014 left is tears, right "
         "is luck, everyone knows that.",
         "your left eye keeps jumping"),
    Omen("right_eye",
         "Your right eyelid flutters and will not settle.",
         "The taxi uncle grins \u2014 right eye, good news coming, wait and see.",
         "Your aunt disagrees flatly: for a woman it runs the other way, and "
         "today that's a warning.",
         "your right eye won't settle"),
    Omen("itchy_right_palm",
         "Your right palm itches maddeningly over breakfast.",
         "Money coming IN, says the whole market \u2014 the right hand receives.",
         "Only if you don't scratch it, warns the noodle man \u2014 scratch, and "
         "you scratch the luck clean away.",
         "your right palm still itches"),
    Omen("itchy_left_palm",
         "Your left palm prickles and itches.",
         "Some say any itching palm means baht on the way, left or right.",
         "The old-timers shake their heads \u2014 left hand, money going OUT. "
         "Hold your wallet today.",
         "your left palm prickles"),
    Omen("jingjok",
         "A jing-jok clicks from the wall as you reach the door \u2014 tok, tok, tok.",
         "Three calls: the spirits say the way is open, go, the monk taught you.",
         "A gecko calling as you leave is the house telling you to wait, says "
         "your landlady, and she means it.",
         "the wall-gecko's warning still nags"),
    Omen("gecko_fall",
         "A fat tukkae drops from the eaves and lands square on your shoulder.",
         "Where it lands tells all \u2014 the shoulder means a burden about to "
         "lift, says the fortune-book.",
         "The girl next door shrieks \u2014 a lizard falling on you is a debt "
         "about to land, everybody knows.",
         "you can still feel where the tukkae landed"),
    Omen("sneeze",
         "You sneeze three times, hard, over your morning rice.",
         "Someone, somewhere, is speaking your name kindly, says your sister.",
         "Or cursing it, mutters the man at the next table \u2014 a sneeze cuts "
         "both ways.",
         "someone, somewhere, is talking about you"),
    Omen("crow",
         "A crow settles on the wire above your door and caws, and caws.",
         "A caller's coming \u2014 guests, news \u2014 says the tea lady; crows "
         "announce arrivals.",
         "Death-bird, says the trishaw man, and spits \u2014 a crow at your door "
         "is never nothing.",
         "the crow's cawing still rings in your ears"),
    Omen("ringing_ear",
         "Your ears ring, a high thin note out of nowhere.",
         "Left ear ringing \u2014 someone far off speaks well of you.",
         "Right ear, corrects the barber \u2014 and that's gossip, the unkind kind.",
         "your ears are still ringing"),
    Omen("broken_glass",
         "A glass slips your hand at dawn and shatters on the floor.",
         "'Break away the bad!' your mother always cried \u2014 broken glass "
         "breaks a curse.",
         "The neighbour peers in, worried \u2014 things break in threes, she "
         "says; watch the next two.",
         "the shattered glass is swept up, but still"),
    Omen("butterfly",
         "A big dark butterfly wanders into the room and will not leave.",
         "An ancestor visiting, says the aunt at the shrine \u2014 be gracious, "
         "it blesses the house.",
         "A black one, though? The cook frowns. Black butterfly, someone's "
         "grief coming to call.",
         "the dark butterfly is still circling"),
    Omen("money_spider",
         "A tiny spider is walking up your sleeve when you glance down.",
         "Little spider, little fortune climbing to you \u2014 don't brush it off!",
         "Brush it DOWN and the luck goes with it, warns the boy \u2014 and you "
         "already moved, didn't you.",
         "you keep checking your sleeve for the spider"),
    Omen("black_dog",
         "A black soi dog crosses your path dead slow, then looks back at you.",
         "The black dog guards the road, says the rider \u2014 it cleared your "
         "way, walk easy.",
         "It looked back, though \u2014 that's the part the drivers don't like, "
         "says the fruit seller.",
         "the black dog's backward look stays with you"),
    Omen("spilled_rice",
         "You knock the pot and rice scatters white across the floor.",
         "Spilled rice, spilled plenty \u2014 the house has more than enough, "
         "says your uncle.",
         "Waste the Rice Goddess's gift and she remembers, tuts the grandmother "
         "\u2014 pick up every grain.",
         "grains of spilled rice keep turning up underfoot"),
    Omen("itchy_foot",
         "The sole of your foot itches fiercely as you lace your shoes.",
         "Itchy feet \u2014 a journey coming, and a good one, says the shoe-mender.",
         "Or you'll walk to a funeral, says his wife, not looking up. Depends "
         "on the foot.",
         "the sole of your foot still itches"),
]

_BY_KEY = {o.key: o for o in OMENS}


def by_key(key: str) -> Omen | None:
    return _BY_KEY.get(key)


# --- the day's tilt --------------------------------------------------------
def raise_luck(pc, amount: int = 1) -> int:
    """Court fortune: nudge the day's hidden tilt, clamped to [-1, +1]. Returns
    the actual change applied (0 if already maxed). Used by dressing in the day's
    colour and by shedding bad luck at a shrine."""
    before = pc.luck
    pc.luck = max(-1, min(1, pc.luck + amount))
    return pc.luck - before


def roll_day(pc, rng: random.Random | None = None) -> list[str]:
    """Set the smuggler's hidden luck for the day and hand back the dawn omen —
    a sign, and the two folk voices who read it opposite ways. Mutates pc.luck
    (+1 / 0 / -1), pc.omen, pc.hunch, pc.dressed_today. Returns display lines;
    the number stays secret."""
    r = rng or random
    omen = r.choice(OMENS)
    pc.luck = r.choices((1, 0, -1), weights=(3, 4, 3))[0]
    pc.omen = omen.key
    pc.dressed_today = False
    name, color = weekday_color(pc.day)
    lines = [
        f"\u2726 {omen.sign}",
        f"  {omen.good}",
        f"  {omen.bad}",
        f"  ({name} \u2014 {_a(color)} {color} day.)",
    ]
    # Some dawns a number surfaces from a dream and won't leave you — the seed
    # of a lottery hunch. It fades if unspent by the next dawn.
    if r.random() < 0.30:
        pc.hunch = f"{r.randint(0, 99):02d}"
        lines.append(f"  A number came to you in the night and lodged there: "
                     f"{pc.hunch}. You can't say why.")
    else:
        pc.hunch = ""
    return lines


def status_line(pc) -> str:
    """A soft one-line reminder for status: the day's colour and this dawn's
    lingering omen — never the hidden number."""
    name, color = weekday_color(pc.day)
    o = by_key(getattr(pc, "omen", ""))
    if not o:
        return f"{name} \u2014 {_a(color)} {color} day."
    return f"{name}, {_a(color)} {color} day \u2014 {o.short}."
