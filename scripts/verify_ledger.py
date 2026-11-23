"""Verify the hash chain of runs/ledger.jsonl."""
import hashlib
import json
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "runs" / "ledger.jsonl"
prev = "0" * 64
for i, line in enumerate(LEDGER.read_text().splitlines(), 1):
    rec = json.loads(line)
    h = rec.pop("hash")
    if rec["prev_hash"] != prev or hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest() != h:
        sys.exit(f"ledger broken at line {i}")
    prev = h
print(f"ledger OK: {i} records")
