#!/usr/bin/env python3
"""Manage which real businesses the game is currently allowed to name.

Consent here is a dead-man's switch. A grant carries a term; when it runs out
the game stops using the real name on its own and the venue falls back to its
fictional composite. To keep a business featured you have to go back and ask
again. Silence lapses a permission — it never extends one.

    python3.13 tools/consent.py report
    python3.13 tools/consent.py grant v01234 --name "…" --scope "…" \
        --contact "…" --days 180
    python3.13 tools/consent.py renew v01234 --days 180
    python3.13 tools/consent.py withdraw v01234
    python3.13 tools/consent.py pending v01234 --contact "…"

Written to be run from the numbered-menu side of things too: `report` alone
tells you who to visit this month.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
DATA = HERE / "data" / "venues.json"
sys.path.insert(0, str(HERE))

from game import venues as V   # noqa: E402


def _load() -> dict:
    return json.loads(DATA.read_text())


def _save(doc: dict) -> None:
    DATA.write_text(json.dumps(doc, ensure_ascii=False, indent=1))


def _find(doc: dict, key: str) -> dict:
    for v in doc["venues"]:
        if v["key"] == key:
            return v
    raise SystemExit(f"no venue {key!r}")


def cmd_grant(a) -> None:
    doc = _load()
    v = _find(doc, a.key)
    today = _dt.date.today()
    v["consent"].update({
        "status": "granted",
        "real_name": a.name,
        "granted_on": today.isoformat(),
        "expires_on": (today + _dt.timedelta(days=a.days)).isoformat(),
        "term_days": a.days,
        "last_asked": today.isoformat(),
        "scope": a.scope,
        "contact": a.contact,
    })
    _save(doc)
    print(f"{a.key}: '{a.name}' named until "
          f"{v['consent']['expires_on']} ({a.days} days), then it lapses.")


def cmd_renew(a) -> None:
    doc = _load()
    v = _find(doc, a.key)
    c = v["consent"]
    if not c.get("real_name"):
        raise SystemExit(f"{a.key} has never been granted — use 'grant'.")
    today = _dt.date.today()
    c.update({
        "status": "granted",
        "expires_on": (today + _dt.timedelta(days=a.days)).isoformat(),
        "term_days": a.days,
        "renewals": int(c.get("renewals", 0)) + 1,
        "last_asked": today.isoformat(),
    })
    _save(doc)
    print(f"{a.key}: '{c['real_name']}' renewed to {c['expires_on']} "
          f"(renewal #{c['renewals']}).")


def cmd_withdraw(a) -> None:
    doc = _load()
    v = _find(doc, a.key)
    v["consent"].update({"status": "withdrawn",
                         "expires_on": _dt.date.today().isoformat()})
    _save(doc)
    print(f"{a.key}: withdrawn. The game falls back to "
          f"'{v['descriptor']}' immediately.")


def cmd_pending(a) -> None:
    doc = _load()
    v = _find(doc, a.key)
    v["consent"].update({"status": "pending", "contact": a.contact,
                         "last_asked": _dt.date.today().isoformat()})
    _save(doc)
    print(f"{a.key}: marked as asked, awaiting an answer.")


def cmd_report(a) -> None:
    today = _dt.date.today()
    rep = V.consent_report(today)
    print(f"== Naming permissions, {today.isoformat()} ==")
    print(f"  live:     {len(rep['live'])}")
    print(f"  pending:  {len(rep['pending'])}")
    print(f"  lapsed:   {len(rep['lapsed'])}")
    if rep["expiring"]:
        print(f"\n  Go and ask again — lapsing within "
              f"{V.RENEWAL_WARNING_DAYS} days:")
        for d, v in rep["expiring"]:
            print(f"    {v.key}  {v.consent['real_name']}  ({v.district}) "
                  f"— {d} days left, contact {v.consent.get('contact') or '?'}")
    if rep["lapsed"]:
        print("\n  Already lapsed — the game is calling these by descriptor:")
        for v in rep["lapsed"]:
            print(f"    {v.key}  was '{v.consent['real_name']}'  ({v.district})"
                  f" — now '{v.descriptor}', contact "
                  f"{v.consent.get('contact') or '?'}")
    if not rep["live"] and not rep["pending"] and not rep["lapsed"]:
        print("\n  No real business is named in the game right now. Every venue "
              "is a fictional composite.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grant", help="permission to use a real name")
    g.add_argument("key")
    g.add_argument("--name", required=True)
    g.add_argument("--scope", required=True,
                   help="what the owner actually agreed to, in their words")
    g.add_argument("--contact", required=True)
    g.add_argument("--days", type=int, default=180)
    g.set_defaults(func=cmd_grant)

    r = sub.add_parser("renew", help="they said yes again")
    r.add_argument("key")
    r.add_argument("--days", type=int, default=180)
    r.set_defaults(func=cmd_renew)

    w = sub.add_parser("withdraw", help="they changed their mind")
    w.add_argument("key")
    w.set_defaults(func=cmd_withdraw)

    p = sub.add_parser("pending", help="asked, waiting on an answer")
    p.add_argument("key")
    p.add_argument("--contact", required=True)
    p.set_defaults(func=cmd_pending)

    rep = sub.add_parser("report", help="who is live, lapsing, or lapsed")
    rep.set_defaults(func=cmd_report)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
