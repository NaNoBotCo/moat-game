"""The arc over the web: *The Silence of the Pillar*.

The relationship graph in `relationships.py` is the *stage*; this module is the
**play**. It reads nothing but the smuggler's own state — the secrets you've been
trusted with, the bonds you keep, the wants you've met — and from that alone it
tells a four-act Lanna mystery, one beat at a time.

The city rests on a promise. Legend holds that when King Mangrai's people raised
Chiang Mai in 1296, the guardian spirits (the kumphan) were given the **Sao
Inthakhin**, the city pillar, to keep — and each year, when the Inthakhin flowers
are laid at Wat Chedi Luang, the city renews the vow and keeps its protection. Kawila
revived the pillar and set it where it stands in 1800.

Since the rains, the guardian has fallen silent. And the Ping's old drowned
capital, **Wiang Kum Kam** — Mangrai's first city, silted under a century of
floods — has begun to give up pieces of itself, each marked with the same
half-finished yantra. Someone broke the promise on purpose, and the festival is
coming. The living know half the tale; only the dead saw the rest.

The arc is **data**: acts, and beats that fire when combinations of confided
secrets line up into a deduction. Grow it by adding beats, not machinery.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import festivals
from . import persuasion
from . import relationships as rel
from .dice import Outcome

# The Inthakhin flowers are laid on this day — the clock the whole arc runs on.
# Owned by the festival calendar, so the arc and the calendar never drift apart.
FESTIVAL_DAY = festivals.INTHAKHIN_DAY
RELIC = "phra_rod"   # the broken piece, to be returned to the pillar


def _relic_name() -> str:
    """The broken piece's display name — never leak the raw item key to players."""
    from .items import get
    return get(RELIC).name


# --- reading the smuggler's state (no story is stored on the contacts) ------
def _heard(pc, key: str) -> bool:
    return key in pc.secrets_heard


def _heard_any(pc, keys, n: int = 1) -> bool:
    return sum(1 for k in keys if _heard(pc, k)) >= n


def _bond(pc, key: str) -> int:
    return pc.bonds.get(key, 0)


def _met(pc, key: str) -> bool:
    return key in pc.wants_met


# --- the shape of the play --------------------------------------------------
@dataclass(frozen=True)
class Act:
    n: int
    name: str
    question: str


ACTS = {
    1: Act(1, "The Silence", "Why has the pillar's guardian gone quiet?"),
    2: Act(2, "The Surfacing",
           "What is rising from drowned Wiang Kum Kam — and who is buying it?"),
    3: Act(3, "The Dead's Road",
           "How does the broken piece leave the city, and on whose order?"),
    4: Act(4, "Return or Ruin",
           "Can you carry the piece back to the pillar before the flowers are laid?"),
}


@dataclass(frozen=True)
class Beat:
    key: str
    act: int
    title: str
    text: str
    when: object          # callable pc -> bool
    advances: bool = False  # firing this closes its act and opens the next


# The connective tissue: each beat is a deduction you reach by holding the right
# confidences at once. `advances` beats are the spine; the rest are illumination.
BEATS: list[Beat] = [
    Beat("opening", 1, "The job in front of you",
         "You smuggle amulets through Chiang Mai's moat-gate checkpoints for a "
         "living. You are unfailingly kind about it — a warm word for every "
         "officer, a fair price for every favour, a bow for everyone you cross. "
         "It is only that the warmth and the prices are how the work gets done. "
         "Here is what you've walked into. The city is protected by a "
         "guardian spirit that lives in the Sao Inthakhin — the city pillar at Wat "
         "Chedi Luang. Every year at the Inthakhin festival the city renews a "
         "promise to it and keeps that protection. This year the guardian has gone "
         "silent and the protection is failing. Your first job is simple: find out "
         "why. Ask the people who'd notice first — a gate officer, a lantern-maker, "
         "the grandmother at your family shrine.",
         when=lambda pc: True),
    Beat("the_silence", 1, "Confirmed: the guardian has gone silent",
         "Two people tell you the same thing. Since the floods, the guardian in "
         "the city pillar has stopped answering — no blessings, no warnings, "
         "nothing. That guardian is what keeps Chiang Mai safe, and its protection "
         "is fading fast. Something made it go quiet on purpose. Next question: "
         "what changed after the floods? Look to what the water dug up.",
         when=lambda pc: _heard_any(pc, ("prasit", "seng", "mae_kaew"), 2),
         advances=True),

    Beat("the_broken_piece", 2, "What the floods dug up",
         "Marisa, a scholar at the university, dates the artifacts surfacing from "
         "the river to Wiang Kum Kam — Mangrai's original capital, drowned and "
         "buried centuries ago. Every piece carries the same half-finished "
         "carving, as if one hand was stopped mid-stroke. Someone is quietly "
         "buying up all of them: paying triple, asking nothing, destroying none. "
         "They aren't collecting trophies — they're assembling something. Find out "
         "what these pieces are and why they matter.",
         when=lambda pc: _heard(pc, "marisa") and _heard_any(pc, ("naruemon", "lawan")),
         advances=True),
    Beat("promise_and_piece", 2, "The promise was carved in stone",
         "Now it fits. The promise that binds the guardian to the city was never "
         "just words — it was carved into a sacred stone. That stone has been "
         "broken and a piece of it carried off. No stone, no promise; no promise, "
         "no protection. That missing piece is what you need to recover.",
         when=lambda pc: _heard(pc, "mae_kaew") and _heard(pc, "marisa")),
    Beat("name_the_hand", 2, "Someone powerful is behind it",
         "The trail points upward. Pa Lawan's hush-money and Sgt. Anong's "
         "rewritten orders lead to the same place: someone powerful — above the "
         "traders' guild, able to change a customs post's orders — wants that "
         "stone out of Chiang Mai before the festival. You don't have a name yet, "
         "but the buyer is no small player.",
         when=lambda pc: _heard(pc, "lawan") and _heard(pc, "anong")),

    Beat("the_witness", 3, "A witness who saw it leave",
         "Noi died at the Suan Prung gate the night the guardian went silent, and "
         "no one performed her rites, so her ghost lingers there. She watched the "
         "thieves carry the broken stone out through that gate — the one kept for "
         "the dead, where officers don't look closely — certain no living eye could "
         "see them. They didn't count on her.",
         when=lambda pc: _heard(pc, "noi")),
    Beat("the_route", 3, "The full smuggling route",
         "Now you can trace the whole route. The stone leaves through the Suan "
         "Prung death-gate, then goes north on Haji Karim's old smuggling tracks — "
         "goat paths no border post watches — toward the Golden Triangle, to be "
         "sold across the border. If it crosses, it's gone for good. Intercept it "
         "first. The festival is close.",
         when=lambda pc: _heard(pc, "noi") and _heard(pc, "karim"),
         advances=True),

    Beat("the_reliquary", 4, "The abbot spells out the stakes",
         "Phra Ajahn Ket shows you a relic the official histories deny exists. The "
         "broken stone belongs to the city pillar, he says — not a collector, not "
         "a buyer in the Triangle. Get it back and set it in the pillar before the "
         "Inthakhin flowers are laid, or Chiang Mai loses its protection for a "
         "generation.",
         when=lambda pc: rel.is_known(pc, "ajahn_ket") and _heard(pc, "ajahn_ket")),
    Beat("the_pillar_speaks", 4, "The Guardian tells you its terms",
         "At the foot of the pillar, the Guardian speaks to you directly — the "
         "first time since the floods. Its terms are simple: bring the broken "
         "stone home before the festival flowers are laid, and the city's "
         "protection returns. Miss the day, and Chiang Mai goes unguarded for a "
         "generation. You know what to do — now do it in time.",
         when=lambda pc: rel.is_known(pc, "inthakhin")),
]

BEAT_BY_KEY = {b.key: b for b in BEATS}


# --- talent gates: the trials of charm and bargain --------------------------
# The deductions above tell you *what* is happening — but knowing is not enough.
# At the pivots you must actually *move* people who don't want to be moved: an
# honest sergeant you cannot bribe, a fence who already has the relic half-sold.
# These resolve through the same 2d6 persuasion the whole game runs on, and you
# can lose them. Build Charcha and Mahaniyom, keep a Salika at your throat,
# compose a glow-up, carry a fine plate — or the hardest turns stay shut. The
# good ending is gated on *winning* the bargain, not merely holding secrets.

_ROLE_FACTION = {
    "police": "law", "customs": "law", "human": "guild",
    "monk": "monkhood", "phii": "unseen", "ancestor": "unseen", "deva": "unseen",
}


def _worldly(role: str) -> bool:
    return role in ("human", "police", "customs")


@dataclass(frozen=True)
class Trial:
    key: str
    act: int
    title: str
    role: str          # the persuasion audience the trial is fought on
    difficulty: int
    lever: str         # the talent it leans on, named for the prompt
    intro: str
    available: object  # pc -> bool: when you may attempt it
    leverage: object   # pc -> (difficulty_reduction, notes): your standing edges
    on_strong: object  # pc -> list[str]
    on_weak: object    # pc -> list[str]
    on_miss: object    # pc -> list[str]


# --- trial 1: turn the one honest scanner (Act III) -------------------------
def _anong_available(pc) -> bool:
    return rel.is_known(pc, "anong") and _heard(pc, "anong")


def _anong_leverage(pc):
    dred, notes = 0, []
    b = _bond(pc, "anong")
    if b >= 3:
        dred += 2
        notes.append("She trusts you; that is worth more than any bribe. (-2)")
    elif b >= 1:
        dred += 1
        notes.append("She knows your face, at least. (-1)")
    # holding her secret means you can appeal to the conscience it wounds
    dred += 1
    notes.append("You know her orders were changed against her will — appeal to "
                 "the honest woman, not the officer. (-1)")
    return dred, notes


def _anong_strong(pc):
    _st(pc)["anong_turned"] = True
    return ["Sgt. Anong holds your eye a long moment, then nods once. She gives you "
            "the exact window the piece will move — and swears she'll be looking the "
            "other way when you carry it home. Turned by conscience, not coin.",
            "(When you make the bargain, you'll know precisely when to strike.)"]


def _anong_weak(pc):
    pc.add_heat(1)
    return ["She won't dirty her hands — but quietly, not meeting your eyes, she "
            "tells you the window and asks you never to speak her name. You have "
            "the timing, not her cover. (+1 heat)"]


def _anong_miss(pc):
    pc.add_heat(2)
    rel.adjust_bond(pc, "anong", -1, pc.day)
    return ["You misjudge her badly — you reach for a lever that feels like a bribe. "
            "She doesn't bristle; she goes gentle and very formal, thanks you warmly "
            "for coming, and says she's certain a person like you meant nothing by "
            "it. The warmth has quietly gone out of her. \u201cI'll be seeing you at "
            "the gate,\u201d she says, kindly. (+2 heat, and she cools toward you.)"]


# --- trial 2: the climax bargain for the relic (Act IV) ---------------------
def _bargain_available(pc) -> bool:
    return "the_route" in _st(pc)["beats"]


def _bargain_leverage(pc):
    dred, notes = 0, []
    if _st(pc).get("anong_turned"):
        dred += 2
        notes.append("Anong's window puts you on the fence mid-handoff, off-balance. (-2)")
    if _heard(pc, "lawan") and _heard(pc, "anong"):
        dred += 1
        notes.append("You can name the hand above the guild; saying it aloud rattles him. (-1)")
    if _bond(pc, "karim") >= 2:
        dred += 1
        notes.append("Haji Karim's word on the caravan road opens the fence's door. (-1)")
    return dred, notes


def _bargain_strong(pc):
    pc.add_item(RELIC, 1)
    return ["You out-talk the fence on his own ground — leverage, flattery, and a "
            "price he cannot refuse that costs you nothing but nerve. The broken "
            "piece is in your hands, and not one baht left your purse.",
            f"(You carry the {_relic_name()} — the piece the pillar is "
            "missing. Bring it home before the flowers.)"]


def _bargain_weak(pc):
    paid = min(pc.baht, 4000)
    pc.baht -= paid
    pc.add_heat(2)
    pc.add_item(RELIC, 1)
    return [f"He drives a hard bargain and you blink first — {paid:,}\u0e3f gone and "
            "heat on your trail, but the piece is yours. (+2 heat)",
            "(You have the broken piece, at a price. Now carry it back to the pillar.)"]


def _bargain_miss(pc):
    pc.add_stress(2)
    pc.add_heat(1)
    return ["The fence hears you out to the last word, nodding warmly, and thanks "
            "you sincerely for the pleasure of your company — such a promising young "
            "trader. \u201cMai pen rai, mai pen rai,\u201d he says, patting your "
            "hand. \u201cToday, not yet. You come back another day, na.\u201d Then, "
            "with every courtesy, he keeps the piece — and the refusal is so "
            "gracious you are halfway to the door before you feel it. It edges "
            "toward the border, and the festival closer still. (+2 stress, +1 heat)",
            "(Build your leverage — charm, a turned sergeant, a named patron — and "
            "try the bargain again before the flowers are laid.)"]


TRIALS: list[Trial] = [
    Trial("turn_anong", 3, "The Sergeant's Conscience", "police", 3,
          "charm and honest appeal (Mahaniyom / Charcha)",
          "Sgt. Anong is the one honest scanner at Tha Phae, and her orders were "
          "changed against her will. Move her — not with coin, which insults her, "
          "but with charm and the truth of her own conscience — and the gate opens.",
          _anong_available, _anong_leverage,
          _anong_strong, _anong_weak, _anong_miss),
    Trial("the_bargain", 4, "The Bargain at Sop Ruak", "human", 5,
          "hard negotiation (Charcha)",
          "At the edge of the Triangle you face the fence who holds the broken "
          "piece, half-sold already. There is no taking it by force. You must "
          "out-bargain a professional on his own ground — the steepest negotiation "
          "in the game, and the most important.",
          _bargain_available, _bargain_leverage,
          _bargain_strong, _bargain_weak, _bargain_miss),
]
TRIAL_BY_KEY = {t.key: t for t in TRIALS}


def _trial_edges(pc, t: Trial) -> tuple[int, int, list[str]]:
    """Fold your standing into a trial: return (difficulty, bonus, notes).

    Spends a glamour charge if you have one — presence buys you the room."""
    notes: list[str] = []
    dred, lnotes = t.leverage(pc)
    diff = t.difficulty - dred
    notes.extend(lnotes)
    bonus = 0
    if _worldly(t.role) and pc.has("salika"):
        bonus += 1
        notes.append("The Salika Lin Thong lends your words a honeyed pull. (+1)")
    if pc.glamour > 0:
        pc.glamour -= 1
        bonus += 1
        notes.append("You spend a glow-up; the room's eyes soften. (+1)")
    fac = _ROLE_FACTION.get(t.role)
    if fac and rel.standing(pc).get(fac, 0) >= 6:
        bonus += 1
        notes.append(f"Your standing among {rel.FACTIONS[fac]} precedes you. (+1)")
    return max(0, diff), bonus, notes


def available_trial(pc) -> Trial | None:
    """The pivotal test you may attempt right now, if any (earliest first)."""
    s = _st(pc)
    for t in TRIALS:
        if s["trials"].get(t.key) in ("strong", "weak"):
            continue  # already carried
        if t.act <= s["act"] and t.available(pc):
            return t
    return None


def attempt_trial(pc, key: str, food_bonus: int = 0, rng=None) -> list[str]:
    """Fight a pivotal negotiation through the 2d6 resolver. Returns prose."""
    s = _st(pc)
    t = TRIAL_BY_KEY.get(key)
    out: list[str] = []
    if t is None:
        return out
    if s["trials"].get(t.key) in ("strong", "weak"):
        out.append(f"You have already carried the day at {t.title}.")
        return out
    diff, bonus, notes = _trial_edges(pc, t)
    bonus += food_bonus
    out.append(f"\u2726 {t.title}")
    out.append(t.intro)
    out.extend(notes)
    att = persuasion.persuade(pc, t.role, difficulty=diff, bonus=bonus, rng=rng)
    out.extend(att.notes)
    out.append(att.roll.describe())
    if att.outcome is Outcome.STRONG:
        s["trials"][t.key] = "strong"
        out.extend(t.on_strong(pc))
    elif att.outcome is Outcome.WEAK:
        s["trials"][t.key] = "weak"
        out.extend(t.on_weak(pc))
    else:
        s["trials"][t.key] = "miss"
        out.extend(t.on_miss(pc))
    return out


# --- state on the smuggler --------------------------------------------------
def begin(pc) -> list[str]:
    """Open the pillar arc. It is a side story now, not the opening.

    The player earns their way in by learning to read the city's time — until
    then the silence of the Sao Inthakhin is somebody else's problem, and the
    banner says nothing about it."""
    if pc.story.get("started"):
        return []
    pc.story.update({"started": True, "act": 1, "beats": [], "ending": "",
                     "epilogue": "", "trials": {}, "anong_turned": False,
                     "unread": True})
    return ["",
            "\u2726 The Silence of the Pillar",
            "Now that you can hear the watches, you notice what is missing from "
            "them. The Sao Inthakhin keeps no hour at all. Since the rains the "
            "city pillar's guardian has said nothing, and the drowned lanes of "
            "Wiang Kum Kam keep surfacing where the river runs low.",
            "(Type 'journal' for the tale so far.)"]


def started(pc) -> bool:
    return bool(pc.story.get("started"))


def _st(pc) -> dict:
    s = pc.story
    if not s:
        s.update({"act": 1, "beats": [], "ending": "", "epilogue": "",
                  "trials": {}, "anong_turned": False, "unread": False,
                  "started": False})
    s.setdefault("trials", {})       # forward-compat for older saves
    s.setdefault("anong_turned", False)
    s.setdefault("unread", False)
    return s


def has_unread(pc) -> bool:
    """True if a beat fired that the player hasn't opened the journal on since."""
    return bool(pc.story.get("started")) and _st(pc).get("unread", False)


def act(pc) -> Act:
    return ACTS[_st(pc)["act"]]


def days_left(pc) -> int:
    return FESTIVAL_DAY - pc.day


# --- endings ----------------------------------------------------------------
def _bargain_won(pc) -> bool:
    # The relic returns only to one who out-bargained the fence for it.
    return _st(pc)["trials"].get("the_bargain") in ("strong", "weak")


def _restored(pc) -> bool:
    # You won the piece back, reached the Guardian, and gave it home in time.
    return (_bargain_won(pc) and rel.is_known(pc, "inthakhin")
            and _met(pc, "inthakhin"))


def _check_ending(pc, s: dict) -> str | None:
    if s["ending"]:
        return None
    if _restored(pc):
        s["ending"] = "restored"
        named = "name_the_hand" in s["beats"]
        s["epilogue"] = (
            "You set the broken piece back into the socket at the pillar's foot. "
            "The yantra closes, and the guardian answers: the scanners at the moat "
            "gates read true again, the mesh signal holds after dark, and the city's "
            "protection is restored in time for the Inthakhin flowers. You did it. "
            + ("Because you named the buyer above the guild, the police have someone "
               "real to arrest this year. " if named else "")
            + "Chiang Mai is safe again."
        )
        return s["ending"]
    if pc.day > FESTIVAL_DAY:
        s["ending"] = "ruin"
        s["epilogue"] = (
            "The Inthakhin flowers are laid without you. The broken piece crosses "
            "north out of Lanna for good, and the socket at the pillar's foot stays "
            "empty. Without it the guardian can't be restored: the gate scanners "
            "will keep failing after dark, and the city's protection is gone. No one "
            "will say it out loud — they'll call the bad year a bad year. You were "
            "too late."
        )
        return s["ending"]
    return None


# --- the one call the engine makes ------------------------------------------
def advance(pc) -> list[str]:
    """Fire any beats now earned, move the act, and resolve an ending if due.

    Returns prose lines for anything that fired this tick (empty if nothing)."""
    if not pc.story.get("started"):
        return []                    # the side arc has not been opened yet
    s = _st(pc)
    out: list[str] = []
    if s["ending"]:
        return out
    # Fire beats in order, but only up to the current act (no spoiling ahead).
    moved = True
    while moved:
        moved = False
        for b in BEATS:
            if b.key in s["beats"] or b.act > s["act"]:
                continue
            if b.when(pc):
                s["beats"].append(b.key)
                s["unread"] = True
                out.append(f"\u2726 {b.title}")
                out.append(b.text)
                if b.advances and s["act"] < 4:
                    s["act"] += 1
                    nxt = ACTS[s["act"]]
                    out.append(f"— {nxt.name}: {nxt.question} —")
                    moved = True  # a new act may make earlier-gated beats fire
    end = _check_ending(pc, s)
    if end == "restored":
        out.append("\u2726 The city is saved")
        out.append(s["epilogue"])
    elif end == "ruin":
        out.append("\u2726 The city loses its guardian")
        out.append(s["epilogue"])
    return out


def street_lead(pc) -> str | None:
    """A rumor tied to the mystery, pointing at the person who moves it forward.

    Returns None when the story has nothing live to whisper, so the caller can
    fall back to an ordinary market tip."""
    s = _st(pc)
    if s["ending"]:
        return None
    a = s["act"]
    if a == 1:
        if not rel.is_known(pc, "seng"):
            return ("They say the Yi Peng lanterns won't rise in Wualai this year — "
                    "the Shan maker, Sai Seng, has stopped smiling. He'd know what "
                    "changed.")
        return ("Officer Prasit at the south gate lights extra incense on his shift "
                "now. Ask him what his scanners keep flaring at.")
    if a == 2:
        if not _heard(pc, "marisa"):
            return ("A scholar at the university is quietly logging every relic "
                    "pulled from the low river. Her name's Marisa.")
        return ("Word on the silver row: someone's paying triple for anything with "
                "the old guardian's mark, and melting none of it. Naruemon's seen "
                "the buyer's men.")
    if a == 3:
        if not rel.is_known(pc, "noi"):
            return ("The Suan Prung officers swear a dead runner still waits at the "
                    "gate. Whatever left the city that night, she watched it go.")
        return ("Haji Karim's people still walk the old mule tracks north. Nothing "
                "reaches the Triangle that he can't trace.")
    if a == 4:
        if not _bargain_won(pc):
            return ("The broken stone is already moving north toward Sop Ruak. Once "
                    "it crosses the border it's gone — you'll have to bargain it "
                    "back first.")
        return ("You hold the stone. The pillar's own guardian is the last door — "
                "it opens only to one the ghost, the grandmother, and the abbot all "
                "trust.")
    return None


def deadline_note(pc) -> str | None:
    """A quiet nudge as the festival nears — for the day-rollover to surface."""
    s = _st(pc)
    if s["ending"]:
        return None
    d = days_left(pc)
    if d == 3:
        return "Three days until the Inthakhin flowers. The city is stringing lights."
    if d == 1:
        return "Tomorrow the flowers are laid at the pillar. Whatever you mean to do, do it."
    if d == 0:
        return ("Today the Inthakhin flowers are laid. This is your last chance to "
                "set the stone in the pillar — do it before you sleep.")
    return None


# --- the journal (a read-only view of where the story stands) ---------------
def objective(pc) -> str:
    """One concrete line for the turn banner: what to do next, and by when."""
    s = _st(pc)
    if s["ending"] == "restored":
        return "You brought the stone home. The city is safe. (Play on, or begin anew.)"
    if s["ending"] == "ruin":
        return "The festival passed and the stone is gone. The city is unguarded now."
    a = ACTS[s["act"]]
    d = days_left(pc)
    when = (f"{d} day{'s' if d != 1 else ''} to the flowers" if d > 0
            else "the flowers are laid TODAY")
    tag = f"[Act {a.n}/4] "
    t = available_trial(pc)
    if t:
        return f"{tag}NOW: {t.title} — attempt the negotiation ('bargain').  ({when})"
    hint = _next_hint(pc, s) or a.question
    return f"{tag}{hint}  ({when})"


def journal(pc) -> list[str]:
    s = _st(pc)
    s["unread"] = False
    a = ACTS[s["act"]]
    lines = ["== The Silence of the Pillar =="]
    if s["ending"] == "restored":
        lines.append("  RESOLVED — the guardian was restored.")
        lines.append("  " + s["epilogue"])
        return lines
    if s["ending"] == "ruin":
        lines.append("  ENDED — the city lost its guardian.")
        lines.append("  " + s["epilogue"])
        return lines
    d = days_left(pc)
    clock = (f"{d} day{'s' if d != 1 else ''} until the flowers" if d > 0
             else "the flowers are due")
    lines.append(f"  Act {a.n}: {a.name}   ({clock})")
    lines.append(f"  {a.question}")
    known = [BEAT_BY_KEY[k] for k in s["beats"] if k in BEAT_BY_KEY]
    revealed = [b for b in known if b.key != "opening"]
    if revealed:
        lines.append("")
        lines.append("  What you've pieced together:")
        for b in revealed:
            lines.append(f"    \u2022 {b.title}")
    # a gentle pointer at what would move things
    nudge = _next_hint(pc, s)
    if nudge:
        lines.append("")
        lines.append(f"  {nudge}")
    # a pivotal test of talent standing open right now
    t = available_trial(pc)
    if t:
        lines.append("")
        lines.append(f"  A test of talent awaits — {t.title}:")
        lines.append(f"    {t.lever}.  Attempt it with 'bargain'.")
    return lines


def _next_hint(pc, s: dict) -> str | None:
    act_n = s["act"]
    if act_n == 1:
        return ("Ask who'd notice the silence first — talk to Sai Seng the "
                "lantern-maker in Wualai, Officer Prasit at the south gate, or "
                "your grandmother at the old-city shrine.")
    if act_n == 2:
        if not _heard(pc, "marisa"):
            return ("Reach Marisa, the scholar at CMU (Nimman) — she can date the "
                    "pieces surfacing from the river. Pa Lawan can introduce you.")
        return ("Find out who's buying: Naruemon on the Wualai silver row and Pa "
                "Lawan at the Warorot gold shop both know.")
    if act_n == 3:
        if not rel.is_known(pc, "noi"):
            return ("Only the dead saw it leave. Reach Noi, the ghost at Suan Prung "
                    "gate (evenings) — Officer Prasit can open that door.")
        return ("Get Haji Karim (Warorot) to show you the caravan tracks the piece "
                "will travel north.")
    if act_n == 4:
        if not _bargain_won(pc):
            return ("The broken piece is being smuggled north. Only a hard bargain "
                    "wins it back — build your Charcha and 'bargain' for it.")
        if not rel.is_known(pc, "inthakhin"):
            return ("You hold the piece. Now reach the Guardian of the Pillar — it "
                    "opens only to one trusted by the ghost, the ancestor, and the "
                    "abbot alike.")
        if not _met(pc, "inthakhin"):
            return (f"Bring the broken piece — the {_relic_name()} — and give it "
                    "back to the Guardian before the flowers are laid.")
    return None
