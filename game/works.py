"""Great works — what a billion baht is actually for.

Buying amulets with this much money is like bailing the Ping with a cup. The
pile only becomes interesting when it stops being money and starts being
infrastructure: a railway where the road always sucked, a drain under a district
that floods every year, papers for people the formal economy has locked out.

Great works are funded **in instalments**, over months, and every instalment is
visible. You do not quietly build a railway. Funding one at scale is the single
loudest thing you can do with the pile — it puts your name on a thing that
cannot be moved, and the city adjusts its estimate of you accordingly.

Each work carries a real mechanical consequence, not a score. What it changes is
named in `effect`, and the systems that care read it through the helpers at the
bottom of this module rather than hard-coding a flag.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Work:
    key: str
    name: str
    cost: int
    blurb: str
    effect: str
    where: str = ""          # district it visibly touches, if any


WORKS: dict[str, Work] = {
    "train_north": Work(
        "train_north", "The northern line to Chiang Rai",
        cost=900_000_000,
        blurb="One hundred and ninety kilometres of mountain that has defeated "
              "every government that ever costed it. Tunnels, viaducts, and a "
              "route survey that three ministries have lost.",
        effect="A train runs the Chiang Rai corridor — fast, cheap, and the "
               "safest road north you will ever have.",
    ),
    "drainage": Work(
        "drainage", "Drainage under the eastern flats",
        cost=340_000_000,
        blurb="Culverts, pumps, and a retention pond where the market used to "
              "flood to the knee. The water has opinions about being moved, and "
              "so do the people who live in it — both must be settled with.",
        effect="The damp stops eating your stash, and a district that flooded "
               "every year stops flooding.",
        where="ping_river",
    ),
    "papers": Work(
        "papers", "A standing fund for papers",
        cost=180_000_000,
        blurb="Lawyers, filing fees, translators, and the patience to sit in "
              "the queue for people who cannot afford to lose the day's work. "
              "Status is the gate everything else in this city hangs on.",
        effect="People locked out of the formal economy get in — and the ones "
               "you helped remember it. Claims on your pile drop sharply.",
    ),
    "market_hall": Work(
        "market_hall", "A market hall for the vendor families",
        cost=260_000_000,
        blurb="Roof, water, power, cold storage, and — the part that costs — "
              "tenure. Stalls that cannot be cleared by anybody with a "
              "clipboard and a friend at the district office.",
        effect="The vendor families hold their ground, and they price you as "
               "one of their own rather than as a mark.",
        where="warorot",
    ),
    "wat_hall": Work(
        "wat_hall", "Restoration of the clock's hall",
        cost=120_000_000,
        blurb="Teak, tile, gold leaf, and a maintenance endowment for the one "
              "movement in this city that everything else keeps time by. "
              "Nobody has funded its upkeep in fifty years. Nobody had to.",
        effect="The clock is safe for another century, and the sangha knows "
               "exactly who paid for it.",
        where="old_city",
    ),
    "land_bank": Work(
        "land_bank", "Land assembly ahead of the flood maps",
        cost=500_000_000,
        blurb="Buy the low ground cheap, before the drainage study is public "
              "and after you have read it. Entirely legal. Not entirely nice.",
        effect="You own the ground the outer city is about to be rebuilt on.",
    ),
}

# You may put money in a bit at a time; a work only lands when it is fully paid.
MIN_INSTALMENT = 1_000_000


def progress(pc, key: str) -> int:
    return pc.works.get(key, 0)


def complete(pc, key: str) -> bool:
    return progress(pc, key) >= WORKS[key].cost

def completed(pc) -> list[Work]:
    return [w for k, w in WORKS.items() if complete(pc, k)]


def remaining(pc, key: str) -> int:
    return max(0, WORKS[key].cost - progress(pc, key))


def fund(pc, key: str, amount: int) -> tuple[bool, list[str]]:
    """Put money into a great work. Returns (landed_just_now, lines)."""
    w = WORKS[key]
    amount = int(amount)
    if amount < MIN_INSTALMENT:
        return False, [f"An instalment under {MIN_INSTALMENT:,}฿ is not worth "
                       f"the paperwork it generates."]
    if amount > pc.reserve:
        return False, ["The rail doesn't hold that much."]
    was_done = complete(pc, key)
    pc.reserve -= amount
    pc.works = {**pc.works, key: progress(pc, key) + amount}
    lines = [f"{amount:,}฿ into {w.name}."]
    if not was_done and complete(pc, key):
        if key == "train_north":
            # The route table has always read the old project store; keep it the
            # single source of truth for whether the rails exist.
            from .world import TRAIN_NORTH_GOAL
            pc.projects = {**pc.projects, "train_north": TRAIN_NORTH_GOAL}
        lines += ["", f"— {w.name} is finished. {w.effect}"]
    else:
        left = remaining(pc, key)
        lines.append(f"{left:,}฿ still wanted "
                     f"({100 * progress(pc, key) // w.cost}% funded).")
    return (not was_done and complete(pc, key)), lines


# --- what finished works actually change -----------------------------------
def bleed_factor(pc) -> float:
    """Drainage keeps the damp out of a cash hoard."""
    return 0.45 if complete(pc, "drainage") else 1.0


def claim_factor(pc) -> float:
    """People you got papers for do not send anyone round to shake you down."""
    return 0.5 if complete(pc, "papers") else 1.0


def price_factor(pc) -> float:
    """The families you housed stop charging you the outsider price."""
    return 0.85 if complete(pc, "market_hall") else 1.0


def monk_bonus(pc) -> int:
    """The sangha knows who paid for the hall."""
    return 2 if complete(pc, "wat_hall") else 0


def summary(pc) -> list[str]:
    lines = []
    for key, w in WORKS.items():
        p = progress(pc, key)
        if complete(pc, key):
            lines.append(f"  ✔ {w.name} — finished")
        elif p:
            lines.append(f"    {w.name} — {100 * p // w.cost}% "
                         f"({remaining(pc, key):,}฿ to go)")
    return lines or ["  Nothing under way. The pile is just sitting there."]
