"""The pile and the rails — where a billion baht actually sits.

You do not start poor. You start sitting on a pile bigger than one person can
police: **one billion baht** in 20-baht notes and coins, damp at the bottom,
and every week somebody new remembers they have a claim on it. That is the
opening problem, and the difficulty setting is nothing but how hard the pile is
to keep.

Money here is not one number. There is what's **in your pocket** (`pc.baht` —
what every shop, bribe and bowl of khao soi actually spends) and what's **on
your rail** (`pc.reserve` — the pile, wherever you've put it). Moving between
them is the whole game of logistics: cash has weight, crypto has keys, banks
have opinions.

The rail is a class choice disguised as a wallet choice. Four exist:

  cash        no gate. Weight, volume, damp, rats, and claimants. Strongest
              inside the informal economy, weakest at any distance.
  crypto      no gate. Keys, power and network become survival dependencies;
              the exchange knows exactly what you're holding.
  foreign     a foreign bank. KYC and status gates, correspondent chokepoints,
              and someone else's jurisdiction holding the off switch.
  thai_bank   not offered at the start. You open one the way anybody opens one
              here: with a deposit large enough to make you interesting, or by
              being so charming across the desk that the papers follow you.

**Busting out is not the end.** If the pile and your pocket both reach zero you
may bind yourself to a different rail — but the new one opens cold, and you
have to carry it up from nothing by hand before it works. That is the grind,
and it is deliberately unpleasant.

Pure functions where possible; the engine narrates.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .dice import Outcome
from .persuasion import persuade

# --- the pile ---------------------------------------------------------------
# One billion baht, made of the smallest paper the country still prints and the
# coins under it. A 20-baht note weighs about 0.8 g; assume a third of the pile
# by value is coin, which is vastly heavier per baht. The number that matters is
# that it does not fit in a room and it does not move quietly.
PILE_BAHT = 1_000_000_000
NOTE_VALUE = 20
NOTE_GRAMS = 0.8
COIN_SHARE = 0.33          # share of value held as coin
COIN_GRAMS_PER_BAHT = 0.55  # mixed 1/2/5/10฿ coin, averaged

# What you can keep on your person without it being an event.
POCKET_SOFT_CAP = 60_000


def weight_kg(baht: int) -> float:
    """Physical mass of a cash sum in 20-baht notes and mixed coin."""
    if baht <= 0:
        return 0.0
    coin_value = baht * COIN_SHARE
    note_value = baht - coin_value
    grams = (note_value / NOTE_VALUE) * NOTE_GRAMS + coin_value * COIN_GRAMS_PER_BAHT
    return grams / 1000.0


def weight_note(baht: int) -> str:
    kg = weight_kg(baht)
    if kg < 1:
        return f"{kg * 1000:,.0f} g"
    if kg < 1000:
        return f"{kg:,.1f} kg"
    return f"{kg / 1000:,.1f} tonnes"


# --- difficulty = the defence burden on wealth ------------------------------
# Difficulty never touches enemy dice. It scales only how hard the pile is to
# keep: how often claimants come, how much walks off, how fast damp and rats
# take the bottom layers.
@dataclass(frozen=True)
class Difficulty:
    key: str
    name: str
    blurb: str
    bleed: float        # share of the reserve lost per day to theft & spoilage
    claim_chance: float  # chance per day someone arrives with a claim
    claim_bite: float   # share of reserve a successful claim takes


DIFFICULTIES: dict[str, Difficulty] = {
    "easy": Difficulty(
        "easy", "Easy — the pile mostly stays put",
        "Word hasn't really got out. Losses are a rounding error and the "
        "claimants are polite.",
        bleed=0.0006, claim_chance=0.10, claim_bite=0.01),
    "medium": Difficulty(
        "medium", "Medium — the pile is known",
        "Enough people know to make it a standing job of work. Something walks "
        "off most weeks; someone knocks most weeks.",
        bleed=0.0022, claim_chance=0.22, claim_bite=0.03),
    "hard": Difficulty(
        "hard", "Hard — the pile is a public fact",
        "Everyone knows, and the queue starts at the gate. You will spend your "
        "life defending it, and it will still shrink.",
        bleed=0.0055, claim_chance=0.38, claim_bite=0.06),
}


# --- the rails --------------------------------------------------------------
@dataclass(frozen=True)
class Rail:
    key: str
    name: str
    blurb: str
    strength: str
    weakness: str
    openable: bool = True     # offered in the opening choice
    withdraw_minutes: int = 30
    # How much of a day's bleed the rail actually absorbs (1.0 = full physical
    # exposure, 0.0 = untouchable by damp and hands).
    bleed_factor: float = 1.0
    # Its own hazard, rolled per day.
    hazard_chance: float = 0.0
    hazard: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


RAILS: dict[str, Rail] = {
    "cash": Rail(
        "cash", "Cash — the pile stays a pile",
        "It sits where you put it, in sacks and biscuit tins and under the "
        "floor of somewhere you hope nobody thinks about.",
        strength="Nothing to freeze, nothing to trace, and every door in the "
                 "informal economy opens to it.",
        weakness="It weighs what it weighs. Damp, rats, fire, hands, and a "
                 "line of people who feel owed.",
        withdraw_minutes=45, bleed_factor=1.0,
        hazard_chance=0.0,
        tags=("informal", "heavy", "local"),
    ),
    "crypto": Rail(
        "crypto", "Crypto — the pile becomes a key",
        "A seed phrase, and whatever power and signal Chiang Mai can give you "
        "on the day you need it.",
        strength="Weightless, and it crosses any distance you like.",
        weakness="Keys, power and network are now survival. The chain "
                 "remembers, and the exchange knows precisely what you hold.",
        withdraw_minutes=25, bleed_factor=0.05,
        hazard_chance=0.06,
        hazard="The mesh drops out, or the ramp does. Nothing moves off-chain "
               "today.",
        tags=("distant", "traceable", "fragile"),
    ),
    "foreign": Rail(
        "foreign", "A foreign bank — the pile becomes respectable",
        "Someone else's jurisdiction, someone else's compliance desk, and a "
        "monthly statement in a language you may not read.",
        strength="Respectable, insurable, and it survives fire and flood.",
        weakness="It assumes papers you may not have. Limits, correspondent "
                 "chokepoints, and a stranger holding the off switch.",
        withdraw_minutes=90, bleed_factor=0.0,
        hazard_chance=0.09,
        hazard="Compliance has a question about a transfer. The account is "
               "read-only until someone in another timezone is satisfied.",
        tags=("formal", "revocable", "papers"),
    ),
    "thai_bank": Rail(
        "thai_bank", "A Thai bank account — the pile becomes ordinary",
        "A passbook, a branch that knows your face, and a manager who "
        "remembers what you did to get the account.",
        strength="Local, fast, unremarkable, and it spends everywhere the cash "
                 "does without the weight.",
        weakness="You are inside the system now, and the system files reports.",
        openable=False,                      # earned, never offered at the start
        withdraw_minutes=40, bleed_factor=0.0,
        hazard_chance=0.04,
        hazard="A large movement trips a reporting threshold. The branch wants "
               "a word before anything else clears.",
        tags=("formal", "local", "earned"),
    ),
}

OPENING_RAILS = tuple(k for k, r in RAILS.items() if r.openable)

# --- opening a Thai account -------------------------------------------------
# Two doors, and both are real doors here: put in enough money that the branch
# wants your business, or be so persuasive across the desk that the paperwork
# arrives afterwards.
THAI_BANK_DEPOSIT = 25_000_000       # "a large cash investment"
THAI_BANK_TALK_FLOOR = 7             # charcha + mahaniyom ranks, out of 10
THAI_BANK_DIFFICULTY = 4             # a stiff roll even for the very charming


def thai_bank_talk_ready(pc) -> bool:
    """Is the smuggler charming enough to be allowed to even try talking?"""
    return (pc.skill("charcha") + pc.skill("mahaniyom")) >= THAI_BANK_TALK_FLOOR


def thai_bank_state(pc) -> str:
    """'have' | 'deposit' | 'talk' | 'both' | 'no' — what door is open today."""
    if pc.rail == "thai_bank" or "thai_bank" in pc.rails_open:
        return "have"
    can_deposit = (pc.baht + pc.reserve) >= THAI_BANK_DEPOSIT
    can_talk = thai_bank_talk_ready(pc)
    if can_deposit and can_talk:
        return "both"
    if can_deposit:
        return "deposit"
    if can_talk:
        return "talk"
    return "no"


def open_thai_bank_by_talk(pc, rng: random.Random | None = None):
    """Charm the desk into an account. Returns the persuasion Attempt."""
    return persuade(pc, "human", difficulty=THAI_BANK_DIFFICULTY, rng=rng)


# --- the grind --------------------------------------------------------------
# Bust out and you may bind to another rail, but it opens cold: it holds nothing
# and protects nothing until you have carried this much into it by hand.
GRIND_BAHT = 120_000


def is_busted(pc) -> bool:
    return (pc.baht + pc.reserve) <= 0


def start_grind(pc, rail_key: str) -> None:
    """Bind to a new rail from zero. The rail is inert until the grind clears."""
    pc.rails_burned = [*pc.rails_burned, pc.rail] if pc.rail not in pc.rails_burned \
        else pc.rails_burned
    pc.rail = rail_key
    pc.reserve = 0
    pc.rail_grind = GRIND_BAHT
    if rail_key not in pc.rails_open:
        pc.rails_open = [*pc.rails_open, rail_key]


def grind_progress(pc, amount: int) -> int:
    """Feed baht into a cold rail. Returns how much of it counted."""
    if pc.rail_grind <= 0:
        return 0
    counted = min(amount, pc.rail_grind)
    pc.rail_grind -= counted
    return counted


def rail_live(pc) -> bool:
    return pc.rail_grind <= 0


# --- moving money -----------------------------------------------------------
def deposit(pc, amount: int) -> tuple[bool, str]:
    """Pocket -> rail. Clears the grind first if one is running."""
    amount = int(amount)
    if amount <= 0:
        return False, "Nothing to move."
    if amount > pc.baht:
        return False, f"You don't have {amount:,}฿ on you."
    pc.baht -= amount
    rail = RAILS[pc.rail]
    if pc.rail_grind > 0:
        counted = grind_progress(pc, amount)
        pc.reserve += amount
        if pc.rail_grind <= 0:
            return True, (f"{amount:,}฿ in. That clears it — {rail.name.split(' —')[0]} "
                          f"is live, and it holds what you put in it.")
        return True, (f"{amount:,}฿ in. Still {pc.rail_grind:,}฿ of cold grind "
                      f"before the rail is worth anything.")
    pc.reserve += amount
    extra = ""
    if pc.rail == "cash":
        extra = f" The stack you added weighs {weight_note(amount)}."
    return True, f"{amount:,}฿ moved onto the rail.{extra}"


def withdraw(pc, amount: int) -> tuple[bool, str]:
    """Rail -> pocket."""
    amount = int(amount)
    if amount <= 0:
        return False, "Nothing to move."
    if not rail_live(pc):
        return False, ("The rail is still cold — it holds nothing you can draw "
                       f"on. {pc.rail_grind:,}฿ of grind left.")
    if amount > pc.reserve:
        return False, f"The rail doesn't hold {amount:,}฿."
    if pc.rail_frozen:
        return False, f"Nothing moves today. {RAILS[pc.rail].hazard}"
    pc.reserve -= amount
    pc.baht += amount
    extra = ""
    if pc.rail == "cash" and weight_kg(amount) > 8:
        extra = (f" You are now carrying {weight_note(amount)} of money, and it "
                 f"shows.")
    return True, f"{amount:,}฿ drawn.{extra}"


# --- the daily burden -------------------------------------------------------
@dataclass
class DayReport:
    lost: int = 0
    claim: int = 0
    lines: list[str] = field(default_factory=list)


CLAIMANTS = (
    "A cousin you have never met arrives with a photograph of your father and "
    "a number in mind.",
    "Two men from the market association explain, warmly, about contributions.",
    "A monk's nephew asks for a donation to a roof, and names the roof, and "
    "names the sum.",
    "The woman who owns the room below yours has worked out what is above her "
    "ceiling.",
    "A traffic officer you have never met asks after your mother by name.",
)


def daily(pc, rng: random.Random | None = None) -> DayReport:
    """One dawn's worth of pressure on the pile. Called by the engine."""
    r = rng or random
    rep = DayReport()
    diff = DIFFICULTIES.get(pc.difficulty, DIFFICULTIES["medium"])
    rail = RAILS[pc.rail]

    pc.rail_frozen = False
    if rail.hazard and r.random() < rail.hazard_chance:
        pc.rail_frozen = True
        rep.lines.append(rail.hazard)

    if pc.reserve > 0 and rail.bleed_factor > 0:
        from . import works
        lost = int(pc.reserve * diff.bleed * rail.bleed_factor
                   * works.bleed_factor(pc))
        if lost > 0:
            pc.reserve -= lost
            rep.lost = lost
            rep.lines.append(
                f"Damp, rats, and quiet hands: {lost:,}฿ gone off the bottom of "
                f"the pile overnight.")

    from . import wealth, works
    claim_chance = (diff.claim_chance * wealth.claim_multiplier(pc)
                    * works.claim_factor(pc))
    if pc.reserve > 0 and r.random() < claim_chance:
        bite = int(pc.reserve * diff.claim_bite)
        if bite > 0:
            pc.reserve -= bite
            rep.claim = bite
            rep.lines.append(f"{r.choice(CLAIMANTS)} It costs you {bite:,}฿.")

    return rep


def summary(pc) -> list[str]:
    """The passbook, such as it is."""
    rail = RAILS[pc.rail]
    lines = [f"Rail: {rail.name}"]
    if pc.rail_grind > 0:
        lines.append(f"  COLD — {pc.rail_grind:,}฿ of grind before it works.")
    lines.append(f"  On the rail: {pc.reserve:,}฿"
                 + (f"   ({weight_note(pc.reserve)})" if pc.rail == "cash" else ""))
    lines.append(f"  In pocket:   {pc.baht:,}฿"
                 + (f"   ({weight_note(pc.baht)})" if pc.baht > POCKET_SOFT_CAP else ""))
    if pc.rail_frozen:
        lines.append(f"  FROZEN today — {rail.hazard}")
    lines.append(f"  Strength: {rail.strength}")
    lines.append(f"  Weakness: {rail.weakness}")
    if pc.rails_burned:
        burned = ", ".join(RAILS[k].name.split(" —")[0] for k in pc.rails_burned)
        lines.append(f"  Burned behind you: {burned}")
    return lines
