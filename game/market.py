"""Markets: what each district buys and sells, and how price flexes.

Two forces set a price. A **stable daily drift** (seeded on the day + district)
makes the world feel alive while keeping a given day consistent, and rewards
moving goods across the moat: amulets fetch more at the tourist-facing Night
Bazaar, herbs are cheap at their Doi Suthep source, the Jatukham bubble is
priced to burst. On top of that sits **your own price pressure**: every unit you
sell into a stall gluts it and drops the price; every unit you buy corners it and
lifts the price. Pressure is remembered per district+item on the player and heals
toward zero each dawn, so dumping your whole bag in one place is a bad idea and
timing a return trip is a real decision.

The model never prints. `buy`/`sell` mutate the player and the market and return
a list of `Event`s; a renderer turns those into words.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .events import Event, ev
from .items import ALL_ITEMS, AMULETS, POTIONS, Item

# How hard one unit traded shoves the local price, and the band it can move in.
IMPACT_PER_UNIT = 0.05
PRESSURE_CAP = 0.6
DAILY_HEAL = 0.6          # fraction of pressure that remains after a night
PRESSURE_FLOOR = 0.02     # below this, forget it

# Two forces that bend prices around *who you are*, not just what you carry.
# 1) Heat: a smuggler the whole city is watching is a liability. Fences lowball
#    a hot seller — so heat is a running tax on every baht you cash out.
HEAT_SELL_PENALTY = 0.03  # sell price shaved per point of city heat
HEAT_SELL_CAP = 0.30      # ...never more than this much
# 2) A well-kept fence works their own floor in your favour: better sell, kinder
#    buy. Bonds you cultivate become money.
FENCE_PER_BOND = 0.04
# Kept below the tightest fence-district spread (Warorot 0.18) so a favour can
# never push sell above buy at the same stall — no free-money loop.
FENCE_CAP = 0.15
# Which contact's favour sweetens which district's floor (their boons say so).
FENCE_BOONS = {
    "warorot": "lawan",      # Pa Lawan — better prices on the Warorot floor
    "wualai": "naruemon",    # Naruemon — silver and small charms in Wualai
}

# Each dawn settles a small account. A flat ALLOWANCE lands (a household
# remittance) so you're never forced to grind just to eat; against it runs your
# cost of living — a floor (room, rice) plus a slice of your net worth, because
# a growing stash and a fat purse cost more to keep safe and quiet. Early on the
# allowance covers you; get rich and upkeep bites, so coin must keep moving.
ALLOWANCE = 120
UPKEEP_BASE = 80
UPKEEP_WEALTH_RATE = 0.005   # per-day cost as a fraction of everything you hold


@dataclass
class Listing:
    item: Item
    buy: int    # price you pay to buy here
    sell: int   # price you get selling here
    drift: float = 0.0   # your standing pressure on this price (-cap..+cap)


# Which districts run a market, and their demand character.
MARKET_PROFILES: dict[str, dict] = {
    # The gate of the dead. Nobody decent will trade here, so the spread is the
    # narrowest in the city and nobody asks a single question. See curse.py.
    "suan_prung": {
        "name": "Under the arch at Suan Prung",
        "stock": list(AMULETS) + ["ya_dong_black", "ya_dong", "samun_phrai",
                                  "takrut"],
        "demand": {"amulet": 0.78, "potion": 0.8},   # buy cheap here
        "spread": 0.06,                              # and the house barely cuts
    },
    "warorot": {
        "name": "Kad Luang guild floor",
        "stock": list(AMULETS) + ["ya_dong", "samun_phrai", "doi_brew", "miang"],
        "demand": {"amulet": 1.05, "potion": 1.0, "food": 1.0},
        "spread": 0.18,   # buy/sell gap (the house's cut)
    },
    "night_bazaar": {
        "name": "Chang Klan buyers",
        "stock": ["khun_paen", "takrut", "jatukham", "salika",
                  "khruba_srivichai", "ya_dong", "ya_dong_black"],
        "demand": {"amulet": 1.35, "potion": 1.1},  # tourists pay for a story
        "spread": 0.22,
    },
    "doi_suthep": {
        "name": "Monastery stalls",
        "stock": ["luang_phu_thuat", "khruba_srivichai", "phra_kring",
                  "samun_phrai", "ya_hom", "doi_brew"],
        "demand": {"amulet": 0.9, "potion": 0.7},   # cheap herbs at the source
        "spread": 0.12,
    },
    "kad_chang_phuak": {
        "name": "Kad Chang Phuak food stalls",
        "stock": ["khao_soi", "sai_ua", "pad_krapow", "miang", "samun_phrai",
                  "ya_hom"],
        "demand": {"food": 0.75, "potion": 0.95},   # cheap food at the source
        "spread": 0.10,
    },
    "wualai": {
        "name": "Wualai Saturday market",
        "stock": ["khruba_srivichai", "phra_kring", "salika", "takrut",
                  "jatukham", "khao_soi"],
        "demand": {"amulet": 1.25, "food": 1.2},    # weekend buyers, silver crowd
        "spread": 0.20,
    },
    "nimman": {
        "name": "Nimman & CMU stalls",
        "stock": ["salika", "khun_paen", "khruba_srivichai", "doi_brew",
                  "khao_soi", "sai_ua"],
        "demand": {"amulet": 1.2, "potion": 1.3, "food": 1.15},  # students, cafés
        "spread": 0.19,
    },
}


# --- your standing pressure on local prices ---------------------------------
def _pkey(district: str, key: str) -> str:
    return f"{district}|{key}"


def pressure(state: dict | None, district: str, key: str) -> float:
    if not state:
        return 0.0
    return state.get(_pkey(district, key), 0.0)


def _nudge(state: dict, district: str, key: str, delta: float) -> None:
    p = max(-PRESSURE_CAP, min(PRESSURE_CAP,
                               pressure(state, district, key) + delta))
    if abs(p) < PRESSURE_FLOOR:
        state.pop(_pkey(district, key), None)
    else:
        state[_pkey(district, key)] = p


def settle(state: dict) -> None:
    """A night's healing: local prices drift back toward their natural level."""
    for k in list(state):
        p = state[k] * DAILY_HEAL
        if abs(p) < PRESSURE_FLOOR:
            del state[k]
        else:
            state[k] = p


# --- pricing ----------------------------------------------------------------
def _day_seed(day: int, district: str) -> random.Random:
    return random.Random(f"{day}:{district}")


def _flux(day: int, district: str, item: Item) -> float:
    r = _day_seed(day, district + item.key)
    base = r.uniform(0.85, 1.18)
    if "bubble" in item.tags:
        # Jatukham: wild daily swing, trending down over the run.
        base *= r.uniform(0.6, 1.6) * max(0.5, 1.15 - 0.03 * day)
    return base


# Market floors open and shut on the watch. Which watch is deterministic per
# floor, so the city's hours are stable forever and learnable — that is the
# whole point of them. See game/coucal.py.
MARKET_WATCHES = 3          # nine hours: a working day, on the bird's clock


def market_window(district: str) -> tuple[int, int]:
    from . import coucal
    return coucal.span(f"market:{district}", MARKET_WATCHES)


def market_open(district: str, minutes: int) -> bool:
    from . import coucal
    if district not in MARKET_PROFILES:
        return False
    return coucal.open_at(market_window(district), minutes)


def price_mods(pc, district: str) -> tuple[int, float]:
    """How *who you are* bends this floor's prices right now.

    Returns (heat, fence): the smuggler's city heat (a sell-side tax) and a
    >=0 sweetener earned from a fence who works this district and trusts you.
    """
    heat = max(0, getattr(pc, "heat", 0))
    fence = 0.0
    who = FENCE_BOONS.get(district)
    if who:
        bond = pc.bonds.get(who, 0)
        if bond > 0:
            fence = min(FENCE_CAP, bond * FENCE_PER_BOND)
    return heat, fence


def listings(district: str, day: int, state: dict | None = None,
             heat: int = 0, fence: float = 0.0) -> list[Listing]:
    prof = MARKET_PROFILES.get(district)
    if not prof:
        return []
    heat_pen = min(HEAT_SELL_CAP, max(0, heat) * HEAT_SELL_PENALTY)
    out: list[Listing] = []
    for key in prof["stock"]:
        item = ALL_ITEMS[key]
        demand = prof["demand"].get(item.kind, 1.0)
        flux = _flux(day, district, item)
        p = pressure(state, district, key)
        mid = item.base_price * demand * flux * (1 + p)
        spread = prof["spread"]
        buy = mid * (1 + spread) * (1 - fence)
        sell = mid * (1 - spread) * (1 + fence) * (1 - heat_pen)
        out.append(Listing(
            item=item,
            buy=max(1, round(buy)),
            sell=max(1, round(sell)),
            drift=p,
        ))
    return out


def find_listing(district: str, day: int, key: str, state: dict | None = None,
                 heat: int = 0, fence: float = 0.0) -> Listing | None:
    for lst in listings(district, day, state, heat, fence):
        if lst.item.key == key:
            return lst
    return None


# --- trading: mutate the world, return events (never print) -----------------
def buy(pc, district: str, key: str, qty: int, day: int) -> list[Event]:
    prof = MARKET_PROFILES.get(district)
    if not prof:
        return [ev("market_none")]
    heat, fence = price_mods(pc, district)
    lst = find_listing(district, day, key, pc.market, heat, fence)
    if not lst:
        return [ev("not_sold_here", key=key)]
    if qty <= 0:
        qty = 1
    # Stallholders charge what they think you can pay. Being read as rich is a
    # tax on everything you buy for the rest of your life.
    from . import roads, wealth, works
    unit = int(round(lst.buy * wealth.price_multiplier(pc)
                     * works.price_factor(pc) * roads.price_factor(pc)))
    lst = Listing(lst.item, unit, lst.sell, lst.drift)
    cost = lst.buy * qty
    if cost > pc.baht:
        afford = pc.baht // lst.buy
        return [ev("cant_afford", name=lst.item.name, can=afford, want=qty,
                   unit=lst.buy)]
    pc.baht -= cost
    pc.add_item(key, qty)
    _nudge(pc.market, district, key, IMPACT_PER_UNIT * qty)
    new = find_listing(district, day, key, pc.market, heat, fence)
    return [ev("bought", name=lst.item.name, qty=qty, cost=cost, unit=lst.buy,
               baht=pc.baht, new_buy=new.buy if new else lst.buy)]


def sell(pc, district: str, key: str, qty: int, day: int) -> list[Event]:
    prof = MARKET_PROFILES.get(district)
    if not prof:
        return [ev("market_none")]
    if qty <= 0:
        qty = 1
    have = pc.inventory.get(key, 0)
    if have < qty:
        return [ev("not_enough", have=have, want=qty)]
    heat, fence = price_mods(pc, district)
    lst = find_listing(district, day, key, pc.market, heat, fence)
    if not lst:
        return [ev("no_buyer_here", key=key)]
    # Anyone who can read an amulet can read what came through the gate with it.
    from . import curse
    factor = curse.value_factor(pc, key)
    if factor != 1.0:
        lst = Listing(lst.item, lst.buy, int(round(lst.sell * factor)), lst.drift)
    gain = lst.sell * qty
    pc.baht += gain
    pc.add_item(key, -qty)
    _nudge(pc.market, district, key, -IMPACT_PER_UNIT * qty)
    new = find_listing(district, day, key, pc.market, heat, fence)
    return [ev("sold", name=lst.item.name, qty=qty, gain=gain, unit=lst.sell,
               baht=pc.baht, new_sell=new.sell if new else lst.sell)]


# --- the recurring sink: a day in the city costs money ----------------------
def holdings_value(pc) -> int:
    """Everything you're worth right now: coin plus the market value of your bag."""
    stash = sum(ALL_ITEMS[k].base_price * n for k, n in pc.inventory.items()
                if k in ALL_ITEMS)
    return pc.baht + stash


def daily_upkeep(pc) -> list[Event]:
    """Settle a day's allowance against a wealth-scaled cost of living.

    Short of coin to cover the gap, you go without and strain (+1 stress).
    """
    upkeep = UPKEEP_BASE + round(holdings_value(pc) * UPKEEP_WEALTH_RATE)
    net = ALLOWANCE - upkeep
    if pc.baht + net >= 0:
        pc.baht += net
        return [ev("upkeep", allowance=ALLOWANCE, upkeep=upkeep, net=net,
                   baht=pc.baht)]
    short = -(pc.baht + net)
    pc.baht = 0
    pc.add_stress(1)
    return [ev("upkeep_short", allowance=ALLOWANCE, upkeep=upkeep, short=short,
               baht=0)]
