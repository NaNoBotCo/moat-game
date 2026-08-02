"""Suan Prung: the gate the dead go out by, and what it does to a bargain.

For six hundred years the corpses left the city through the south-western gate,
because that is where the custom put them, and custom of that age does not wear
off because somebody bolted a scanner to the arch. Suan Prung is half-shunned.
The officers keep the spirit-heat alarm switched off because it will not stop
screaming. And **every transaction made at that gate is cursed** — not the goods
in general, not the trade in general: *that* exchange, the one you made there,
with the dead going past.

Which is exactly why there is a market there. Nobody decent will trade at Suan
Prung, so the prices are the best in the city, and everybody who does it knows
what they are buying along with the goods. That is the whole bargain the gate
offers: cheap, quiet, unwatched, and it costs you something you cannot see yet.

A curse settles in two places. It settles on **you** — a weight that tilts the
day against you and does not lift on its own. And it settles on the **goods**,
which is worse, because a cursed amulet is worthless to anyone who can read one,
and the bearer is carrying whatever came through the gate with it.

The remedy stands two hundred metres away, which is not a coincidence: through
the gate and down the silver road is **the Silver Temple**, whose smiths have
been beating consecrated silver since long before anybody put a customs post on
the moat. Silver takes a curse off a thing. It is not cheap and it is not quick,
and the smith will want to know where you got it.

*(This temple is the game's own, not a portrait of any actual one. In this
world the silver does not merely decorate the hall — it holds what it has been
given. A panel that has taken a curse goes dull and stays dull, and is replaced,
and the old one is racked in the shed behind the fire. Fifty years of the
south-west gate are stacked back there in flat grey sheets. Everyone knows what
they are. Nobody melts them down.)*
"""

from __future__ import annotations

import random

CURSED_GATE = "suan_prung"
SILVER_TEMPLE = "wualai"          # through the gate, down the silversmiths' road

# What a curse does, per mark held.
LUCK_FLOOR = -1                   # a cursed smuggler's day cannot come up lucky
SCAN_PENALTY = 1                  # per mark, at every gate, for as long as you hold it
VALUE_LOSS = 0.55                 # what a cursed thing is worth to someone who can read it

# Lifting one, at the Silver Temple.
LIFT_COST = 4_000                 # silver, and the smith's hours
LIFT_MINUTES = 180


def marks(pc) -> int:
    return int(pc.cursed.get("marks", 0))


def cursed_items(pc) -> list[str]:
    return list(pc.cursed.get("items", []))


def is_cursed_item(pc, key: str) -> bool:
    return key in pc.cursed.get("items", [])


def at_cursed_gate(pc) -> bool:
    return pc.location == CURSED_GATE


def take(pc, item_key: str | None = None) -> list[str]:
    """A transaction happened at the gate. Settle what it costs."""
    st = dict(pc.cursed)
    st["marks"] = marks(pc) + 1
    if item_key:
        st["items"] = sorted({*st.get("items", []), item_key})
    pc.cursed = st
    lines = ["",
             "The bargain closes. Somewhere behind you, out along the road the "
             "dead take, something registers the exchange and files it."]
    if item_key:
        lines.append("What you just took in hand came through this gate with "
                     "you, and it will read that way to anyone who can read.")
    if marks(pc) == 1:
        lines.append("(You are carrying a curse. The Silver Temple down the "
                     "road can take it off you.)")
    else:
        lines.append(f"({marks(pc)} curses on you now.)")
    return lines


def clamp_luck(pc) -> bool:
    """A cursed day cannot come up lucky. Called after the dawn omen."""
    if marks(pc) and pc.luck > LUCK_FLOOR:
        pc.luck = LUCK_FLOOR
        return True
    return False


def scan_penalty(pc) -> int:
    """What the arch reads off you, on top of everything else you're carrying."""
    return marks(pc) * SCAN_PENALTY


def value_factor(pc, key: str) -> float:
    """What a cursed thing fetches from a buyer who can tell."""
    return VALUE_LOSS if is_cursed_item(pc, key) else 1.0


def can_lift(pc) -> bool:
    return pc.location == SILVER_TEMPLE and marks(pc) > 0


def lift(pc, item_key: str | None = None,
         rng: random.Random | None = None) -> list[str]:
    """The Silver Temple takes one curse off you, or off a thing you carry."""
    r = rng or random
    if marks(pc) <= 0:
        return ["There is nothing on you for them to take off."]
    if pc.baht < LIFT_COST:
        return [f"The silver alone runs {LIFT_COST:,}฿, and you haven't got it."]
    pc.baht -= LIFT_COST
    st = dict(pc.cursed)
    st["marks"] = max(0, marks(pc) - 1)
    lines = [
        "The smith does not ask what you did. He asks where, and when you say "
        "the south-west gate he nods once and starts weighing silver. The work "
        "happens at the fire in the compound, not in the hall — the hall is "
        "where the metal ends up, not where it is made to take anything."]
    if item_key and is_cursed_item(pc, item_key):
        st["items"] = [k for k in st.get("items", []) if k != item_key]
        lines.append(
            "The thing lies in the beaten dish overnight with a sheet of silver "
            "under it and comes out in the morning reading clean. The sheet "
            "does not. It has gone the grey of a cold sky, and it goes on the "
            "rack in the shed with all the others.")
    else:
        lines.append(
            "You sit by the fire with your hands on a sheet of silver until "
            "your arms ache, and something that has been on your shoulders "
            "since the gate goes out of you and into the metal. The smith takes "
            "the sheet away without looking at it. It is dull right through.")
    pc.cursed = st
    if st["marks"]:
        lines.append(f"({st['marks']} still on you.)")
    return lines


def status_line(pc) -> str | None:
    n = marks(pc)
    if not n:
        return None
    items = cursed_items(pc)
    tail = f", and {len(items)} thing{'s' if len(items) != 1 else ''} you carry"
    return (f"Cursed: {n} — every day tilts against you"
            f"{tail if items else ''}. The Silver Temple can take them off.")
