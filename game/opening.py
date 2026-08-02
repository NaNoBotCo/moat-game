"""The first few days: things that go right.

The opening of this game is a refusal. Doors are shut, nobody explains why, and
the one thing you are supposed to work out is deliberately unmarked. That is the
design and it stays — but a player who is *only* refused for three days puts the
game down before the good part, and a refusal only reads as intriguing when
something else is going well.

So the first days carry a short chain of small, guaranteed, unmissable wins.
Each one pays a little, teaches exactly one verb, and cannot fail. None of them
is a quest and none has a marker: they are just things a person in your position
would obviously do on their first morning, offered on the front screen.

They are also, quietly, the seed of the real opening. The woman who rents you
your room tells you Kad Luang is open *now* — and it is, and you go, and it
works. Nobody says the word "hours". Days later, when four doors in a row have
been shut in your face, that morning is the thing you remember.

Every beat fires once, inside the first `FIRST_DAYS` days, and then the scaffold
is gone for good.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

FIRST_DAYS = 6
ERRAND_PAY = 350
NEW_HAND_BONUS = 2       # extra practice xp while you're finding your feet


@dataclass(frozen=True)
class Beat:
    key: str
    label: str
    when: Callable          # (pc) -> bool
    run: Callable           # (game) -> list[str]


def _kad_luang_open(pc) -> bool:
    from . import market
    return market.market_open("warorot", pc.minutes)


def done(pc, key: str) -> bool:
    return key in pc.opening.get("done", [])


def _finish(pc, key: str) -> None:
    pc.opening = {**pc.opening, "done": [*pc.opening.get("done", []), key]}


def early(pc) -> bool:
    return pc.day <= FIRST_DAYS


# --- the beats --------------------------------------------------------------
def _breakfast(g) -> list[str]:
    pc = g.pc
    from . import market, coucal
    pc.add_health(2)
    pc.add_stress(-1)
    _finish(pc, "breakfast")
    g.advance(30)
    # Point at a floor that is genuinely open right now. It will be — this is
    # only offered in the morning, and Kad Luang keeps the morning watches.
    o, _c = market.market_window("warorot")
    return [
        "The woman you rent the room from is already up, and there is rice "
        "soup, and she will not hear of you leaving without eating it.",
        "",
        "She asks after nobody in particular in a way that means she has "
        "noticed you have money and is being polite about it. Then, on your "
        "way out, without looking up: “Kad Luang now, na. Go now.”",
        "",
        "(+2 health, -1 stress. She is right: the guild floor at Warorot is "
        "open at this hour.)",
    ]


def _errand(g) -> list[str]:
    pc = g.pc
    from . import skills
    pc.baht += ERRAND_PAY
    _finish(pc, "errand")
    g.advance(45)
    skills.gain_xp(pc, "charcha", 2)
    return [
        "It is a flat parcel wrapped in newspaper and string, it weighs "
        "nothing, and it is going four streets. Nobody searches anybody inside "
        "the wall.",
        "",
        "The man who takes it does not open it in front of you, counts out the "
        "money slowly enough that you know it is all there, and says you can "
        "come back.",
        "",
        f"(+{ERRAND_PAY}฿, and a little practice at talking money.)",
    ]


def _word(g) -> list[str]:
    pc = g.pc
    from . import dictionary
    _finish(pc, "word")
    g.advance(20)
    pool = [w for w in dictionary.all_words()
            if w["rarity"] == "common" and w["term"] not in pc.words]
    if not pool:
        return ["Nothing left for him to teach you."]
    w = max(pool, key=lambda x: x["listings"])
    dictionary.learn(pc, w["term"])
    return [
        "He asks what you call the thing you are carrying, and you tell him, "
        "and he laughs — not unkindly — and tells you what people who do this "
        "for a living call it.",
        "",
        f"✦ {w['term']} ({w['roman']}) — {w['en']}",
        "",
        "(One word. Say it at a stall and you will be quoted a different price "
        "than you were this morning.)",
    ]


def _first_sale(g) -> list[str]:
    pc = g.pc
    from .items import get
    _finish(pc, "first_sale")
    held = [k for k in pc.inventory if get(k).kind == "amulet"]
    name = get(held[0]).name if held else "what you're carrying"
    return [
        "You do the arithmetic properly for the first time since you inherited "
        "the problem in the corner of your room.",
        "",
        f"{name} is worth real money to the right buyer, and you know roughly "
        f"who that is. The pile is not the business. The pile is the thing that "
        f"makes the business dangerous.",
        "",
        "(Sell at a floor that wants your sort of goods — the guild at Warorot "
        "pays fairly; the Night Bazaar pays more, later, for a story.)",
    ]


BEATS: tuple[Beat, ...] = (
    # Only offered while Kad Luang is genuinely open, because she says it is
    # and the entire point of this beat is that she turns out to be right.
    Beat("breakfast", "Eat what you're given (the woman downstairs insists)",
         lambda pc: (pc.location == "old_city" and not done(pc, "breakfast")
                     and pc.minutes < 11 * 60 and _kad_luang_open(pc)),
         _breakfast),
    Beat("errand", "Run a parcel four streets for a neighbour (easy money)",
         lambda pc: (pc.location == "old_city" and done(pc, "breakfast")
                     and not done(pc, "errand")),
         _errand),
    Beat("word", "Ask him what the trade calls it",
         lambda pc: (pc.location == "old_city" and done(pc, "errand")
                     and not done(pc, "word")),
         _word),
    Beat("first_sale", "Work out what your own bag is actually worth",
         lambda pc: done(pc, "errand") and not done(pc, "first_sale"),
         _first_sale),
)


def available(pc) -> list[Beat]:
    if not early(pc):
        return []
    return [b for b in BEATS if not done(pc, b.key) and b.when(pc)]


def practice_bonus(pc) -> int:
    """Skills move faster while you're new, so the first practice shows."""
    return NEW_HAND_BONUS if early(pc) else 0
