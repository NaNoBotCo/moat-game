"""The map of Chiang Mai as a graph of districts.

The old city (Nai Wiang) is a near-perfect square about 1.5 km a side — roughly
a mile — ringed by the moat King Mangrai's people dug in 1296. Its wall has
**five gates** and **four corner bastions (jaeng)**: reading clockwise, the gates
are Chang Phuak (N), Tha Phae (E), Chiang Mai (S), Suan Prung (SW) and Suan Dok
(W); the corners are Jaeng Si Phum (NE), Jaeng Katam (SE), Jaeng Ku Ruang (SW)
and Jaeng Hua Lin (NW). Movement between the walled interior and the outer city
passes through one of the gates. In 2076 each gate is a customs post — so any
edge flagged `crossing=True` triggers a moat checkpoint.

The tech is near-future but worn-in: solar shingles and sensor-arches bolted onto
teak and brick, EV songthaews sharing the lane with long-tail boats, a city mesh
that everyone carries and no one trusts. And since the Sao Inthakhin pillar fell
silent after the rains, none of it works quite right after dark — signals rot to
static, scanners flag empty air, and the drowned lanes of Wiang Kum Kam keep
surfacing where the river runs low.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class District:
    key: str
    name: str
    zone: str            # "inside" | "gate" | "outside" | "city"
    blurb: str
    features: tuple[str, ...] = field(default_factory=tuple)
    region: str = "chiangmai"


@dataclass(frozen=True)
class Edge:
    to: str
    crossing: bool = False   # True == passes the moat gate (customs scan)
    minutes: int = 20


DISTRICTS: dict[str, District] = {
    "old_city": District(
        "old_city", "Old City (Nai Wiang)", "inside",
        "Inside the moat: a mile-square grid of teak houses and temple compounds, "
        "solar shingles glinting on the old tin roofs, the corner bastions of Si "
        "Phum, Katam, Ku Ruang and Hua Lin anchoring its four angles. Wat Chedi "
        "Luang's broken chedi looms over the quarter that once cradled the Emerald "
        "Buddha; the Sao Inthakhin pillar sleeps at its heart, and since it went "
        "quiet the mesh-signal dies to static within a block of it. On Sundays the "
        "Ratchadamnoen walking street still floods with stalls and drifting "
        "lantern-drones. Quiet, watched, and home — and lately, after dark, the "
        "grid feels one resident too many.",
        features=("safehouse", "shrine", "rumors", "walking_street"),
    ),
    # --- the five historic gates ------------------------------------------
    "tha_phae": District(
        "tha_phae", "Tha Phae Gate", "gate",
        "The eastern gate, mouth of the old city. By day a plaza where live "
        "pigeons mob the drone kind for dropped rice; by night a lit lane of "
        "aura-scanners funnels every crossing toward the river. The booth reads "
        "body-heat and something the officers only call 'the other heat' — and it "
        "has been twitching at empty air since the rains.",
        features=("checkpoint",),
    ),
    "chang_phuak": District(
        "chang_phuak", "Chang Phuak Gate", "gate",
        "The northern 'Elephant Gate', famed for its late-night khao kha moo. "
        "Customs here is sleepy — a bored officer, a humming scanner-arch, a "
        "coffee-drone on a wire — but the stall queue hides many eyes, and the "
        "night-shift CCTV keeps logging the same phi tai hong: a woman dead "
        "before her time, drifting the khao kha moo line, never reaching the "
        "counter.",
        features=("checkpoint",),
    ),
    "suan_dok": District(
        "suan_dok", "Suan Dok Gate", "gate",
        "The western gate opening toward the mountain and Wat Suan Dok's white "
        "royal stupas, their tips wrapped now in signal-repeaters that pray and "
        "broadcast at once. The switchbacked charge-road to Doi Suthep begins past "
        "the scanners; EV scooters top up under the bodhi trees while a monk "
        "blesses the charging bays each dawn.",
        features=("checkpoint",),
    ),
    "chiang_mai_gate": District(
        "chiang_mai_gate", "Chiang Mai Gate", "gate",
        "The southern gate, flanked by the Pratu Chiang Mai market — flowers, "
        "curry, and charcoal smoke that still, somehow, blinds the scanners better "
        "than any jammer. Marigold garlands hang from the camera masts, and the "
        "officers buy amulets off their own confiscation table.",
        features=("checkpoint",),
    ),
    "suan_prung": District(
        "suan_prung", "Suan Prung Gate", "gate",
        "The south-western gate. For centuries the dead left the city this way "
        "for cremation, so custom keeps it half-shunned; the scanners here glitch "
        "worse than at any other gate and no one has bothered to fix them in "
        "years. The officers are as superstitious as they are bored — they keep "
        "the arch's spirit-heat alarm switched off, because it will not stop "
        "screaming. It opens toward Wualai's silver lanes, and the Silver "
        "Temple's roof shows over the wall from here \u2014 which is not a "
        "coincidence, and never was. Under the arch, in the shade nobody wants "
        "to stand in, there is trade: the best prices in Chiang Mai, and every "
        "bargain struck here comes with something attached.",
        features=("checkpoint", "market", "cursed_market"),
    ),
    # --- outer city -------------------------------------------------------
    "kad_chang_phuak": District(
        "kad_chang_phuak", "Kad Chang Phuak", "outside",
        "The night-market sprawl just north of the Elephant Gate: the famous "
        "khao kha moo stall in its cowboy hat, sai ua sizzling under buzzing LED, "
        "and a bus yard where autonomous songthaews and the whole north load and "
        "unload. Cheap food, cheaper eyes, and a face-recognition board that no "
        "one trusts and everyone feeds a false name. A 24-hour chemist's glows "
        "blue between the food stalls, cheap remedies stacked to the ceiling.",
        features=("market", "night", "rumors", "pharmacy"),
    ),
    "warorot": District(
        "warorot", "Warorot Market (Kad Luang)", "outside",
        "The great riverside bazaar. Gold shops behind hardened shutters, dried "
        "goods, QR-charms sold by the sheet, and the traders' guild who can move "
        "anything — physical or ledgered — for a cut. Upstairs, a back room of "
        "humming servers keeps two sets of books and one small shrine. A "
        "generations-old chemist's shop on the lane sells liniments over the "
        "counter and ya of a different sort beneath it.",
        features=("market", "fence", "guild", "pharmacy"),
    ),
    "wualai": District(
        "wualai", "Wualai Road (Saturday Walking Street)", "outside",
        "The silversmiths' road south of the wall, where hammers have beaten "
        "temple repoussé for generations and now tap the same rhythm into "
        "laser-etched pendants. On Saturday nights it becomes a river of stalls "
        "and drifting sky-lanterns; buyers who came for silver leave with charms — "
        "and lately the lanterns keep sinking back down, though the night is "
        "still.",
        features=("market", "buyers", "silver", "teacher:mudra",
                  "silver_temple"),
    ),
    "nimman": District(
        "nimman", "Nimman & Suan Dok Road (CMU)", "outside",
        "West of the mountain gate: Wat Suan Dok's white royal stupas, CMU's "
        "crowds, and Nimmanhaemin's cafés where the young and polished trade in "
        "stories and follower-counts. The Khruba Srivichai road climbs from here "
        "toward Doi Suthep, its first switchback strung with prayer-flags and "
        "charging cables both. Glass-fronted beauty clinics promise glow by the "
        "hour, and the great teaching hospital at Suan Dok anchors the far end of "
        "the road — real medicine, at real-money prices.",
        features=("market", "buyers", "teacher:mahaniyom", "clinic", "hospital"),
    ),
    "ping_river": District(
        "ping_river", "Ping Riverside (Mae Ping)", "outside",
        "Wooden jetties, long-tail boats, and a line of sensor-buoys the city "
        "swears watches the water. Where the gates fail, the river runners succeed "
        "— for a price and a risk. Since the rains the Ping runs low and gives "
        "things back: bricks, votive tablets, whole drowned lanes of Wiang Kum "
        "Kam surfacing in the shallows.",
        features=("docks", "smuggle_route"),
    ),
    "night_bazaar": District(
        "night_bazaar", "Night Bazaar (Chang Klan)", "outside",
        "Chang Klan Road after dark: a river of stalls, tourists, holo-signage, "
        "and buyers who pay premium for a charm with a story and a scannable "
        "certificate of blessing. The tuk-tuks are electric now; the pickpockets, "
        "augmented. Between the stalls, a bright wellness-and-beauty clinic sells "
        "tourists the glow they flew in for.",
        features=("market", "buyers", "night", "clinic"),
    ),
    "doi_suthep": District(
        "doi_suthep", "Doi Suthep", "outside",
        "The mountain temple at the head of Khruba Srivichai's road. Wat Phra "
        "That's golden chedi crowns the forest, ringed by pilgrims' phones held up "
        "like a second row of candles; the monasteries here consecrate amulets — "
        "chip and clay alike — and grow the herbs that fill the potions. Reached "
        "by the long climb up from Nimman, not across the moat. Above the cloud "
        "line the mesh finally comes clean, as if the mountain still listens where "
        "the city has stopped.",
        features=("monastery", "herbs", "blessing", "shrine",
                  "teacher:aksorn", "teacher:saiyasat", "teacher:phasa_phii"),
    ),
    # --- greater Lanna: reachable only by the road or rail --------------------
    "lamphun": District(
        "lamphun", "Lamphun (Hariphunchai)", "city",
        "The old Mon city south of Chiang Mai, older even than Lan Na. Wat Phra "
        "That Hariphunchai's golden chedi presides; this is the birthplace of the "
        "revered Phra Rod, and scholars here still read the ancient hand — now "
        "cross-checking it against script-scanners that keep mis-transcribing one "
        "glyph as a name no dictionary holds.",
        features=("market", "shrine", "teacher:aksorn", "phra_rod_source"),
        region="lamphun",
    ),
    "lampang": District(
        "lampang", "Lampang", "city",
        "Horse-carriages still clop past teak shophouses, sharing the lane with "
        "silent EV vans. Wat Phra That Lampang Luang guards the plain; the kilns "
        "and the cooks here are famous, and the kiln-masters fire ceramic "
        "sensor-beads the smuggling trade quietly loves.",
        features=("market", "teacher:khrua", "teacher:mudra", "kilns"),
        region="lampang",
    ),
    "chiang_rai": District(
        "chiang_rai", "Chiang Rai", "city",
        "King Mangrai's first capital, up the punishing mountain road. A frontier "
        "town, gateway to the north and its quiet trades, where border drones and "
        "border spirits are given equal, wary respect.",
        features=("market", "fence", "teacher:mahaniyom"),
        region="chiang_rai",
    ),
    "golden_triangle": District(
        "golden_triangle", "Golden Triangle (Sop Ruak)", "city",
        "Where the Ruak meets the Mekong and three borders blur. Chiang Saen's "
        "ruins watch a river that has moved contraband for centuries — by raft, "
        "by drone, by darker means. The satellites lose track of boats here, and "
        "always have.",
        features=("fence", "smuggle_route", "buyers"),
        region="golden_triangle",
    ),
}
# Teacher of Charcha sits with the Warorot guild; the glow-up crowd of the
# Night Bazaar will teach Mahaniyom to anyone charming enough to ask.
DISTRICTS["warorot"] = District(
    **{**DISTRICTS["warorot"].__dict__,
       "features": DISTRICTS["warorot"].features + ("teacher:charcha",)})
DISTRICTS["night_bazaar"] = District(
    **{**DISTRICTS["night_bazaar"].__dict__,
       "features": DISTRICTS["night_bazaar"].features + ("teacher:mahaniyom",)})

# Adjacency. Gate<->outside edges cross the moat (customs scan).
EDGES: dict[str, list[Edge]] = {
    "old_city": [
        Edge("chang_phuak"), Edge("tha_phae"),
        Edge("chiang_mai_gate"), Edge("suan_prung"), Edge("suan_dok"),
    ],
    "tha_phae": [
        Edge("old_city"),
        Edge("warorot", crossing=True),
        Edge("ping_river", crossing=True),
        Edge("night_bazaar", crossing=True, minutes=30),
    ],
    "chang_phuak": [
        Edge("old_city"),
        Edge("kad_chang_phuak", crossing=True),
    ],
    "suan_dok": [
        Edge("old_city"),
        Edge("nimman", crossing=True),
    ],
    "chiang_mai_gate": [
        Edge("old_city"),
        Edge("wualai", crossing=True),
        Edge("night_bazaar", crossing=True),
    ],
    "suan_prung": [
        Edge("old_city"),
        Edge("wualai", crossing=True),
    ],
    "kad_chang_phuak": [
        Edge("chang_phuak", crossing=True),
    ],
    "warorot": [
        Edge("tha_phae", crossing=True),
        Edge("ping_river"),
        Edge("night_bazaar"),
    ],
    "ping_river": [
        Edge("tha_phae", crossing=True),
        Edge("warorot"),
    ],
    "night_bazaar": [
        Edge("chiang_mai_gate", crossing=True),
        Edge("tha_phae", crossing=True, minutes=30),
        Edge("warorot"),
        Edge("wualai"),
    ],
    "wualai": [
        Edge("chiang_mai_gate", crossing=True),
        Edge("suan_prung", crossing=True),
        Edge("night_bazaar"),
    ],
    "nimman": [
        Edge("suan_dok", crossing=True),
        Edge("doi_suthep", minutes=40),
    ],
    "doi_suthep": [
        Edge("nimman", minutes=40),
    ],
}


def neighbors(key: str) -> list[Edge]:
    return EDGES.get(key, [])


def edge_between(a: str, b: str) -> Edge | None:
    for e in neighbors(a):
        if e.to == b:
            return e
    return None


def region_of(key: str) -> str:
    return DISTRICTS[key].region


# --- Inter-city travel ------------------------------------------------------
# A transport mode: (minutes, cost in baht, danger 0..3). Scooters dominate and
# are cheap but exposed; buses/songthaew are steadier; the northern train only
# runs south to Lamphun/Lampang — the line to Chiang Rai has never been built,
# which is exactly why funding it is a long-game project.
@dataclass(frozen=True)
class Mode:
    name: str
    minutes: int
    cost: int
    danger: int


@dataclass(frozen=True)
class Route:
    to: str              # destination region
    arrive: str          # district you land in
    km: int
    modes: tuple[Mode, ...]


# Star topology on Chiang Mai, plus the northern spur to the Golden Triangle.
ROUTES: dict[str, list[Route]] = {
    "chiangmai": [
        Route("lamphun", "lamphun", 26, (
            Mode("scooter", 55, 60, 1),
            Mode("songthaew", 70, 40, 0),
            Mode("train", 40, 30, 0),
        )),
        Route("lampang", "lampang", 100, (
            Mode("scooter", 150, 180, 2),
            Mode("bus", 130, 120, 1),
            Mode("train", 120, 90, 0),
        )),
        Route("chiang_rai", "chiang_rai", 190, (
            # The road always sucks: mountainous, switchbacked, and slow.
            Mode("scooter", 330, 300, 3),
            Mode("bus", 240, 220, 2),
        )),
    ],
    "lamphun":  [Route("chiangmai", "old_city", 26, (
        Mode("scooter", 55, 60, 1), Mode("train", 40, 30, 0)))],
    "lampang":  [Route("chiangmai", "old_city", 100, (
        Mode("bus", 130, 120, 1), Mode("train", 120, 90, 0)))],
    "chiang_rai": [
        Route("chiangmai", "old_city", 190, (
            Mode("scooter", 330, 300, 3), Mode("bus", 240, 220, 2))),
        Route("golden_triangle", "golden_triangle", 60, (
            Mode("scooter", 90, 100, 2), Mode("songthaew", 110, 70, 1))),
    ],
    "golden_triangle": [Route("chiang_rai", "chiang_rai", 60, (
        Mode("scooter", 90, 100, 2), Mode("songthaew", 110, 70, 1)))],
}

# The train build-out to Chiang Rai: a real-world dream, here a fundable work.
TRAIN_NORTH_GOAL = 40000
TRAIN_NORTH_MODE = Mode("train", 150, 110, 0)


def routes_from(region: str, projects: dict) -> list[Route]:
    out = [Route(r.to, r.arrive, r.km, r.modes) for r in ROUTES.get(region, [])]
    # Once the northern line is funded, add a train option on the CR corridor.
    if projects.get("train_north", 0) >= TRAIN_NORTH_GOAL:
        for i, r in enumerate(out):
            if {region, r.to} == {"chiangmai", "chiang_rai"}:
                out[i] = Route(r.to, r.arrive, r.km, r.modes + (TRAIN_NORTH_MODE,))
    return out
