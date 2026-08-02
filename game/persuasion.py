"""Persuasion: the slick negotiation game, one resolver for every audience.

You must move humans, devas, phii, ancestors, police, customs, and monks — and
each yields to different arts. A trader bends to Charcha; a monk to merit and
letters; a ghost only to one who can actually speak to it. The resolver picks
your best applicable lever (skill rank + its governing attribute), rolls 2d6,
and reads the tabletop tiers. Offerings and standing tilt the odds.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .dice import Outcome, Roll, roll
from .skills import SKILLS

# audience -> (levers, note). A lever is a skill key; if the smuggler lacks it
# entirely, that lever contributes only its governing attribute.
AUDIENCES: dict[str, tuple[tuple[str, ...], str]] = {
    "human":   (("charcha", "mahaniyom"), "traders, touts, and marks"),
    "police":  (("mahaniyom", "charcha"), "the beat cop with a quota"),
    "customs": (("mahaniyom", "charcha"), "the officer at the gate"),
    "monk":    (("aksorn", "khrua"), "the abbot who weighs your merit"),
    "phii":    (("phasa_phii", "mudra"), "the restless dead of a place"),
    "ancestor":(("phasa_phii", "khrua"), "your line, watching and judging"),
    "deva":    (("mudra", "aksorn"), "a shining one, above mere words"),
}


@dataclass
class Attempt:
    audience: str
    lever: str
    roll: Roll
    outcome: Outcome
    modifier: int
    notes: list[str] = field(default_factory=list)


def best_lever(pc, audience: str) -> tuple[str, int]:
    """Return (lever_key, modifier) for the smuggler's strongest angle."""
    levers, _ = AUDIENCES[audience]
    best_key, best_mod = levers[0], -99
    for key in levers:
        attr = SKILLS[key][2]
        mod = pc.skill(key) + pc.mod(attr)
        if mod > best_mod:
            best_key, best_mod = key, mod
    return best_key, best_mod


def persuade(pc, audience: str, difficulty: int = 0,
             bonus: int = 0, rng: random.Random | None = None) -> Attempt:
    r = rng or random
    lever, base = best_lever(pc, audience)
    attr = SKILLS[lever][2]
    luck = getattr(pc, "luck", 0)
    # People treat you by what they think you're worth. Greed opens a trader and
    # a bored officer; it closes an abbot, who has met rich penitents before.
    from . import roads, wealth, works
    money, money_note = wealth.persuasion_bonus(pc, audience)
    if audience == "monk":
        money += works.monk_bonus(pc)
    dry = roads.persuasion_penalty(pc)
    if dry:
        money += dry
        money_note = ("Everyone who meets you now knows what you did to the "
                      "water.")
    modifier = base + bonus - difficulty + luck + money
    rl = roll(modifier, rng=r)
    notes = [f"Best angle: {SKILLS[lever][0]} "
             f"(rank {pc.skill(lever)} + {attr} {pc.mod(attr):+d}"
             + (f", offering {bonus:+d}" if bonus else "")
             + (f", the day {luck:+d}" if luck else "")
             + (f", how you're read {money:+d}" if money else "")
             + (f", difficulty -{difficulty}" if difficulty else "") + ")."]
    if money_note:
        notes.append(money_note)
    # A ghost or deva simply will not hear someone with no way to speak to it.
    if audience in ("phii", "ancestor") and pc.skill("phasa_phii") == 0:
        notes.append("Without any Spirit-speech, your words scatter unheard.")
        rl = roll(modifier - 3, rng=r)
    return Attempt(audience, lever, rl, rl.outcome, modifier, notes)
