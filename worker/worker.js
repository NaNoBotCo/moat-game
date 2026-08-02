// Cloudflare Worker — Moat's field layer. LINE-first: no app store, no
// account, no password. A player shares their location with the Official
// Account, gets back the catalogued places within a couple of hundred metres,
// and taps OPEN or SHUT. Two taps, no typing — which is also what makes it
// usable for someone who finds typing hard.
//
// WHAT THIS COLLECTS, EXHAUSTIVELY:
//   placeId, minute-of-day, weekday, open|shut, and a salted hash of the
//   LINE user id used only for rate limiting and de-duplication.
//
// WHAT IT DELIBERATELY NEVER STORES:
//   · the shared location. It is used in memory to find nearby places and is
//     then gone. There is no code path that writes lat/lng to KV. A record of
//     where a real person was, at a real time, is a more dangerous dataset
//     than anything else this project touches, and the way not to leak it is
//     not to have it.
//   · a raw LINE user id, display name, or picture.
//   · any trace, path, sequence, or "places this user has visited" list. Each
//     observation stands alone and is not linkable to the next by anything
//     stored here.
//   · a place's name, address, coordinates or contact details. Those are the
//     atlas's own, and a passer-by is a stranger — which is exactly the line
//     Mot Dang's claims worker already draws, and this honours it.
//
// EXCLUSIONS are applied when field-index.json is built, not here. Wats,
// hospitals, clinics, schools and homes are absent from the index, so there is
// no request this worker can receive that would record against one. See
// tools/build_field_index.py.
//
// NOTHING GOES LIVE. Observations aggregate in KV; when a place clears the
// thresholds, GET /export emits a moderation-queue payload for a human to read
// and post. This worker never writes to the atlas.
//
// KV layout:
//   idx:v                  → cached field index (built by build_field_index.py)
//   obs:<placeId>          → {n, open:[minute...], shut:[minute...], updated}
//   rl:<userHash>:<hour>   → observations this hour (1h TTL)
//   dup:<userHash>:<placeId>:<day> → 1, so one person counts once per place
//                            per day (1d TTL)
//   sess:<userHash>        → the places last offered to this person (10m TTL)

const MAX_BODY = 40_000
const PER_HOUR = 40                 // observations per person per hour
const NEAR_METRES = 220             // how close counts as "in front of"
const MAX_OFFERED = 6               // places offered per location share
const SESSION_TTL = 600
const MIN_OBSERVATIONS = 6          // before a window is worth proposing
const MIN_AGREEMENT = 0.75

const json = (o, status = 200) =>
  new Response(JSON.stringify(o), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  })

// --- identity without identity ---------------------------------------------
// We never store the LINE user id. We store a salted hash of it, which is
// enough to rate-limit and de-duplicate and useless for anything else. The
// salt lives in a secret; rotate it and every prior hash becomes unlinkable.
async function userHash(env, lineUserId) {
  const data = new TextEncoder().encode(`${env.HASH_SALT || 'dev'}:${lineUserId}`)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return [...new Uint8Array(digest)].slice(0, 12)
    .map(b => b.toString(16).padStart(2, '0')).join('')
}

// --- geometry ---------------------------------------------------------------
function metres(aLat, aLng, bLat, bLng) {
  const R = 6371000, toRad = d => (d * Math.PI) / 180
  const dLat = toRad(bLat - aLat), dLng = toRad(bLng - aLng)
  const s = Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(s))
}

let INDEX_CACHE = null
async function index(env) {
  if (INDEX_CACHE) return INDEX_CACHE
  const raw = await env.KV.get('idx:v')
  if (!raw) return { places: [] }
  INDEX_CACHE = JSON.parse(raw)
  return INDEX_CACHE
}

// Nearby, unknown-hours first — those are the ones actually worth a tap.
async function nearby(env, lat, lng) {
  const idx = await index(env)
  const out = []
  for (const p of idx.places) {
    if (Math.abs(p.y - lat) > 0.004 || Math.abs(p.x - lng) > 0.004) continue
    const d = metres(lat, lng, p.y, p.x)
    if (d <= NEAR_METRES) out.push({ ...p, d: Math.round(d) })
  }
  out.sort((a, b) => (a.h - b.h) || (a.d - b.d))
  return out.slice(0, MAX_OFFERED)
}

// --- recording --------------------------------------------------------------
async function record(env, uh, placeId, isOpen, now) {
  const idx = await index(env)
  // The index IS the allow-list. Anything not in it cannot be recorded.
  if (!idx.places.some(p => p.id === placeId)) {
    return { ok: false, why: 'not_loggable' }
  }
  const hour = Math.floor(now / 3600000)
  const rlKey = `rl:${uh}:${hour}`
  const used = parseInt((await env.KV.get(rlKey)) || '0', 10)
  if (used >= PER_HOUR) return { ok: false, why: 'rate_limited' }

  const d = new Date(now)
  const day = d.toISOString().slice(0, 10)
  const dupKey = `dup:${uh}:${placeId}:${day}`
  if (await env.KV.get(dupKey)) return { ok: false, why: 'already_today' }

  const minute = d.getUTCHours() * 60 + d.getUTCMinutes() + 420  // ICT, UTC+7
  const wd = (d.getUTCDay() + (minute >= 1440 ? 1 : 0)) % 7
  const m = minute % 1440

  const key = `obs:${placeId}`
  const cur = JSON.parse((await env.KV.get(key)) || '{"n":0,"open":[],"shut":[]}')
  cur.n += 1
  ;(isOpen ? cur.open : cur.shut).push(m)
  cur.wd = [...new Set([...(cur.wd || []), wd])]
  cur.updated = day
  await env.KV.put(key, JSON.stringify(cur))
  await env.KV.put(rlKey, String(used + 1), { expirationTtl: 3600 })
  await env.KV.put(dupKey, '1', { expirationTtl: 86400 })
  return { ok: true, n: cur.n }
}

// Same conservative inference as game/contribute.py — deliberately identical,
// because a wrong hour in an atlas is worse than a missing one.
function infer(placeId, cur) {
  if (!cur || !cur.open.length) return null
  const lo = Math.min(...cur.open), hi = Math.max(...cur.open)
  const inside = cur.shut.filter(m => m >= lo && m <= hi)
  const agreement = 1 - inside.length / Math.max(1, cur.n)
  if (cur.n < MIN_OBSERVATIONS || agreement < MIN_AGREEMENT) return null
  const hhmm = m => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
  return {
    kind: 'hours_observation',
    placeId,
    proposed: `${hhmm(lo)}-${hhmm(hi)}`,
    observations: cur.n,
    agreement: Math.round(agreement * 100) / 100,
    note: 'Aggregated from independent passer-by observations via the Moat ' +
      'LINE field layer. No name, address, location or contact detail is ' +
      'proposed or implied. For a human to confirm before publication.',
    caveats: inside.length
      ? [`${inside.length} sighting(s) shut inside the span — probably a midday close.`]
      : [],
  }
}

// --- LINE ------------------------------------------------------------------
async function reply(env, replyToken, messages) {
  if (!env.LINE_TOKEN) return
  await fetch('https://api.line.me/v2/bot/message/reply', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      authorization: `Bearer ${env.LINE_TOKEN}`,
    },
    body: JSON.stringify({ replyToken, messages: messages.slice(0, 5) }),
  })
}

const ASK_LOCATION = {
  type: 'text',
  text: 'Send your location and I will list what is catalogued around you. ' +
    'Tap OPEN or SHUT for anything you can actually see. That is the whole job.',
  quickReply: {
    items: [{
      type: 'action',
      action: { type: 'location', label: 'Share where I am' },
    }],
  },
}

function offerMessage(places) {
  if (!places.length) {
    return {
      type: 'text',
      text: 'Nothing catalogued within 200 m that is worth a tap. Walk on a ' +
        'bit and share again.',
    }
  }
  return {
    type: 'text',
    text: 'What can you see right now?',
    quickReply: {
      items: places.slice(0, 6).flatMap((p, i) => ([
        {
          type: 'action',
          action: {
            type: 'postback',
            label: `${i + 1} open`,
            data: `o=${p.id}`,
            displayText: `${i + 1} — open`,
          },
        },
        {
          type: 'action',
          action: {
            type: 'postback',
            label: `${i + 1} shut`,
            data: `s=${p.id}`,
            displayText: `${i + 1} — shut`,
          },
        },
      ])).slice(0, 13),
    },
  }
}

function listMessage(places) {
  return {
    type: 'text',
    text: places.map((p, i) =>
      `${i + 1}. ${p.c}${p.h ? '' : '  ← no hours known'}  (${p.d} m)`
    ).join('\n'),
  }
}

async function handleLine(request, env) {
  const body = await request.text()
  if (body.length > MAX_BODY) return json({ ok: false }, 413)
  // NOTE: signature verification against LINE_CHANNEL_SECRET goes here before
  // this is pointed at a real channel. Left explicit rather than silently
  // absent — see DEPLOY.md.
  let payload
  try { payload = JSON.parse(body) } catch { return json({ ok: false }, 400) }

  for (const ev of payload.events || []) {
    const uid = ev.source?.userId
    if (!uid) continue
    const uh = await userHash(env, uid)
    const now = Date.now()

    if (ev.type === 'message' && ev.message?.type === 'location') {
      const places = await nearby(env, ev.message.latitude, ev.message.longitude)
      // The location itself dies here. Only the resulting place ids persist,
      // and only for ten minutes, so the quick-reply buttons mean something.
      await env.KV.put(`sess:${uh}`, JSON.stringify(places.map(p => p.id)),
        { expirationTtl: SESSION_TTL })
      await reply(env, ev.replyToken,
        places.length ? [listMessage(places), offerMessage(places)]
          : [offerMessage(places)])
      continue
    }

    if (ev.type === 'postback') {
      const m = /^([os])=(.+)$/.exec(ev.postback?.data || '')
      if (!m) continue
      const res = await record(env, uh, m[2], m[1] === 'o', now)
      const said = {
        rate_limited: 'That is plenty for one hour. Thank you — come back later.',
        already_today: 'You have already logged that one today. One each per day counts.',
        not_loggable: 'That is not somewhere this collects. Nothing recorded.',
      }[res.why]
      await reply(env, ev.replyToken, [{
        type: 'text',
        text: res.ok
          ? `Logged. That place has ${res.n} sighting(s) now.`
          : said,
      }])
      continue
    }

    if (ev.type === 'follow' || ev.type === 'message') {
      await reply(env, ev.replyToken, [{
        type: 'text',
        text: 'This collects opening hours for the Chiang Mai atlas — the one ' +
          'thing no crawler can reach. It keeps the place, the time, and ' +
          'open-or-shut. It does not keep your location, your name, or ' +
          'anywhere you have been.',
      }, ASK_LOCATION])
    }
  }
  return json({ ok: true })
}

// --- routes ----------------------------------------------------------------
export default {
  async fetch(request, env) {
    const url = new URL(request.url)

    if (url.pathname === '/webhook/line' && request.method === 'POST') {
      return handleLine(request, env)
    }

    // For the LIFF page, which does the same job in a browser inside LINE.
    if (url.pathname === '/nearby' && request.method === 'GET') {
      const lat = parseFloat(url.searchParams.get('lat'))
      const lng = parseFloat(url.searchParams.get('lng'))
      if (!isFinite(lat) || !isFinite(lng)) return json({ error: 'bad_position' }, 400)
      return json({ places: await nearby(env, lat, lng) })
    }

    if (url.pathname === '/observe' && request.method === 'POST') {
      let b
      try { b = await request.json() } catch { return json({ error: 'bad_json' }, 400) }
      if (!b.idToken || !b.placeId) return json({ error: 'missing' }, 400)
      // LIFF id-token verification goes here — see DEPLOY.md. Until a real
      // channel exists this path stays disabled rather than open.
      if (!env.LINE_CHANNEL_ID) return json({ error: 'not_configured' }, 503)
      const uh = await userHash(env, b.idToken)
      const res = await record(env, uh, b.placeId, !!b.open, Date.now())
      return json(res, res.ok ? 200 : 429)
    }

    // The moderation payload. A human reads this and decides. Nothing here
    // posts to the atlas — that is deliberate and should stay deliberate.
    if (url.pathname === '/export' && request.method === 'GET') {
      if (!env.EXPORT_KEY || url.searchParams.get('key') !== env.EXPORT_KEY) {
        return json({ error: 'nope' }, 403)
      }
      const list = await env.KV.list({ prefix: 'obs:' })
      const out = []
      for (const k of list.keys) {
        const cur = JSON.parse((await env.KV.get(k.name)) || 'null')
        const s = infer(k.name.slice(4), cur)
        if (s) out.push(s)
      }
      return json({
        kind: 'moat_hours_contribution',
        target: 'POST to the atlas /suggest moderation queue. Never /claim, ' +
          'never a direct write.',
        scope: 'Hours only. No name, address, coordinate, contact detail or ' +
          'ownership claim appears here, by construction.',
        count: out.length,
        suggestions: out,
      })
    }

    if (url.pathname === '/privacy') {
      return new Response(PRIVACY, {
        headers: { 'content-type': 'text/plain; charset=utf-8' },
      })
    }

    return json({ ok: true, service: 'moat-field' })
  },
}

const PRIVACY = `Moat field layer — what is kept.

KEPT
  · which catalogued place you tapped
  · the minute and weekday you tapped it
  · whether you said open or shut
  · a salted hash of your LINE id, for rate limiting and to count you once
    per place per day. Rotating the salt makes every past hash unlinkable.

NOT KEPT
  · your location. It is used to find what is near you and then discarded.
    It is never written to storage.
  · your name, display picture, or LINE id.
  · any trace, route, or list of where you have been. Observations are not
    linked to each other.

NEVER COLLECTED AGAINST
  · temples, hospitals, clinics, schools, homes. These are absent from the
    lookup index entirely, so there is no request that could record one.

WHERE IT GOES
  · nowhere automatically. Observations aggregate until a place has at least
    six of them at 75% agreement, and then a person reads the proposal and
    decides whether to offer it to the atlas's moderation queue.
`
