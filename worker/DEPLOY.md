# Moat field layer — what it needs before it can run

The worker is written and its logic is tested. It cannot be deployed from here:
it needs a Cloudflare account, a LINE channel, and secrets that only you can
issue. Everything below is a thing you have to do, not a thing I skipped.

## 1. Cloudflare

```bash
cd worker
npx wrangler kv namespace create MOAT_KV
```

Paste the returned id into `wrangler.toml` under `[[kv_namespaces]]`. Keep the
binding as `KV` — the title is `MOAT_KV`, the binding is `KV`, and wrangler's
own printed snippet gets this wrong. Then:

```bash
npx wrangler deploy
npx wrangler kv key put --binding=KV idx:v --path=field-index.json --remote
```

Rebuild and re-upload the index whenever Mot Dang's catalogue changes:

```bash
python3.13 tools/build_field_index.py
```

## 2. LINE

A Messaging API channel on the LINE Developers console, plus a LIFF app
pointing at `liff.html`. Point the channel webhook at
`https://<worker>/webhook/line`.

Per memory the `NaNoBotCo` LINE OA exists but is unverified — an unverified OA
can still do all of this, it just cannot be found in search, so the entry point
has to be a QR code or a link you hand people.

## 3. Secrets

```bash
npx wrangler secret put HASH_SALT
npx wrangler secret put LINE_TOKEN
npx wrangler secret put LINE_CHANNEL_SECRET
npx wrangler secret put LINE_CHANNEL_ID
npx wrangler secret put EXPORT_KEY
```

`HASH_SALT` is any long random string. **Rotating it makes every previously
stored user hash permanently unlinkable** — that is a feature, not a migration
problem. Rotate it whenever you feel like it.

## 4. Two things that are deliberately unfinished

Both are marked in `worker.js` and both are open on purpose rather than
silently missing, because pretending they exist would be worse than saying so:

- **Webhook signature verification** against `LINE_CHANNEL_SECRET`. Without it
  anybody who learns the URL can post fake events. Must be written before the
  webhook is pointed at a real channel.
- **LIFF id-token verification** on `POST /observe`. Until `LINE_CHANNEL_ID` is
  set, that route returns 503 and records nothing — the safe failure. Verify
  the token against LINE's endpoint before switching it on.

## 5. Before a single real player uses it

- Read `GET /privacy`. It is the complete list of what is kept, and it should
  stay complete. If a change makes it inaccurate, the change is wrong.
- The exclusion list lives in `tools/build_field_index.py` and is applied at
  **build** time — wats, hospitals, clinics, schools and homes are absent from
  the index, so no request can record against one. Currently 3,343 of the
  atlas's 10,673 places are excluded and 7,330 are loggable, of which 5,393
  have no hours at all.
- Nothing posts to the atlas automatically. `GET /export?key=…` emits a
  moderation payload; a person reads it and decides. Keep it that way.
