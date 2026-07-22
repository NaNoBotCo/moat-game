"""Contraband: amulets (phra khrueang) and potions (ya).

All amulet lineages named here are real Thai devotional objects documented well
before 2007, and the spirit-lore invoked around them — Luang Phu Thuat's shield
against an untimely death, the ruesi's wicha rolled into a takrut, the Pu Sae–Ya
Sae ogre-guardians of the mountain herbs — is drawn from documented Northern
Thai belief, not invention. Legality/heat values are game constructs for 2076
Chiang Mai, where export of consecrated antiquities and unlicensed brews is
controlled at the moat gates.

  base_price : fair market value in baht
  heat       : how much a customs scan flags it (0 clean .. 3 red-hot)
  bulk       : how hard it is to conceal (feeds Hands checks)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    key: str
    name: str
    kind: str            # "amulet" or "potion"
    base_price: int
    heat: int            # customs risk 0..3
    bulk: int            # concealment difficulty 0..3
    note: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


# --- Amulets: real lineages, historically grounded ------------------------
AMULETS: dict[str, Item] = {
    "phra_rod": Item(
        "phra_rod", "Phra Rod of Lamphun", "amulet",
        base_price=9000, heat=3, bulk=0,
        note="Clay votive from Wat Mahawan, Lamphun. Among the oldest revered "
             "amulets in the north; a genuine one is a controlled antiquity.",
        tags=("antique", "northern", "protective"),
    ),
    "phra_somdej": Item(
        "phra_somdej", "Phra Somdej", "amulet",
        base_price=6500, heat=2, bulk=0,
        note="The 'king of amulets', tied to Somdej To of Bangkok. Endless "
             "fakes; provenance is everything.",
        tags=("classic", "prestige", "protective"),
    ),
    "luang_phu_thuat": Item(
        "luang_phu_thuat", "Luang Phu Thuat", "amulet",
        base_price=3200, heat=1, bulk=0,
        note="The monk who 'walked on water'. His bearer, the belief runs, cannot "
             "die a violent or untimely death — which is why runners of the night "
             "roads pay triple, and a scanner reads only the metal.",
        tags=("protective", "travel"),
    ),
    "khun_paen": Item(
        "khun_paen", "Phra Khun Paen", "amulet",
        base_price=2800, heat=1, bulk=0,
        note="Charm of charisma and attraction, from the Ayutthaya folk epic. "
             "Sells fast in the night market.",
        tags=("charm", "metta"),
    ),
    "jatukham": Item(
        "jatukham", "Jatukham Rammathep", "amulet",
        base_price=1500, heat=1, bulk=1,
        note="The Nakhon Si Thammarat medallion whose 2006-07 craze minted and "
             "then broke fortunes. Volatile — buy the hype, dump before it dies.",
        tags=("wealth", "speculative", "bubble"),
    ),
    "khruba_srivichai": Item(
        "khruba_srivichai", "Khruba Srivichai medallion", "amulet",
        base_price=4000, heat=2, bulk=0,
        note="The saint of Lanna (1878-1939) who raised the road up Doi Suthep "
             "in 1935 with volunteer hands. His likeness is the north's own "
             "protector — merit cast in metal.",
        tags=("northern", "merit", "protective", "monastic"),
    ),
    "phra_khong": Item(
        "phra_khong", "Phra Khong of Lamphun", "amulet",
        base_price=5000, heat=2, bulk=0,
        note="One of Hariphunchai's classic votive set beside the Phra Rod. "
             "Kiln-fired clay, a thousand years old, and just as controlled.",
        tags=("antique", "northern", "protective"),
    ),
    "phra_bang": Item(
        "phra_bang", "Phra Bang of Lamphun", "amulet",
        base_price=4500, heat=2, bulk=0,
        note="Another of the old Lamphun set — smaller, seated, serene. "
             "Collectors chase the whole family; a matched pair fetches a premium.",
        tags=("antique", "northern", "protective"),
    ),
    "phra_kring": Item(
        "phra_kring", "Phra Kring", "amulet",
        base_price=5500, heat=2, bulk=1,
        note="A cast bronze Buddha of Bhaisajyaguru with a tiny ball sealed "
             "inside; shake it and it rings. Prized for healing — and for the "
             "sound that proves it whole.",
        tags=("healing", "prestige", "protective"),
    ),
    "salika": Item(
        "salika", "Salika Lin Thong", "amulet",
        base_price=2200, heat=1, bulk=0,
        note="The golden-tongued myna charm: metta and a silver tongue. Traders "
             "and touts swear by it. Carry one and doors open a little wider.",
        tags=("charm", "metta", "silver_tongue"),
    ),
    "takrut": Item(
        "takrut", "Takrut Scroll", "amulet",
        base_price=1200, heat=1, bulk=0,
        note="A rolled metal yantra scroll, the yant drawn in old khom letters by "
             "a ruesi's hand. Easy to hide in a belt or hem — and a scanner reads "
             "the foil, never the wicha rolled inside.",
        tags=("yantra", "concealable"),
    ),
}

# --- Potions: traditional ya, plus lightly-altered 2076 brews -------------
POTIONS: dict[str, Item] = {
    "ya_dong": Item(
        "ya_dong", "Ya Dong (herbal liquor)", "potion",
        base_price=400, heat=1, bulk=2,
        note="Roadside roots-and-spirits tonic. Bulky bottles, mild scrutiny.",
        tags=("tonic", "common"),
    ),
    "ya_hom": Item(
        "ya_hom", "Ya Hom (herbal inhalant)", "potion",
        base_price=250, heat=0, bulk=0,
        note="Fragrant powder for faintness and nausea. Utterly ordinary — good "
             "camouflage packed beside hotter goods.",
        tags=("remedy", "cover"),
    ),
    "samun_phrai": Item(
        "samun_phrai", "Samun Phrai bundle", "potion",
        base_price=600, heat=0, bulk=1,
        note="Fresh medicinal-herb bundle from the Doi Suthep slopes, gathered "
             "where the old ogre-guardians Pu Sae and Ya Sae are still fed each "
             "year. Half medicine, half a ruesi's herbcraft.",
        tags=("herb", "raw"),
    ),
    "miang": Item(
        "miang", "Miang (fermented tea)", "potion",
        base_price=150, heat=0, bulk=1,
        note="Pickled tea leaves from the hills — chewed, offered, and once the "
             "very currency of the northern trails. Utterly legal, endlessly "
             "useful cover for what travels beside it.",
        tags=("trade", "common", "cover"),
    ),
    "ya_dong_black": Item(
        "ya_dong_black", "Black-Label Ya Dong", "potion",
        base_price=2400, heat=3, bulk=2,
        note="A 2076 gilded brew — potent, unlicensed, and exactly what the "
             "gate scanners are calibrated for.",
        tags=("tonic", "unlicensed", "potent"),
    ),
    "doi_brew": Item(
        "doi_brew", "Suthep Clarity Brew", "potion",
        base_price=1800, heat=2, bulk=1,
        note="Monastery nootropic infusion, distilled by a ruesi's recipe and "
             "quietly traded since the '60s. Drinkers swear the clarity is the "
             "hermit-sage lending them his eyes. Legal to drink, illegal in "
             "quantity.",
        tags=("nootropic", "monastic"),
    ),
}

# --- Food: the great social lubricant -------------------------------------
FOODS: dict[str, Item] = {
    "pad_krapow": Item(
        "pad_krapow", "Pad Krapow", "food",
        base_price=80, heat=0, bulk=1,
        note="Holy-basil stir-fry over rice with a runny egg. Made well, it is "
             "the most persuasive thing in Thailand. A worthy offering.",
        tags=("food", "offering", "morale"),
    ),
    "khao_soi": Item(
        "khao_soi", "Khao Soi", "food",
        base_price=120, heat=0, bulk=1,
        note="Chiang Mai's own: curried coconut broth, soft egg noodles under a "
             "crown of crisp ones, shallot and lime and pickled mustard. The "
             "north's finest bribe against a hard heart.",
        tags=("food", "offering", "morale", "northern"),
    ),
    "sai_ua": Item(
        "sai_ua", "Sai Ua", "food",
        base_price=100, heat=0, bulk=1,
        note="Northern herb sausage — lemongrass, kaffir lime, chilli, coiled "
             "and grilled. Travels well, shares easily, and buys goodwill at "
             "any bus yard.",
        tags=("food", "offering", "morale", "northern"),
    ),
}

# Foods usable as an offering, and the persuasion bonus each carries.
OFFERINGS: dict[str, int] = {"khao_soi": 3, "pad_krapow": 2, "sai_ua": 2}

ALL_ITEMS: dict[str, Item] = {**AMULETS, **POTIONS, **FOODS}


def get(key: str) -> Item:
    return ALL_ITEMS[key]
