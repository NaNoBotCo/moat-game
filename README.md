# Moat

A text, tabletop-style game about an amulet-and-potion smuggler in **Chiang Mai,
2076** — a lightly altered future laid over a world that is historically accurate
to the real Chiang Mai up to 2007. Very Lanna in orientation.

## Run it

```
cd moat
python3 -m game
```

Or double-click **`Moat.command`** in Finder.

## The setting

The square old city (Nai Wiang) — a near-perfect **mile-square** grid — sits
inside the **moat** King Mangrai's people dug in 1296. Its wall carries five
historic gates and four corner bastions (*jaeng*). Clockwise, the gates are
**Chang Phuak** (N), **Tha Phae** (E), **Chiang Mai** (S), **Suan Prung** (SW,
the old gate of the dead) and **Suan Dok** (W); the corners are Si Phum (NE),
Katam (SE), Ku Ruang (SW) and Hua Lin (NW). In 2076 every gate is a **customs
checkpoint**, and crossing the ring with contraband is the core tension of the
game.

Everything outside the fiction is real to 2007: Wat Chedi Luang, the Sunday
Ratchadamnoen walking street, Warorot Market (Kad Luang), the Ping River, the
silversmiths of Wualai and its Saturday market, Kad Chang Phuak's khao kha moo,
Nimman and CMU below **Khruba Srivichai's** road up **Doi Suthep**, the Night
Bazaar on Chang Klan, and the greater Lanna world — Lamphun (Hariphunchai, home
of the Phra Rod and its votive set), Lampang, Chiang Rai (up the road that
always sucks), and the Golden Triangle at Sop Ruak.

## Mechanics (2d6, PbtA/Blades-flavored)

Every check is `2d6 + modifier`:

- **10+** clean success · **7–9** success at a cost · **6–** trouble

**Attributes** — who you are: `Nerve`, `Guile`, `Lore`, `Hands`.
**Resources** — `Baht`, `Heat` (city suspicion, scales patrols), `Stress`.

### Skills (D&D-style, ranks 0–5, learned)

| Skill | What it's for |
|---|---|
| **Aksorn** | Reading the old Lanna/khom script, yantra, and contracts. Literacy gates appraisal, crafting, and not getting swindled. |
| **Charcha** | Negotiation and haggling — the evergreen Thai art. |
| **Mahaniyom** | Glamour: charm and the *glow-up* that makes a checkpoint's eyes slide off you. |
| **Phasa Phii** | Spirit-speech — the words that reach ghosts, ancestors, and devas. |
| **Saiyasat** | Occult craft — hun payont guardians, takrut, consecration. |
| **Khrua** | Cookery — pad krapow and the food that opens every door. |
| **Mudra** | Nonverbal communication when words won't serve. |

Skills grow by **practice** (grinding — required, but not a slog). Past rank 2 you
need a **teacher** on site, so grinding alone can't carry you: the monks of Doi
Suthep teach reading, occult craft, and spirit-speech; the Warorot guild teaches
negotiation; Lamphun's scholars teach the ancient hand; Lampang teaches cookery
and gesture; and so on.

### Persuasion — one game, every audience

You must move **humans, police, customs, monks, phii, ancestors, and devas**, and
each yields to a different art. The resolver finds your strongest applicable
lever (skill + governing attribute), rolls, and reads the tiers. A food offering
tilts the odds — the finer the plate (khao soi > pad krapow > sai ua), the
better — and carrying a **Salika Lin Thong** sweetens worldly audiences (humans,
police, customs). A ghost simply won't hear you without Spirit-speech.

### The festival calendar — the anchors you plan around

Time matters more than money, and the **festival calendar** (`game/festivals.py`)
is what you plan it around. The week turns on real Thai weekdays; the great
recurring gatherings fall on fixed days you can steer toward: the **Ratchadamnoen
Sunday Walking Street**, the **Wualai Saturday Walking Street** in the silver
quarter, the roughly-weekly **Wan Phra** temple sabbath, and — the arc's anchor —
**Inthakhin Bucha** at Wat Chedi Luang. Type **`calendar`** to see today, what's
coming, and the wider turning Lanna year (Songkran, Yi Peng, and the rest);
**`celebrate`** to give yourself to a festival on where you stand — the surest way
to **deepen every bond in the crowd** at once, cool your heat, and breathe. A
festival eats the better part of a day, which is the point: presence is the cost.
Each one teaches a true piece of Lanna culture as you stand in it.

### The day and its hours — time is the budget

A day is not an infinite tape; it's a purse of hours (`game/clock.py`). The clock
runs in four **parts** — ☀ *morning*, ⛅ *afternoon*, ☾ *evening*, ✵ *night* — and
every screen stamps the day, weekday, part, and time. Visits and travel spend it;
when the day is done you **`sleep`** to end it, cross into a new dawn (heat and
stress ease, festivals announce themselves), and wake at 06:00 restored. `rest`
still buys six quiet hours mid-day; `sleep` gives the whole night back. Being in
the *right place at the right hour* is the real puzzle — people keep their own
hours, and a shut door at midnight is the point.

### Knowing people — schedules, tastes, and the moments between

Contacts are not always-on vendors; they live on the clock. Each keeps a
**schedule** (Sai Seng the lantern-maker works Wualai by day and watches the
river sky at night), so you must learn *when* to find *whom*. **`profile <name>`**
shows what you've come to know: where they are right now, their **birthday** (a
gift that day lands harder), what they **love / like / won't thank you for**, the
**heart moments** you've witnessed, and whether you carry their secret — and it
tells you *more* as your bond deepens. Gifts read against real taste now: their
true want lands like a promise kept, a loved thing nearly so, a disliked one
sours the mood. Deep bonds unlock **heart scenes** — quiet, hand-authored beats
that reveal who someone really is. The aim is Stardew-plain: you can *really know*
these people.

### The story — *The Silence of the Pillar*

The relationships aren't only a systems layer; they carry a **four-act mystery**
(`game/story.py`) that reads nothing but the secrets you've been trusted with and
the bonds you keep. Since the rains, the guardian of the **Sao Inthakhin** city
pillar has fallen silent, and pieces of drowned **Wiang Kum Kam** are surfacing.
The acts — *The Silence → The Surfacing → The Dead's Road → Return or Ruin* —
advance as you hold the right confidences at once: two watchers' accounts reveal
the silence; the scholar's clay plus a buyer's greed reveal the broken piece; the
dead's eyewitness plus the caravan-master's tracks reveal the smuggling route.
Knowing, though, is never enough — at the pivots you must **win** it. Two **trials
of talent** (`bargain`) gate the climax: charm the one honest sergeant into
opening her gate, then out-negotiate the fence who holds the broken piece on his
own ground. These roll the same 2d6 persuasion the whole game runs on — tilted by
Charcha, Mahaniyom, a Salika, a glow-up, a fine plate, and every bond you keep —
and they can be **lost**. The good ending is gated on *winning* the bargain, not
merely holding secrets, so building real talent matters. A
**festival clock** runs the whole arc — the Inthakhin flowers are laid on a fixed
day, and you either carry the broken piece back to the pillar before then (the
city keeps its shade) or you don't (a generation in the sun). Type **`journal`**
for the tale so far and the days remaining.

### Signature actions

- **cook [dish]** — pad krapow, sai ua, or Chiang Mai's own **khao soi** (higher
  Khrua unlocks the better dishes; a finer plate is a stronger offering).
- **commune** — speak to the phii at a shrine for leads and cooling heat.
- **craft hun** / **craft takrut** — occult work (needs Saiyasat + reading). A
  woken **hun payont** rides with you and throws itself between you and disaster
  at the next gate.
- **glamour** — the glow-up: social invisibility that discounts checkpoint risk.
- **appraise** — read and value an item (needs Aksorn, or you're guessing).

### Getting around

People move much as they do now. **Scooters dominate** (cheap, flexible, a bit
exposed); songthaews and buses are steadier; the northern **train** runs south to
Lamphun and Lampang. Walking the old city is slow and hazardous. The **road to
Chiang Rai always sucks** — long, mountainous, dangerous. There is no train north
— yet: **`invest train <baht>`** funds the Chiang Rai railway build-out, and once
it's paid for, the rails run where the road never could.

## Commands

Type `help` in-game. Core verbs: `look`, `go`, `map`, `market`, `buy`, `sell`,
`inv`, `appraise`, `travel`, `invest`, `skills`, `practice`, `learn`, `cook`,
`commune`, `craft`, `glamour`, `network`, `profile`, `talk`, `give`, `ask`,
`journal`, `calendar`, `celebrate`, `bargain`, `persuade`, `rumors`, `rest`,
`sleep`, `status`, `save`/`load`.

## Code layout

```
game/
  dice.py        2d6 resolution + degrees of success
  world.py       districts, moat gates, Lanna cities, transport routes
  items.py       amulets (real phra khrueang), potions, food
  character.py   attributes, skills, resources, save serialization
  market.py      per-district pricing, demand, the Jatukham bubble
  checkpoint.py  the moat scan (glamour + hun payont interact here)
  skills.py      ranks, literacy, practice/teacher rules
  persuasion.py  audience-based negotiation resolver
  clock.py       the day's parts (morning/afternoon/evening/night) & sleep
  relationships.py contacts, bonds, secrets, schedules, gift tastes, heart scenes
  festivals.py   the Lanna festival calendar — weekly streets, Wan Phra, Inthakhin
  story.py       the four-act arc that reads your secrets & bonds
  engine.py      game loop, commands, time & heat
  __main__.py    entry + character creation
```

## The visual game (`web/`)

The Python CLI is the **design reference**; the game itself is moving to a
tap/arrow/touch build with **no typing**, aimed at eventually playing on mobile
like Stardew Valley. It's crazy-weird-and-spooky-but-cute, and it teaches **Thai
reading** and **Lanna history** as you play.

The **hub map** (`web/index.html`) is the home screen: a stylized night map of
Chiang Mai — the square moat glowing at its heart with the Sao Inthakhin pillar,
its five historic gates, the four *jaeng* corners, the outer districts (Warorot,
Wualai, Nimman, Doi Suthep…) and the roads out to the Lanna cities. Tap a **gate**
to cross (the traffic subgame); tap the **pillar** or any district to reach its
**people** (the web of contacts). Subgames not built yet show an honest *soon*
tag on the shell that's ready for them. Drifting Yi Peng lanterns, big tap
targets, no typing.

The **traffic crossing** (`web/traffic.html`) is the first arcade grind: a
Frogger-style dash — dodge scooters, songthaews, tuk-tuks and elephants, ride the
lotus and krathong across the moat, and reach the four gate niches. Each crossing
teaches a Thai consonant (ก ไก่ = *ko kai*, "chicken"); each cleared level reveals
a piece of old Chiang Mai. Play with arrow keys / WASD, swipe, or the on-screen
buttons.

The **web of contacts** (`web/contacts.html`) is the visual face of the game's
spine — the relationship graph from `game/relationships.py`, rendered as glowing
faction-colored spirits on a night sky. Tap a light to **Talk** (2d6 moves the
bond), **Give** from your pouch (meeting a want lands like a promise kept),
**Tell** (carry one contact's secret to another who longs to hear it), or **Ask**
to be introduced — networking *is* graph growth. You start knowing a handful of
people; the rest of the web, living and unseen alike, opens only when you're
vouched for. Deepen the three who touch the other world and the **Guardian of the
Pillar** herself will finally speak. No typing; big tap targets for low vision.

Run it: **double-click `web/index.html`** (opens the hub in your browser), or serve
the folder — `python3 -m http.server 4180 --directory web` — and open
`http://127.0.0.1:4180/`. The three screens cross-link from the map. More subgames
(a wok-timing cook game, a gesture-based persuasion game) will hang off this same
shell — the map already has slots waiting for them.

## Status

Playable vertical slice. Deliberately scoped narrow-but-extensible: the systems
are in place (moat, skills, literacy, persuasion, crafting, Lanna travel, the
railway project) and the content — more NPCs, contracts, encounters, devas, and
cities — is data to grow from here. The **web** game has its first arcade subgame
(traffic crossing); the CLI world is the model it grows from.
