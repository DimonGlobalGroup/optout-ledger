#!/usr/bin/env python3
"""Smoke test for OptOut Ledger.

Copies optout.py into a temporary directory (the tool stores its data next
to itself), then exercises the real workflow end to end:
  init -> add a broker -> update a status -> list -> due -> report
and checks the data file and the HTML report.

Run:  python3 tests/test_smoke.py
Exit code 0 = pass.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "optout.py"


def run(workdir, *argv):
    r = subprocess.run(
        [sys.executable, "optout.py", *argv],
        cwd=workdir, capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(argv)}\nstdout: {r.stdout}\nstderr: {r.stderr}")
    return r.stdout


def main():
    tmp = Path(tempfile.mkdtemp(prefix="optout-ledger-smoke-"))
    try:
        shutil.copy(SRC, tmp / "optout.py")

        out = run(tmp, "init")
        assert "Seeded 30 brokers" in out, out
        data = json.loads((tmp / "brokers.json").read_text(encoding="utf-8"))
        assert len(data["brokers"]) == 30, len(data["brokers"])
        assert all(b["status"] == "not-started" for b in data["brokers"].values())
        print("init: OK (30 brokers seeded, all not-started)")

        out = run(tmp, "add", "Example Broker",
                  "--url", "https://example.com/opt-out", "--priority")
        assert "Added 'Example Broker'." in out, out
        print("add: OK")

        out = run(tmp, "update", "Example Broker", "submitted",
                  "--note", "Form submitted via smoke test")
        assert "not-started -> submitted" in out, out
        data = json.loads((tmp / "brokers.json").read_text(encoding="utf-8"))
        b = data["brokers"]["Example Broker"]
        assert b["status"] == "submitted"
        assert b["next_followup"], "active status must set a follow-up date"
        assert b["notes"] and "smoke test" in b["notes"][0]["text"]
        assert b["history"][-1]["to"] == "submitted"
        print(f"update: OK (follow-up set to {b['next_followup']})")

        out = run(tmp, "list", "--status", "submitted")
        assert "Example Broker" in out, out
        print("list: OK")

        out = run(tmp, "due")
        assert out.strip(), "due produced no output"
        print("due: OK")

        out = run(tmp, "report")
        assert "Opt-out campaign" in out, out
        page = tmp / "report.html"
        assert page.exists() and "Example Broker" in page.read_text(encoding="utf-8")
        print("report: OK (summary printed, report.html rendered)")

        print("\nSMOKE TEST PASSED")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
