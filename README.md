# OptOut Ledger

**Run a data-broker opt-out campaign like a project — not like a pile of browser tabs.**

Data brokers publish your name, addresses, phone numbers, and relatives, then
make you opt out one site at a time. Most people submit a few forms, forget
which ones, miss the follow-ups, and give up. OptOut Ledger turns the whole
campaign into one tracked list: every broker, its status, its next follow-up
date, and a dated history of everything you did — so removals actually finish.

- **One file.** A single Python script. No dependencies, no install step.
- **No accounts, no cloud.** Your campaign data lives in one JSON file on your
  machine. The tool makes no network calls, ever.
- **Seeded and ready.** Ships with a starter list of 30 well-known brokers,
  priority-first, plus a status workflow and 14-day follow-up reminders.
- **Proof built in.** Every status change is timestamped in a per-broker
  history, and one command renders a clean HTML dashboard of the campaign.

By **Dimon Global Group**.

## Why

Opting out works — brokers do remove listings — but the process is designed
to wear you down: dozens of sites, different forms, confirmation emails,
"processing" queues, and listings that quietly come back. The failure mode
isn't the forms; it's losing track. A ledger fixes that. You always know:

- which brokers you have not started,
- which submissions are aging and due a follow-up nudge,
- which removals are confirmed done,
- and what you did, when, for every single broker.

Your data never leaves your computer, because the tool has no way to send it
anywhere. That is a deliberate design choice: a privacy tool should not be a
new privacy risk.

## Requirements

- Python 3.8+ (standard library only — nothing to install)

## Usage

```bash
# 1. Seed the broker list (creates brokers.json next to the script)
python3 optout.py init

# 2. See the campaign
python3 optout.py list
python3 optout.py list --status not-started

# 3. Work a broker: submit the opt-out on the broker's site, then record it
python3 optout.py update FastPeopleSearch submitted --note "Form submitted"

#    Statuses: not-started -> submitted -> in-progress
#              -> removed | failed | not-found
#    Entering an active status automatically sets a follow-up 14 days out
#    (override with --followup-days N).

# 4. Check what needs a nudge today
python3 optout.py due

# 5. Add a broker that is not on the list yet
python3 optout.py add "Some New Broker" --url "https://example.com/opt-out" --priority

# 6. Render the report (summary in the terminal + report.html dashboard)
python3 optout.py report
```

`init --force` reseeds from scratch and wipes existing campaign data — use it
only when you mean to start over.

## How it works

- Campaign state is a single human-readable file, `brokers.json`, stored next
  to `optout.py`. Back it up like any document.
- Status transitions are validated: you cannot jump from `not-started`
  straight to `removed`, so the ledger reflects the real process. Terminal
  states (`removed`, `failed`) can be reopened to `submitted` if a listing
  reappears or a retry is needed.
- Notes and a full timestamped history are kept per broker — your proof of
  submission when a broker claims they never received it.

## What it does not do

- It does **not** submit opt-outs for you, visit broker sites, or send email.
  You file each opt-out yourself; the ledger tracks the campaign.
- It does not guarantee removal — brokers control their own queues. It
  guarantees you will not lose track of one.

## License

MIT — see [LICENSE](LICENSE).

---

*OptOut Ledger v1.0.0 — by Dimon Global Group.*
