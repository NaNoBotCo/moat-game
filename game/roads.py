"""The ways in and out, and the water they were dug around.

Two things live here because in this city they are the same subject.

**Roads.** Everything outside the wall is mutable, and the roads most of all.
They close — constantly, for reasons that are never dramatic: a culvert goes,
the flats flood, a procession has the road for the afternoon, somebody is
resurfacing a kilometre of it and will be for a month. Closures are seeded from
the day and the road, so a save replays identically and the same seed always
gives the same history. Navigation is therefore a real skill: knowing the
alternate is worth more than knowing the shortest.

The player has **some control** over this, outside the wall only. Fund a road
and it seals, drains, widens; the closures that plague it thin out. Inside the
wall nothing is fundable, because inside the wall nothing changes, ever.

**The moat.** You can fill it in. This is possible, it is not expensive, and it
is the single most tempting thing in the game for a smuggler, because a moat
with no water is a moat with no gates, and a city with no gates has no customs
posts at all. Every scan you have ever sweated goes away in an afternoon.

It is also the most cursed act available to you. The naga are in the hydrology
— that is not a metaphor here, it is where they live — and the ring of water is
the oldest agreement the city has. Break it and the city does not punish you
dramatically. It punishes you the way a body punishes you: everything gets
harder and slower and stays that way. You can dig it out again. It costs far
more than the filling did, it takes months, and nothing lifts until the water
comes back.
"""

from __future__ import annotations

import random

# --- closures ---------------------------------------------------------------
# Reasons, with how long they hold and whether anything gets through at all.
CLOSURE_KINDS = (
    ("flood", "The flats are under water again. Nothing wheeled is getting "
              "through until it drains.", True, 0),
    ("culvert", "A culvert went in the night and took a lane of the road with "
                "it. One lane working, alternating.", False, 45),
    ("resurfacing", "Resurfacing. Half the carriageway, a man with a flag, and "
                    "no indication of how long this has been going on.", False, 35),
    ("procession", "A procession has the road for the afternoon, and it would "
                   "be a poor idea as well as a rude one to push through.",
     False, 50),
    ("landslide", "The mountain has put part of itself across the road. They "
                  "are moving it. They are not moving it quickly.", True, 0),
    ("checkpoint", "An unscheduled checkpoint, well away from any gate, run by "
                   "people who do not have to explain themselves.", False, 60),
    ("market_day", "The whole road is stalls today. You knew this. You forgot.",
     False, 30),
)

# How often a road closes at all, before any road works you have paid for.
BASE_CLOSURE = {
    "inner": 0.06,      # outer-city district to district
    "intercity": 0.22,  # the roads out of town — these go constantly
}


class Closure:
    __slots__ = ("kind", "note", "impassable", "extra")

    def __init__(self, kind, note, impassable, extra):
        self.kind, self.note = kind, note
        self.impassable, self.extra = impassable, extra

    def __repr__(self):
        return f"<Closure {self.kind} impassable={self.impassable}>"


def _seed(day: int, a: str, b: str) -> random.Random:
    """Deterministic per day and per road, and symmetric: the same stretch of
    road is shut in both directions, which is the entire point of a road."""
    return random.Random(f"{day}:{'|'.join(sorted((a, b)))}")


def closure(pc, day: int, a: str, b: str, kind: str = "inner") -> Closure | None:
    """Is this road shut today? Seeded, so a save replays identically."""
    if pc is not None and moat_filled(pc):
        # With the ring gone the city's drainage has nowhere to go. Everything
        # that could close, closes more.
        pass
    r = _seed(day, a, b)
    chance = BASE_CLOSURE.get(kind, 0.06)
    if pc is not None:
        chance *= sealed_factor(pc, a, b)
        if moat_filled(pc):
            chance *= 2.0
    if r.random() >= chance:
        return None
    k, note, impassable, extra = r.choice(CLOSURE_KINDS)
    return Closure(k, note, impassable, extra)


# --- roads the player has paid for -----------------------------------------
# Sealing a road is a local, cheap, outside-the-wall work. It does not stop the
# rain; it stops the road dissolving every time it rains.
SEAL_COST = 12_000_000
SEAL_FACTOR = 0.35          # closures on a sealed road, against an unsealed one


def road_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def sealed(pc, a: str, b: str) -> bool:
    return road_key(a, b) in pc.roads.get("sealed", [])


def sealed_factor(pc, a: str, b: str) -> float:
    return SEAL_FACTOR if sealed(pc, a, b) else 1.0


def seal(pc, a: str, b: str) -> tuple[bool, list[str]]:
    """Pay to seal and drain a stretch of road. Outside the wall only."""
    from .world import DISTRICTS
    for k in (a, b):
        if k in DISTRICTS and DISTRICTS[k].zone == "inside":
            return False, ["Nothing inside the wall is yours to rebuild. The "
                           "old city is not a thing that gets improved."]
    if sealed(pc, a, b):
        return False, ["That road is already sealed."]
    if pc.reserve < SEAL_COST:
        return False, [f"Sealing a stretch runs {SEAL_COST:,}฿ and the rail "
                       f"doesn't hold it."]
    pc.reserve -= SEAL_COST
    st = dict(pc.roads)
    st["sealed"] = sorted({*st.get("sealed", []), road_key(a, b)})
    pc.roads = st
    return True, [f"{SEAL_COST:,}฿ into the road.",
                  "Base course, drainage, a proper camber, and a culvert that "
                  "will still be there next year. It will still close — but it "
                  "will close the way a road closes, not the way a track does."]


# --- the moat ---------------------------------------------------------------
FILL_COST = 60_000_000        # cheap. That is the trap.
FILL_DAYS = 20
DIG_COST = 900_000_000        # dredging back out is nearly the northern line
DIG_DAYS = 240

# What it costs you while the ring is dry.
FILLED_TRAVEL = 2.6           # everything takes this much longer
FILLED_PERSUASION = -2        # nobody wants to deal with you and few say why
FILLED_PRICE = 1.4            # and everything costs more
FILLED_CURSE_PER_WEEK = 1     # the city hands you one of these, weekly, forever


def state(pc) -> dict:
    return pc.moat or {}


def moat_filled(pc) -> bool:
    return bool(state(pc).get("filled"))


def digging(pc) -> bool:
    return state(pc).get("dig_paid", 0) > 0 and moat_filled(pc)


def fill(pc) -> list[str]:
    """Fill in the moat. You can do this. It is a door that opens outward."""
    if moat_filled(pc):
        return ["It is already dry."]
    if pc.reserve < FILL_COST:
        return [f"Filling the ring runs {FILL_COST:,}฿ and the rail doesn't "
                f"hold it."]
    pc.reserve -= FILL_COST
    pc.moat = {"filled": True, "filled_day": pc.day, "dig_paid": 0}
    return [
        "",
        "It takes twenty days and it is the least dramatic thing you have ever "
        "paid for. Fill, compact, fill, compact. Lorries in a queue at each "
        "bastion. Somebody plants grass.",
        "",
        "And then there are no gates. Not closed gates — no gates. There is "
        "nothing for a customs post to sit on and nothing for a scanner arch to "
        "span, and the arches come down in a week because the metal is worth "
        "something. You walk into the old city with whatever you like, from any "
        "direction, at any hour, and nobody stops you, because there is nowhere "
        "left to stand and stop anybody.",
        "",
        "For about a month it is the best decision you have ever made.",
        "",
        "Then the wells go strange. Then the drains, which have run one "
        "direction since Mangrai, stop agreeing about which direction that was. "
        "Nobody in the city will say the word out loud, and everybody knows "
        "which word it is, and everyone who meets you now knows what you did.",
    ]


def dig_out(pc, amount: int) -> tuple[bool, list[str]]:
    """Pay to dredge the ring back open. Nothing lifts until the water returns."""
    if not moat_filled(pc):
        return False, ["The water is where it should be."]
    amount = int(amount)
    if amount <= 0 or amount > pc.reserve:
        return False, ["The rail doesn't hold that."]
    pc.reserve -= amount
    st = dict(state(pc))
    st["dig_paid"] = st.get("dig_paid", 0) + amount
    if st["dig_paid"] >= DIG_COST:
        pc.moat = {"filled": False, "filled_day": 0, "dig_paid": 0,
                   "was_filled": True}
        return True, [
            f"{amount:,}฿ into the dig.",
            "",
            "It takes the better part of a year and it costs fifteen times what "
            "the filling did, which everybody could have told you and several "
            "people did.",
            "",
            "The water comes back in over one night in the rains, all the way "
            "round, faster than the engineers expected and from directions they "
            "had not entirely accounted for. In the morning the ring is full and "
            "the city is quiet in the way a room is quiet after an argument "
            "ends.",
            "",
            "The gates go back up within the month, because of course they do. "
            "You will be scanned at every one of them for the rest of your life, "
            "and you will be glad of it, which is its own kind of joke.",
        ]
    pc.moat = st
    left = DIG_COST - st["dig_paid"]
    return False, [f"{amount:,}฿ into the dig.",
                   f"{left:,}฿ and months of it still to go. Nothing lifts "
                   f"until the water is back — not some of it, all of it."]


# --- what a dry ring does to everything else -------------------------------
def travel_factor(pc) -> float:
    return FILLED_TRAVEL if moat_filled(pc) else 1.0


def persuasion_penalty(pc) -> int:
    return FILLED_PERSUASION if moat_filled(pc) else 0


def price_factor(pc) -> float:
    return FILLED_PRICE if moat_filled(pc) else 1.0


def gates_exist(pc) -> bool:
    """The whole temptation, in one boolean."""
    return not moat_filled(pc)


def daily(pc) -> list[str]:
    """The weekly reminder that the city has not forgotten."""
    if not moat_filled(pc):
        return []
    since = pc.day - state(pc).get("filled_day", pc.day)
    if since and since % 7 == 0:
        from . import curse
        curse.take(pc)
        return ["The wells taste of iron again this week. Something that used "
                "to be owed to the water is being collected from you instead."]
    return []


def status_line(pc) -> str | None:
    if not moat_filled(pc):
        return None
    st = state(pc)
    paid = st.get("dig_paid", 0)
    tail = (f" Dig-out {100 * paid // DIG_COST}% funded."
            if paid else " Nothing is being done about it.")
    return (f"THE RING IS DRY. No gates, no scans — and everything is slower, "
            f"dearer and against you.{tail}")
