"""The lottery (huay): the wandering ticket-seller, and the fortnightly draw.

Everyone plays. Sellers drift through every lane at every hour with a wooden
board of tickets, and whether you buy comes down to feel, not maths:

  1. the NUMBERS — does a tail pull at your gut? (a dream-hunch, the laughing
     five and the climbing nine, the day's own number),
  2. how WELCOME the seller is when they appear — a lucky day, your own home
     lane, a settled mind make the meeting auspicious; a sour mood makes it wrong,
  3. whether the SELLER is one the city holds lucky — the blind, the very old,
     the katoey sisters, a child fresh from the temple, one who's been to the
     spirit-tree. Buying from lucky hands is buying luck.

All three genuinely tilt the (hidden) odds frozen onto the ticket at purchase.
The government draws on the 1st and the 16th; you match the last two digits.
Mostly you lose — that is the honest truth of it — but now and then the seller
was right, and your tail comes up.

It is **data**: to grow the folklore, add vendors, not machinery.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import luck

# The draws that fall inside the ~18-day window (the real 1st & 16th rhythm).
DRAW_DAYS = (8, 16)

TAIL_PAYOUT = 50    # matching the last two digits pays 50x the ticket
FULL_PAYOUT = 400   # the rare full-number dream pays 400x
FULL_CHANCE = 0.08  # of the wins that land, this share are the full six digits


def next_draw(day: int) -> int | None:
    """The next draw strictly after `day`, or None if none remain in the window."""
    for d in DRAW_DAYS:
        if d > day:
            return d
    return None


# --- the sellers -----------------------------------------------------------
@dataclass(frozen=True)
class Vendor:
    key: str
    name: str          # how they read as they walk up
    aura: int          # cultural luck the city grants them: +2 blessed .. -1 sour
    aura_note: str     # the belief, said plainly (no lampshade)


# Weighted so the plainly-lucky sellers are a little rarer — meeting one is a
# small event. Grounded in living huay belief: the blind and the very old are
# close to fortune, the katoey sisters carry the luck-touch, twins and temple
# children are auspicious, a spirit-tree reader sells numbers off the bark.
VENDORS: list[Vendor] = [
    Vendor("blind", "a blind seller, tapping her board along the kerb", 2,
           "The blind walk close to fortune, people say \u2014 buy from her hand "
           "and you buy a little of it."),
    Vendor("granny", "a tiny ancient grandmother, older than the moat, it seems", 2,
           "So old she's half in the other world already; her fingers on a "
           "ticket are as good as a blessing."),
    Vendor("katoey", "a statuesque katoey with a board of tickets and a better "
           "manicure than yours", 1,
           "The sisters carry the luck-touch \u2014 everyone reaches for a ticket "
           "from their hand."),
    Vendor("twins", "a pair of identical twins working the lane shoulder to "
           "shoulder", 1,
           "Twins are auspicious; two of one soul selling you the same number "
           "doubles the omen."),
    Vendor("temple_boy", "a lay boy just down from the temple, incense still in "
           "his shirt", 1,
           "His numbers came straight off the abbot's calendar this morning."),
    Vendor("tree", "a woman with bark-dust on her sleeve, fresh from the "
           "Nang Ta-khian tree", 1,
           "She read these tails off the spirit-tree's trunk \u2014 the lady "
           "gives numbers to those who ask right."),
    Vendor("hawker", "a regular hawker working the lane, flip-flops and a tin "
           "of tickets", 0,
           "No story to him; just a man selling paper. The luck, if any, is "
           "all in the numbers."),
    Vendor("hawker2", "a bored teenager with a board slung off one shoulder", 0,
           "Ordinary as rain. You'd be buying the tail, not the seller."),
    Vendor("tout", "a sweaty tout who reeks of Chang and won't take a no", -1,
           "Something about him sets your teeth on edge \u2014 an unlucky hand "
           "to take paper from, your gut says."),
]

_LUCKY_DIGITS = set("95")   # the laughing five, the climbing nine


@dataclass
class Encounter:
    vendor: Vendor
    tickets: list[dict] = field(default_factory=list)
    welcome: int = 0        # how auspicious the meeting is (context)
    welcome_note: str = ""


def _tail_charm(tail: str, hunch: str) -> list[str]:
    """The gut-reading cues on a single tail — never the odds, just the folklore."""
    cues = []
    if hunch and tail == hunch:
        cues.append("the very number from your dream")
    lucky = [d for d in tail if d in _LUCKY_DIGITS]
    if "9" in lucky and "5" in lucky:
        cues.append("the laughing five beside the climbing nine")
    elif "9" in lucky:
        cues.append("the climbing nine")
    elif "5" in lucky:
        cues.append("the laughing five")
    if tail in ("00", "11", "22", "33", "44", "55", "66", "77", "88", "99"):
        cues.append("a matched pair, a strong-looking tail")
    return cues


def _win_chance(pc, vendor: Vendor, tail: str, mood: int) -> float:
    """The hidden odds, frozen onto a ticket at the moment of buying. All three
    feel-factors — seller, gut, welcome — plus the day's tilt genuinely count,
    each a distinct term so none is double-weighed."""
    p = 0.05
    p += 0.04 * vendor.aura                       # (3) a lucky seller's hand
    if pc.hunch and tail == pc.hunch:
        p += 0.09                                 # (1) the dream-number pull
    p += 0.02 * sum(1 for d in tail if d in _LUCKY_DIGITS)  # (1) lucky digits
    p += 0.03 * mood                              # (2) how welcome the meeting is
    p += 0.04 * getattr(pc, "luck", 0)            # the day itself
    return max(0.01, min(0.35, p))


def appear(pc, rng: random.Random | None = None) -> Encounter | None:
    """A seller drifts up out of the lane. Returns an Encounter to offer, or
    None if there's no draw left to sell toward."""
    r = rng or random
    draw = next_draw(pc.day)
    if draw is None:
        return None
    vendor = r.choices(VENDORS, weights=[2, 2, 3, 3, 3, 3, 5, 5, 3])[0]

    # How welcome the meeting is: a settled mind makes the meeting auspicious, a
    # frayed one makes it wrong (mood); the day's own tilt colours it too. Mood
    # is its own odds-term; the day's tilt is counted separately in _win_chance.
    mood = 0
    if pc.stress <= 2:
        mood = 1
    elif pc.stress >= 7:
        mood = -1
    welcome = mood + (1 if getattr(pc, "luck", 0) > 0 else
                      -1 if getattr(pc, "luck", 0) < 0 else 0)
    if welcome > 0:
        wnote = ("They've come at a good moment \u2014 the day feels open, and an "
                 "open day is when you should say yes.")
    elif welcome < 0:
        wnote = ("Something's off in the timing; they've caught you at a sour "
                 "hour, and a sour hour is a poor time to tempt fortune.")
    else:
        wnote = "An ordinary moment \u2014 no wind either way."

    n = r.randint(2, 3)
    tickets = []
    for i in range(n):
        tail = f"{r.randint(0, 99):02d}"
        if i == 0 and pc.hunch and r.random() < 0.5:
            tail = pc.hunch                       # your dream-number can show up
        number = f"{r.randint(0, 9999):04d}{tail}"
        cost = r.choice((80, 80, 100))
        tickets.append({
            "number": number, "tail": tail, "cost": cost,
            "draw_day": draw, "vendor": vendor.name,
            "p": _win_chance(pc, vendor, tail, mood),
            "hunch": bool(pc.hunch and tail == pc.hunch),
        })
    return Encounter(vendor, tickets, welcome, wnote)


def ticket_label(pc, t: dict) -> str:
    """A rich, gut-level label for one ticket in the buy menu — cues, not odds."""
    cues = _tail_charm(t["tail"], getattr(pc, "hunch", ""))
    charm = f"  \u2014 {'; '.join(cues)}" if cues else ""
    return (f"No. {t['number']}  (tail {t['tail']})   {t['cost']}\u0e3f"
            f"   draws day {t['draw_day']}{charm}")


# --- the draw --------------------------------------------------------------
def settle(pc, rng: random.Random | None = None) -> list[str]:
    """At dawn, resolve every held ticket whose draw has now passed. Each is its
    own small fate, weighted by the luck frozen onto it at purchase. Pays out and
    clears resolved tickets. Returns narration lines."""
    r = rng or random
    due = [t for t in pc.tickets if t["draw_day"] <= pc.day]
    if not due:
        return []
    lines = ["\u2726 The lottery is drawn \u2014 the numbers read out over every "
             "radio and phone in the city."]
    for t in due:
        won = r.random() < t.get("p", 0.05)
        if won:
            full = r.random() < FULL_CHANCE
            prize = t["cost"] * (FULL_PAYOUT if full else TAIL_PAYOUT)
            pc.baht += prize
            if full:
                lines.append(
                    f"  Your No. {t['number']} \u2014 all six, the whole number, "
                    f"come up. The board can't be right, but it is. "
                    f"{prize:,}\u0e3f. The seller knew.")
            else:
                lines.append(
                    f"  The tail comes up {t['tail']} \u2014 and you have it. "
                    f"Your ticket from {t['vendor']} pays {prize:,}\u0e3f. "
                    f"Fortune was real today.")
        else:
            miss = f"{(int(t['tail']) + r.choice((-3, -2, 2, 3, 7))) % 100:02d}"
            lines.append(
                f"  Tail {miss} takes it; your {t['tail']} was nothing after all. "
                f"The paper's dead \u2014 mai pen rai, there's always the 16th.")
    pc.tickets = [t for t in pc.tickets if t["draw_day"] > pc.day]
    return lines
