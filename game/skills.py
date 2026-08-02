"""Skills, literacy, and grinding.

Attributes (Nerve/Guile/Lore/Hands) are who you are; skills are what you've
learned. Skills are D&D-style ranks 0..5 and improve by *practice* (grind) —
but past rank 2 you need a teacher present, so grinding alone can't carry you.

Literacy is the skill `aksorn`: reading the old Lanna and khom scripts, yantra
inscriptions, and — bluntly — contracts, so a fence can't swindle you. Many of
the deeper crafts are gated behind being able to read at all.
"""

from __future__ import annotations

# key -> (display, blurb, governing attribute for its checks)
SKILLS: dict[str, tuple[str, str, str]] = {
    "aksorn": ("Aksorn — Reading",
               "Lanna & khom script, yantra, and contracts you won't be cheated by.",
               "lore"),
    "charcha": ("Charcha — Negotiation",
                "Haggling and the long deal. The evergreen Thai art.",
                "guile"),
    "mahaniyom": ("Mahaniyom — Glamour",
                  "Charm and being unseen: the glow-up that slips a checkpoint.",
                  "guile"),
    "phasa_phii": ("Phasa Phii — Spirit-speech",
                   "The words that reach ghosts, ancestors, and devas.",
                   "nerve"),
    "saiyasat": ("Saiyasat — Occult craft",
                 "Hun payont, takrut, and the consecration that wakes them.",
                 "lore"),
    "khrua": ("Khrua — Cookery",
              "Pad krapow and the food that opens every door in Thailand.",
              "hands"),
    "mudra": ("Mudra — Nonverbal",
              "Hands and posture when words won't serve — or aren't allowed.",
              "nerve"),
}

# Cumulative practice-xp needed to REACH each rank. Kept gentle: grinding is
# required, but not a slog.
_RANK_XP = [0, 2, 5, 9, 14, 20]

# Past this rank, self-practice stalls without a teacher on site.
SELF_TAUGHT_CAP = 2


def rank_for_xp(xp: int) -> int:
    r = 0
    for rank, need in enumerate(_RANK_XP):
        if xp >= need:
            r = rank
    return r


def xp_to_next(xp: int) -> int | None:
    r = rank_for_xp(xp)
    if r >= len(_RANK_XP) - 1:
        return None
    return _RANK_XP[r + 1] - xp


def teacher_here(features: tuple[str, ...], skill: str) -> bool:
    return f"teacher:{skill}" in features


def can_practice(pc, skill: str, features: tuple[str, ...]) -> tuple[bool, str]:
    rank = pc.skill(skill)
    if rank >= len(_RANK_XP) - 1:
        return False, "You've mastered this; there's nothing left to grind."
    if rank >= SELF_TAUGHT_CAP and not teacher_here(features, skill):
        return False, ("You've gone as far as practice alone can take you. "
                       "Find a teacher of this craft.")
    return True, ""


def gain_xp(pc, skill: str, amount: int) -> int | None:
    """Add xp; return the new rank if it went up, else None."""
    before = pc.skill(skill)
    from . import opening
    amount += opening.practice_bonus(pc)
    pc.xp[skill] = pc.xp.get(skill, 0) + amount
    after = rank_for_xp(pc.xp[skill])
    if after > before:
        pc.skills[skill] = after
        return after
    return None


def literate(pc) -> bool:
    return pc.skill("aksorn") >= 1
