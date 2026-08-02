"""What people think you have — which is the number that actually governs you.

You hold a billion baht. That is not a secret you get to keep; it is a secret
you get to *delay*. A billion in cash is two hundred tonnes of paper and coin
and somebody had to help you move it. A billion on a chain is a wallet somebody
can read. A billion in a bank is a file, and files have readers.

So the game tracks two numbers. **Actual** wealth is what you have. **Perceived**
wealth is what the city believes you have, and it is perception that sets your
prices, your claimants, and how a room changes when you walk into it.

Perception is sticky. It rises fast on evidence — a big withdrawal, a heavy
haul, a bribe that was too easy, a gift too fine for the occasion — and it falls
slowly, because a reputation for money outlives the money. You can push it down
deliberately by living small, but living small takes time you would rather spend.

**Being read as rich is not simply bad.** Doors open, fences take you seriously,
officials become negotiable. It is just that everything costs more, everyone
wants a piece, and you will never again be sure whether someone likes you or
likes the pile. That last one is the point.
"""

from __future__ import annotations

from dataclasses import dataclass

# The bands the city sorts you into. Each is a floor, in perceived baht.
@dataclass(frozen=True)
class Band:
    key: str
    name: str
    floor: int
    read: str            # how a stranger reads you
    price_mult: float    # what stallholders think you can pay
    greed: int           # persuasion tilt with people who want something
    respect: int         # persuasion tilt with people who grant things
    claim_mult: float    # how much more often somebody comes with a claim


BANDS: tuple[Band, ...] = (
    Band("invisible", "nobody in particular", 0,
         "Nobody looks twice. You get the first price and the short answer.",
         price_mult=1.00, greed=0, respect=0, claim_mult=0.4),
    Band("getting_by", "someone doing all right", 40_000,
         "You are read as working, and solvent, which is the safest thing to be.",
         price_mult=1.05, greed=0, respect=0, claim_mult=0.8),
    Band("comfortable", "someone with a bit put by", 400_000,
         "People start asking after your family, and mean it two ways.",
         price_mult=1.15, greed=1, respect=0, claim_mult=1.0),
    Band("known", "someone who is doing well", 5_000_000,
         "Your name is said in rooms you are not in. Fences return your calls.",
         price_mult=1.35, greed=1, respect=1, claim_mult=1.4),
    Band("rich", "a rich person", 60_000_000,
         "You are treated well and watched closely, and never told the real "
         "price of anything.",
         price_mult=1.70, greed=2, respect=1, claim_mult=2.0),
    Band("the_pile", "the one with the money", 400_000_000,
         "Everyone knows. Every kindness now has a second meaning, and you will "
         "never be certain of a friend again.",
         price_mult=2.20, greed=3, respect=2, claim_mult=3.0),
)


def band_for(amount: int) -> Band:
    out = BANDS[0]
    for b in BANDS:
        if amount >= b.floor:
            out = b
    return out


def band(pc) -> Band:
    return band_for(pc.perceived)


# --- how a secret leaks -----------------------------------------------------
# Each rail leaks differently. Cash leaks by weight — you cannot move two
# hundred tonnes without hands, and hands talk. Crypto leaks by readability.
# A bank leaks by paperwork, slowly and to the worst possible readers.
RAIL_LEAK = {
    "cash":      0.020,   # share of the gap between actual and perceived, per day
    "crypto":    0.012,
    "foreign":   0.008,
    "thai_bank": 0.010,
}

# Evidence the player creates themselves. These land immediately.
EVIDENCE = {
    "big_withdrawal": (0.35, "Somebody watched you carry it out."),
    "heavy_haul":     (0.50, "You needed help to move it, and help remembers."),
    "easy_bribe":     (0.25, "You did not even flinch at the number."),
    "fine_gift":      (0.20, "That was too good a gift for the occasion."),
    "big_project":    (0.60, "A work that size has a name attached, and it is yours."),
    "branch_visit":   (0.30, "A branch that size does not forget a deposit like that."),
}


def actual(pc) -> int:
    return pc.baht + pc.reserve


# Rumour alone can only take people so far. Left completely untouched, a hoard
# gets *talked about* up to this share of its real size and no further — the
# rest of the truth only ever arrives as evidence, and the evidence is your own
# behaviour. This is where the player's agency lives: a pile that sits still and
# is spent in small amounts stays a rumour. One heavy haul and it is a fact.
RUMOUR_CEILING = 0.15


def leak(pc) -> int:
    """One day of the secret getting out on its own. Returns the rise."""
    ceiling = int(actual(pc) * RUMOUR_CEILING)
    gap = ceiling - pc.perceived
    if gap <= 0:
        return 0                     # rumour has said all it can say
    rate = RAIL_LEAK.get(pc.rail, 0.012)
    rise = int(gap * rate)
    pc.perceived = min(ceiling, pc.perceived + rise)
    return rise


def saw(pc, kind: str) -> str | None:
    """Somebody saw something. Perception jumps toward the truth."""
    if kind not in EVIDENCE:
        return None
    share, note = EVIDENCE[kind]
    gap = actual(pc) - pc.perceived
    if gap <= 0:
        return None
    before = band(pc)
    pc.perceived = min(actual(pc), pc.perceived + int(gap * share))
    after = band(pc)
    if after.key != before.key:
        return f"{note} You are now read as {after.name}."
    return note


def live_small(pc) -> tuple[int, str]:
    """Spend a day being nobody. Costs time; drags perception down."""
    before = band(pc)
    drop = int(pc.perceived * 0.12)
    pc.perceived = max(0, pc.perceived - drop)
    after = band(pc)
    if after.key != before.key:
        return drop, (f"A week of cheap rice and the wrong sandals. They have "
                      f"stopped reading you as {before.name}; you are "
                      f"{after.name} again.")
    return drop, ("You keep your head down and buy nothing anyone would "
                  "remember. It helps, a little.")


# --- what the band does to the world ---------------------------------------
def price_multiplier(pc) -> float:
    return band(pc).price_mult


def persuasion_bonus(pc, audience: str) -> tuple[int, str]:
    """Money moves some audiences and hardens others."""
    b = band(pc)
    if audience in ("human", "police", "customs"):
        if b.greed:
            return b.greed, f"They can see what you are ({b.name}), and want some."
        return 0, ""
    if audience == "monk":
        # Merit is not bought, and a rich donor is watched for the reason.
        return (-1 if b.greed >= 2 else 0), (
            "The abbot has met wealthy penitents before." if b.greed >= 2 else "")
    if audience in ("phii", "ancestor", "deva"):
        return 0, ""       # the dead are famously unimpressed
    return 0, ""


def claim_multiplier(pc) -> float:
    return band(pc).claim_mult


def sincerity_doubt(pc) -> int:
    """How hard it is to believe a kindness. Feeds the relationship layer."""
    return band(pc).greed


def status_line(pc) -> str:
    b = band(pc)
    hidden = actual(pc) - pc.perceived
    tail = ""
    if hidden > 0:
        share = hidden / max(1, actual(pc))
        if share > 0.5:
            tail = "  Most of it is still your own business."
        elif share > 0.15:
            tail = "  Some of it is still your own business."
        else:
            tail = "  There is almost nothing left to hide."
    return f"Read as: {b.name}.{tail}"
