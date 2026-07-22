"""The moat gate scan — the game's signature risk.

When the smuggler crosses a gate carrying anything hot, customs runs a scan.
The player picks an approach; each leans on a different attribute and fails in a
different way. Resolution uses the 2d6 tabletop engine, penalised by how much
heat is on your person and how suspicious the city already is.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .character import Character
from .dice import Outcome, Roll, roll
from .items import get

APPROACHES = {
    "bluff": ("nerve", "Walk through calm and talk your way past."),
    "conceal": ("hands", "Trust your hidden pockets and false linings."),
    "bribe": ("guile", "Slip the officer a fold of baht (costs money)."),
}


@dataclass(frozen=True)
class GateCarry:
    """How a carried thing reads at the moat gate — and whether its wicha works
    SHOWN or HIDDEN. A negative delta eases the scan; positive worsens it. The
    smuggler's whole craft is knowing which things to display and which to hide.
    """
    shown: int = 0
    hidden: int = 0
    shown_note: str = ""
    hidden_note: str = ""
    bluff_only: bool = False   # a shown charm that only helps the 'bluff' talk-past


# The wicha and cover goods whose effect at the gate turns on show-vs-hide.
# Grounded in the item lore in items.py: the takrut's yant reads as foil, Luang
# Phu Thuat's shield turns the scanner's eye, cover goods look like nothing.
GATE_CARRY: dict[str, GateCarry] = {
    "luang_phu_thuat": GateCarry(
        hidden=-1,
        hidden_note="Luang Phu Thuat rides hidden against your skin; the shield "
                    "against an untimely death turns the scanner's eye — it reads "
                    "only the metal. (-1)"),
    "takrut": GateCarry(
        hidden=-1,
        hidden_note="Your takrut is rolled into a hem. The scanner reads the foil, "
                    "never the wicha inked inside. (-1)"),
    "ya_hom": GateCarry(
        hidden=-1,
        hidden_note="A twist of Ya Hom sits among your things — dull, fragrant, "
                    "ordinary cover for what travels beside it. (-1)"),
    "miang": GateCarry(
        hidden=-1,
        hidden_note="Pickled miang packs your bag like any trader's; there is "
                    "nothing here worth reading. (-1)"),
    "khruba_srivichai": GateCarry(
        shown=-1,
        shown_note="You wear the Khruba Srivichai medallion openly. To the officer "
                   "you read as a pilgrim of the north's own saint, not a runner. (-1)"),
    "salika": GateCarry(
        shown=-1, bluff_only=True,
        shown_note="The Salika Lin Thong shows at your throat; its golden-tongue "
                   "metta gentles the officer's questions. (-1 to your bluff)"),
}

EASE_CAP = 3   # concealment and charm can only carry you so far


@dataclass
class ScanResult:
    approach: str
    roll: Roll | None
    outcome: str          # "clean" | "cost" | "seized" | "waved"
    lines: list[str]
    baht_spent: int = 0
    heat_delta: int = 0
    stress_delta: int = 0
    seized_key: str | None = None


def _city_penalty(heat: int) -> int:
    return heat // 3


def _loadout(pc: Character, approach: str) -> tuple[int, list[str]]:
    """Read what the smuggler shows and what they hide. Returns a signed penalty
    delta and legible gate lines. Easing (concealment, pilgrim's poise) is capped;
    flaunting a hot antiquity is not — show the wrong thing and it costs you."""
    ease, lines = 0, []
    for k, n in pc.inventory.items():
        if n <= 0:
            continue
        eff = GATE_CARRY.get(k)
        worn = pc.is_worn(k)
        if worn and eff and eff.shown:
            if eff.bluff_only and approach != "bluff":
                continue
            ease += eff.shown
            lines.append(eff.shown_note)
        elif worn and get(k).heat >= 2:
            ease += 2
            lines.append(f"You wear the {get(k).name} in the open — the very sort "
                         f"of thing they hunt for. (+2)")
        elif not worn and eff and eff.hidden:
            ease += eff.hidden
            lines.append(eff.hidden_note)
    if ease < -EASE_CAP:
        ease = -EASE_CAP
        lines.append(f"(Concealment carries you only so far — eased by {EASE_CAP} at most.)")
    return ease, lines


def scan(pc: Character, approach: str, rng: random.Random | None = None,
         boon_ease: int = 0, boon_note: str = "") -> ScanResult:
    r = rng or random
    carried = pc.carried_heat()

    if carried == 0:
        # Nothing hot. Still a slim chance a jumpy officer waves you aside —
        # unless a friend on the booth is smoothing your way.
        if _city_penalty(pc.heat) >= 2 and r.random() < 0.25 and not boon_ease:
            return ScanResult(
                approach, None, "waved",
                ["The aura-scanner chirps a false positive at nothing behind you. "
                 "A pat-down, a scowl, and you are through. (+1 stress)"],
                stress_delta=1,
            )
        return ScanResult(
            approach, None, "clean",
            ["Nothing to declare — and today that is even true. \u201cSawatdee,\u201d "
             "you say, and mean it; \u201cGo, go, no problem,\u201d the officer says "
             "back, waving you on. The arch stays green, the spirit-heat needle "
             "flat, and you pass with a bow."],
        )

    attr, _ = APPROACHES[approach]
    penalty = carried + _city_penalty(pc.heat)
    glow = 0
    if pc.glamour > 0:
        glow = 2                 # the glow-up: scanners' eyes slide off you
        pc.glamour -= 1
        penalty = max(0, penalty - glow)

    # What you chose to show, and what you chose to hide.
    ease, load_lines = _loadout(pc, approach)
    penalty = max(0, penalty + ease)

    # A sick smuggler reads wrong at the arch — pale, sweating, twitchy.
    if pc.health <= 3:
        penalty += 1
        load_lines.append(f"You're unwell (health {pc.health}/10) — pale and "
                          f"clammy, you draw a longer look than you'd like. (+1)")

    # A trusted officer on this gate eases you through.
    if boon_ease:
        penalty = max(0, penalty - boon_ease)
        load_lines.append(boon_note or f"A friend on this booth smooths your "
                          f"way. (-{boon_ease})")

    modifier = pc.mod(attr) - penalty

    # The day's hidden tilt rides with you to the arch — the omen was never
    # only talk. A lucky day steadies your hand; an unlucky one shows.
    if pc.luck:
        modifier += pc.luck
        if pc.luck > 0:
            load_lines.append("The day runs with you \u2014 the arch seems to "
                              "want to let you pass.")
        else:
            load_lines.append("The day runs against you \u2014 everything at the "
                              "arch takes a beat too long.")

    # Bribe costs money up front regardless of the roll.
    baht_spent = 0
    if approach == "bribe":
        baht_spent = min(pc.baht, 300 + 150 * carried)

    rl = roll(modifier, rng=r)
    lines = [f"Approach: {approach} ({attr} {pc.mod(attr):+d}, "
             f"scan penalty -{penalty}).", *load_lines, rl.describe()]
    if glow:
        lines.insert(1, "Your glow-up holds — eyes slide right past you.")

    if rl.outcome is Outcome.STRONG:
        return ScanResult(approach, rl, "clean",
                          lines + ["You cross clean. \u201cReep roy,\u201d you say "
                                   "— all in order — and the officer smiles you "
                                   "through: \u201cOkay okay, go.\u201d A small, "
                                   "courteous transaction, settled to the "
                                   "satisfaction of you both."],
                          baht_spent=baht_spent)

    if rl.outcome is Outcome.WEAK:
        # Through, but it cost you.
        if approach == "bribe":
            lines.append("The officer's hand closes on the baht and the barrier "
                         "lifts. Expensive, but done.")
            return ScanResult(approach, rl, "cost", lines,
                              baht_spent=baht_spent, heat_delta=1, stress_delta=1)
        lines.append("You make it through, but a lingering stare follows you. "
                     "(+1 heat, +1 stress)")
        return ScanResult(approach, rl, "cost", lines,
                          baht_spent=baht_spent, heat_delta=1, stress_delta=1)

    # MISS — but a woken hun payont will throw itself between you and the law.
    if "hun_payont" in pc.charms:
        pc.charms.remove("hun_payont")
        return ScanResult(
            approach, rl, "cost",
            lines + ["The arch shrieks and the spirit-heat needle pins red — then "
                     "your hun payont stirs. A wooden guardian's dread floods the "
                     "booth, every screen whites out to static, the officer waves "
                     "you on, and the effigy goes still, spent. (+1 heat)"],
            baht_spent=baht_spent, heat_delta=1, stress_delta=0)

    # They find something. Lose your hottest item.
    hottest = max(pc.inventory, key=lambda k: get(k).heat)
    lines.append(f"The arch shrieks and the readout floods red. They pull your "
                 f"{get(hottest).name} into the light. Confiscated. "
                 f"(+2 heat, +2 stress)")
    return ScanResult(approach, rl, "seized", lines,
                      baht_spent=baht_spent, heat_delta=2, stress_delta=2,
                      seized_key=hottest)


def apply(pc: Character, res: ScanResult) -> None:
    if res.baht_spent:
        pc.baht -= res.baht_spent
    if res.heat_delta:
        pc.add_heat(res.heat_delta)
    if res.stress_delta:
        pc.add_stress(res.stress_delta)
    if res.seized_key:
        pc.add_item(res.seized_key, -1)
