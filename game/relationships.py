"""The spine of the game: a living web of contacts, bonds, and introductions.

People, police, monks, ghosts, ancestors and devas are persistent **contacts**,
each a node with a **bond** you cultivate. Persuasion is the verb that moves a
bond; **introductions** grow the graph (you reach new contacts by being vouched
for, not by wandering there); faction **standing** emerges from the bonds you
keep; and neglect quietly cools them.

The seed cast is deliberately diverse — khon mueang, Chinese-Thai and Yunnanese
Muslim (Chin Haw) traders, Shan and Hmong hill folk, a mixed-heritage scholar,
women on both sides of the law, monks, and the unseen — and it carries one slow
mystery: since the rains, the guardian of the **Sao Inthakhin** (Chiang Mai's
city pillar) has fallen silent, and pieces of the flood-drowned city of **Wiang
Kum Kam** are surfacing, each marked with the same unfinished yantra. The living
know half; only the dead know the rest.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import clock, persuasion
from .dice import Outcome
from .world import DISTRICTS

# --- bond scale -------------------------------------------------------------
BOND_MIN, BOND_MAX = -3, 5
TIERS = [
    (-3, "hostile"), (-2, "hostile"), (-1, "wary"), (0, "a stranger"),
    (1, "an acquaintance"), (2, "friendly"), (3, "trusted"),
    (4, "close"), (5, "sworn to you"),
]
FACTIONS = {
    "guild": "the Kad Luang guild & traders",
    "law": "police & customs",
    "monkhood": "the sangha",
    "street": "the night roads",
    "unseen": "the dead, the line, and the shining ones",
}


def tier(bond: int) -> str:
    b = max(BOND_MIN, min(BOND_MAX, bond))
    return dict(TIERS)[b]


# --- data model -------------------------------------------------------------
@dataclass(frozen=True)
class Want:
    kind: str          # 'food' | 'amulet' | 'word'
    ref: str = ""      # item key, or contact key (for 'word')
    note: str = ""


@dataclass(frozen=True)
class Intro:
    to: str            # contact key this unlocks
    at: int            # bond needed with the introducer
    line: str = ""     # how they make the introduction


@dataclass(frozen=True)
class Heart:
    at: int            # bond threshold at which this scene unlocks
    title: str         # a short name for the moment
    text: str          # the scene — a layer of who they are


@dataclass(frozen=True)
class Contact:
    key: str
    name: str
    role: str          # a persuasion audience key
    faction: str
    where: str         # district key; "" == reached only through the graph
    heritage: str      # who they are, in a phrase
    bio: str
    greet: str = ""    # their voice — a Thaiglish line on a warm hello (optional)
    want: Want | None = None
    secret: str = ""
    secret_at: int = 3
    intros: tuple[Intro, ...] = ()
    boon: str = ""              # the human description of what their trust buys
    boon_kind: str = ""        # mechanized effect: "fence"|"gate"|"courier"|
    #                            "appraise" — "" means the boon is narrative only
    boon_at: int = 3           # bond needed before the mechanized boon activates
    start_hidden: bool = True   # if False, you meet them by being where they are
    # --- depth: when they're out, what they love, when they were born, who ---
    #     they become as you know them better ---------------------------------
    hours: tuple[str, ...] = ()        # day-parts they're reachable ('' = always)
    schedule: tuple[tuple[str, str], ...] = ()  # (day-part, district) — overrides where
    loves: tuple[str, ...] = ()        # item keys that land as a real gift
    likes: tuple[str, ...] = ()        # item keys they appreciate
    dislikes: tuple[str, ...] = ()     # item keys that sour the mood
    birthday: int = 0                  # game day; 0 == unknown/none
    hearts: tuple[Heart, ...] = ()     # scenes that reveal them, by bond threshold


# Apex nodes that open only when several bonds are all deep enough.
APEX: dict[str, list[tuple[str, int]]] = {
    "inthakhin": [("noi", 3), ("mae_kaew", 3), ("ajahn_ket", 3)],
}


CONTACTS: dict[str, Contact] = {
    # --- the living, met by being where they are ---------------------------
    "lawan": Contact(
        "lawan", "Pa Lawan", "human", "guild", "warorot",
        "Teochew Chinese-Thai gold-shop matriarch",
        "She runs the quiet side of a Kad Luang gold shop, where amulets change "
        "hands and money learns to forget where it came from. Nothing crosses "
        "the river trade without her knowing.",
        greet="Aiyah, you come again. Sit, sit. Tea first, business after — but "
              "business, we do, na.",
        want=Want("food", "khao_soi", "A proper khao soi, and she'll talk."),
        secret="The Jatukham money doesn't end in gold — it buys silence at the "
               "gates. Someone above the guild wants the old Lamphun clay out of "
               "the city before the Inthakhin festival. I don't ask whose orders.",
        secret_at=3,
        intros=(Intro("marisa", 2, "There's a half-farang girl at the university "
                      "who reads old clay better than the monks. Tell her I sent you."),
                Intro("anong", 3, "A sergeant at Tha Phae owes my family a debt of "
                      "years. Be gentle; she's honest, which makes her useful and sad.")),
        boon="fence: better prices on the Warorot floor",
        boon_kind="fence", boon_at=1,
        start_hidden=False,
    ),
    "karim": Contact(
        "karim", "Haji Karim", "human", "street", "warorot",
        "Yunnanese Chin Haw Muslim caravan trader",
        "Third-generation of the muleteers who brought tea and jade down from "
        "Yunnan. He keeps a tea stall by the Ban Haw mosque and a map of the old "
        "smuggling tracks in his head.",
        greet="Come, drink tea. Good one, from up the mountain. We talk slow slow, "
              "talk true.",
        want=Want("food", "miang", "Share miang the old caravan way."),
        secret="The caravan roads remember. What leaves by Suan Prung goes north "
               "to the Triangle on the mule tracks, not the highway — no scanner "
               "watches a goat path. I can show a friend the way.",
        secret_at=2,
        intros=(Intro("seng", 2, "The Shan lantern-maker in Wualai sees the night "
                      "roads clearer than I do. Go to him."),),
        boon="route: the old northern mule track",
        start_hidden=False,
    ),
    "seng": Contact(
        "seng", "Sai Seng", "human", "street", "wualai",
        "Shan (Tai Yai) lantern-maker",
        "He folds khom loi lanterns by the hundred for Yi Peng, and his are the "
        "ones that fly highest. He watches the night sky like other men watch "
        "the road.",
        greet="You. Long time. Everything okay okay lah.",
        want=Want("food", "sai_ua", "Northern sausage, shared at his workbench."),
        secret="I float a lantern each Yi Peng for a boy who never came home "
               "through the dead-gate. This year not one of my lanterns will rise "
               "— they haven't since the night the pillar went quiet. The guardian "
               "that used to carry them up has gone silent. That's your answer: "
               "start there.",
        secret_at=2,
        boon="rumor: what the night saw",
        start_hidden=False,
        # He keeps a maker's day: the workbench by light, the street at dusk, and
        # the riverbank after dark, where he still sends a lantern up alone.
        schedule=(("morning", "wualai"), ("afternoon", "wualai"),
                  ("evening", "wualai"), ("night", "ping_river")),
        loves=("sai_ua", "khao_soi"),
        likes=("miang", "pad_krapow"),
        dislikes=("ya_dong",),   # he doesn't drink; grief keeps him clear
        birthday=9,
        hearts=(
            Heart(2, "The workbench",
                  "He clears a stool for you among the bamboo ribs and rice-paper. "
                  "\u201cShan hands, khon-mueang sky,\u201d he says of himself. He "
                  "learned the fold from his grandmother in Kengtung, before the "
                  "family came down. Each lantern is sixteen ribs and one prayer; "
                  "he ties the prayer in last, where the flame will read it."),
            Heart(3, "The boy called Ta",
                  "You ask, finally, whose lantern flies highest. His hands go "
                  "still. \u201cMy brother's son. Ta. He ran the night roads too, "
                  "and one Yi Peng he went out the Suan Prung side and the dark "
                  "kept him.\u201d No lamp was lit for the boy at the gate of the "
                  "dead. \u201cSo I light the sky instead. Every year. It is the "
                  "only road left to send anything up.\u201d"),
            Heart(4, "The name inside the paper",
                  "He shows you the newest lantern, unlit. Inside, in Shan script "
                  "along a rib where only the flame will ever see it, is written a "
                  "name: \u0e15\u0e30 — Ta. \u201cIf you ever truly reach the "
                  "dead-gate,\u201d he says, not looking at you, \u201cand something "
                  "there will listen — tell the boy his uncle's lanterns are still "
                  "trying. Tell him I have not stopped.\u201d"),
            Heart(5, "The sky answers",
                  "One evening he sets a single lantern in your hands beside his "
                  "own. \u201cTogether, then.\u201d You light them; they lift, "
                  "wobble, and rise — his first to catch the sky since the rains. "
                  "He watches it climb with something that is not quite grief and "
                  "not quite hope. \u201cIf the pillar wakes,\u201d he says softly, "
                  "\u201cmaybe the sky is listening again. Maybe Ta's is up there "
                  "somewhere too, still climbing.\u201d He does not let you pay for "
                  "the paper, ever again."),
        ),
    ),
    "naruemon": Contact(
        "naruemon", "Naruemon", "human", "street", "wualai",
        "Hmong silversmith's daughter",
        "She came down from the hills to sell her father's repoussé on the "
        "Saturday walking street. Sharp-eyed about who buys what, and why.",
        greet="Look look — handmade, real silver, not same-same factory one. For "
              "you, special price.",
        want=Want("amulet", "salika", "A golden-tongue charm — she's shy of "
                  "buyers and it would help her sell."),
        secret="The old temple patterns are going missing from the silver. "
               "Someone's buying up anything that carries the guardian's mark — "
               "paying triple, asking no questions, and melting nothing down.",
        secret_at=3,
        boon="fence: silver and small charms in Wualai",
        boon_kind="fence", boon_at=1,
        start_hidden=False,
    ),
    "marisa": Contact(
        "marisa", "Marisa", "human", "guild", "nimman",
        "mixed Thai-farang antiquities scholar at CMU",
        "Raised between Chiang Mai and abroad, she catalogs votive clay for the "
        "university and can date a Hariphunchai tablet by its temper. Curious to "
        "a fault about where the new pieces are coming from.",
        greet="Oh! You're the one Pa Lawan send. Okay okay, come see — but careful "
              "na, this one very very old.",
        want=Want("word", "noi", "She'd give anything to know what the dead-gate "
                  "ghost actually witnessed."),
        secret="The pieces surfacing aren't fakes. They're from Wiang Kum Kam — "
               "the drowned city is giving up its dead. And every one carries the "
               "same unfinished yantra, as if a single hand was interrupted.",
        secret_at=3,
        intros=(Intro("ajahn_ket", 3, "The abbot on Doi Suthep let me catalog a "
                      "reliquary the histories pretend doesn't exist. He'll see you "
                      "if I vouch."),),
        boon="appraise: true valuations, no guessing",
        boon_kind="appraise", boon_at=2,
        start_hidden=False,
    ),
    "anong": Contact(
        "anong", "Sgt. Anong", "police", "law", "tha_phae",
        "khon mueang police sergeant",
        "Twenty years on the Tha Phae beat, and the only officer who still writes "
        "up what she sees. That honesty is exactly why someone wants her looking "
        "the other way.",
        greet="You have business, say business. The other thing — cannot, na. Not me.",
        want=Want("amulet", "doi_brew", "A quiet bottle of the monastery brew "
                  "for the long night shifts."),
        secret="My orders changed after the rains. We're told to wave through "
               "anything marked with a certain sign and to lose the paperwork. I "
               "don't like being made someone's blind eye.",
        secret_at=2,
        boon="gate: a wave-through at Tha Phae when she trusts you",
        boon_kind="gate", boon_at=3,
        start_hidden=False,
        hours=("afternoon", "evening", "night"),   # the long beat, not the dawn
    ),
    "prasit": Contact(
        "prasit", "Officer Prasit", "customs", "law", "chiang_mai_gate",
        "superstitious southern-gate customs officer",
        "He drew the Chiang Mai Gate post and hates it — too near the old ways, "
        "too near the dead's road. He'd trade a month's pay for something to keep "
        "the cold off his neck at night.",
        greet="Shh — not so loud, na. You bring something keep the cold off my "
              "neck? ... Later. Too many eye here.",
        want=Want("amulet", "takrut", "A takrut scroll — protection he can hide "
                  "under his collar."),
        secret="Since the rains the Suan Prung scanners flare at nothing. The old "
               "men say the pillar's guardian has stopped answering. I light extra "
               "incense and pray my shift ends before dark.",
        secret_at=2,
        intros=(Intro("noi", 2, "Something at the dead-gate says my name in the "
                      "quiet. You've the tongue for the unseen; I haven't. Go and "
                      "hear it, and tell me I'm not mad."),),
        boon="gate: the southern-gate schedule",
        boon_kind="gate", boon_at=2,
        start_hidden=False,
        hours=("morning", "evening", "night"),   # gate shifts, not the afternoon lull
    ),
    "ajahn_ket": Contact(
        "ajahn_ket", "Phra Ajahn Ket", "monk", "monkhood", "doi_suthep",
        "abbot and keeper of a denied reliquary",
        "Decades of dawns on the mountain have worn him patient and unbluffable. "
        "He teaches the old script to those with the merit to learn it, and keeps "
        "what should not be kept.",
        greet="เจริญพร นั่งลงก่อนเถิด สิ่งที่เจ้าถือมา วางลงเสียก่อน แล้วค่อยพูดกัน",
        secret="We hold a reliquary the histories deny. What was taken from Wiang "
               "Kum Kam belongs to the pillar, not a collector's shelf. Return it "
               "before Inthakhin, or the city loses its protection for a generation.",
        secret_at=3,
        intros=(Intro("mae_kaew", 3, "Your own line still lights lamps in the old "
                      "city, child. Kneel at the shrine and speak to them — they "
                      "have been waiting to be asked."),),
        boon="teacher: the old script, and a blessing that cools heat",
        start_hidden=False,
        hours=("morning", "afternoon"),   # the mountain keeps dawn hours
    ),
    "aof": Contact(
        "aof", "Aof", "human", "street", "night_bazaar",
        "khon mueang tom, boss of the Chang Klan rider collective",
        "She built a delivery crew out of forty win-motosai riders and one "
        "group chat, and now nothing moves across the night city faster than "
        "her word. Black crew vest, cropped hair, a toothpick and a grin — she "
        "runs the roads the way Pa Lawan runs the river.",
        greet="Eh, you again! Sit sit — no, cannot sit, I working. Talk while I "
              "load, na. You need something go somewhere fast? My rider go anywhere.",
        want=Want("food", "pad_krapow", "She never stops to eat — bring her a "
                  "rice plate and she'll actually sit down for once."),
        secret="My rider see everything, every night. Lately somebody pay "
               "triple to move little clay boxes gate-to-gate after dark — no "
               "address, no name, always mark with the same half-draw yantra. "
               "We don't ask. But we remember every drop, na.",
        secret_at=2,
        boon="courier: riders who'll run a hot load past a gate for a fee",
        boon_kind="courier", boon_at=2,
        start_hidden=False,
        hours=("afternoon", "evening", "night"),
        loves=("pad_krapow", "khao_soi"),
        likes=("miang", "sai_ua"),
        dislikes=("ya_dong",),   # never drinks on shift
        birthday=14,
        hearts=(
            Heart(2, "The vest",
                  "She tosses you a spare crew vest to sit on so you don't "
                  "dirty your clothes on the curb. \u201cForty rider now,\u201d "
                  "she says — not bragging, just counting. \u201cStart with me "
                  "and one borrow bike. People say a girl cannot boss the road. "
                  "Okay okay — I let the road decide.\u201d The road decided."),
            Heart(3, "Nong Fon",
                  "A woman brings two iced coffees without being asked and "
                  "squeezes Aof's shoulder before slipping back into the "
                  "stalls. \u201cMy wife, Fon — she sell the best khao soi on "
                  "Chang Klan,\u201d Aof says. \u201cWe meet because I keep "
                  "order delivery from her own cart, can you believe. Forty "
                  "rider, and I still cannot cook.\u201d She laughs, loud, and "
                  "waves the next loaded bike off into the dark."),
            Heart(4, "The part nobody watches",
                  "\u201cYou want know why I never sleep?\u201d She nods at the "
                  "gates glowing across the dark. \u201cScanner don't read a "
                  "rider like a truck. One person, one bike, one helmet — the "
                  "city cannot see us. That is the whole business. We are the "
                  "part of the city nobody watch.\u201d She grins. \u201cUntil "
                  "somebody need us. Then everybody know my number.\u201d"),
        ),
    ),
    # --- the unseen, reached only through the graph ------------------------
    "noi": Contact(
        "noi", "Noi-who-waits", "phii", "unseen", "suan_prung",
        "a phi tai hong lingering at the gate of the dead",
        "A young runner who died at Suan Prung the night the pillar went quiet, "
        "and whose lamp no one lit. She is not angry. She is worse than angry: "
        "she is patient, and she remembers.",
        greet="You see me? ... Nobody see me long time already. Ask, then. I wait. "
              "I always wait.",
        secret="I died at this gate the night the pillar fell silent — and no one "
               "lit my lamp. But the dead keep watch. I saw them carry the broken "
               "piece out through the dead's own road, certain no living eye was "
               "on them. They forgot I am not living.",
        secret_at=3,
        boon="clue: an eyewitness the living can never have",
        hours=("evening", "night"),   # the dead keep the dark hours
    ),
    "mae_kaew": Contact(
        "mae_kaew", "Mae Kaew", "ancestor", "unseen", "old_city",
        "a grandmother of your line, watching from the shrine",
        "She keeps the household spirits and the family's long memory, and she "
        "will judge you before she helps you — as is her right.",
        greet="Gin khao reu yang, laan? Gin hai im kon na. Reuang muang, koi wa gan.",
        want=Want("food", "pad_krapow", "Set a plate at the shrine, as a "
                  "grandchild should."),
        secret="The Sao Inthakhin is a promise, child. The Lawa gave their "
               "guardian to the city so it would never fall. Break the promise and "
               "the guardians stop protecting us. Someone has broken it.",
        secret_at=3,
        boon="clue: the shape of the old promise",
    ),
    "inthakhin": Contact(
        "inthakhin", "the Guardian of the Pillar", "deva", "unseen", "old_city",
        "the deva sworn to the Sao Inthakhin",
        "The shining one who has stood beneath the city pillar since Kawila set "
        "it at Wat Chedi Luang. It has not spoken since the rains — until, at "
        "last, you are one it will speak to.",
        want=Want("amulet", "phra_rod", "Return what was broken and taken, before "
                  "the festival lanterns rise."),
        secret="Return the stolen piece to the pillar before the Inthakhin flowers "
               "are laid, and the guardians will protect the city again. "
               "Fail, and Chiang Mai goes a generation with no protection at all.",
        secret_at=1,
        boon="the spine of the whole matter",
    ),
}


# --- character-state helpers -----------------------------------------------
def is_known(pc, key: str) -> bool:
    return key in pc.contacts


def bond_of(pc, key: str) -> int:
    return pc.bonds.get(key, 0)


def has_boon(pc, kind: str, at_where: str = "") -> Contact | None:
    """The trusted contact granting a mechanized boon of `kind`, or None.

    A boon is earned, not given: the contact must be known and the bond at or
    past their `boon_at`. `at_where` (a district key) narrows to a boon tied to
    a place — e.g. a gate wave-through only counts at that officer's own gate.
    """
    for k in pc.contacts:
        c = CONTACTS[k]
        if c.boon_kind == kind and bond_of(pc, k) >= c.boon_at:
            if at_where and c.where != at_where:
                continue
            return c
    return None


def discover(pc, key: str, day: int) -> bool:
    """Add a contact to the network. Returns True if newly met."""
    if key in pc.contacts:
        return False
    pc.contacts.append(key)
    pc.bonds[key] = 0
    pc.contact_seen[key] = day
    return True


def adjust_bond(pc, key: str, delta: int, day: int) -> int:
    b = max(BOND_MIN, min(BOND_MAX, bond_of(pc, key) + delta))
    pc.bonds[key] = b
    pc.contact_seen[key] = day
    return b


def present_location(c: Contact, minutes: int) -> str | None:
    """Where a contact is *right now*, or None if they aren't out yet.

    A `schedule` (day-part -> district) wins; otherwise they keep to `where`
    during their `hours` (empty hours == always around)."""
    part = clock.part_of(minutes)
    if c.schedule:
        return dict(c.schedule).get(part)
    if c.hours and part not in c.hours:
        return None
    return c.where or None


def is_present(c: Contact, minutes: int, location: str) -> bool:
    return present_location(c, minutes) == location


def whereabouts(c: Contact, minutes: int) -> str:
    """A human hint about where/when to find them — for 'they aren't here' notes."""
    loc = present_location(c, minutes)
    if loc:
        return f"at {DISTRICTS[loc].name} right now"
    # find their next open part today-ish
    parts = [p for p, _d in c.schedule] if c.schedule else (c.hours or clock.PARTS)
    where = DISTRICTS[c.where].name if c.where else "out"
    return f"not out just now — look in the {' or '.join(parts)}" + (
        f", around {where}" if c.where and not c.schedule else "")


def auto_meet(pc, location: str, day: int) -> list[Contact]:
    """Meet the visible locals who are out here now. Returns any newly met."""
    met = []
    for c in CONTACTS.values():
        if (not c.start_hidden and is_present(c, pc.minutes, location)
                and discover(pc, c.key, day)):
            met.append(c)
    return met


def here(pc, location: str) -> list[Contact]:
    """Known contacts who are physically present here at the current hour."""
    return [CONTACTS[k] for k in pc.contacts
            if is_present(CONTACTS[k], pc.minutes, location)]


# --- the core interactions --------------------------------------------------
@dataclass
class Result:
    lines: list[str] = field(default_factory=list)


def _reveal_secret(pc, c: Contact, res: Result) -> None:
    if c.secret and c.key not in pc.secrets_heard and bond_of(pc, c.key) >= c.secret_at:
        pc.secrets_heard.append(c.key)
        res.lines.append(f"\u201c{c.secret}\u201d")
        res.lines.append(f"(You now hold {c.name}'s secret — another contact may "
                         f"want to hear it. Use 'share' to trade it for a favour.)")


def _offer_intros(pc, c: Contact, res: Result) -> None:
    for it in c.intros:
        if bond_of(pc, c.key) >= it.at and not is_known(pc, it.to):
            res.lines.append(f"{c.name}: \u201c{it.line}\u201d")
            res.lines.append(f"(Ask to be introduced to {CONTACTS[it.to].name}.)")


def _reveal_hearts(pc, c: Contact, res: Result) -> None:
    """Fire any get-to-know-you scene the current bond has newly unlocked."""
    for h in c.hearts:
        tag = f"{c.key}:{h.at}"
        if bond_of(pc, c.key) >= h.at and tag not in pc.hearts_seen:
            pc.hearts_seen.append(tag)
            res.lines.append(f"\u2014 {c.name}: {h.title} \u2014")
            res.lines.append(h.text)


def _deva_voice(bond: int) -> str:
    """The Guardian speaks in the register its mood allows. The more difficult it
    is being — the less it trusts you — the less it will meet you in your own
    tongue: remote in Thai when cold, softening to transliterated Thai, and plain
    (almost human) Thaiglish only once you have truly won it over."""
    if bond <= 1:
        return "เจ้าเป็นผู้ใด จึงกล้ามารบกวนเสาอินทขีล"
    if bond <= 3:
        return "Jao ma ha sing dai, luuk?"
    return "You come back. Good, good. The city — you and me, we keep together, na."


def talk(pc, key: str, day: int, bonus: int = 0,
         rng: random.Random | None = None) -> Result:
    """Persuade a contact; the outcome moves the lasting bond."""
    c = CONTACTS[key]
    res = Result()
    att = persuasion.persuade(pc, c.role, bonus=bonus, rng=rng)
    res.lines.extend(att.notes)
    res.lines.append(att.roll.describe())
    delta = {Outcome.STRONG: 2, Outcome.WEAK: 1, Outcome.MISS: -1}[att.outcome]
    before = tier(bond_of(pc, key))
    b = adjust_bond(pc, key, delta, day)
    after = tier(b)
    if delta > 0:
        voice = _deva_voice(b) if key == "inthakhin" else c.greet
        if voice:
            res.lines.append(f"{c.name}: \u201c{voice}\u201d")
        res.lines.append(f"{c.name} warms to you — now {after}." if after != before
                         else f"{c.name} hears you out.")
    else:
        res.lines.append(f"You misjudge {c.name}; the mood cools to {after}.")
    _reveal_secret(pc, c, res)
    _reveal_hearts(pc, c, res)
    _offer_intros(pc, c, res)
    return res


def _gift_delta(c: Contact, item_key: str) -> tuple[int, str]:
    """How a gift lands: (bond delta, flavour). Their want is the deepest love."""
    loved = item_key in c.loves or (c.want and c.want.kind in ("food", "amulet")
                                    and c.want.ref == item_key)
    if loved:
        return 2, " — exactly what they hoped for. It lands like a promise kept."
    if item_key in c.likes:
        return 2, " — a thing they genuinely like."
    if item_key in c.dislikes:
        return -1, (". They accept it with both hands and a gracious smile and "
                    "thank you kindly — but something in the smile tells you it "
                    "wasn't to their taste.")
    return 1, ". A small kindness, noted."


def give(pc, key: str, item_key: str, day: int) -> Result:
    """Give a contact something. Their loves land hardest; a birthday, harder still."""
    c = CONTACTS[key]
    res = Result()
    if not pc.has(item_key):
        res.lines.append("You aren't carrying that.")
        return res
    from .items import get
    it = get(item_key)
    pc.add_item(item_key, -1)
    delta, flavour = _gift_delta(c, item_key)
    # Fulfilling their true want is the thing the story listens for.
    wanted = c.want and c.want.kind in ("food", "amulet") and c.want.ref == item_key
    if wanted and c.key not in pc.wants_met:
        pc.wants_met.append(c.key)
    birthday = c.birthday and c.birthday == day and delta > 0
    if birthday:
        delta += 1
    adjust_bond(pc, key, delta, day)
    res.lines.append(f"You give {c.name} the {it.name}{flavour}")
    if birthday:
        res.lines.append(f"— and it's {c.name}'s birthday. That you remembered "
                         f"means more than the gift.")
    res.lines.append(f"{c.name} is now {tier(bond_of(pc, key))}.")
    _reveal_secret(pc, c, res)
    _reveal_hearts(pc, c, res)
    _offer_intros(pc, c, res)
    return res


def share_word(pc, key: str, day: int) -> Result:
    """Carry one contact's secret to another who longs to hear it."""
    c = CONTACTS[key]
    res = Result()
    if not (c.want and c.want.kind == "word"):
        res.lines.append(f"{c.name} listens warmly, thanks you for thinking of "
                         f"them, and lets it pass — there's no word they're "
                         f"waiting to hear from you just now.")
        return res
    if c.want.ref not in pc.secrets_heard:
        src = CONTACTS[c.want.ref].name
        res.lines.append(f"{c.name} smiles and says they'd love to hear it another "
                         f"time — you've nothing to trade them yet. First win "
                         f"{src}'s trust and hear their secret.")
        return res
    if c.key in pc.wants_met:
        res.lines.append(f"You've already told {c.name} what you know.")
        return res
    pc.wants_met.append(c.key)
    adjust_bond(pc, key, 2, day)
    res.lines.append(f"You tell {c.name} what {CONTACTS[c.want.ref].name} let slip. "
                     f"That was the favour they wanted; your bond jumps to "
                     f"{tier(bond_of(pc, key))}.")
    _reveal_secret(pc, c, res)
    _reveal_hearts(pc, c, res)
    _offer_intros(pc, c, res)
    return res


# --- networking: growing the graph -----------------------------------------
def available_intros(pc) -> list[tuple[str, str]]:
    """Return (introducer_key, target_key) pairs you can act on now."""
    out = []
    for k in pc.contacts:
        for it in CONTACTS[k].intros:
            if bond_of(pc, k) >= it.at and not is_known(pc, it.to):
                out.append((k, it.to))
    # apex nodes: unlocked when several bonds are all deep enough
    for target, reqs in APEX.items():
        if not is_known(pc, target) and all(
                is_known(pc, rk) and bond_of(pc, rk) >= rb for rk, rb in reqs):
            out.append(("*", target))
    return out


def introduce(pc, target_key: str, day: int) -> Result:
    """Follow an available introduction to a new contact."""
    res = Result()
    if is_known(pc, target_key):
        res.lines.append("You already know them.")
        return res
    if target_key not in {t for _, t in available_intros(pc)}:
        res.lines.append("Everyone you ask is happy to help — another time, they "
                         "say, warmly, when the moment is right. No one has quite "
                         "offered to open that door yet; deepen a friendship and "
                         "someone gladly will.")
        return res
    c = CONTACTS[target_key]
    discover(pc, target_key, day)
    res.lines.append(f"A door opens. You are introduced to {c.name} — "
                     f"{c.heritage}.")
    res.lines.append(c.bio)
    if c.want:
        res.lines.append(f"They seem to want: {c.want.note}")
    return res


# --- standing & upkeep ------------------------------------------------------
def standing(pc) -> dict[str, int]:
    out = {f: 0 for f in FACTIONS}
    for k in pc.contacts:
        out[CONTACTS[k].faction] = out.get(CONTACTS[k].faction, 0) + bond_of(pc, k)
    return out


# Bonds cool only after a real stretch of neglect, and never below "friendly":
# a friendship you've built stays a friendship. This keeps a gentle nudge to
# visit people without turning the web into an anxious maintenance chore.
DECAY_AFTER_DAYS = 5
DECAY_FLOOR = 2       # tier(2) == "friendly"


def daily_decay(pc, day: int) -> list[str]:
    """Long-neglected bonds cool a little, but never past friendly. Returns notes."""
    faded = []
    for k in list(pc.contacts):
        seen = pc.contact_seen.get(k, day)
        if day - seen >= DECAY_AFTER_DAYS and bond_of(pc, k) > DECAY_FLOOR:
            pc.bonds[k] = bond_of(pc, k) - 1
            pc.contact_seen[k] = day  # reset the idle clock
            faded.append(f"{CONTACTS[k].name} drifts to {tier(pc.bonds[k])} "
                         f"in your absence.")
    return faded
