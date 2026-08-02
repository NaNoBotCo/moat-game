"""The unmarked opening: notice that time is different, then find the clock.

There is no quest-log entry for this and there is no marker. The player arrives
keeping ordinary time and the city quietly refuses it. A shop is shut at eleven
and open at eleven thirty-seven. A tout says come back at the right time and
will not say when that is. Two schedules that have nothing to do with each other
agree with each other exactly, and neither agrees with your watch.

The quest does not begin when the player is told about it. It begins when they
**demonstrate that they have noticed** — by waiting out a window on purpose, and
by comparing two lanes' hours instead of one. Only then does it become a thing
they are doing.

Finding the wat is triangulation, not navigation. The bird is heard three times
a day and every wat inside the wall is a candidate — forty-nine of them, taken
straight from the real city. You stand in a quarter, you hear the call, and you
learn how tightly that quarter's windows sit against it. Do that from three
quarters and the candidate list collapses to one.

Completing it is the tutorial for the game's only real skill — reading windows —
and the reward is that the lattice becomes visible. There is no other reward and
there does not need to be one.
"""

from __future__ import annotations

import random

from . import coucal, venues

# The four quarters inside the wall, named for the corner bastions that anchor
# them, plus the middle. The old city never changes, so these are hand-authored
# and permanent — this is the beginning of the map the player keeps for good.
QUARTERS = {
    "si_phum": ("the north-east quarter (Jaeng Si Phum)",
                "Teak houses and a lane of school gates. Quiet by nine."),
    "katam": ("the south-east quarter (Jaeng Katam)",
              "Guesthouses and repair shops, the loudest corner inside the wall."),
    "ku_ruang": ("the south-west quarter (Jaeng Ku Ruang)",
                 "Low walls, mango shade, and the lane that smells of charcoal "
                 "at exactly the same hour every day."),
    "hua_lin": ("the north-west quarter (Jaeng Hua Lin)",
                "Half of it is monastery wall. Nothing here is in a hurry."),
    "centre": ("the middle of the old city",
               "Chedi Luang's broken mass, the pillar in its shade, and the "
               "crossing where every lane in the grid eventually admits it "
               "is going."),
}
QUARTER_KEYS = tuple(QUARTERS)

# Walking between quarters, inside the wall, on foot.
WALK_MINUTES = 25

# What it takes before the player has demonstrably noticed.
NEED_OBSERVATIONS = 3
NEED_WAITED = 1
NEED_CROSSREF = 1
# Quarters you must hear the call from before the candidates collapse.
NEED_BEARINGS = 3

PHASE_BLIND = "blind"        # the city is simply refusing you, and you don't know it
PHASE_NOTICED = "noticed"    # you know time is the problem; you don't know where
PHASE_FOUND = "found"        # you have the wat, and the lattice is visible


def state(pc) -> dict:
    return pc.noticing


def phase(pc) -> str:
    return state(pc).get("phase", PHASE_BLIND)


def init(pc, seed: int = 1296) -> None:
    """Choose the wat. Seeded from the save, so a world is stable forever."""
    if state(pc):
        return
    wats = [v for v in venues.in_district("old_city") if v.cat == "wat"]
    rng = random.Random(seed)
    # The bird sits in one of them, and it has for fifty years.
    idx = rng.randrange(len(wats)) if wats else 0
    home = wats[idx].key if wats else "v00000"
    pc.noticing = {
        "phase": PHASE_BLIND,
        "wat": home,
        "quarter": rng.choice(QUARTER_KEYS),   # which quarter the wat stands in
        "here": "centre",                      # where the player is inside the wall
        "observations": [],                    # civil minutes of window-flips seen
        "waited": 0,                           # deliberate wait-outs
        "crossref": [],                        # districts compared in one day
        "crossrefs": 0,
        "bearings": {},                        # quarter -> tightness reading
        "candidates": len(wats) or 1,
    }


# --- the refusal (phase 1: the player does not know there is a puzzle) ------
DEFLECTIONS = (
    "“Ah — not now, na. You come back the right time.” He does "
    "not say what the right time is. It does not seem to occur to him that you "
    "would not know.",
    "The shutter is down. A hand-lettered card behind the grille gives hours, "
    "and the hours are not round numbers.",
    "“Too early.” You point out that it is the middle of the "
    "afternoon. She agrees that it is the middle of the afternoon, and repeats "
    "that it is too early.",
    "Somebody is already waiting, sitting on the step with the patience of a "
    "person who knows exactly how long this is going to take.",
    "“My uncle open. Not me. He come after the bird.”",
)


def deflection(rng: random.Random) -> str:
    return rng.choice(DEFLECTIONS)


def observe_flip(pc, minutes: int) -> str | None:
    """Called when the player is present as a window turns over."""
    if phase(pc) != PHASE_BLIND:
        return None
    st = state(pc)
    st["observations"] = [*st["observations"], minutes][-12:]
    return None      # deliberately silent — noticing is the player's job


def note_wait(pc, ended_at: int) -> None:
    """The player deliberately waited, and the wait ended on a hinge."""
    if coucal.on_boundary(ended_at, slack=12):
        state(pc)["waited"] = state(pc).get("waited", 0) + 1


def note_crossref(pc, district: str) -> None:
    """The player read one lane's hours, then another's."""
    st = state(pc)
    seen = st.get("crossref", [])
    if district not in seen:
        seen = [*seen, district]
        st["crossref"] = seen
        if len(seen) >= 2:
            st["crossrefs"] = st.get("crossrefs", 0) + 1
            st["crossref"] = []


def _aligned(observations: list[int]) -> int:
    """How many observed flips sit on a coucal hinge. The whole tell."""
    return sum(1 for m in observations if coucal.on_boundary(m, slack=10))


def check_noticed(pc) -> list[str]:
    """Has the player demonstrated it? If so, the quest quietly becomes real."""
    if phase(pc) != PHASE_BLIND:
        return []
    st = state(pc)
    if (_aligned(st.get("observations", [])) < NEED_OBSERVATIONS
            or st.get("waited", 0) < NEED_WAITED
            or st.get("crossrefs", 0) < NEED_CROSSREF):
        return []
    st["phase"] = PHASE_NOTICED
    return [
        "",
        "You are standing in a lane you have stood in before, and the shutter "
        "goes up, and you already knew it was going to.",
        "",
        "It is not the hour. It has never been the hour. Yesterday the clinic "
        "two streets over opened at the same wrong minute, and the tout on the "
        "corner changed shift at the same wrong minute, and the shop in front "
        "of you is opening at it now. Your watch has nothing to do with any of "
        "it. Their hours are not agreeing with the day. They are agreeing with "
        "each other.",
        "",
        "Something in this city is keeping time, and everything is listening "
        "to it except you.",
    ]


# --- the call and the triangulation (phase 2) ------------------------------
def hear_call(pc, minutes: int) -> list[str]:
    """The bird sounds. What you get out of it depends on whether you're ready."""
    if not coucal.is_call(minutes):
        return []
    if phase(pc) == PHASE_BLIND:
        # Pure texture. You have no idea this matters.
        return ["Somewhere over the roofs a bird calls, three low notes, and "
                "along the lane a shutter goes up."]
    if phase(pc) == PHASE_FOUND:
        return [f"The bird sounds — {coucal.watch_name(minutes)} turning over."]
    return _take_bearing(pc, minutes)


def _take_bearing(pc, minutes: int) -> list[str]:
    """From this quarter, how tightly do local windows sit against the call?"""
    st = state(pc)
    here = st.get("here", "centre")
    target = st.get("quarter", "centre")
    # Tightness: the closer you are to the bird, the less slack in local hours.
    order = list(QUARTER_KEYS)
    dist = abs(order.index(here) - order.index(target))
    dist = min(dist, len(order) - dist)          # the wall wraps
    tight = max(0, 4 - dist)
    st["bearings"] = {**st.get("bearings", {}), here: tight}
    words = {
        4: "Every shutter on this lane moves inside the same half-minute as the "
           "call. There is no slack here at all.",
        3: "The lane answers the call almost at once — a beat behind, no more.",
        2: "Shutters move a minute or two after the call, unhurried.",
        1: "The call reaches here thin, and the lane takes its time about it.",
        0: "You can barely hear it from this quarter, and nothing here seems to "
           "be listening.",
    }
    lines = ["The bird sounds. You stand still and watch the lane instead of "
             "the bird.", words[tight]]
    got = len(st["bearings"])
    if got < NEED_BEARINGS:
        lines.append(f"({got} of {NEED_BEARINGS} quarters heard from.)")
    else:
        lines += _collapse(pc)
    return lines


def _collapse(pc) -> list[str]:
    st = state(pc)
    best = max(st["bearings"].items(), key=lambda kv: kv[1])
    if best[1] < 3:
        return ["You have heard it from three quarters and it is loudest in "
                "none of them. Somewhere you have not stood yet, then."]
    st["quarter_found"] = best[0]
    name = QUARTERS[best[0]][0]
    return ["",
            f"Three quarters, three readings, and they point the same way: "
            f"{name}. Not the whole answer — there are wats in there — but the "
            f"search has stopped being the size of a city.",
            "You can go and find it now."]


def can_search(pc) -> bool:
    return (phase(pc) == PHASE_NOTICED
            and state(pc).get("quarter_found")
            and state(pc)["here"] == state(pc)["quarter_found"])


def search(pc) -> list[str]:
    """Walk the quarter the readings pointed at, and find the thing itself."""
    st = state(pc)
    st["phase"] = PHASE_FOUND
    return [
        "",
        "It takes most of a morning, and it is not hidden. It is in the third "
        "compound you try, in a side hall nobody has any reason to lock: a case "
        "of teak and glass the height of a man, a brass bird on a bracket, and "
        "a movement behind it that has not been wound in your lifetime and does "
        "not appear to need it.",
        "",
        "The bird comes out at the turn of the watch. It calls three times. "
        "Every shutter within half a mile answers, and now you know why.",
        "",
        "Nobody at the wat can tell you who set it. The abbot was not born. "
        "The novice who sweeps the hall thinks it has always been there, which "
        "is nearly true, and says so in the tone people use for weather.",
        "",
        "— You can read the lattice now. Every window in this city hangs "
        "off eight watches a day, beginning thirty-seven minutes after "
        "midnight, and you will never again walk up to a shut door by accident.",
    ]


def objective(pc) -> str | None:
    """What the banner says — and it says nothing at all until you've noticed."""
    p = phase(pc)
    if p == PHASE_BLIND:
        return None                     # no marker, no prompt, no quest
    if p == PHASE_FOUND:
        return None
    st = state(pc)
    if st.get("quarter_found"):
        if st["here"] == st["quarter_found"]:
            return "Find the clock. It is in this quarter somewhere."
        return f"Go to {QUARTERS[st['quarter_found']][0]} and find the clock."
    got = len(st.get("bearings", {}))
    return (f"Something is keeping this city's time. Stand where you can hear "
            f"it and watch what answers. ({got}/{NEED_BEARINGS} quarters)")


def lattice_visible(pc) -> bool:
    return phase(pc) == PHASE_FOUND
