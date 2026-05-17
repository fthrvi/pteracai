#!/usr/bin/env python3
"""Migrate bank.json from v1 (flat) to v2 (keyed by test).

v1 shape:
    { "version": 1, "tips": {...}, "questions": [...] }

v2 shape:
    {
      "schema": 2,
      "tests": {
        "pte":   { "label": "PTE Academic", "tips": {...}, "questions": [...] },
        "ielts": { "label": "IELTS Academic", "tips": {...}, "questions": [...] }
      }
    }

Idempotent — running on v2 leaves it unchanged.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


def migrate():
    raw = json.loads(BANK.read_text())
    if raw.get("schema") == 2:
        print("Already v2 — no change.")
        return
    new = {
        "schema": 2,
        "tests": {
            "pte": {
                "label": "PTE Academic",
                "short": "PTE",
                "tips": raw.get("tips", {}),
                "questions": raw.get("questions", []),
            },
            "ielts": {
                "label": "IELTS Academic",
                "short": "IELTS",
                "tips": {},
                "questions": [],
            },
        },
    }
    BANK.write_text(json.dumps(new, indent=2, ensure_ascii=False))
    print(f"Migrated to v2. PTE: {len(new['tests']['pte']['questions'])} questions, "
          f"{sum(len(v) for v in new['tests']['pte']['tips'].values())} tips. IELTS: empty (ready for content).")


if __name__ == "__main__":
    migrate()
