# Moat

A text, tabletop-style game about an amulet-and-potion smuggler in **Chiang Mai,
2076** — a lightly altered future laid over a world that is historically accurate
to the real Chiang Mai up to 2007. Very Lanna in orientation.

## Run it

Double-click **`Moat.command`** in Finder — it finds a suitable interpreter on
its own. From a shell:

```
cd moat-game
python3.13 -m game
```

Needs **Python 3.12+**. Apple's stock `/usr/bin/python3` is 3.9 and cannot parse
this codebase, and Homebrew's `python@3.13` installs no bare `python3` — so name
the version explicitly, or let `Moat.command` resolve it.

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

### The side arc — *The Silence of the Pillar*

**This is no longer the opening.** It does not exist for you until you have found the coucal clock: only once you can hear the watches do you notice what is missing from them — that the Sao Inthakhin keeps no hour at all. Until then the banner says nothing about it and the journal is empty.

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

### The first days — things that go right

A player who is only ever refused puts the game down before the good part, and
a shut door only reads as intriguing when something else is going well. So the
first six days carry a short chain of small, guaranteed wins (`game/opening.py`)
— each pays a little, teaches exactly one verb, and cannot fail. Eat the rice
soup the woman downstairs insists on. Run a parcel four streets for 350฿.
Ask the man who takes it what the trade calls the thing you are carrying, and
get your first word free. Work out what your own bag is worth. Skills also move
faster while you are new, so a first practice visibly moves.

None of them is a quest and none has a marker. They are the seed, though: she
tells you Kad Luang is open **now**, and it is, and you go, and it works. The
beat is only ever offered while that is literally true. Nobody says the word
"hours". Days later, when four doors in a row have been shut in your face, that
morning is the thing you remember.

### The opening — nobody tells you there is a puzzle

There is no quest-log entry for the first thing you do, and no marker. You
arrive keeping ordinary time and the city quietly refuses it: a shop is shut at
eleven and open at 11:37, a tout says come back at the right time and will not
say when that is, and two lanes that have nothing to do with each other keep
hours that agree exactly — with each other, never with your watch.

**The coucal clock** (`game/coucal.py`) is why, and it is the one authoritative
time in the world. Somebody set it in a wat fifty years ago and it has not
stopped. It keeps **eight watches to the day, beginning 37 minutes after civil
midnight**, and every window, shift, round and rotation in the city hangs off
it. No entity keeps private time; everything asks this module.

Market floors keep the bird's hours, not yours — Kad Luang runs 06:37–15:37,
the Night Bazaar 12:37–21:37, Wualai 21:37–06:37 — so you spend the first days
walking into shut doors and being told, without explanation, to come back at the
right time. Nobody will tell you when that is.

The quest begins only when you **demonstrate that you have noticed**: three
shut doors is the floor, plus waiting one out on purpose (twice) and comparing
two different lanes' hours (twice). Waiting *an hour* will never do it — a fixed
step from a fixed start visits the same three points of the watch forever. You
have to wait for *something*. Then finding the clock is triangulation, not navigation: the bird sounds
three times a day, **49 wats inside the wall** are candidates (taken from the
real city, via Mot Dang), and you stand in a quarter and watch how tightly the
local shutters answer the call. Three quarters collapses the search to one.

The old city is walkable on foot as five permanent, hand-authored places — the
four corner quarters and the middle. It never changes. That is the map you keep.

The reward is the lattice itself: afterwards you can read every window in the
city, and you never walk up to a shut door by accident again.

### The pile and the rails — the opening problem

You do not start poor. You start on **one billion baht** in 20-baht notes and
coins — **208 tonnes** of money in a room, going soft with damp at the bottom,
and too big for one person to police. That is the opening problem, and the
**difficulty setting is nothing but how hard it is to keep**: easy, medium and
hard change theft, spoilage and how often somebody arrives with a claim. They
never touch enemy dice.

Money is therefore two numbers: what's **in your pocket** (`baht` — what shops
and bribes actually take) and what's **on your rail** (`reserve` — the pile).
Before anything else you bind the pile to a rail, and the rail is a class choice
wearing a wallet's clothes (`game/rails.py`):

| Rail | Gate | Strong | Fragile |
|---|---|---|---|
| **Cash** | none | nothing to freeze or trace; every informal door opens | weight, damp, rats, hands, claimants |
| **Crypto** | none | weightless, crosses any distance | keys, power, signal; the chain remembers |
| **Foreign bank** | none at the start | survives fire and flood | assumes papers you may not have; someone else's off switch |
| **Thai bank** | **earned in play** | local, fast, unremarkable, weightless | you are inside the system, and it files reports |

You cannot pick the **Thai account** at the start. You open one the way anyone
opens one here: walk in with **25,000,000฿** on the desk, or be so good across
it that the paperwork follows you — the charm door only unlocks at **Charcha +
Mahaniyom ≥ 7** and is still a stiff roll. Hauling that much cash to the branch
is itself a visible act, and costs you heat.

**Busting out is not the end.** If the pile and your pocket both hit zero you
bind to a different rail — but it opens **cold**: it holds nothing and protects
nothing until you have carried **120,000฿** into it by hand. That is the grind,
and it is meant to be unpleasant.

### Suan Prung — the cursed gate, and the silver two hundred metres away

For six hundred years the dead left the city by the south-western gate, and
custom of that age does not wear off because somebody bolted a scanner to the
arch. **Every transaction made at Suan Prung is cursed** (`game/curse.py`) —
not trade in general, not the goods in general: *that* exchange, the one you
made there, with the road of the dead going past.

Which is exactly why there is a market under the arch, and why it is the best
market in the city. Nobody decent will trade at the gate of the dead, so the
spread is the narrowest anywhere (6% against Kad Luang's 18%) and nobody asks a
single question. A Phra Somdej is **5,583฿** under the arch against **6,969฿**
on the guild floor.

Then the bill arrives. A curse settles in two places at once:

- **On you.** Your day cannot come up lucky again while you hold one — whatever
  sign the morning gives you, it does not reach you. Every arch in the city
  reads it, at +1 scan penalty per curse, for as long as you carry it.
- **On the goods**, which is worse. A cursed amulet is worth **45%** of its
  price to any buyer who can read one. That same Phra Somdej now fetches
  **2,664฿** at Kad Luang instead of 4,843฿.

So the cheap gate is a real trap and a real temptation: you save 1,386฿ and lose
2,179฿ on the resale — unless you are buying to carry rather than to flip, or
unless you clean it first.

The remedy stands two hundred metres away, through the gate and down the silver
road, and that is not a coincidence and never was. **The Silver Temple** has
been beating consecrated silver on Wualai since long before anyone put a customs
post on the moat, and here the silver does not decorate the hall so much as
*hold* what it is given. 4,000฿ and three hours apiece, worked at the fire in
the compound: either off you, or off the object, which lies overnight on a sheet
of silver and comes out reading clean. The sheet does not — it goes the grey of
a cold sky and takes no light again.

That is why one panel in twenty on the hall is dull, why the smiths are always
up a ladder replacing them, and why there is a rack in the shed behind the fire
holding fifty years of the south-west gate in flat grey sheets. Everyone knows
what they are. Nobody melts them down.

*The Silver Temple is the game's own — it takes the silver road and the craft
from the real Wualai and goes its own way from there. It is not a portrait of
any actual temple, and none of its rules are anybody's real ones.*

### Being seen — what people think you have

The city runs on **perceived** wealth, not actual (`game/wealth.py`). Perception
sets your prices, your claimants, and how a room changes when you walk into it,
and it sorts you into six bands from *nobody in particular* to *the one with the
money* (prices ×1.0 → ×2.2, claims ×0.4 → ×3.0).

You cannot keep a billion secret, but you can keep it a **rumour**. Left
untouched, talk only ever reaches about **15% of the truth** — a cash pile sits
at *a rich person* after three quiet months and stops there. The rest of the
truth arrives as evidence, and the evidence is your own behaviour: one heavy
haul takes 125m of rumour to 560m of fact in an afternoon. Withdrawals, branch
deposits, easy bribes, gifts too fine for the occasion and — loudest of all —
funding a great work each push perception toward what you really hold. The rail
matters: cash leaks fastest, a foreign bank slowest. **Live small** for a few
days to drag it back down.

Money moves some audiences and hardens others: traders, police and customs bend
to it (up to +3), an abbot does not (−1, because he has met rich penitents), and
the dead are famously unimpressed.

### The ways in and out — and the water

Everything outside the wall is mutable, and the roads most of all. They close
constantly (`game/roads.py`), for reasons that are never dramatic: a culvert
goes, the flats flood, a procession has the road for the afternoon, the mountain
has put part of itself across the Chiang Rai road again. Closures are seeded from
the day and the road, so a save replays identically, and they are **symmetric** —
the same stretch is shut in both directions, because that is what a road is.

The roads out of town go constantly: over 100 days the Chiang Rai corridor is
shut or crawling **22 times**, against **5** for a stretch inside the outer city.
This is why navigation is a real skill and why knowing the alternate beats
knowing the shortest. It is also the argument for the northern railway in one
number — **a closure on the highway cannot touch a train.**

The player has **some control, outside the wall only**. Seal a stretch for
12m฿ — base course, drainage, a proper camber, a culvert that will still be there
next year — and closures on it drop from 5 in 100 days to 1. Inside the wall
nothing is fundable: the old city is not a thing that gets improved.

#### Filling in the moat

You can do this. It costs 60m฿, which is cheap, and it is the most tempting
thing in the game, because **a moat with no water is a moat with no gates**.
Not shut gates — none. Nothing for a customs post to sit on, nothing for a
scanner arch to span. Every scan you have ever sweated, gone. The arches come
down within the week because the metal is worth something.

For about a month it is the best decision you have ever made.

Then the wells go strange, and the drains that have run one direction since
Mangrai stop agreeing about which direction that was. The naga are in the
hydrology — in this world that is where they live, not a figure of speech — and
the ring is the oldest agreement the city has. While it is dry: **travel ×2.6,
prices ×1.4, persuasion −2 with everyone** (they all know what you did), road
closures double, and the city hands you a fresh curse every week, forever.

You can dig it out. It costs **900m฿** — fifteen times the filling, and nearly
the price of the northern line — and takes months, and *nothing* lifts until the
water is back. All of it, not some of it. Then the gates go back up within the
month, because of course they do, and you will be scanned at every one of them
for the rest of your life, and you will be glad of it.

### Great works — what the pile is actually for

Buying amulets with a billion baht is bailing the Ping with a cup. Great works
(`game/works.py`) are funded in instalments off the rail and each has a real
mechanical consequence: the **northern line to Chiang Rai** (900m฿), **drainage
under the eastern flats** (340m฿, and the damp stops eating your stash),
a standing fund for **papers** (180m฿, and claims on your pile halve), a
**market hall** for the vendor families (260m฿, and they stop pricing you as a
mark), **restoration of the clock's hall** (120m฿, and the sangha knows who paid),
and **land assembly ahead of the flood maps** (500m฿ — entirely legal, not
entirely nice). None of it can be done quietly.

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

## Playing it

**Numbers change; letters never do.** The numbered list is only what this place,
at this hour, is actually offering — it is short, and it moves as you move. The
things you can always do sit on fixed letter keys that are identical on every
screen in the game, so you learn them once instead of re-reading a sixteen-line
list every turn:

```
[B] Bag   [M] Money   [P] People   [K] Skills   [N] News   [J] Journal
[E] Eat   [W] Wait    [R] Rest     [S] Sleep    [X] More   [?] Help
```

Amounts are picked from a list rather than typed. A new game opens with thirty
seconds on how the screen works and the two things that trip everyone up —
money living in two places, and time rather than baht being the real budget —
and says nothing whatever about what is worth doing, because that is the part
you are meant to find.

## Commands

You can also type. `help` in-game. Core verbs: `look`, `go`, `map`, `market`, `buy`, `sell`,
`inv`, `appraise`, `travel`, `invest`, `skills`, `practice`, `learn`, `cook`,
`commune`, `craft`, `glamour`, `network`, `profile`, `talk`, `give`, `ask`,
`journal`, `calendar`, `celebrate`, `bargain`, `persuade`, `rumors`, `rest`,
`sleep`, `status`, `money`, `words`, `around`, `wait`, `quarter`, `works`, `silver`, `roads`, `save`/`load`.

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
  coucal.py      THE clock — eight watches a day; everything subscribes to it
  opening.py     the first days' small guaranteed wins, then it gets out of the way
  curse.py       Suan Prung's price, and the Silver Temple that undoes it
  roads.py       closures, roads you can pay for, and the moat you can fill in
  contribute.py  hours observed in the real city, for Mot Dang's atlas
  noticing.py    the unmarked opening: notice the time, triangulate, find the wat
  rails.py       the pile, the four payment rails, the grind after a bust-out
  wealth.py      perceived vs actual money, and how the city treats you for it
  works.py       great works — where a billion baht goes
  venues.py      the city's shopfronts + the consent dead-man's switch
  dictionary.py  the trade's vocabulary and what fluency buys you
  relationships.py contacts, bonds, secrets, schedules, gift tastes, heart scenes
  festivals.py   the Lanna festival calendar — weekly streets, Wan Phra, Inthakhin
  story.py       the four-act arc that reads your secrets & bonds
  engine.py      game loop, commands, time & heat
  __main__.py    entry + character creation
```

## The city's real data (`data/`, `tools/`)

The game reads two of NaN's existing bodies of work rather than inventing
Chiang Mai twice. Both import to JSON, so writers and artists can edit content
without touching code.

**Mot Dang → the venue layer.** `tools/import_motdang.py` pulls the ~9,000-place
Chiang Mai catalogue into `data/venues.json`: **1,804 shopfronts inside the
moat**, real category mix, real opening hours, and **93 places whose hours are
too narrow to be about selling anything** — the front-business primitive,
straight out of the real city. What it deliberately drops is identity: no name,
phone, address, website or exact coordinate survives the import. A venue is *"a
noodle counter"* until somebody names it.

**wichaa.net → the dictionary.** `tools/import_wichaa.py` pulls the glossary
into `data/dictionary.json` — 33 terms in Thai, romanised, glossed in English
and 中文, each carrying how many catalogued manuscripts and market listings
really use it. That count grades the word: one used by 1,198 listings is stall
talk, one used by three marks you as someone who reads the old hand. You pick
words up by appraising things, and your **fluency** decides whether a dealer
quotes you the first price or the second (`words` in-game).

### The field layer — LINE-first, and it gives back

Mot Dang has 9,075 catalogued places in Chiang Mai and **7,109 of them have no
opening hours**. Hours are the largest hole in the atlas and the one field a
crawler fundamentally cannot reach — they live on a hand-lettered card behind a
grille. This game's core skill is reading windows, so the mechanic *already is*
the observation. That is the only reason this layer exists.

**LINE-first** (`worker/`): no app store, no account, no password. Share your
location with the Official Account, get back what is catalogued within 200 m,
tap OPEN or SHUT. Two taps, no typing. A LIFF page does the same job as a list
for people who would rather see one, with tap targets sized for one hand
outdoors in sun.

What it keeps, exhaustively: **which place, the minute, the weekday, open or
shut**, and a salted hash of the LINE id used only to rate-limit and to count
one person once per place per day.

What it never keeps: **your location** (used in memory to find what is near you,
then gone — there is no code path that writes a coordinate to storage), your
name or LINE id, and **any trace, route or sequence**. Observations are not
linkable to each other. Rotating `HASH_SALT` makes every past hash unlinkable,
which is a feature and not a migration problem.

Never collected against: **wats, hospitals, clinics, schools, homes.** The
exclusion runs at index *build* time, so those places are absent from the lookup
entirely and no request exists that could record one. 3,343 of 10,673 places are
excluded; 7,330 remain loggable.

Nothing goes live. Six observations at 75% agreement before a window is even
proposed; a shut sighting inside a proposed span is reported as a probable
midday close rather than averaged away. `GET /export` emits a payload for the
atlas's **moderation queue** — the path a human reads — and never `/claim`,
which is for an owner speaking about their own business, and never a direct
write. See `worker/DEPLOY.md` for what is still needed and what is deliberately
unfinished.

### Naming a real business — consent is a dead-man's switch

Real Chiang Mai businesses **can** appear by name, with the owner's written
permission, as cross-promotion. Two rules hold, and both are enforced in data
rather than left to memory (`game/venues.py`, `tools/consent.py`):

1. **A permissioned business is only ever depicted doing its actual trade.** It
   can be a landmark, a shop you buy from, a teacher, a meeting place. It is
   never a front, a fence, a drop or a raid. Every criminal role belongs to a
   fictional composite. Once a venue has been named under consent it is barred
   from the shadow layer permanently — even after the permission lapses.
2. **Permission expires on its own.** A grant carries a term (default 180 days).
   Past it the game stops using the real name by itself and the venue falls back
   to its descriptor — no code change, no rebuild. Silence *un-names* a business
   rather than naming it forever, so losing touch with an owner fails safe.
   `live_consent()` is closed by default and refuses anything malformed,
   undated, withdrawn or expired.

```
python3.13 tools/consent.py report            # who is live, lapsing, lapsed
python3.13 tools/consent.py grant  <key> --name "…" --scope "…" --contact "…"
python3.13 tools/consent.py renew  <key> --days 180
python3.13 tools/consent.py withdraw <key>
```

Place data © OpenStreetMap contributors, ODbL, via Mot Dang — attribution is
shown in-game and is a separate obligation from any owner's permission.

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


## Licence

Records, prose and pages: CC BY-SA 4.0. Code: AGPL-3.0-or-later. Anything
carried in from elsewhere keeps its own terms — see [LICENSE](LICENSE).

**Commercial licence.** If share-alike doesn't fit your use — a corpus, a
product, a model — a commercial licence is available.
[Open an issue](https://github.com/NaNoBotCo/moat-game/issues) and say what you need.
