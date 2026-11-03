#!/usr/bin/env python3
"""Turn the public Google Calendar "Eventi ad Assisi" into data/eventi-assisi.json.

Usage: python3 -I .github/scripts/eventi_assisi.py FEED.ics data/eventi-assisi.json

The workflow .github/workflows/eventi-assisi.yml downloads the feed and runs this
every day. The pages vivere-ad-assisi/ and en/life-in-assisi/ read the JSON.

Each event's description has up to three lines: the Italian text, a line that
starts with "EN: " (the English text) and a URL (the "Dettagli" link). Other
lines are ignored.

Kept: events that end today or later (Europe/Rome), sorted by start.
Repeating events (RRULE) are expanded for one year ahead: FREQ, INTERVAL,
COUNT, UNTIL and EXDATE are read, BYDAY only for weekly rules. Other BY* parts
are ignored. A changed occurrence (RECURRENCE-ID) replaces its date.

The file is written only when the list of events changes, so "aggiornato" is
the day of the last change. Standard library only.
"""
import datetime as dt
import html
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")
HORIZON_DAYS = 366
WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
URL = re.compile(r"https?://\S+")


def unfold(text):
    return re.sub(r"\r?\n[ \t]", "", text).splitlines()


def unescape(value):
    return re.sub(r"\\([\\,;nN])", lambda m: "\n" if m.group(1) in "nN" else m.group(1), value)


def parse(text):
    """The VEVENTs of the feed, each a dict {NAME: (params, value)}."""
    events, cur = [], None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            head, value = line.split(":", 1)
            name, *params = head.split(";")
            params = dict(p.split("=", 1) for p in params if "=" in p)
            if name == "EXDATE":
                cur.setdefault("EXDATE", []).append((params, value))
            else:
                cur[name.upper()] = (params, value)
    return events


def when(prop):
    """(local Rome datetime, all day?) of a DTSTART/DTEND-like property."""
    params, value = prop
    value = value.strip()
    if params.get("VALUE") == "DATE" or len(value) == 8:
        return dt.datetime.strptime(value[:8], "%Y%m%d"), True
    t = dt.datetime.strptime(value.rstrip("Z"), "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        t = t.replace(tzinfo=dt.timezone.utc)
    else:
        t = t.replace(tzinfo=ZoneInfo(params.get("TZID", "Europe/Rome")))
    return t.astimezone(ROME).replace(tzinfo=None), False


def description(raw):
    """(Italian text, English text, link) from the event description."""
    text = re.sub(r"<br\s*/?>|</p>|</div>", "\n", raw, flags=re.I)
    hrefs = re.findall(r'href="([^"]+)"', text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    it = en = link = ""
    for line in (l.strip() for l in text.splitlines()):
        if not line:
            continue
        if line[:3].upper() == "EN:":
            en = en or line[3:].strip()
        elif URL.fullmatch(line):
            link = link or line
        elif not it:
            it = line
    if not link and hrefs:
        link = hrefs[0]
    if not link:
        m = URL.search(text)
        link = m.group(0) if m else ""
    return it, en, link


def add_months(t, n):
    y, m = divmod(t.month - 1 + n, 12)
    try:
        return t.replace(year=t.year + y, month=m + 1)
    except ValueError:  # 31 in a short month: skip, like Google does
        return None


def occurrences(start, rule, limit):
    """Start times of a repeating event, up to limit."""
    r = dict(p.split("=", 1) for p in rule.split(";") if "=" in p)
    freq, step = r.get("FREQ"), int(r.get("INTERVAL", "1"))
    count = int(r["COUNT"]) if "COUNT" in r else None
    until = when(({}, r["UNTIL"]))[0] if "UNTIL" in r else None
    days = [WEEKDAYS.index(d[-2:]) for d in r.get("BYDAY", "").split(",") if d[-2:] in WEEKDAYS]
    out, i = [], 0
    while True:
        if freq == "DAILY":
            batch = [start + dt.timedelta(days=i * step)]
        elif freq == "WEEKLY":
            week = start + dt.timedelta(weeks=i * step)
            monday = week - dt.timedelta(days=week.weekday())
            batch = sorted(monday + dt.timedelta(days=d) for d in days) if days else [week]
            batch = [t for t in batch if t >= start]
        elif freq == "MONTHLY":
            batch = [t for t in [add_months(start, i * step)] if t]
        elif freq == "YEARLY":
            batch = [t for t in [add_months(start, 12 * i * step)] if t]
        else:
            return [start]
        for t in batch:
            if (until and t > until) or t > limit or (count is not None and len(out) >= count):
                return out
            out.append(t)
        i += 1


def build(text, today):
    limit = dt.datetime.combine(today + dt.timedelta(days=HORIZON_DAYS), dt.time())
    raw = parse(text)
    moved = {}  # (UID, original start) -> replacement event
    for ev in raw:
        if "RECURRENCE-ID" in ev:
            moved[(ev.get("UID", ({}, ""))[1], when(ev["RECURRENCE-ID"])[0])] = ev
    rows = []
    for ev in raw:
        if "DTSTART" not in ev or "RECURRENCE-ID" in ev:
            continue
        if ev.get("STATUS", ({}, ""))[1].upper() == "CANCELLED":
            continue
        start, all_day = when(ev["DTSTART"])
        if "DTEND" in ev:
            end = when(ev["DTEND"])[0]
        else:
            end = start + (dt.timedelta(days=1) if all_day else dt.timedelta())
        length = end - start
        starts = occurrences(start, ev["RRULE"][1], limit) if "RRULE" in ev else [start]
        skip = {when(p)[0] for p in ev.get("EXDATE", [])}
        uid = ev.get("UID", ({}, ""))[1]
        for s in starts:
            if s in skip:
                continue
            item = moved.get((uid, s))
            if item:
                if item.get("STATUS", ({}, ""))[1].upper() == "CANCELLED":
                    continue
                rows.append(row(item))
            else:
                rows.append(row(ev, s, s + length, all_day))
    rows = [r for r in rows if r and r["fine"] >= today.isoformat()]
    rows.sort(key=lambda r: (r["inizio"], r["ora"] or "99", r["titolo"]))
    return rows


def row(ev, start=None, end=None, all_day=None):
    if start is None:
        start, all_day = when(ev["DTSTART"])
        end = when(ev["DTEND"])[0] if "DTEND" in ev else start + dt.timedelta(days=1 if all_day else 0)
    if all_day:
        end -= dt.timedelta(days=1)  # the iCal end date is the day after
    end = max(end, start)
    it, en, link = description(unescape(ev.get("DESCRIPTION", ({}, ""))[1]))
    return {
        "inizio": start.date().isoformat(),
        "fine": end.date().isoformat(),
        "ora": "" if all_day else start.strftime("%H:%M"),
        "titolo": unescape(ev.get("SUMMARY", ({}, ""))[1]).strip(),
        "luogo": unescape(ev.get("LOCATION", ({}, ""))[1]).strip(),
        "descrizione_it": it,
        "descrizione_en": en,
        "link": link,
    }


def main():
    feed, out = sys.argv[1], sys.argv[2]
    with open(feed, encoding="utf-8") as f:
        text = f.read()
    if "BEGIN:VCALENDAR" not in text:
        sys.exit(f"{feed}: not an iCal feed")
    today = dt.datetime.now(ROME).date()
    events = build(text, today)
    old = None
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            old = json.load(f)
    if old and old.get("eventi") == events:
        print(f"{out}: no change ({len(events)} events)")
        return
    data = {"aggiornato": today.isoformat(), "fuso": "Europe/Rome", "eventi": events}
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{out}: {len(events)} events")


if __name__ == "__main__":
    main()
