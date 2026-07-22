"""Game loop: parsing, presentation, and the flow of a day in the old city."""

from __future__ import annotations

import random
import textwrap

from . import (checkpoint, clock, festivals, lottery, luck, market, persuasion,
               relationships, save, skills, story)
from .character import ATTR_BLURB, ATTRS, BACKGROUNDS, Character
from .dice import Outcome, roll
from .items import OFFERINGS, get
from .world import (DISTRICTS, TRAIN_NORTH_GOAL, neighbors, region_of,
                    routes_from)

WRAP = 76


def _p(text: str = "") -> None:
    for para in text.split("\n"):
        if not para:
            print()
        else:
            print(textwrap.fill(para, WRAP))


def _clock(pc: Character) -> str:
    return (f"Day {pc.day} \u00b7 {festivals.weekday_name(pc.day)} "
            f"\u00b7 {clock.label(pc.minutes)}")


def _bar(label: str, value: int, cap: int) -> str:
    filled = "#" * value + "." * (cap - value)
    return f"{label:<7}[{filled}] {value}/{cap}"


class Game:
    def __init__(self, pc: Character, rng: random.Random | None = None):
        self.pc = pc
        self.rng = rng or random.Random()
        self.running = True
        self.lottery = None   # transient: a ticket-seller working the lane right now

    # --- time & upkeep ----------------------------------------------------
    def advance(self, minutes: int) -> None:
        pc = self.pc
        prev_day = pc.day
        pc.minutes += minutes
        while pc.minutes >= 24 * 60:
            pc.minutes -= 24 * 60
            pc.day += 1
        if pc.day > prev_day:
            # A new dawn cools the city and rests the smuggler a little.
            pc.add_heat(-(pc.day - prev_day))
            pc.add_stress(-(pc.day - prev_day))
            pc.add_health(pc.day - prev_day)   # a dented body mends with rest
            for line in luck.roll_day(pc, self.rng):   # the day's omen & hidden tilt
                _p(line)
            for line in lottery.settle(pc, self.rng):  # any lottery draw now landed
                _p(line)
            market.settle(pc.market)
            for _ in range(pc.day - prev_day):
                self._render(market.daily_upkeep(pc))
            for note in relationships.daily_decay(pc, pc.day):
                _p(note)
            self._announce_festivals()
            note = story.deadline_note(pc)
            if note:
                _p(note)
            for line in story.advance(pc):
                _p(line)

        # A lottery seller might drift up out of the lane while time passes.
        # (Transient — they walk on when you move.) Only if a draw's still coming
        # and you've the baht to be worth their while.
        if (self.lottery is None and pc.baht >= 80
                and lottery.next_draw(pc.day) is not None
                and self.rng.random() < 0.14):
            self.lottery = lottery.appear(pc, self.rng)

    def _announce_festivals(self) -> None:
        """At each dawn, name any festival today and nudge one on the horizon."""
        pc = self.pc
        for f in festivals.on_day(pc.day):
            where = DISTRICTS[f.where].name if f.where else "the temples"
            _p(f"\u273f Today is {f.name} \u2014 at {where}. ({f.boon})")
        soon = festivals.upcoming(pc.day, within=2)
        if soon:
            d, f = soon[0]
            when = "Tomorrow" if d == 1 else f"In {d} days"
            _p(f"  {when}: {f.name}.")

    # --- rendering --------------------------------------------------------
    def look(self) -> None:
        d = DISTRICTS[self.pc.location]
        _p(f"== {d.name} ==")
        _p(d.blurb)
        if d.features:
            _p("Here: " + ", ".join(d.features))
        for f in festivals.here_now(d.key, self.pc.day):
            _p("")
            _p(f"\u273f {f.name} is on here today. {f.blurb} ('celebrate' to join.)")
        met = relationships.auto_meet(self.pc, d.key, self.pc.day)
        for c in met:
            _p(f"You fall into talk with {c.name} — {c.heritage}.")
        known_here = relationships.here(self.pc, d.key)
        if known_here:
            _p("People here: " + ", ".join(
                f"{c.name} ({relationships.tier(relationships.bond_of(self.pc, c.key))})"
                for c in known_here))
        exits = neighbors(d.key)
        if exits:
            _p("")
            _p("Ways out:")
            for i, e in enumerate(exits, 1):
                tag = "  [MOAT GATE — customs]" if e.crossing else ""
                print(f"  {i}. {DISTRICTS[e.to].name} ({e.minutes}m){tag}")
        if clock.is_night(self.pc.minutes):
            _p("")
            _p("It's deep night; most doors are shut and most people abed. "
               "'sleep' to end the day.")

    def status(self) -> None:
        pc = self.pc
        _p(f"== {pc.name} — {BACKGROUNDS[pc.background]['name']} ==")
        print(f"  {_clock(pc)}   Location: {DISTRICTS[pc.location].name}")
        print(f"  Baht: {pc.baht:,}")
        print("  " + "   ".join(f"{a.title()} {pc.mod(a):+d}" for a in ATTRS))
        print("  " + _bar("Heat", pc.heat, 10))
        print("  " + _bar("Stress", pc.stress, 9))
        print("  " + _bar("Health", pc.health, 10))
        carried = pc.carried_heat()
        if carried:
            print(f"  Carrying heat: {carried} (customs risk on your person)")
        print("  " + luck.status_line(pc))
        if pc.tickets:
            tails = ", ".join(f"{t['tail']} (day {t['draw_day']})"
                              for t in pc.tickets)
            print(f"  Lottery held: {tails}")

    def inventory(self) -> None:
        pc = self.pc
        if not pc.inventory:
            _p("Your bag is empty.")
            return
        _p("== Carrying ==")
        for key, n in pc.inventory.items():
            it = get(key)
            state = "shown" if pc.is_worn(key) else "stowed"
            print(f"  {n}x {it.name}  [{state}]  (~{it.base_price:,}฿, "
                  f"heat {it.heat}, bulk {it.bulk})")
        _p("")
        _p("'wear <name>' to show a thing openly, 'stow <name>' to hide it. At the "
           "gate a shown pilgrim's amulet reassures — a shown hot antiquity damns "
           "you. Some wicha only works hidden.")

    def wear_item(self, arg: str) -> None:
        pc = self.pc
        key = self._resolve_item_name(arg)
        if not key or not pc.has(key):
            _p("You're not carrying that.")
            return
        it = get(key)
        if pc.is_worn(key):
            _p(f"You're already showing the {it.name}.")
            return
        pc.wear(key)
        _p(f"You wear the {it.name} openly now.")
        note = checkpoint.GATE_CARRY.get(key)
        if note and note.shown_note:
            _p("At a gate: " + note.shown_note)
        elif it.heat >= 2:
            _p("At a gate: this is the sort of thing customs hunts for — showing "
               "it invites a hard look.")

    def stow_item(self, arg: str) -> None:
        pc = self.pc
        key = self._resolve_item_name(arg)
        if not key or not pc.has(key):
            _p("You're not carrying that.")
            return
        it = get(key)
        if not pc.is_worn(key):
            _p(f"The {it.name} is already stowed out of sight.")
            return
        pc.stow(key)
        _p(f"You tuck the {it.name} away out of sight.")
        note = checkpoint.GATE_CARRY.get(key)
        if note and note.hidden_note:
            _p("At a gate: " + note.hidden_note)

    def show_market(self) -> None:
        pc = self.pc
        prof = market.MARKET_PROFILES.get(pc.location)
        if not prof:
            _p("No market floor here. Try Warorot, the Night Bazaar, or Doi "
               "Suthep.")
            return
        heat, fence = market.price_mods(pc, pc.location)
        _p(f"== {prof['name']} ==")
        if heat and heat * market.HEAT_SELL_PENALTY > 0:
            pct = round(min(market.HEAT_SELL_CAP, heat * market.HEAT_SELL_PENALTY)
                        * 100)
            _p(f"You're hot (heat {heat}/10) — fences shade your sells down "
               f"~{pct}%. Cool off before you cash out big.")
        if fence:
            who = market.FENCE_BOONS.get(pc.location)
            name = relationships.CONTACTS[who].name if who else "a friend"
            pct = round(fence * 100)
            _p(f"{name}'s favour works this floor: ~{pct}% better prices for you.")
        print(f"  {'Item':<26}{'Buy':>8}{'Sell':>8}  heat")
        for lst in market.listings(pc.location, pc.day, pc.market, heat, fence):
            mark = ("  \u2191 you've cornered this" if lst.drift > 0.05
                    else "  \u2193 you've glutted this" if lst.drift < -0.05
                    else "")
            print(f"  {lst.item.name:<26}{lst.buy:>8,}{lst.sell:>8,}"
                  f"{lst.item.heat:>6}{mark}")
        _p("")
        _p("buy <name> [n] / sell <name> [n]. Your own trades move the price; "
           "it drifts back over the days.")

    def show_map(self) -> None:
        _p("== Chiang Mai — the ring and beyond ==")
        _p("The moat squares the mile-wide old city; its five gates are the only "
           "crossings. Beyond the outer city, the greater Lanna cities lie down "
           "the road or rail.")
        zones = {"inside": "(walled)", "gate": "(gate)",
                 "outside": "(outer)", "city": "(Lanna)"}
        for key, d in DISTRICTS.items():
            zone = zones.get(d.zone, "")
            here = " <- you" if key == self.pc.location else ""
            print(f"  {d.name:<32}{zone}{here}")

    # --- actions ----------------------------------------------------------
    def _resolve_item_name(self, text: str) -> str | None:
        text = text.strip().lower()
        # match by key or by leading words of the display name
        for key, it in ((k, get(k)) for k in
                        set(self.pc.inventory) |
                        set().union(*[set(p["stock"]) for p in
                                      market.MARKET_PROFILES.values()])):
            if text == key or text in it.name.lower():
                return key
        return None

    def go(self, arg: str) -> None:
        pc = self.pc
        exits = neighbors(pc.location)
        target = None
        arg = arg.strip().lower()
        if arg.isdigit():
            i = int(arg) - 1
            if 0 <= i < len(exits):
                target = exits[i]
        else:
            for e in exits:
                if arg in DISTRICTS[e.to].name.lower() or arg == e.to:
                    target = e
                    break
        if not target:
            _p("You can't go there from here. Type 'look' for ways out.")
            return

        self.lottery = None   # any seller here was working this lane, not the next
        if target.crossing:
            self._cross(target)
        else:
            self.advance(target.minutes)
            pc.location = target.to
            _p(f"You make your way to {DISTRICTS[target.to].name}.")
            self.look()

    def _cross(self, edge) -> None:
        pc = self.pc
        dest = DISTRICTS[edge.to].name
        _p(f"You come to the moat gate toward {dest} with a pilgrim's easy smile "
           f"and a kind word ready for the officer. Scanners hum.")
        carried = pc.carried_heat()

        # Aof's riders, arranged in advance, take the load through the back
        # lanes so you walk the gate empty-handed.
        if carried > 0 and pc.courier_ready:
            pc.courier_ready = False
            _p("Aof's riders peel off with your load into the back lanes — a "
               "dozen bikes, a dozen possible routes, and nothing on you but a "
               "smile. You walk through empty-handed; they fall back in beside "
               "you on the far side, the load untouched. The scanner finds "
               "nothing to find.")
            self.advance(edge.minutes)
            pc.location = edge.to
            self.look()
            return

        # A trusted officer on *this* gate eases the scan.
        gate_key = edge.to if DISTRICTS[edge.to].zone == "gate" else pc.location
        friend = relationships.has_boon(pc, "gate", gate_key)
        boon_ease, boon_note = 0, ""
        if friend:
            boon_ease = 2
            boon_note = (f"{friend.name} has the booth in hand — a glance, a "
                         f"small nod, and you're waved into the slow lane where "
                         f"no one looks too hard. (-{boon_ease})")

        if carried == 0:
            res = checkpoint.scan(pc, "bluff", rng=self.rng,
                                  boon_ease=boon_ease, boon_note=boon_note)
        else:
            _p(f"You are carrying heat {carried}. How do you cross?")
            shown = [get(k).name for k in pc.worn if pc.has(k)]
            if shown:
                _p("On show: " + ", ".join(shown) +
                   ".  (Everything else is stowed. 'wear'/'stow' to change before "
                   "you commit.)")
            else:
                _p("Nothing on show — it's all stowed away, discreet and "
                   "unremarkable, nothing to trouble a busy officer.")
            opts = [(f"{k.title()}  ({attr} {pc.mod(attr):+d}) — {desc}", k)
                    for k, (attr, desc) in checkpoint.APPROACHES.items()]
            choice = self._choose(opts, "Cross how")
            if choice is None:
                _p("You lose your nerve and hang back. (no crossing)")
                return
            res = checkpoint.scan(pc, str(choice), rng=self.rng,
                                  boon_ease=boon_ease, boon_note=boon_note)
        for line in res.lines:
            _p(line)
        checkpoint.apply(pc, res)
        self.advance(edge.minutes)
        pc.location = edge.to
        if pc.stress >= 9:
            _p("Your nerves are shot — you need to lie low. (forced rest)")
            self.rest()
        self.look()

    def _render(self, events) -> bool:
        """Turn market Events into words. Returns True if a trade landed."""
        traded = False
        for e in events:
            if e.kind == "market_none":
                _p("No stalls keep a proper floor here — try Warorot, the Night "
                   "Bazaar, or Doi Suthep.")
            elif e.kind == "not_sold_here":
                _p("The stallholder spreads their hands, all smiles. \u201cAiyah, "
                   "that one no have, na. Good choice — but not here. You try other "
                   "market maybe.\u201d")
            elif e.kind == "no_buyer_here":
                _p("\u201cSo nice, so nice — but this one, I cannot do it justice, "
                   "na. Nobody buying that here today, sorry sorry.\u201d")
            elif e.kind == "cant_afford":
                _p(f"The seller keeps smiling, holds the price. \u201c{e.name}, "
                   f"{e.unit:,}\u0e3f each one. Your money enough for {e.can}, not "
                   f"{e.want} — mai pen rai, next time, na.\u201d")
            elif e.kind == "not_enough":
                _p(f"\u201cYou want sell {e.want}? But you have only {e.have} lah. "
                   f"Bring more, we do business.\u201d")
            elif e.kind == "bought":
                move = ("" if e.new_buy == e.unit
                        else f"  (price now {e.new_buy:,}฿ \u2191)")
                _p(f"Bought {e.qty}x {e.name} for {e.cost:,}฿. "
                   f"Baht: {e.baht:,}.{move}")
                _p("  \u201cKhob jai, na \u2014 good choice, good choice.\u201d")
                traded = True
            elif e.kind == "sold":
                move = ("" if e.new_sell == e.unit
                        else f"  (price now {e.new_sell:,}฿ \u2193)")
                _p(f"Sold {e.qty}x {e.name} for {e.gain:,}฿. "
                   f"Baht: {e.baht:,}.{move}")
                _p("  \u201cReep roy, na \u2014 good doing business. You come "
                   "back, we talk again.\u201d")
                traded = True
            elif e.kind == "upkeep":
                sign = "+" if e.net >= 0 else "-"
                _p(f"Dawn accounts: +{e.allowance}฿ allowance, -{e.upkeep:,}฿ "
                   f"upkeep (room, rice, keeping your stash quiet). "
                   f"Net {sign}{abs(e.net):,}฿. Baht: {e.baht:,}.")
            elif e.kind == "upkeep_short":
                _p(f"Your allowance (+{e.allowance}฿) couldn't cover the day's "
                   f"upkeep (-{e.upkeep:,}฿ — a big stash is expensive to keep). "
                   f"You come up {e.short:,}฿ short: go hungry, sleep uneasy. "
                   f"(+1 stress)")
            elif e.kind == "festival_none":
                _p("No festival is on here today. A festival runs only on its own "
                   "day, in its own district — check the 'calendar' for the next "
                   "one and where to be.")
            elif e.kind == "festival_repeat":
                _p(f"You already spent today at {e.name}; joining again does "
                   "nothing. Come back on its next day.")
            elif e.kind == "festival_joined":
                _p(f"\u273f You spend the day at {e.name}.")
                _p(e.lanna)
                if e.warmed:
                    names = ", ".join(n + (f" (now {t})" if t else "")
                                      for n, t in e.warmed)
                    _p(f"Joining deepens your bond with everyone here: {names}.")
                else:
                    _p("You know no one who gathers here, so no bond deepens. "
                       "Meet the people who turn out for this festival, then come "
                       "back — that's when it pays off.")
                _p(f"The day lowers the city's heat on you and eases your stress. "
                   f"({e.heat:+d} heat, {e.stress:+d} stress)")
            elif e.kind == "festival_merit":
                _p(f"You make merit, giving your {e.item} to the monks. That buys "
                   f"extra goodwill: more heat and stress come off. "
                   f"({e.extra_heat:+d} heat, {e.extra_stress:+d} stress)")
            elif e.kind == "festival_merit_none":
                _p("(You could make merit here for extra heat and stress relief, "
                   "but you carry no food offering — bring khao soi, pad krapow, "
                   "or sai ua next time.)")
        return traded

    def buy(self, arg: str, qty: int) -> None:
        pc = self.pc
        key = self._resolve_item_name(arg)
        if not key:
            _p("No such item.")
            return
        events = market.buy(pc, pc.location, key, qty, pc.day)
        if self._render(events):
            self.advance(10)

    def sell(self, arg: str, qty: int) -> None:
        pc = self.pc
        key = self._resolve_item_name(arg)
        if not key:
            _p("No such item.")
            return
        events = market.sell(pc, pc.location, key, qty, pc.day)
        if self._render(events):
            self.advance(10)

    def appraise(self, arg: str) -> None:
        pc = self.pc
        key = self._resolve_item_name(arg)
        if not key or not pc.has(key):
            _p("You need it in hand to appraise it.")
            return
        it = get(key)
        scholar = relationships.has_boon(pc, "appraise")
        if scholar:
            self.advance(10)
            _p(f"You send {scholar.name} a photo of the {it.name}; she reads it "
               f"true and pings you back before you've pocketed your phone.")
            _p(it.note)
            _p(f"Fair value around {it.base_price:,}฿ — no guessing, no fake "
               f"slips past her eye.")
            return
        if not skills.literate(pc):
            self.advance(10)
            _p(f"You turn the {it.name} over, but the inscriptions are just "
               f"marks to you. Without reading (aksorn), you can only guess. "
               f"Rumoured worth {it.base_price:,}฿ — trust it at your peril.")
            return
        rl = roll(pc.mod("lore") + pc.skill("aksorn"), rng=self.rng)
        self.advance(10)
        _p(f"Appraising {it.name}... {rl.describe()}")
        if rl.outcome is Outcome.STRONG:
            _p(it.note)
            _p(f"Fair value around {it.base_price:,}฿. You'd know a fake at a "
               f"glance.")
        elif rl.outcome is Outcome.WEAK:
            _p(it.note)
            _p("You can vouch for the broad strokes, not the fine detail.")
        else:
            _p("You can't get a clean read — could be a masterwork, could be a "
               "temple-market fake. (+1 stress)")
            pc.add_stress(1)

    def rest(self) -> None:
        pc = self.pc
        self.advance(6 * 60)
        pc.add_stress(-3)
        pc.add_heat(-1)
        _p("You lie low for six hours. Your nerves settle and the heat on you "
           "cools. (-3 stress, -1 heat)")

    def sleep(self) -> None:
        """End the day: sleep until the 06:00 dawn, and wake mostly restored."""
        pc = self.pc
        mins = clock.minutes_to_wake(pc.minutes)
        hrs = mins / 60
        _p(f"You bed down and let the day go. ({hrs:.1f}h until dawn.)")
        self.advance(mins)      # crosses midnight — dawn announcements fire here
        pc.add_stress(-3)
        pc.add_heat(-1)
        _p(f"You wake at {clock.label(pc.minutes)}, rested. The night eased your "
           "stress and let the city's heat cool a little. (-3 stress, -1 heat)")

    def rumors(self) -> None:
        d = DISTRICTS[self.pc.location]
        if "rumors" not in d.features and "buyers" not in d.features:
            _p("No one here has anything worth hearing.")
            return
        leads = [
            "Tourists at the Night Bazaar are paying wildly for Khun Paen charms.",
            "The guild at Warorot moves amulets quiet — better spread than the "
            "street.",
            "Doi Suthep's monks bless herbs cheap; carry them down before dawn.",
            "Jatukham's cooling off. Whatever you're holding, sell before it's "
            "worthless.",
            "Suan Prung gate spooks its own officers — the dead-gate. A steady "
            "hand crosses it easier than the busy ones.",
            "Khruba Srivichai medallions move best up his own mountain, or to the "
            "CMU crowd who romance the old saint.",
            "The Lamphun set — Phra Rod, Phra Khong, Phra Bang — a matched trio "
            "pays a collector far more than the sum of three sales.",
            "Wualai on a Saturday is all silver and sightseers; a good charm "
            "sells itself in that crush.",
            "Carry a Salika and even customs warms to you — the golden tongue "
            "works both ways.",
            "Chang Phuak gate barely scans past midnight, and the khao kha moo "
            "queue at Kad Chang Phuak hides a hundred pairs of eyes.",
        ]
        self.advance(15)
        _p("You buy a coffee and listen. Word is:")
        # Half the time, surface a lead tied to the mystery you're chasing.
        lead = story.street_lead(self.pc)
        if lead and self.rng.random() < 0.6:
            _p("  \u2022 " + lead)
        else:
            _p("  \u2022 " + self.rng.choice(leads))

    # --- skills & literacy ------------------------------------------------
    def show_skills(self) -> None:
        pc = self.pc
        _p("== Skills ==  (rank 0-5; practice to grow, teachers for the deep ranks)")
        for key, (name, blurb, attr) in skills.SKILLS.items():
            rank = pc.skill(key)
            nxt = skills.xp_to_next(pc.xp.get(key, 0))
            prog = f"  (+{nxt} practice to rank {rank + 1})" if nxt else "  (maxed)"
            print(f"  {name:<26} rank {rank}/5   [{attr}]{prog}")
            print(f"      {blurb}")
        if pc.charms:
            _p("Charms carried: " + ", ".join(pc.charms))
        if not skills.literate(pc):
            _p("You cannot yet read the old script. Learn 'aksorn' to unlock "
               "true appraisal, crafting, and safe contracts.")

    def practice(self, arg: str) -> None:
        pc = self.pc
        key = arg.strip().lower()
        if key not in skills.SKILLS:
            _p("Practice which? " + ", ".join(skills.SKILLS))
            return
        feats = DISTRICTS[pc.location].features
        ok, why = skills.can_practice(pc, key, feats)
        if not ok:
            _p(why)
            return
        attr = skills.SKILLS[key][2]
        teaching = skills.teacher_here(feats, key)
        self.advance(120)
        rl = roll(pc.mod(attr) + (2 if teaching else 0), rng=self.rng)
        _p(f"You drill {skills.SKILLS[key][0]}"
           + (" under a teacher's eye." if teaching else ".") + f" {rl.describe()}")
        gain = 2 if rl.outcome is Outcome.STRONG else 1 if rl.outcome is Outcome.WEAK else 0
        if gain == 0:
            _p("It won't come together today.")
            return
        up = skills.gain_xp(pc, key, gain)
        if up is not None:
            _p(f"Breakthrough — {skills.SKILLS[key][0]} rises to rank {up}!")
        else:
            _p("Progress made.")

    def learn(self, arg: str) -> None:
        # 'learn' is just practice, but reads better at a monastery/teacher.
        self.practice(arg)

    # --- signature actions ------------------------------------------------
    def _take_offering(self) -> int:
        """Consume the best food offering on hand; return its persuasion bonus."""
        pc = self.pc
        best = None
        for key, bonus in OFFERINGS.items():
            if pc.has(key) and (best is None or bonus > best[1]):
                best = (key, bonus)
        if not best:
            return 0
        pc.add_item(best[0], -1)
        _p(f"You set down {get(best[0]).name} as an offering.")
        return best[1]

    _RECIPES = {  # dish -> (khrua rank needed, item key, display, strong bonus)
        "pad_krapow": (0, "pad_krapow", "pad krapow", 1),
        "sai_ua": (1, "sai_ua", "sai ua", 1),
        "khao_soi": (2, "khao_soi", "khao soi", 2),
    }

    def cook(self, arg: str = "") -> None:
        pc = self.pc
        dish = arg.strip().lower().replace(" ", "_") or "pad_krapow"
        if dish not in self._RECIPES:
            _p("You can cook: pad_krapow, sai_ua, khao_soi.")
            return
        need, key, label, strong_extra = self._RECIPES[dish]
        if pc.skill("khrua") < need:
            _p(f"{label.title()} is beyond your kitchen yet — you'd need Khrua "
               f"rank {need}. Practice, or start with pad krapow.")
            return
        rl = roll(pc.skill("khrua") + pc.mod("hands"), rng=self.rng)
        self.advance(45)
        _p(f"You fire the wok for {label}. {rl.describe()}")
        if rl.outcome is Outcome.STRONG:
            pc.add_item(key, 1 + strong_extra)
            pc.add_stress(-1)
            _p(f"The best {label} in the province. {1 + strong_extra} servings "
               f"put by, and the cooking soothed you. (-1 stress)")
        elif rl.outcome is Outcome.WEAK:
            pc.add_item(key, 1)
            _p(f"Solid, honest food. One plate of {label} saved.")
        else:
            _p("You burn the aromatics and choke the kitchen with smoke.")

    def commune(self) -> None:
        pc = self.pc
        if "shrine" not in DISTRICTS[pc.location].features:
            _p("No spirits gather here to answer. Seek a shrine.")
            return
        offering = self._take_offering()
        att = persuasion.persuade(pc, "phii", bonus=offering, rng=self.rng)
        self.advance(30)
        for n in att.notes:
            _p(n)
        _p(att.roll.describe())
        if att.outcome is Outcome.STRONG:
            pc.add_heat(-2)
            _p("The chao thi of this ground and the phi pu ya — the grandmother "
               "and grandfather spirits — speak plainly through the incense: "
               "which patrols sleep, which gate is blind tonight. Their goodwill "
               "quiets the streets. (-2 heat)")
        elif att.outcome is Outcome.WEAK:
            pc.add_heat(-1)
            _p("A phi phong's cold glow hangs at the treeline — the Northern night "
               "spirit — and its whisper is a warning you mostly understand. "
               "(-1 heat)")
        else:
            pc.add_stress(2)
            _p("Something cold takes offence at your fumbling words: a phi ka "
               "stirs, the inherited hunger that rides a careless tongue. "
               "(+2 stress)")

    def craft(self, arg: str) -> None:
        pc = self.pc
        what = arg.strip().lower()
        if not skills.literate(pc):
            _p("You cannot inscribe what you cannot read. Learn 'aksorn' first.")
            return
        if pc.skill("saiyasat") < 1:
            _p("You lack the occult craft (saiyasat) to make anything yet.")
            return
        if "hun" in what or "payont" in what:
            cost = 1200
            if pc.baht < cost:
                _p(f"A hun payont needs {cost}฿ of teak, metals, and offerings.")
                return
            pc.baht -= cost
            rl = roll(pc.skill("saiyasat") + pc.skill("aksorn") + pc.mod("lore"),
                      rng=self.rng)
            self.advance(180)
            _p(f"You carve and inscribe a hun payont guardian. {rl.describe()}")
            if rl.outcome is Outcome.MISS:
                pc.add_stress(1)
                _p("The yantra won't take; the figure stays dead wood. Materials "
                   "wasted. (+1 stress)")
            else:
                pc.charms.append("hun_payont")
                _p("It wakes. A guardian rides with you now — it will throw "
                   "itself between you and the next disaster at a gate.")
        elif "takrut" in what:
            if pc.baht < 300:
                _p("A takrut needs 300฿ of metal foil.")
                return
            pc.baht -= 300
            rl = roll(pc.skill("saiyasat") + pc.skill("aksorn"), rng=self.rng)
            self.advance(90)
            _p(f"You roll and inscribe a takrut scroll. {rl.describe()}")
            if rl.outcome is Outcome.MISS:
                _p("The inscription smudges; worthless.")
            else:
                pc.add_item("takrut", 1)
                _p("A sound takrut, ready to sell or carry. (+1 takrut)")
        else:
            _p("You can craft: hun (payont), takrut.")

    def glamour(self) -> None:
        pc = self.pc
        rl = roll(pc.skill("mahaniyom") + pc.mod("guile"), rng=self.rng)
        self.advance(20)
        _p(f"You compose the glow-up — bearing, gaze, an air of belonging. "
           f"{rl.describe()}")
        if rl.outcome is Outcome.STRONG:
            pc.glamour += 2
            _p("Radiant and unremarkable at once. Two crossings' worth of "
               "invisibility. (+2 glamour)")
        elif rl.outcome is Outcome.WEAK:
            pc.glamour += 1
            _p("It settles, thin but real. One crossing. (+1 glamour)")
        else:
            _p("It won't hold; you only look like you're trying too hard.")

    # --- the body: dares that win face, and the places that mend it --------
    _DARES = {
        # key: (display food, nerve modifier, health hit, Thaiglish cheer)
        "chili": ("a bowl of nam prik noom heaped with a fistful of raw prik kee "
                  "noo", 1, 1,
                  "Aiyoh! The mouse-shit chili also you eat? Jai rip, jai rip! "
                  "Same-same local now, na."),
        "bug": ("a paper cone of rot duan and one fried maeng daa, giant "
                "water-bug and all", 0, 1,
                "Look look \u2014 the whole maeng daa, shell also! Farang run "
                "away, you no run. Good one!"),
        "offal": ("a plate of laab lu \u2014 the northern larb served dib, raw, "
                  "dressed in its own blood", -1, 2,
                  "Dib dib, real Lanna one \u2014 not everybody dare this. You "
                  "eat, we remember, na."),
    }

    def feast(self, arg: str = "") -> None:
        """Eat something fearsome to win face before a watching contact. It
        deepens a bond; your body pays for the bravado until it mends."""
        pc = self.pc
        feats = DISTRICTS[pc.location].features
        if "market" not in feats and "night" not in feats:
            _p("No street-food scene here to make a show of. Try a market or a "
               "night bazaar, where the woks are lit and there's a crowd.")
            return
        crowd = relationships.here(pc, pc.location)
        if not crowd:
            _p("You could wolf a plate of something fearsome, but there's no one "
               "here whose regard is worth the bellyache. Do this where a friend "
               "or a mark is watching.")
            return
        dare = (arg.strip().lower() or "chili")
        if dare not in self._DARES:
            _p("Take on which dare? chili, bug, or offal.")
            return
        label, diff, hit, cheer = self._DARES[dare]
        mark = crowd[0]
        self.advance(30)
        rl = roll(pc.mod("nerve") + diff, rng=self.rng)
        _p(f"You call for {label}, and {mark.name} and the others lean in to "
           f"watch. {rl.describe()}")
        if rl.outcome is Outcome.MISS:
            pc.add_health(-(hit + 1))
            pc.add_stress(1)
            _p(f"You can't finish \u2014 you go grey and set the spoon down. No "
               f"one is unkind; {mark.name} laughs warmly and waves the cook over "
               f"with a glass of nam yen. \u201cMai pen rai, na \u2014 next time "
               f"you train first.\u201d (-{hit + 1} health, +1 stress)")
            return
        relationships.adjust_bond(pc, mark.key, 1, pc.day)
        pc.add_health(-hit)
        _p(f"{mark.name}: \u201c{cheer}\u201d")
        tail = "clean and grinning" if rl.outcome is Outcome.STRONG else "sweating but game"
        extra = ""
        if rl.outcome is Outcome.STRONG and len(crowd) > 1:
            second = crowd[1]
            relationships.adjust_bond(pc, second.key, 1, pc.day)
            extra = f" {second.name}, watching, warms to you too."
        _p(f"You finish it {tail}. Shared heat is shared trust here \u2014 "
           f"{mark.name} warms to you.{extra} (+1 bond{' \u00d72' if extra else ''}, "
           f"-{hit} health)")

    def pharmacy(self) -> None:
        """A chemist's counter: a course of remedies over the table, and the
        quiet potion trade beneath it (fair price, no heat)."""
        pc = self.pc
        if "pharmacy" not in DISTRICTS[pc.location].features:
            _p("No chemist's here. Try Warorot or the Kad Chang Phuak night market.")
            return
        HEAL_COST, HEAL_AMT = 250, 3
        while True:
            potions = [k for k, n in pc.inventory.items()
                       if n > 0 and get(k).kind == "potion"]
            opts: list[tuple[str, object]] = [
                (f"A course of remedies \u2014 +{HEAL_AMT} health ({HEAL_COST}฿)",
                 "heal")]
            if potions:
                opts.append(("Sell a potion under the table (fair price, no heat)",
                             "sell"))
            pick = self._choose(
                opts,
                "The chemist folds her hands. \u201cWelcome, welcome. Medicine "
                "for the body \u2014 or the other kind, mai bok khrai, na?\u201d")
            if pick == "heal":
                if pc.health >= 10:
                    _p("\u201cYou? Strong like buffalo already. Keep your baht, "
                       "na.\u201d She waves it away.")
                    continue
                if pc.baht < HEAL_COST:
                    _p(f"\u201cAiyah \u2014 the full course is {HEAL_COST}฿. Not "
                       f"enough today. You come back, na.\u201d")
                    continue
                pc.baht -= HEAL_COST
                pc.add_health(HEAL_AMT)
                self.advance(20)
                _p(f"She measures a paper twist of powders and a small brown "
                   f"bottle, talking the whole while. The ache lets go. "
                   f"(+{HEAL_AMT} health, -{HEAL_COST}฿)")
            elif pick == "sell":
                sub = [(f"{get(k).name} \u2014 {pc.inventory[k]} on hand, "
                        f"{get(k).base_price:,}฿ each", k) for k in potions]
                k = self._choose(sub, "Which one? She takes it quiet.")
                if not k:
                    continue
                n = pc.inventory[k]
                take = get(k).base_price * n
                pc.baht += take
                pc.add_item(k, -n)
                _p(f"It goes under the counter without a word, and the baht comes "
                   f"back the same way \u2014 {n}\u00d7 {get(k).name}, {take:,}฿, "
                   f"nothing on any ledger or scanner. (+{take:,}฿)")
            else:
                _p("\u201cReep roy. Take care of the body, na.\u201d")
                return

    def clinic(self) -> None:
        """A beauty clinic: buy attraction and poise (glamour) — not health."""
        pc = self.pc
        if "clinic" not in DISTRICTS[pc.location].features:
            _p("No beauty clinic here. Nimman and the Night Bazaar have the "
               "bright glass ones.")
            return
        COST, CHARGES = 500, 2
        if pc.baht < COST:
            _p(f"A session of glow runs {COST}฿, paid up front. Not today.")
            return
        pc.baht -= COST
        pc.glamour += CHARGES
        self.advance(60)
        _p(f"An hour under warm lights and cool hands \u2014 a facial, a little "
           f"radiance, a practised word about your cheekbones. You walk out "
           f"polished and certain, the kind of attraction a scanner's eye slides "
           f"right off. (+{CHARGES} glamour, -{COST}฿)")
        _p("(Charisma and poise \u2014 not health. The clinic mends how you read, "
           "not how you feel.)")

    def hospital(self) -> None:
        """The teaching hospital: real healing, at real-money prices."""
        pc = self.pc
        if "hospital" not in DISTRICTS[pc.location].features:
            _p("No hospital here. The big teaching hospital sits at Suan Dok, off "
               "the Nimman road.")
            return
        COST = 1500
        if pc.health >= 10:
            _p("The triage nurse looks you over. \u201cYou are well, na. Go home "
               "\u2014 keep your baht for someone sick.\u201d")
            return
        if pc.baht < COST:
            _p(f"Real care, real money \u2014 {COST}฿ up front, and the desk "
               f"won't bend on it. You're short today.")
            return
        pc.baht -= COST
        pc.add_health(10)
        self.advance(180)
        _p(f"Proper medicine, clean and unhurried: a drip, a scan, a doctor who "
           f"actually looks at you. You leave hale and whole. (health full, "
           f"-{COST}฿, and half a day gone)")

    # Food is everywhere in this city, and cheap. The scenes rotate; the
    # people in them are just the people who feed the city — no one remarkable,
    # everyone worth a nod.
    _BITE_SCENES = (
        "A 7-Eleven hums on the corner \u2014 there's one on every corner. You "
        "grab a toasted sandwich and a cold Milo, and the clerk rings you up "
        "mid-yawn.",
        "A som-tam cart, the pestle going pok-pok-pok. The auntie makes yours "
        "medium and still watches your face to see if you can take it.",
        "A khao-gaeng shop: you point at three of the dishes under the glass "
        "and they arrive ladled over rice before you've finished pointing.",
        "A khao-soi cart parked in its usual spot. The owner and his husband "
        "work it shoulder to shoulder \u2014 one ladling curry, one making "
        "change \u2014 and neither misses a beat.",
        "A moto-side noodle stall. The cook, a tom in a faded football jersey, "
        "blanches your noodles and cracks an egg one-handed, sliding you the "
        "bowl without looking up.",
        "A night-stall of grilled moo ping and warm sticky rice, handed over "
        "by a vendor who calls you \u2018nong\u2019 and tells you to eat more, "
        "you're too thin.",
    )

    def grab_bite(self) -> None:
        """Food is everywhere here and cheap \u2014 a quick plate that settles
        the nerves and puts a little back in the body. No dare, no crowd, no
        ceremony; just eating, the way the city always feeds you."""
        pc = self.pc
        COST = 40
        if pc.baht < COST:
            _p(f"Even street food wants a few baht, and your pockets are that "
               f"empty just now. (need {COST}฿)")
            return
        pc.baht -= COST
        self.advance(20)
        _p(self.rng.choice(self._BITE_SCENES))
        healed = pc.health < 10
        if healed:
            pc.add_health(1)
        pc.add_stress(-1)
        body = "+1 health, " if healed else ""
        _p(f"You eat standing up, the way everyone does, and feel the day "
           f"loosen its grip a little. ({body}-1 stress, -{COST}฿)")

    def courier(self) -> None:
        """Call Aof's rider collective to run your hot load through the next
        gate for you — a boon earned by winning her trust."""
        pc = self.pc
        boss = relationships.has_boon(pc, "courier")
        if not boss:
            _p("You've no riders to call on yet. Win Aof's trust at the Night "
               "Bazaar and her collective will run your loads for you.")
            return
        carried = pc.carried_heat()
        if carried == 0:
            _p("Nothing hot on you to move — the riders would only laugh. Call "
               "them when you've a load worth hiding.")
            return
        if pc.courier_ready:
            _p("Your riders are already standing by for the next gate.")
            return
        fee = 200 + 200 * carried
        if pc.baht < fee:
            _p(f"Aof names the price for a load this hot — {fee:,}฿ — and your "
               f"pockets don't reach it. \u201cNo money, no ride, na.\u201d")
            return
        pc.baht -= fee
        pc.courier_ready = True
        self.advance(15)
        _p(f"You ping Aof's group chat. Minutes later a rider idles at the "
           f"curb, helmet nodding. \u201cOne gate, we take it — you walk "
           f"through clean, we meet you after, na.\u201d Set for your next "
           f"crossing. (-{fee:,}฿)")

    # --- courting luck ----------------------------------------------------
    def dress(self) -> None:
        """Wear the day's lucky colour — the small, everyday courting of fortune
        every Thai grandmother swears by. Free, quick, once a day; nudges the
        day your way."""
        pc = self.pc
        name, color = luck.weekday_color(pc.day)
        if pc.dressed_today:
            _p(f"You're already turned out in {color} for {name}. Fortune's been "
               f"given its due today.")
            return
        pc.dressed_today = True
        self.advance(10)
        got = luck.raise_luck(pc, 1)
        base = (f"You pick out {color} for {name} and put it on with a little "
                f"care \u2014 the colour of the day, worn the way your "
                f"grandmother taught you.")
        if got:
            _p(base + " The day feels like it tips a shade your way. (courted luck)")
        else:
            _p(base + " The day was already running with you; the colour just "
               "keeps faith with it.")

    def sadao(self) -> None:
        """Sadao khro: shed the day's bad luck at a shrine, paid for with a food
        offering. The rite that turns a wrong day less wrong."""
        pc = self.pc
        if "shrine" not in DISTRICTS[pc.location].features:
            _p("No shrine here to carry off your bad luck. Find one \u2014 Doi "
               "Suthep, or a city spirit-house.")
            return
        if pc.luck >= 1:
            _p("The day already runs with you \u2014 no bad luck here to shed. "
               "Don't tempt the spirits by asking twice.")
            return
        offering = self._take_offering()
        if not offering:
            _p("The rite wants an offering set down \u2014 khao soi, pad krapow, "
               "something cooked with care \u2014 and you've none to give.")
            return
        self.advance(20)
        got = luck.raise_luck(pc, 1)
        _p("You kneel, name the day's ill luck aloud, and let the smoke carry it "
           "off \u2014 sadao khro, the shedding. The knot in the day loosens.")
        if got:
            _p("Something lifts. The day sits a little kinder on you now. "
               "(shed bad luck)")

    def lottery_flow(self) -> None:
        """A wandering ticket-seller is here. Buy on gut — the numbers, how
        welcome they feel, whether the seller's a lucky one — or wave them on."""
        pc = self.pc
        enc = self.lottery
        if enc is None:
            _p("No seller working the lane just now. They come and go; wait, and "
               "one will drift by.")
            return
        _p(f"Up walks {enc.vendor.name}.")
        _p(enc.vendor.aura_note)
        _p(enc.welcome_note)
        if pc.hunch:
            _p(f"(The number from your dream still nags: {pc.hunch}.)")
        while True:
            enc = self.lottery
            if enc is None:
                return
            opts = [(lottery.ticket_label(pc, t), i)
                    for i, t in enumerate(enc.tickets)]
            pick = self._choose(opts, "Buy which ticket  (0 to wave them on)")
            if pick is None:
                _p("You press your palms together, smile, wave them on. "
                   "\u201cMai ao, na \u2014 next time.\u201d They drift off up "
                   "the lane.")
                self.lottery = None
                return
            t = enc.tickets[int(pick)]
            if pc.baht < t["cost"]:
                _p(f"You count your baht and come up short of the {t['cost']}\u0e3f. "
                   f"The seller only smiles. \u201cMai pen rai.\u201d")
                continue
            pc.baht -= t["cost"]
            pc.tickets.append(t)
            enc.tickets.remove(t)
            self.advance(5)
            hunch_hit = t["hunch"]
            _p(f"You take No. {t['number']} \u2014 tail {t['tail']} \u2014 for "
               f"{t['cost']}\u0e3f. It draws on day {t['draw_day']}." +
               (" The dream-number, in your hand at last." if hunch_hit else ""))
            if hunch_hit:
                pc.hunch = ""   # the dream is spent
            if not enc.tickets:
                _p("That's the last of their board. They bow and move on.")
                self.lottery = None
                return

    def _menu_feast(self) -> None:
        dare = self._choose(
            [("Chilies \u2014 raw prik kee noo (easier, -1 health)", "chili"),
             ("Bugs \u2014 rot duan & giant water-bug (-1 health)", "bug"),
             ("Offal \u2014 raw laab lu, blood and all (hard, -2 health)", "offal")],
            "What do you dare to eat?")
        if dare:
            self.feast(dare)

    def do_persuade(self, arg: str) -> None:
        pc = self.pc
        aud = arg.strip().lower()
        if aud not in persuasion.AUDIENCES:
            _p("Persuade whom? " + ", ".join(persuasion.AUDIENCES))
            return
        offering = 0
        if aud in ("monk", "ancestor"):
            offering += self._take_offering()
        if aud in ("human", "police", "customs") and pc.has("salika"):
            offering += 1
            _p("The Salika Lin Thong at your throat lends your words a honeyed "
               "pull. (+1)")
        att = persuasion.persuade(pc, aud, bonus=offering, rng=self.rng)
        self.advance(20)
        for n in att.notes:
            _p(n)
        _p(att.roll.describe())
        _p({Outcome.STRONG: "They come fully around to your side.",
            Outcome.WEAK: "They'll bend — for a concession or a favour owed.",
            Outcome.MISS: "You misjudge them, and it costs you standing."}[att.outcome])
        if att.outcome is Outcome.MISS:
            pc.add_stress(1)

    # --- the relationship spine -------------------------------------------
    def _find_contact(self, arg: str, pool: list[str] | None = None) -> str | None:
        arg = arg.strip().lower()
        for k in (pool if pool is not None else self.pc.contacts):
            c = relationships.CONTACTS[k]
            if arg == k or arg and arg in c.name.lower():
                return k
        return None

    def network(self) -> None:
        pc = self.pc
        if not pc.contacts:
            _p("You know no one yet. Go where people gather — the markets, the "
               "gates, the mountain — and the web will begin to weave itself.")
            return
        _p("== Your web ==")
        by_fac: dict[str, list[str]] = {}
        for k in pc.contacts:
            by_fac.setdefault(relationships.CONTACTS[k].faction, []).append(k)
        for fac, label in relationships.FACTIONS.items():
            ks = by_fac.get(fac)
            if not ks:
                continue
            _p(f"-- {label} --")
            for k in ks:
                c = relationships.CONTACTS[k]
                where = DISTRICTS[c.where].name if c.where else "the unseen"
                mark = " *" if k in pc.secrets_heard else ""
                print(f"  {c.name:<22} {relationships.tier(relationships.bond_of(pc, k)):<14}"
                      f" {where}{mark}")
        intros = relationships.available_intros(pc)
        if intros:
            _p("Doors open to you (use 'ask'): "
               + ", ".join(relationships.CONTACTS[t].name for _, t in intros))
        st = relationships.standing(pc)
        parts = [f"{f} {v:+d}" for f, v in st.items() if v]
        if parts:
            _p("Standing: " + "   ".join(parts))

    def _menu_profile(self) -> None:
        pc = self.pc
        if not pc.contacts:
            _p("You know no one yet.")
            return
        opts = [(f"{relationships.CONTACTS[k].name}  "
                 f"({relationships.tier(relationships.bond_of(pc, k))})", k)
                for k in pc.contacts]
        key = self._choose(opts, "Look someone up \u2014 press a number")
        if key:
            self.profile(key)

    def profile(self, arg: str) -> None:
        pc = self.pc
        key = self._find_contact(arg)
        if not key:
            _p("You don't know anyone by that name. Try 'network'.")
            return
        c = relationships.CONTACTS[key]
        bond = relationships.bond_of(pc, key)
        _p(f"== {c.name} ==")
        _p(f"{c.heritage} · {relationships.FACTIONS[c.faction]}")
        _p(f"Between you: {relationships.tier(bond)}.")
        _p(c.bio)
        # where and when they can be found
        loc = relationships.present_location(c, pc.minutes)
        if loc:
            _p(f"Right now: at {DISTRICTS[loc].name}.")
        else:
            _p(f"Right now: {relationships.whereabouts(c, pc.minutes)}.")
        # the closer you are, the more you know of them
        if bond >= 1 and c.birthday:
            wd = festivals.weekday_name(c.birthday)
            _p(f"Born on Day {c.birthday} ({wd}) — remember it.")
        if c.want:
            _p(f"They seem to want: {c.want.note}")
        if bond >= 3:
            from .items import get as _item
            def _names(keys):
                out = []
                for k in keys:
                    try:
                        out.append(_item(k).name)
                    except Exception:
                        out.append(k)
                return ", ".join(out)
            if c.loves:
                _p(f"Loves: {_names(c.loves)}.")
            if c.likes:
                _p(f"Likes: {_names(c.likes)}.")
            if c.dislikes:
                _p(f"Won't thank you for: {_names(c.dislikes)}.")
        # scenes you've witnessed
        seen = [h for h in c.hearts if f"{c.key}:{h.at}" in pc.hearts_seen]
        if seen:
            _p("You have shared these moments:")
            for h in seen:
                print(f"  · {h.title}")
        if c.hearts and len(seen) < len(c.hearts):
            _p("There is more of them to know, as your bond deepens.")
        if key in pc.secrets_heard:
            _p("You hold their secret.")

    def _contact_at_hand(self, arg: str, verb: str) -> str | None:
        pc = self.pc
        here = [c.key for c in relationships.here(pc, pc.location)]
        key = self._find_contact(arg, pc.contacts)
        if not key:
            if here:
                _p(f"{verb} whom? Here now: "
                   + ", ".join(relationships.CONTACTS[k].name for k in here))
            else:
                _p("No one you know is out here right now. Check your 'network', "
                   "or come back at a different hour.")
            return None
        c = relationships.CONTACTS[key]
        if not relationships.is_present(c, pc.minutes, pc.location):
            _p(f"{c.name} isn't here — {relationships.whereabouts(c, pc.minutes)}.")
            return None
        return key

    def _tell_story(self) -> None:
        """Surface any narrative beats the last interaction earned."""
        for line in story.advance(self.pc):
            _p(line)

    def journal(self) -> None:
        # Make sure the opening beat is set before the first read.
        for line in story.advance(self.pc):
            _p(line)
        for line in story.journal(self.pc):
            _p(line)

    def do_talk(self, arg: str) -> None:
        key = self._contact_at_hand(arg, "Talk to")
        if not key:
            return
        c = relationships.CONTACTS[key]
        bonus = 1 if (c.role in ("human", "police", "customs")
                      and self.pc.has("salika")) else 0
        if bonus:
            _p("The Salika Lin Thong lends your words a honeyed pull. (+1)")
        res = relationships.talk(self.pc, key, self.pc.day, bonus=bonus, rng=self.rng)
        self.advance(20)
        for line in res.lines:
            _p(line)
        self._tell_story()

    def do_give(self, arg: str) -> None:
        # give <item> to <name>
        if " to " not in arg:
            _p("Give what to whom? Try: give khao soi to Lawan")
            return
        item_part, name_part = arg.split(" to ", 1)
        item_key = self._resolve_item_name(item_part)
        key = self._contact_at_hand(name_part, "Give to")
        if not key:
            return
        if not item_key:
            _p("You aren't carrying that.")
            return
        res = relationships.give(self.pc, key, item_key, self.pc.day)
        self.advance(10)
        for line in res.lines:
            _p(line)
        self._tell_story()

    def do_ask(self, arg: str) -> None:
        pc = self.pc
        key = self._find_contact(arg, pc.contacts)
        intros = relationships.available_intros(pc)
        targets = [t for (i, t) in intros if key is None or i == key or i == "*"]
        if targets:
            res = relationships.introduce(pc, targets[0], pc.day)
            self.advance(15)
            for line in res.lines:
                _p(line)
            self._tell_story()
            return
        if key is None:
            if intros:
                _p("Ask whom? Doors open via: "
                   + ", ".join(relationships.CONTACTS[i].name if i != "*" else "the unseen"
                               for i, _ in intros))
            else:
                _p("No introductions await. Deepen a bond and a door will open.")
            return
        # otherwise, maybe carry a word they long to hear
        res = relationships.share_word(pc, key, pc.day)
        self.advance(10)
        for line in res.lines:
            _p(line)
        self._tell_story()

    def bargain(self) -> None:
        """A pivotal test of talent — charm the sergeant, out-deal the fence."""
        pc = self.pc
        for line in story.advance(pc):   # make sure act/beats are current
            _p(line)
        t = story.available_trial(pc)
        if t is None:
            _p("No negotiation is open to you yet. Check 'journal' for the next "
               "step in the story.")
            return
        # a fine plate strengthens a worldly appeal, as it does everywhere
        food = self._take_offering() if t.role in (
            "human", "police", "customs", "monk", "ancestor") else 0
        for line in story.attempt_trial(pc, t.key, food_bonus=food, rng=self.rng):
            _p(line)
        self.advance(30)
        self._tell_story()

    # --- the festival calendar --------------------------------------------
    def calendar(self) -> None:
        pc = self.pc
        _p(f"== The calendar ==   Day {pc.day}, a {festivals.weekday_name(pc.day)}")
        today = festivals.on_day(pc.day)
        if today:
            for f in today:
                where = DISTRICTS[f.where].name if f.where else "the temples"
                _p(f"  Today: {f.name} — {where}.")
                _p(f"    {f.lanna}")
        else:
            _p("  No festival today.")
        soon = festivals.upcoming(pc.day, within=8)
        if soon:
            _p("")
            _p("  Coming up:")
            for d, f in soon:
                where = DISTRICTS[f.where].name if f.where else "the temples"
                when = "tomorrow" if d == 1 else f"in {d} days"
                print(f"    {f.name:<38} {when:<12} ({festivals.weekday_name(pc.day + d)}, {where})")
        _p("")
        _p("  The turning Lanna year:")
        for name, season, note in festivals.LANNA_YEAR:
            print(f"    {name:<28} {season}")

    def celebrate(self) -> None:
        """Give yourself to a festival that's on here today — each pays out its
        own way, and the sacred ones let you make merit with an offering."""
        pc = self.pc
        events = festivals.celebrate(pc, pc.location, pc.day)
        joined = next((e for e in events if e.kind == "festival_joined"), None)
        if joined:
            self.advance(joined.minutes)   # a festival eats much of the day
        self._render(events)
        if joined:
            self._tell_story()

    # --- travel between cities --------------------------------------------
    def travel(self, arg: str) -> None:
        pc = self.pc
        region = region_of(pc.location)
        routes = routes_from(region, pc.projects)
        if not routes:
            _p("No intercity road or rail from here.")
            return
        tokens = arg.split()
        dest = tokens[0].lower() if tokens else ""
        mode_name = tokens[1].lower() if len(tokens) > 1 else ""
        if not dest:
            _p("== Journeys from here ==")
            for r in routes:
                modes = ", ".join(f"{m.name}({m.minutes}m/{m.cost}฿"
                                  f"{'/danger'+str(m.danger) if m.danger else ''})"
                                  for m in r.modes)
                print(f"  {DISTRICTS[r.arrive].name:<26} {r.km}km  [{modes}]")
            _p("travel <place> <mode>")
            return
        route = next((r for r in routes if dest in r.to or dest in
                      DISTRICTS[r.arrive].name.lower()), None)
        if not route:
            _p("No route there from here.")
            return
        mode = next((m for m in route.modes if m.name.startswith(mode_name)), None)
        if not mode:
            _p("Modes: " + ", ".join(m.name for m in route.modes))
            return
        if pc.baht < mode.cost:
            _p(f"That fare is {mode.cost}฿; you can't cover it.")
            return
        pc.baht -= mode.cost
        self.advance(mode.minutes)
        _p(f"You take the {mode.name} toward {DISTRICTS[route.arrive].name}.")
        if mode.danger:
            hz = roll(pc.mod("nerve") - mode.danger, rng=self.rng)
            if hz.outcome is Outcome.MISS:
                pc.add_stress(2)
                _p("The road bites back — a near-miss with a truck on a blind "
                   "bend. You arrive rattled. (+2 stress)")
            elif hz.outcome is Outcome.WEAK:
                pc.add_stress(1)
                _p("Rain, potholes, and traffic wear on you. (+1 stress)")
        pc.location = route.arrive
        self.look()

    def invest(self, arg: str) -> None:
        pc = self.pc
        tokens = arg.split()
        if not tokens or not tokens[-1].lstrip("-").isdigit():
            have = pc.projects.get("train_north", 0)
            _p(f"Northern railway to Chiang Rai: {have:,}/{TRAIN_NORTH_GOAL:,}฿ "
               f"pledged. Fund it and the train will run where the road never "
               f"could. Usage: invest train <baht>")
            return
        amount = int(tokens[-1])
        if amount <= 0 or amount > pc.baht:
            _p("You can't pledge that.")
            return
        pc.baht -= amount
        pc.projects["train_north"] = pc.projects.get("train_north", 0) + amount
        have = pc.projects["train_north"]
        self.advance(30)
        if have >= TRAIN_NORTH_GOAL:
            _p("The northern line is fully funded. Rails will reach Chiang Rai — "
               "and now a train option opens on that corridor.")
        else:
            _p(f"Pledged {amount:,}฿. Railway fund now {have:,}/"
               f"{TRAIN_NORTH_GOAL:,}฿.")

    # --- numbered menus (accessible mode) ---------------------------------
    def _ask(self, prompt: str) -> str | None:
        try:
            return input(f"\n{prompt}\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return None

    def _choose(self, options: list[tuple[str, object]],
                prompt: str = "Press a number") -> object | None:
        """Show a numbered list; return the chosen value, or None for Back."""
        print()
        for i, (label, _v) in enumerate(options, 1):
            print(f"  {i:>2}.  {label}")
        print("   0.  Back")
        while True:
            raw = self._ask(prompt)
            if raw is None:
                return None
            raw = raw.strip().lower()
            if raw in ("", "0", "b", "back"):
                return None
            if raw.isdigit():
                i = int(raw) - 1
                if 0 <= i < len(options):
                    return options[i][1]
            print("  Please press one of the numbers above.")

    def _ask_qty(self) -> int:
        raw = self._ask("How many?  (press Enter for 1)")
        if raw and raw.strip().isdigit() and int(raw.strip()) > 0:
            return int(raw.strip())
        return 1

    def _menu_go(self) -> None:
        exits = neighbors(self.pc.location)
        opts: list[tuple[str, object]] = []
        for e in exits:
            tag = "   [MOAT GATE — customs scan]" if e.crossing else ""
            opts.append((f"{DISTRICTS[e.to].name}  ({e.minutes} min){tag}", e.to))
        dest = self._choose(opts, "Go which way")
        if dest is not None:
            self.go(str(dest))

    def _menu_market(self) -> None:
        pc = self.pc
        if not market.MARKET_PROFILES.get(pc.location):
            _p("No market floor here. Try Warorot, the Night Bazaar, Doi Suthep, "
               "Wualai, Nimman, or Kad Chang Phuak.")
            return
        self.show_market()
        act = self._choose([("Buy something", "buy"), ("Sell something", "sell")],
                           "Buy or sell")
        if act is None:
            return
        heat, fence = market.price_mods(pc, pc.location)
        rows = market.listings(pc.location, pc.day, pc.market, heat, fence)
        who = market.FENCE_BOONS.get(pc.location)
        fname = relationships.CONTACTS[who].name if (fence and who) else None

        def _mark(l) -> str:
            return ("  \u2191 cornered" if l.drift > 0.05
                    else "  \u2193 glutted" if l.drift < -0.05 else "")

        if act == "buy":
            tag = f"  [{fname}'s favour]" if fname else ""
            opts = [(f"{l.item.name}  —  {l.buy:,}฿  (heat {l.item.heat}){_mark(l)}",
                     l.item.key) for l in rows]
            key = self._choose(opts, "Buy which" + tag)
            if key is not None:
                self.buy(str(key), self._ask_qty())
        else:
            bits = []
            if heat and heat * market.HEAT_SELL_PENALTY > 0:
                bits.append(f"heat -{round(min(market.HEAT_SELL_CAP, heat * market.HEAT_SELL_PENALTY) * 100)}%")
            if fname:
                bits.append(f"{fname}'s favour")
            tag = f"  [{', '.join(bits)}]" if bits else ""
            opts = [(f"{l.item.name}  —  sell {l.sell:,}฿  "
                     f"(you have {pc.inventory[l.item.key]}){_mark(l)}", l.item.key)
                    for l in rows if pc.has(l.item.key)]
            if not opts:
                _p("You have nothing they'd buy here.")
                return
            key = self._choose(opts, "Sell which" + tag)
            if key is not None:
                self.sell(str(key), self._ask_qty())

    def _menu_travel(self) -> None:
        pc = self.pc
        routes = routes_from(region_of(pc.location), pc.projects)
        if not routes:
            _p("No intercity road or rail from here.")
            return
        route = self._choose(
            [(f"{DISTRICTS[r.arrive].name}  ({r.km} km)", r) for r in routes],
            "Travel where")
        if route is None:
            return
        mode = self._choose(
            [(f"{m.name} — {m.minutes} min, {m.cost}฿"
              + (f", danger {m.danger}" if m.danger else ""), m)
             for m in route.modes], "By what")
        if mode is not None:
            self.travel(f"{route.to} {mode.name}")

    def _menu_cook(self) -> None:
        opts = []
        for dish, (need, _k, label, _b) in self._RECIPES.items():
            gated = "" if self.pc.skill("khrua") >= need else f"   (needs Khrua {need})"
            opts.append((f"{label.title()}{gated}", dish))
        dish = self._choose(opts, "Cook what")
        if dish is not None:
            self.cook(str(dish))

    def _menu_practice(self) -> None:
        opts = []
        for key, (name, _blurb, attr) in skills.SKILLS.items():
            rank = self.pc.skill(key)
            opts.append((f"{name}  — rank {rank}/5  [{attr}]", key))
        key = self._choose(opts, "Practice which skill")
        if key is not None:
            self.practice(str(key))

    def _menu_craft(self) -> None:
        key = self._choose([("Hun payont (guardian)", "hun"),
                            ("Takrut scroll", "takrut")], "Craft what")
        if key is not None:
            self.craft(str(key))

    _AUDIENCE_LABELS = {
        "human": "A person (trader, tout, local)",
        "police": "Police", "customs": "Customs officer",
        "monk": "A monk", "phii": "A ghost / spirit (phii)",
        "ancestor": "An ancestor", "deva": "A deva",
    }

    def _menu_people(self) -> None:
        pc = self.pc
        crowd = relationships.here(pc, pc.location)
        if not crowd:
            _p("No one you know is here.")
            return
        opts = [(f"{c.name} — {relationships.tier(relationships.bond_of(pc, c.key))}"
                 f"  ({c.heritage})", c.key) for c in crowd]
        key = self._choose(opts, "Talk to whom")
        if key is not None:
            self._menu_contact(str(key))

    def _menu_contact(self, key: str) -> None:
        c = relationships.CONTACTS[key]
        act = self._choose([
            ("Talk — deepen the bond", "talk"),
            ("Give a gift", "give"),
            ("Ask — follow a door / share what you know", "ask"),
        ], f"With {c.name}")
        if act == "talk":
            self.do_talk(key)
        elif act == "give":
            self._menu_give(key)
        elif act == "ask":
            self.do_ask(c.name)

    def _menu_give(self, key: str) -> None:
        pc = self.pc
        if not pc.inventory:
            _p("Your bag is empty — nothing to give.")
            return
        from .items import get
        opts = [(f"{get(k).name}  (x{n})", k) for k, n in pc.inventory.items()]
        item = self._choose(opts, "Give what")
        if item is None:
            return
        res = relationships.give(pc, key, str(item), pc.day)
        self.advance(10)
        for line in res.lines:
            _p(line)

    def _menu_persuade(self) -> None:
        opts = [(self._AUDIENCE_LABELS.get(a, a.title()), a)
                for a in persuasion.AUDIENCES]
        who = self._choose(opts, "Persuade whom")
        if who is not None:
            self.do_persuade(str(who))

    def _menu_save(self) -> None:
        act = self._choose([("Save game", "save"), ("Load saved game", "load")],
                           "Save or load")
        if act == "save":
            _p(f"Saved to {save.save(self.pc)}.")
        elif act == "load":
            self.pc = save.load()
            _p("Loaded.")
            self.look()

    def _menu_sections(self) -> list[tuple[str, list[tuple[str, object]]]]:
        """The main-screen menu, grouped by intent. Contextual, high-value
        actions come first; the rarely-used long tail lives under 'More'."""
        pc = self.pc
        feats = DISTRICTS[pc.location].features

        # -- Here & now: what this place and hour actually offer --------------
        here_now: list[tuple[str, object]] = []
        t = story.available_trial(pc)
        if t:
            here_now.append((f"\u2605 {t.title} \u2014 the pivotal negotiation",
                             self.bargain))
        if self.lottery is not None:
            n = len(self.lottery.tickets)
            here_now.append((f"\u2726 A lottery seller is working the lane "
                             f"\u2014 see the numbers ({n})", self.lottery_flow))
        fest = festivals.here_now(pc.location, pc.day)
        if fest:
            here_now.append((f"Join {fest[0].name} (on here today)", self.celebrate))
        crowd = relationships.here(pc, pc.location)
        if crowd:
            names = ", ".join(c.name for c in crowd[:3])
            more = "\u2026" if len(crowd) > 3 else ""
            here_now.append((f"Talk to someone here \u2014 {names}{more}",
                             self._menu_people))
        prof = market.MARKET_PROFILES.get(pc.location)
        if prof:
            here_now.append((f"Browse {prof['name']} (buy / sell)", self._menu_market))
        if "shrine" in feats:
            here_now.append(("Commune with the spirits at the shrine", self.commune))
            if pc.luck < 1:
                here_now.append(("Shed the day's bad luck (sadao khro \u2014 "
                                 "needs an offering)", self.sadao))
        if ("market" in feats or "night" in feats) and crowd:
            here_now.append(("Take on a food dare to win face", self._menu_feast))
        if "pharmacy" in feats:
            here_now.append(("The chemist's \u2014 remedies & quiet potion trade",
                             self.pharmacy))
        if "clinic" in feats:
            here_now.append(("A beauty clinic \u2014 buy the glow (attraction)",
                             self.clinic))
        if "hospital" in feats:
            here_now.append(("The hospital \u2014 real healing, real money",
                             self.hospital))
        if relationships.has_boon(pc, "courier") and pc.carried_heat() > 0:
            label = ("Riders standing by \u2014 you'll walk the next gate clean"
                     if pc.courier_ready
                     else "Call Aof's riders to run your load past a gate")
            here_now.append((label, self.courier))

        # -- Go: movement -----------------------------------------------------
        go: list[tuple[str, object]] = []
        if neighbors(pc.location):
            go.append(("Go somewhere nearby", self._menu_go))
        if routes_from(region_of(pc.location), pc.projects):
            go.append(("Travel to another city", self._menu_travel))

        # -- Story & people ---------------------------------------------------
        people: list[tuple[str, object]] = []
        jlabel = "The tale so far (journal)"
        if story.has_unread(pc):
            jlabel += "   \u2726 new"
        people.append((jlabel, self.journal))
        people.append(("Your web of contacts", self.network))
        if pc.contacts:
            people.append(("Look someone up (profile)", self._menu_profile))
        people.append(("Listen for word on the street", self.rumors))

        # -- Your day: time & upkeep -----------------------------------------
        day: list[tuple[str, object]] = [
            ("Grab a bite (cheap street food \u2014 +health, -stress)",
             self.grab_bite),
        ]
        if not pc.dressed_today:
            _, color = luck.weekday_color(pc.day)
            day.append((f"Dress in today's lucky colour ({color}) \u2014 court "
                        f"the day's luck", self.dress))
        day += [
            ("Check your bag", self.inventory),
            ("Rest / lie low (6 hours)", self.rest),
            ("Sleep until dawn (end the day)", self.sleep),
        ]

        sections = []
        if here_now:
            sections.append(("Here & now", here_now))
        sections.append(("Go", go))
        sections.append(("Story & people", people))
        sections.append(("Your day", day))
        sections.append(("", [("More\u2026 (craft, cook, skills, map, save)",
                               self._menu_more)]))
        return sections

    def _menu_more(self) -> None:
        """The long tail: everything you reach for now and then."""
        opts: list[tuple[str, object]] = [
            ("Look around (describe this place)", self.look),
            ("The festival calendar", self.calendar),
            ("Cook food", self._menu_cook),
            ("Practice a skill", self._menu_practice),
            ("Craft an amulet", self._menu_craft),
            ("Compose a glow-up (glamour)", self.glamour),
            ("Persuade a stranger", self._menu_persuade),
            ("Your skills", self.show_skills),
            ("Character sheet", self.status),
            ("Map of the region", self.show_map),
            ("Fund the northern railway", lambda: self.invest("")),
            ("Save / load", self._menu_save),
            ("Help (and typed commands)", self.help),
        ]
        act = self._choose(opts, "More \u2014 press a number")
        if callable(act):
            act()

    # --- loop -------------------------------------------------------------
    def help(self) -> None:
        _p("You can play two ways:")
        _p("  \u2022 EASY: just press the number next to what you want to do.")
        _p("  \u2022 TYPED: or type a command word. Both work at every prompt.")
        _p("")
        _p("Commands:")
        for line in [
            "look / l            describe where you are",
            "go <n|name>         travel (may hit a moat gate)",
            "map                 overview of the city",
            "market              show the local market",
            "buy <name> [n]      buy goods",
            "sell <name> [n]     sell goods",
            "inv / i             what you're carrying",
            "appraise <name>     read & value an item (needs aksorn)",
            "travel [place mode] intercity: scooter / bus / train",
            "invest train <baht> fund the Chiang Rai railway",
            "",
            "skills              your learned crafts",
            "practice <skill>    grind a skill (teachers unlock deep ranks)",
            "learn/study <skill> practice, at a monastery or teacher",
            "cook [dish]         cook pad_krapow / sai_ua / khao_soi (offerings)",
            "commune             speak to the phii at a shrine",
            "craft <hun|takrut>  occult craft (needs saiyasat + reading)",
            "glamour             the glow-up: social invisibility",
            "bite / eat          grab cheap street food (+health, -stress)",
            "feast <chili|bug|offal>  a food dare to win face (costs health)",
            "pharmacy            chemist's: remedies + quiet potion trade",
            "clinic              buy attraction/poise (glamour), not health",
            "hospital            real healing, real money",
            "courier / riders    (Aof's trust) run a hot load past your next gate",
            "lottery / huay      buy a ticket if a seller's working the lane",
            "dress               wear the day's lucky colour (court luck, 1/day)",
            "sadao / shed        shed the day's bad luck at a shrine (needs offering)",
            "",
            "network / web       your contacts, bonds, and open doors",
            "profile <name>      what you know of someone — where, wants, tastes",
            "calendar            the festival year, and what's coming",
            "celebrate           join a festival on here today (deepens bonds)",
            "journal / tale      the mystery so far, and days to the festival",
            "talk <name>         deepen a bond with someone here",
            "give <item> to <name>  a gift; meeting their want means more",
            "ask <name>          follow an introduction, or share what you know",
            "bargain             a pivotal charm/negotiation, when one awaits",
            "persuade <who>      a stranger: human/police/customs/monk/phii/...",
            "rumors              listen for a lead",
            "rest                lie low: -stress, -heat, +6h",
            "sleep               end the day; wake at dawn, restored",
            "status / stat       your character sheet",
            "save / load         one save slot",
            "help / quit",
        ]:
            print("  " + line)

    def step(self, raw: str) -> None:
        raw = raw.strip()
        if not raw:
            return
        parts = raw.split()
        cmd, rest = parts[0].lower(), parts[1:]
        arg = " ".join(rest)

        def qty_and_name(tokens: list[str]) -> tuple[str, int]:
            if tokens and tokens[-1].isdigit():
                return " ".join(tokens[:-1]), int(tokens[-1])
            return " ".join(tokens), 1

        if cmd in ("look", "l"):
            self.look()
        elif cmd in ("go", "move", "walk"):
            self.go(arg)
        elif cmd == "map":
            self.show_map()
        elif cmd in ("market", "shop"):
            self.show_market()
        elif cmd == "buy":
            name, n = qty_and_name(rest)
            self.buy(name, n)
        elif cmd == "sell":
            name, n = qty_and_name(rest)
            self.sell(name, n)
        elif cmd in ("inv", "i", "inventory"):
            self.inventory()
        elif cmd in ("wear", "show", "display"):
            self.wear_item(arg)
        elif cmd in ("stow", "hide", "pocket"):
            self.stow_item(arg)
        elif cmd in ("appraise", "read"):
            self.appraise(arg)
        elif cmd in ("rumors", "listen"):
            self.rumors()
        elif cmd in ("skills", "sk"):
            self.show_skills()
        elif cmd in ("practice", "train", "drill"):
            self.practice(arg)
        elif cmd in ("learn", "study"):
            self.learn(arg)
        elif cmd == "cook":
            self.cook(arg)
        elif cmd in ("commune", "pray"):
            self.commune()
        elif cmd in ("craft", "make"):
            self.craft(arg)
        elif cmd in ("glamour", "glowup", "glow"):
            self.glamour()
        elif cmd in ("feast", "dare"):
            self.feast(arg)
        elif cmd in ("bite", "grab", "snack", "eat"):
            self.grab_bite()
        elif cmd in ("pharmacy", "chemist"):
            self.pharmacy()
        elif cmd in ("clinic", "beauty"):
            self.clinic()
        elif cmd in ("hospital", "er"):
            self.hospital()
        elif cmd in ("courier", "riders", "rider"):
            self.courier()
        elif cmd in ("lottery", "huay", "lotto", "ticket", "tickets"):
            self.lottery_flow()
        elif cmd in ("dress", "wear-colour", "colour", "color"):
            self.dress()
        elif cmd in ("sadao", "shed", "sadaokhro"):
            self.sadao()
        elif cmd == "persuade":
            self.do_persuade(arg)
        elif cmd in ("network", "web", "contacts", "people"):
            self.network()
        elif cmd in ("profile", "about", "who"):
            self.profile(arg)
        elif cmd in ("journal", "tale", "story", "quest"):
            self.journal()
        elif cmd in ("calendar", "festivals", "dates", "cal"):
            self.calendar()
        elif cmd in ("celebrate", "join", "festival"):
            self.celebrate()
        elif cmd in ("bargain", "negotiate", "deal"):
            self.bargain()
        elif cmd in ("talk", "meet", "greet"):
            self.do_talk(arg)
        elif cmd in ("give", "gift", "offer"):
            self.do_give(arg)
        elif cmd in ("ask", "introduce", "intro"):
            self.do_ask(arg)
        elif cmd in ("travel", "journey"):
            self.travel(arg)
        elif cmd == "invest":
            self.invest(arg)
        elif cmd == "rest":
            self.rest()
        elif cmd in ("sleep", "bed"):
            self.sleep()
        elif cmd in ("status", "stat", "sheet"):
            self.status()
        elif cmd == "save":
            path = save.save(self.pc)
            _p(f"Saved to {path}.")
        elif cmd == "load":
            self.pc = save.load()
            _p("Loaded.")
            self.look()
        elif cmd in ("help", "?"):
            self.help()
        elif cmd in ("quit", "exit", "q"):
            self.running = False
        else:
            _p("Unknown command. Type 'help'.")

    def _banner(self) -> None:
        """The turn header: where/when/wealth, condition, and the live objective."""
        pc = self.pc
        print()
        print("=" * WRAP)
        print(f"  {_clock(pc)}   \u00b7   {DISTRICTS[pc.location].name}"
              f"   \u00b7   {pc.baht:,}฿")
        cond = f"  Heat {pc.heat}/10   Stress {pc.stress}/9"
        if pc.health < 10:
            cond += f"   Health {pc.health}/10"
        carried = pc.carried_heat()
        if carried:
            cond += f"   \u2022 carrying customs-heat {carried}"
        print(cond)
        print("-" * WRAP)
        for line in textwrap.wrap("\u2192 " + story.objective(pc), WRAP - 2):
            print("  " + line)
        print("=" * WRAP)

    def run(self) -> None:
        # Set the opening beat before the first banner so the objective reads true.
        for line in story.advance(self.pc):
            _p(line)
        # A fresh smuggler wakes to their first omen (loaded saves keep theirs).
        if not self.pc.omen:
            for line in luck.roll_day(self.pc, self.rng):
                _p(line)
        self.look()
        while self.running:
            sections = self._menu_sections()
            self._banner()
            flat: list[object] = []
            for title, items in sections:
                if not items:
                    continue
                if title:
                    print(f"  \u2014 {title} \u2014")
                for label, action in items:
                    flat.append(action)
                    print(f"  {len(flat):>2}.  {label}")
            print("   0.  Quit")
            raw = self._ask("Press a number  (or type a command word)")
            if raw is None:
                break
            raw = raw.strip()
            if raw == "":
                continue
            if raw == "0" or raw.lower() in ("q", "quit", "exit"):
                self.running = False
                break
            if raw.isdigit():
                i = int(raw) - 1
                if 0 <= i < len(flat):
                    flat[i]()  # type: ignore[operator]
                else:
                    _p("That number isn't on the menu.")
            else:
                self.step(raw)
        _p("The scanners hum on without you. \u0e42\u0e0a\u0e04\u0e14\u0e35 "
           "(good luck).")
