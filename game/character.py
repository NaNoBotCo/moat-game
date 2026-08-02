"""The smuggler: attributes, resources, and carried goods."""

from __future__ import annotations

from dataclasses import dataclass, field

ATTRS = ("nerve", "guile", "lore", "hands")
ATTR_BLURB = {
    "nerve": "Cool under a scanner's eye. Bluffing, holding the line.",
    "guile": "Deception, haggling, reading a mark.",
    "lore": "Amulet & potion knowledge — appraisal, authentication, blessing.",
    "hands": "Sleight, concealment, quick and quiet work.",
}

# A few starting builds so the player picks a stance, not just numbers.
BACKGROUNDS = {
    "monk": {
        "name": "Defrocked Monk",
        "desc": "Years at Wat Suan Dok taught you what a real amulet feels like.",
        "attrs": {"nerve": 1, "guile": 0, "lore": 2, "hands": -1},
        "baht": 800,
        "kit": ["luang_phu_thuat", "ya_hom"],
        # You can already read the old script and speak to what lingers.
        "skills": {"aksorn": 2, "saiyasat": 1, "phasa_phii": 1},
    },
    "trader": {
        "name": "Warorot Trader",
        "desc": "You cut your teeth haggling in Kad Luang's gold row.",
        "attrs": {"nerve": 0, "guile": 2, "lore": 0, "hands": 0},
        "baht": 1500,
        "kit": ["jatukham", "ya_dong"],
        "skills": {"charcha": 2, "mahaniyom": 1, "aksorn": 1},
    },
    "runner": {
        "name": "River Runner",
        "desc": "You grew up on the Ping's long-tail boats, hands never still.",
        "attrs": {"nerve": 1, "guile": -1, "lore": 0, "hands": 2},
        "baht": 600,
        "kit": ["takrut", "samun_phrai"],
        # Street-raised: a cook's hands, a charmer's grin, but you can't read.
        "skills": {"khrua": 2, "mahaniyom": 1, "mudra": 1, "aksorn": 0},
    },
}


@dataclass
class Character:
    name: str = "Smuggler"
    background: str = "trader"
    nerve: int = 0
    guile: int = 0
    lore: int = 0
    hands: int = 0
    baht: int = 1000
    heat: int = 0          # 0..10 city-wide suspicion
    stress: int = 0        # 0..9 personal strain; 9 == you break
    health: int = 10       # 0..10 bodily condition; dares dent it, medicine mends it
    location: str = "old_city"
    minutes: int = 8 * 60  # clock, minutes since midnight
    day: int = 1
    inventory: dict[str, int] = field(default_factory=dict)
    worn: list[str] = field(default_factory=list)      # what you carry SHOWN, not stowed
    rep: dict[str, int] = field(default_factory=dict)  # faction -> standing
    skills: dict[str, int] = field(default_factory=dict)   # skill -> rank 0..5
    xp: dict[str, int] = field(default_factory=dict)       # skill -> practice xp
    charms: list[str] = field(default_factory=list)        # crafted guardians
    glamour: int = 0       # charges of "glow-up" social invisibility
    courier_ready: bool = False  # riders standing by to run your next gate for you
    luck: int = 0          # the day's hidden tilt (+1/0/-1); set each dawn by omen
    omen: str = ""         # key of the dawn omen the city handed you today
    hunch: str = ""        # a 2-digit number that "came to you" — pulls at the lottery
    dressed_today: bool = False  # wore the day's lucky colour to court fortune (1/day)
    tickets: list[dict] = field(default_factory=list)  # held lottery tickets
    projects: dict[str, int] = field(default_factory=dict) # baht into big works
    market: dict[str, float] = field(default_factory=dict)  # "district|item" -> price pressure
    # --- the relationship spine ------------------------------------------
    contacts: list[str] = field(default_factory=list)        # keys you've met
    bonds: dict[str, int] = field(default_factory=dict)      # key -> -3..5
    contact_seen: dict[str, int] = field(default_factory=dict)  # key -> last day
    secrets_heard: list[str] = field(default_factory=list)   # keys whose secret you hold
    wants_met: list[str] = field(default_factory=list)       # keys whose want you fulfilled
    story: dict = field(default_factory=dict)                # narrative arc: act, beats, ending
    festivals_seen: dict[str, int] = field(default_factory=dict)  # festival key -> last day joined
    hearts_seen: list[str] = field(default_factory=list)     # "contact:threshold" scenes witnessed
    words: list[str] = field(default_factory=list)          # trade vocabulary you've picked up
    noticing: dict = field(default_factory=dict)            # the unmarked opening: see noticing.py
    perceived: int = 0                                      # what the city believes you're worth
    works: dict[str, int] = field(default_factory=dict)     # baht sunk into great works
    cursed: dict = field(default_factory=dict)              # Suan Prung's ledger: see curse.py
    roads: dict = field(default_factory=dict)               # stretches you've sealed: see roads.py
    moat: dict = field(default_factory=dict)                # whether the ring is dry. see roads.py
    observations: list = field(default_factory=list)        # hours seen, for the atlas: contribute.py
    opening: dict = field(default_factory=dict)             # first-days beats already had
    # --- the pile and its rail -------------------------------------------
    # `baht` above is the pocket — what shops and bribes actually take.
    # `reserve` is the pile, wherever you've bound it. See rails.py.
    difficulty: str = "medium"       # scales the defence burden on wealth only
    rail: str = "cash"               # cash | crypto | foreign | thai_bank
    reserve: int = 0                 # what sits on the rail
    rail_grind: int = 0              # baht still owed to a cold rail
    rail_frozen: bool = False        # today's hazard has the rail shut
    rails_open: list[str] = field(default_factory=list)    # rails you may bind to
    rails_burned: list[str] = field(default_factory=list)  # rails you busted out of

    # --- helpers ----------------------------------------------------------
    def mod(self, attr: str) -> int:
        return int(getattr(self, attr))

    def skill(self, key: str) -> int:
        return self.skills.get(key, 0)

    def add_item(self, key: str, n: int = 1) -> None:
        self.inventory[key] = self.inventory.get(key, 0) + n
        if self.inventory[key] <= 0:
            self.inventory.pop(key, None)
            if key in self.worn:      # can't show what you no longer hold
                self.worn.remove(key)

    def has(self, key: str, n: int = 1) -> bool:
        return self.inventory.get(key, 0) >= n

    def wear(self, key: str) -> bool:
        """Show a carried thing openly. Returns False if you don't hold it."""
        if not self.has(key):
            return False
        if key not in self.worn:
            self.worn.append(key)
        return True

    def stow(self, key: str) -> bool:
        """Hide a shown thing away. Returns False if it wasn't shown."""
        if key in self.worn:
            self.worn.remove(key)
            return True
        return False

    def is_worn(self, key: str) -> bool:
        return key in self.worn

    def carried_heat(self) -> int:
        """Total customs risk currently on your person."""
        from .items import get
        return sum(get(k).heat * n for k, n in self.inventory.items())

    def add_stress(self, n: int) -> None:
        self.stress = max(0, min(9, self.stress + n))

    def add_heat(self, n: int) -> None:
        self.heat = max(0, min(10, self.heat + n))

    def add_health(self, n: int) -> None:
        self.health = max(0, min(10, self.health + n))

    def to_dict(self) -> dict:
        return {
            "name": self.name, "background": self.background,
            "nerve": self.nerve, "guile": self.guile,
            "lore": self.lore, "hands": self.hands,
            "baht": self.baht, "heat": self.heat, "stress": self.stress,
            "health": self.health,
            "location": self.location, "minutes": self.minutes, "day": self.day,
            "inventory": self.inventory, "worn": self.worn, "rep": self.rep,
            "skills": self.skills, "xp": self.xp, "charms": self.charms,
            "glamour": self.glamour, "courier_ready": self.courier_ready,
            "luck": self.luck, "omen": self.omen, "hunch": self.hunch,
            "dressed_today": self.dressed_today, "tickets": self.tickets,
            "projects": self.projects,
            "market": self.market,
            "contacts": self.contacts, "bonds": self.bonds,
            "contact_seen": self.contact_seen,
            "secrets_heard": self.secrets_heard, "wants_met": self.wants_met,
            "story": self.story, "festivals_seen": self.festivals_seen,
            "hearts_seen": self.hearts_seen, "words": self.words,
            "noticing": self.noticing, "perceived": self.perceived,
            "works": self.works, "cursed": self.cursed,
            "roads": self.roads, "moat": self.moat,
            "observations": self.observations, "opening": self.opening,
            "difficulty": self.difficulty, "rail": self.rail,
            "reserve": self.reserve, "rail_grind": self.rail_grind,
            "rail_frozen": self.rail_frozen,
            "rails_open": self.rails_open, "rails_burned": self.rails_burned,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Character":
        # Saves made before a field existed simply take its default.
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def create(cls, name: str, background: str) -> "Character":
        bg = BACKGROUNDS[background]
        c = cls(name=name, background=background, baht=bg["baht"])
        for a, v in bg["attrs"].items():
            setattr(c, a, v)
        for key in bg["kit"]:
            c.add_item(key)
        c.skills = dict(bg.get("skills", {}))
        return c
