#!/usr/bin/env python3
"""Planlægger for fødselsdagshilsner og "jeg tænkte på dig"-beskeder.

Brug:
  python3 scripts/omsorg.py plan [--date YYYY-MM-DD]
      Udskriver (JSON) dagens fødselsdage, kommende fødselsdage og
      hvem der står for tur til en check-in-besked.

  python3 scripts/omsorg.py record <id> <birthday|checkin> "<beskedtekst>" [--date YYYY-MM-DD]
      Logger en foreslået/sendt besked og planlægger næste check-in
      om 4-6 uger (tilfældigt 28-42 dage).

  python3 scripts/omsorg.py init [--date YYYY-MM-DD]
      Fordeler første check-in for alle uden planlagt dato jævnt over
      de næste 5 uger (køres automatisk af plan, hvis nødvendigt).

Ingen eksterne afhængigheder.
"""
import argparse
import datetime as dt
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTACTS = ROOT / "data" / "contacts.json"
STATE = ROOT / "data" / "state.json"
LOG = ROOT / "data" / "messages.jsonl"

MIN_DAYS, MAX_DAYS = 28, 42      # 4-6 uger mellem check-ins
MAX_CHECKINS_PER_DAY = 2         # så det ikke bliver uoverskueligt
UPCOMING_DAYS = 7                # varsel om kommende fødselsdage
BIRTHDAY_QUIET_DAYS = 10         # ingen check-in tæt på fødselsdag


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_state(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")


def contacts():
    return load_json(CONTACTS, {"contacts": []})["contacts"]


def next_birthday(mmdd, today):
    m, d = map(int, mmdd.split("-"))
    for year in (today.year, today.year + 1):
        try:
            day = dt.date(year, m, d)
        except ValueError:  # 29/2 i ikke-skudår
            day = dt.date(year, 3, 1)
        if day >= today:
            return day
    return None


def days_to_birthday(c, today):
    if not c.get("birthday"):
        return None
    return (next_birthday(c["birthday"], today) - today).days


def days_since_birthday(c, today):
    if not c.get("birthday"):
        return None
    m, d = map(int, c["birthday"].split("-"))
    past = []
    for year in (today.year - 1, today.year):
        try:
            day = dt.date(year, m, d)
        except ValueError:
            day = dt.date(year, 3, 1)
        if day <= today:
            past.append(day)
    return (today - max(past)).days


def init_state(state, today):
    pending = [c for c in contacts() if c["id"] not in state or
               (c.get("checkin") and not state[c["id"]].get("next_checkin"))]
    random.Random(today.isoformat()).shuffle(pending)
    span = 35
    for c in pending:
        s = state.setdefault(c["id"], {"last_checkin": None, "last_birthday_greeting": None})
        s["next_checkin"] = None
    pending = [c for c in pending if c.get("checkin")]
    for i, c in enumerate(pending):
        offset = round(i * span / max(len(pending), 1))
        state[c["id"]]["next_checkin"] = (today + dt.timedelta(days=offset)).isoformat()
    return state


def last_messages(cid, n=3):
    if not LOG.exists():
        return []
    rows = [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in rows if r["id"] == cid][-n:]


def plan(today):
    state = load_json(STATE, {})
    if any(c["id"] not in state or (c.get("checkin") and not state[c["id"]].get("next_checkin"))
           for c in contacts()):
        init_state(state, today)
        save_state(state)

    out = {"date": today.isoformat(), "birthdays_today": [], "birthdays_upcoming": [],
           "checkins_due": [], "checkins_postponed": []}
    due = []
    for c in contacts():
        if c.get("paused"):
            continue
        s = state[c["id"]]
        info = {"id": c["id"], "name": c["name"], "group": c["group"],
                "relation": c.get("relation"), "notes": c.get("notes", ""),
                "checkin_greeting": c.get("checkin_greeting"),
                "contact_by": c.get("contact_by", "besked"),
                "recent_messages": last_messages(c["id"])}
        dtb = days_to_birthday(c, today)
        if dtb == 0:
            if s.get("last_birthday_greeting") != today.isoformat():
                out["birthdays_today"].append(info)
        elif dtb is not None and dtb <= UPCOMING_DAYS:
            out["birthdays_upcoming"].append({**info, "in_days": dtb,
                                              "date": next_birthday(c["birthday"], today).isoformat()})
        if not c.get("checkin") or not s.get("next_checkin"):
            continue
        nxt = dt.date.fromisoformat(s["next_checkin"])
        if nxt <= today:
            near_bday = (dtb is not None and dtb <= BIRTHDAY_QUIET_DAYS) or \
                        (days_since_birthday(c, today) or 99) < 14
            if near_bday:
                out["checkins_postponed"].append({"id": c["id"], "name": c["name"],
                                                  "reason": "tæt på fødselsdag"})
            else:
                due.append(((today - nxt).days, info))
    due.sort(key=lambda x: -x[0])
    out["checkins_due"] = [{**i, "days_overdue": d} for d, i in due[:MAX_CHECKINS_PER_DAY]]
    out["birthdays_upcoming"].sort(key=lambda x: x["in_days"])
    return out


def norm(t):
    return " ".join("".join(ch for ch in t.lower() if ch.isalnum() or ch.isspace()).split())


def record(cid, kind, text, today):
    ids = {c["id"] for c in contacts()}
    if cid not in ids:
        raise SystemExit(f"Ukendt id: {cid}")
    prev = last_messages(cid, 2)
    if any(norm(r["text"]) == norm(text) for r in prev) and not text.startswith("("):
        raise SystemExit("Afvist: samme besked som en af de seneste til denne person. Skriv en ny.")
    contact = next(c for c in contacts() if c["id"] == cid)
    state = load_json(STATE, {})
    if cid not in state:
        init_state(state, today)
    s = state[cid]
    if kind == "birthday":
        s["last_birthday_greeting"] = today.isoformat()
        # en fødselsdagshilsen tæller også som kontakt
        if contact.get("checkin"):
            s["next_checkin"] = (today + dt.timedelta(days=random.randint(MIN_DAYS, MAX_DAYS))).isoformat()
    else:
        s["last_checkin"] = today.isoformat()
        s["next_checkin"] = (today + dt.timedelta(days=random.randint(MIN_DAYS, MAX_DAYS))).isoformat()
    save_state(state)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"date": today.isoformat(), "id": cid, "type": kind, "text": text},
                           ensure_ascii=False) + "\n")
    print(json.dumps({"id": cid, **s}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["plan", "record", "init"])
    p.add_argument("args", nargs="*")
    p.add_argument("--date")
    a = p.parse_args()
    today = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    if a.cmd == "plan":
        print(json.dumps(plan(today), ensure_ascii=False, indent=2))
    elif a.cmd == "init":
        save_state(init_state(load_json(STATE, {}), today))
    else:
        if len(a.args) != 3 or a.args[1] not in ("birthday", "checkin"):
            raise SystemExit('Brug: record <id> <birthday|checkin> "<tekst>"')
        record(*a.args, today)


if __name__ == "__main__":
    main()
