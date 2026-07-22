"""Entry point: `python3 -m game` from the moat/ folder."""

from __future__ import annotations

import random

from . import save
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
    return Character.create(name, bg_key)


def main() -> None:
    print(TITLE)
    if save.has_save():
        if input("Continue saved game? (y/n)> ").strip().lower().startswith("y"):
            pc = save.load()
            Game(pc, rng=random.Random()).run()
            return
    pc = new_character()
    _p("")
    _p(f"Welcome, {pc.name}. You start in the old city with "
       f"{pc.baht:,}฿ and a bag of goods. Type 'help' anytime.")
    _p("")
    Game(pc, rng=random.Random()).run()


if __name__ == "__main__":
    main()
