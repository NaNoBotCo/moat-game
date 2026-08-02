"""Entry point: `python3 -m game` from the moat/ folder."""

from __future__ import annotations

import random

from . import rails, save
from .character import BACKGROUNDS, Character
from .engine import Game, _p


TITLE = r"""
   __  __  ___    _   _____
  |  \/  |/ _ \  / \ |_   _|
  | |\/| | | | |/ _ \  | |
  | |  | | |_| / ___ \ | |
  |_|  |_|\___/_/   \_\|_|
  Chiang Mai, 2076 — amulets, potions, and the old city's ring of water.
"""


def new_character() -> Character:
    _p("Choose your past. It sets your dice and your starting kit.")
    _p("")
    keys = list(BACKGROUNDS)
    for i, k in enumerate(keys, 1):
        bg = BACKGROUNDS[k]
        attrs = " ".join(f"{a[:2].title()}{v:+d}" for a, v in bg["attrs"].items())
        print(f"  {i}. {bg['name']} — {bg['desc']}")
        print(f"     {attrs}   {bg['baht']}฿")
    choice = ""
    while choice not in [str(i) for i in range(1, len(keys) + 1)]:
        choice = input("background (1-3)> ").strip()
    bg_key = keys[int(choice) - 1]
    name = input("your name> ").strip() or "Nok"
    pc = Character.create(name, bg_key)
    _the_pile(pc)
    return pc


def _pick(prompt: str, n: int) -> int:
    """Numbered choice, 1..n. Returns the index."""
    choice = ""
    while choice not in [str(i) for i in range(1, n + 1)]:
        choice = input(f"{prompt} (1-{n})> ").strip()
    return int(choice) - 1


def _the_pile(pc: Character) -> None:
    """The opening problem: a pile too big to police, and one choice about it."""
    _p("")
    _p(f"You are also sitting on {rails.PILE_BAHT:,}฿.")
    _p("")
    _p("Not in an account. In a room. Twenty-baht notes in rice sacks and "
       "biscuit tins, coins in the buckets beneath them, the bottom layer "
       f"already going soft with damp. It weighs "
       f"{rails.weight_note(rails.PILE_BAHT)}. You cannot lift it, you cannot "
       "count it, and you certainly cannot watch all of it at once.")
    _p("")
    _p("How hard is it going to be to keep?")
    _p("")
    dkeys = list(rails.DIFFICULTIES)
    for i, k in enumerate(dkeys, 1):
        d = rails.DIFFICULTIES[k]
        print(f"  {i}. {d.name}")
        print(f"     {d.blurb}")
    pc.difficulty = dkeys[_pick("how hard", len(dkeys))]

    _p("")
    _p("And where are you going to put it?")
    _p("")
    rkeys = list(rails.OPENING_RAILS)
    for i, k in enumerate(rkeys, 1):
        rail = rails.RAILS[k]
        print(f"  {i}. {rail.name}")
        print(f"     {rail.blurb}")
        print(f"     + {rail.strength}")
        print(f"     - {rail.weakness}")
    _p("")
    _p("Choose wisely.")
    _p("")
    pc.rail = rkeys[_pick("rail", len(rkeys))]
    pc.rails_open = [pc.rail]
    # The pile goes onto the rail; your pocket keeps what the background gave you.
    pc.reserve = rails.PILE_BAHT


def _orientation(pc: Character) -> None:
    """Thirty seconds on how the screen works. Not what to do — how to act.

    Deliberately says nothing about what is worth doing, because the opening
    is meant to be found rather than issued. It explains the controls and the
    two things that confuse everybody (money in two places, time as the real
    budget), and then gets out of the way.
    """
    _p("")
    _p("=" * 72)
    _p("BEFORE YOU START \u2014 how the screen works")
    _p("")
    _p("  NUMBERS change. They are what this place, at this hour, is offering.")
    _p("  LETTERS never change. [M] is money on every screen, forever.")
    _p("")
    _p("  Two things trip everyone up:")
    _p("")
    _p("  1. Your money is in two places. Your POCKET is what shops and bribes "
       "take. Your RAIL is the pile. Move between them with [M].")
    _p("")
    _p("  2. Time is the budget, not baht. Everything you do spends hours, and "
       "people and doors keep their own hours. A shut door is information.")
    _p("")
    _p("  Press [?] at any point for this again.")
    _p("=" * 72)


def main() -> None:
    print(TITLE)
    if save.has_save():
        if input("Continue saved game? (y/n)> ").strip().lower().startswith("y"):
            pc = save.load()
            Game(pc, rng=random.Random()).run()
            return
    pc = new_character()
    _orientation(pc)
    _p("")
    _p(f"Welcome, {pc.name}. You start in the old city with {pc.baht:,}฿ in "
       f"your pocket, {pc.reserve:,}฿ on the "
       f"{rails.RAILS[pc.rail].name.split(' —')[0].lower()} rail, and a bag of "
       f"goods. Type 'help' anytime.")
    _p("")
    Game(pc, rng=random.Random()).run()


if __name__ == "__main__":
    main()
