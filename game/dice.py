"""Tabletop resolution engine.

Core roll is 2d6 + modifier, read in the Powered-by-the-Apocalypse / Blades
tradition:

    10+   full success            (STRONG)
    7-9   success at a cost       (WEAK)
    6-    failure with a hard move (MISS)

A single natural 12 is a CRIT; a natural 2 is a FUMBLE. These do not change the
tier but let scenes react to a memorable roll.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class Outcome(str, Enum):
    MISS = "miss"        # 6-
    WEAK = "weak"        # 7-9
    STRONG = "strong"    # 10+

    @property
    def label(self) -> str:
        return {
            Outcome.MISS: "trouble",
            Outcome.WEAK: "a mixed result",
            Outcome.STRONG: "clean success",
        }[self]


@dataclass
class Roll:
    dice: tuple[int, int]
    modifier: int
    total: int
    outcome: Outcome
    crit: bool
    fumble: bool

    @property
    def natural(self) -> int:
        return self.dice[0] + self.dice[1]

    def describe(self) -> str:
        d1, d2 = self.dice
        sign = f"+{self.modifier}" if self.modifier >= 0 else str(self.modifier)
        tag = " CRIT!" if self.crit else " FUMBLE!" if self.fumble else ""
        return f"[{d1}][{d2}] {sign} = {self.total} -> {self.outcome.label}{tag}"


def roll(modifier: int = 0, rng: random.Random | None = None) -> Roll:
    r = rng or random
    d1, d2 = r.randint(1, 6), r.randint(1, 6)
    natural = d1 + d2
    total = natural + modifier
    if total >= 10:
        outcome = Outcome.STRONG
    elif total >= 7:
        outcome = Outcome.WEAK
    else:
        outcome = Outcome.MISS
    return Roll(
        dice=(d1, d2),
        modifier=modifier,
        total=total,
        outcome=outcome,
        crit=(natural == 12),
        fumble=(natural == 2),
    )
