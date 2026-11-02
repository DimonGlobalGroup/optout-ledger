# Changelog

All notable changes to OptOut Ledger are recorded here.

## [1.0.0] — 2026-11-01

First public edition.

- Single-file, standard-library-only Python CLI (`optout.py`) — no
  dependencies, no accounts, no network calls.
- Commands: `init`, `list`, `due`, `update`, `add`, `report`.
- Seeds a starter campaign of 30 data brokers, priority-first, each with a
  status, notes, and a timestamped history.
- Validated status workflow:
  `not-started -> submitted -> in-progress -> removed | failed | not-found`,
  with terminal states reopenable to `submitted`.
- Automatic 14-day follow-up dates on active statuses (configurable per
  update), surfaced by the `due` command.
- `report` prints a campaign summary and renders a self-contained HTML
  dashboard (`report.html`).
