#!/usr/bin/env python3
"""optout.py — local data-broker opt-out campaign tracker.

LOCAL ONLY: no network calls, no accounts, no credentials, no auto-submission.
You perform every opt-out yourself on each broker's site; this tool only
tracks the campaign: who is done, who is pending, and who is due a follow-up.

Usage:
  python3 optout.py init [--force]
  python3 optout.py list [--status STATUS]
  python3 optout.py due
  python3 optout.py update <broker> <status> [--note TEXT] [--followup-days N]
  python3 optout.py add <broker> [--url URL] [--method TEXT] [--priority]
  python3 optout.py report

Statuses: not-started -> submitted -> in-progress -> removed | failed | not-found
"""

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
JSON_PATH = DATA_DIR / "brokers.json"
HTML_PATH = DATA_DIR / "report.html"

STATUSES = ["not-started", "submitted", "in-progress", "removed", "failed", "not-found"]
ACTIVE = {"submitted", "in-progress"}
TERMINAL = {"removed", "failed", "not-found"}

# Allowed transitions; terminal states may be reopened to 'submitted'.
TRANSITIONS = {
    "not-started": {"submitted", "not-found"},
    "submitted": {"in-progress", "removed", "failed", "not-found"},
    "in-progress": {"submitted", "removed", "failed", "not-found"},
    "removed": {"submitted"},
    "failed": {"submitted"},
    "not-found": set(),
}

DEFAULT_FOLLOWUP_DAYS = 14

# (name, opt_out_url, method, priority)
SEED = [
    ("FastPeopleSearch", "https://www.fastpeoplesearch.com/do-not-sell",
     "Opt-Out Form, or call (866) 679-8725", True),
    ("MyLife", "", "", False),
    ("TruthFinder", "", "", False),
    ("Intelius", "", "", False),
    ("Spokeo", "", "", False),
    ("BeenVerified", "", "", False),
    ("Whitepages", "", "", False),
    ("PeopleFinders", "", "", False),
    ("ClustrMaps", "", "", False),
    ("TruePeopleSearch", "", "", False),
    ("Pipl", "", "", False),
    ("IDCrawl", "", "", False),
    ("uFind", "", "", False),
    ("AllPeople", "", "", False),
    ("addresses.com", "", "", False),
    ("ThatsThem", "", "", False),
    ("Nuwber", "", "", False),
    ("411.com", "", "", False),
    ("CyberBackgroundChecks", "", "", False),
    ("StateCourts.org", "", "", False),
    ("PublicRecords/PeopleLooker", "", "", False),
    ("Swordfish.ai", "", "", False),
    ("Apollo", "", "", False),
    ("LeadIQ", "", "", False),
    ("OpenPeopleSearch", "", "", False),
    ("Sync.ME", "", "", False),
    ("Yellow Pages Directory", "", "", False),
    ("ConfidentialPhoneLookup", "", "", False),
    ("Areacode-Lookup", "", "", False),
    ("Alabama Arrests", "", "Via Infotracer — opt-out email privacy@infotracer.com", False),
]


def today():
    return dt.date.today().isoformat()


def now_ts():
    return dt.datetime.now().isoformat(timespec="seconds")


def load():
    if not JSON_PATH.exists():
        sys.exit("No data file. Run: python3 optout.py init")
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def save(data):
    data["meta"]["updated"] = now_ts()
    JSON_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def find_broker(data, name):
    key = name.strip().lower()
    exact = [n for n in data["brokers"] if n.lower() == key]
    if exact:
        return exact[0]
    subs = [n for n in data["brokers"] if key in n.lower()]
    if len(subs) == 1:
        return subs[0]
    if not subs:
        sys.exit(f"No broker matching '{name}'.")
    sys.exit(f"Ambiguous '{name}' — matches: {', '.join(subs)}")


def cmd_init(args):
    if JSON_PATH.exists() and not args.force:
        sys.exit("brokers.json already exists. Use --force to reseed (wipes current data).")
    data = {"meta": {"created": now_ts(), "updated": now_ts()}, "brokers": {}}
    for name, url, method, priority in SEED:
        data["brokers"][name] = {
            "name": name,
            "opt_out": url,
            "method": method,
            "status": "not-started",
            "priority": priority,
            "notes": [],
            "history": [{"ts": now_ts(), "from": None, "to": "not-started",
                         "note": "seeded"}],
            "next_followup": None,
        }
    save(data)
    print(f"Seeded {len(SEED)} brokers -> {JSON_PATH}")


def fmt_row(b):
    star = "*" if b.get("priority") else " "
    due = b.get("next_followup") or "-"
    return f"{star} {b['name']:<28} {b['status']:<12} next-followup: {due}"


def cmd_list(args):
    data = load()
    brokers = sorted(data["brokers"].values(),
                     key=lambda b: (not b.get("priority"), b["name"].lower()))
    if args.status:
        if args.status not in STATUSES:
            sys.exit(f"Bad status. Choose from: {', '.join(STATUSES)}")
        brokers = [b for b in brokers if b["status"] == args.status]
    for b in brokers:
        print(fmt_row(b))
    print(f"\n{len(brokers)} shown (* = priority)")


def due_list(data):
    t = today()
    out = [b for b in data["brokers"].values()
           if b["status"] in ACTIVE and b.get("next_followup") and b["next_followup"] <= t]
    return sorted(out, key=lambda b: (b["next_followup"], b["name"].lower()))


def cmd_due(_args):
    data = load()
    due = due_list(data)
    if not due:
        print("Nothing due. No active broker is past its follow-up date.")
        return
    for b in due:
        print(fmt_row(b))
        if b.get("method"):
            print(f"    method: {b['method']}")
        if b.get("opt_out"):
            print(f"    opt-out: {b['opt_out']}")
    print(f"\n{len(due)} due")


def cmd_update(args):
    data = load()
    name = find_broker(data, args.broker)
    b = data["brokers"][name]
    new = args.status
    if new not in STATUSES:
        sys.exit(f"Bad status. Choose from: {', '.join(STATUSES)}")
    old = b["status"]
    if new != old and new not in TRANSITIONS[old]:
        sys.exit(f"Illegal transition {old} -> {new}. "
                 f"Allowed from '{old}': {sorted(TRANSITIONS[old]) or ['none']}")
    b["status"] = new
    note = args.note or ""
    if note:
        b["notes"].append({"ts": now_ts(), "text": note})
    b["history"].append({"ts": now_ts(), "from": old, "to": new, "note": note})
    if new in ACTIVE:
        days = args.followup_days if args.followup_days is not None else DEFAULT_FOLLOWUP_DAYS
        b["next_followup"] = (dt.date.today() + dt.timedelta(days=days)).isoformat()
    else:
        b["next_followup"] = None
    save(data)
    print(f"{name}: {old} -> {new}"
          + (f" (follow up {b['next_followup']})" if b["next_followup"] else ""))


def cmd_add(args):
    data = load()
    name = args.broker.strip()
    if any(n.lower() == name.lower() for n in data["brokers"]):
        sys.exit(f"'{name}' is already tracked.")
    data["brokers"][name] = {
        "name": name,
        "opt_out": args.url or "",
        "method": args.method or "",
        "status": "not-started",
        "priority": bool(args.priority),
        "notes": [],
        "history": [{"ts": now_ts(), "from": None, "to": "not-started", "note": "added"}],
        "next_followup": None,
    }
    save(data)
    print(f"Added '{name}'.")


COLORS = {
    "not-started": "#6b7280", "submitted": "#d97706", "in-progress": "#2563eb",
    "removed": "#16a34a", "failed": "#dc2626", "not-found": "#7c3aed",
}


def cmd_report(_args):
    data = load()
    brokers = sorted(data["brokers"].values(),
                     key=lambda b: (not b.get("priority"), b["name"].lower()))
    counts = {s: 0 for s in STATUSES}
    for b in brokers:
        counts[b["status"]] += 1
    due = due_list(data)

    print("== Opt-out campaign ==")
    for s in STATUSES:
        print(f"  {s:<12} {counts[s]}")
    print(f"  {'TOTAL':<12} {len(brokers)}")
    print(f"  {'due now':<12} {len(due)}")

    rows = []
    for b in brokers:
        star = "&#9733; " if b.get("priority") else ""
        color = COLORS[b["status"]]
        notes = "<br>".join(html.escape(f"{n['ts']}: {n['text']}") for n in b["notes"][-3:])
        rows.append(
            "<tr><td>{star}{name}</td>"
            "<td><span class='badge' style='background:{color}'>{status}</span></td>"
            "<td>{due}</td><td>{method}</td><td>{notes}</td></tr>".format(
                star=star, name=html.escape(b["name"]), color=color,
                status=html.escape(b["status"]),
                due=html.escape(b.get("next_followup") or "-"),
                method=html.escape(b.get("method") or b.get("opt_out") or "-"),
                notes=notes))

    page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Opt-out campaign report</title>
<style>
body{{font-family:system-ui,sans-serif;background:#111827;color:#e5e7eb;margin:0;padding:24px}}
h1{{font-size:1.4em}} .meta{{color:#9ca3af;font-size:.9em;margin-bottom:16px}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
.card{{background:#1f2937;border-radius:8px;padding:12px 16px;min-width:110px}}
.card b{{font-size:1.6em;display:block}} .badge{{color:#fff;border-radius:4px;padding:2px 8px;font-size:.85em}}
table{{border-collapse:collapse;width:100%;font-size:.9em}}
th,td{{text-align:left;padding:8px;border-bottom:1px solid #374151;vertical-align:top}}
th{{color:#9ca3af}} a{{color:#93c5fd}}
</style></head><body>
<h1>Opt-out campaign report</h1>
<div class="meta">Generated {ts} &middot; local only, no data leaves this machine</div>
<div class="cards">{cards}</div>
<h2>Follow-ups due ({ndue})</h2>
<p>{duenames}</p>
<h2>Brokers ({n})</h2>
<table><tr><th>Broker</th><th>Status</th><th>Next follow-up</th><th>Method</th><th>Recent notes</th></tr>
{rows}
</table></body></html>""".format(
        ts=html.escape(now_ts()),
        cards="".join(
            f"<div class='card'><b>{counts[s]}</b>{s}</div>" for s in STATUSES),
        ndue=len(due),
        duenames=html.escape(", ".join(b["name"] for b in due) or "none"),
        n=len(brokers),
        rows="\n".join(rows))
    HTML_PATH.write_text(page, encoding="utf-8")
    print(f"HTML report -> {HTML_PATH}")


def main():
    ap = argparse.ArgumentParser(description="Local data-broker opt-out campaign tracker.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="seed the broker list")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("list", help="list brokers")
    p.add_argument("--status", default=None)
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("due", help="follow-ups due today or earlier")
    p.set_defaults(fn=cmd_due)

    p = sub.add_parser("update", help="change a broker's status")
    p.add_argument("broker")
    p.add_argument("status")
    p.add_argument("--note", default="")
    p.add_argument("--followup-days", type=int, default=None)
    p.set_defaults(fn=cmd_update)

    p = sub.add_parser("add", help="track a new broker")
    p.add_argument("broker")
    p.add_argument("--url", default="")
    p.add_argument("--method", default="")
    p.add_argument("--priority", action="store_true")
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser("report", help="summary + HTML dashboard")
    p.set_defaults(fn=cmd_report)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
