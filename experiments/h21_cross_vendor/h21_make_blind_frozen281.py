import json
import random
from pathlib import Path

INPUT = Path("h21_cross_vendor.jsonl")
BLIND = Path("h21_blind_items.txt")
JUDGE = Path("h21_blind_items_judge.txt")
KEY = Path("h21_blind_key.jsonl")

SEED = 21041

if not INPUT.exists():
    raise SystemExit(
        "h21_cross_vendor.jsonl does not exist yet. "
        "Run this after H21 finishes."
    )

rows = [json.loads(x) for x in INPUT.open() if x.strip()]

if len(rows) != 281:
    raise SystemExit(
        f"REFUSING TO BLIND: expected 281 rows, got {len(rows)}"
    )

keys = [(r["model"], r["arm"], r["id"]) for r in rows]
if len(keys) != len(set(keys)):
    raise SystemExit("REFUSING TO BLIND: duplicate model/arm/id keys")

# Deliberately exclude vendor/model/arm from grader-visible material.
items = []

for r in rows:
    items.append({
        "model": r["model"],
        "arm": r["arm"],
        "id": r["id"],
        "intended": r["intended"],
        "truth": r["truth"],
        "diagnosis": r["diagnosis"],
    })

rng = random.Random(SEED)
rng.shuffle(items)

with BLIND.open("w") as f_blind, \
     JUDGE.open("w") as f_judge, \
     KEY.open("w") as f_key:

    for n, r in enumerate(items):

        ptype = "BUGGY" if r["intended"] == "fail" else "CORRECT"

        # Human-facing file: no truth shown.
        f_blind.write(
            f"=== ITEM {n:03d} | program-type: {ptype} ===\n"
        )
        f_blind.write(r["diagnosis"].strip() + "\n\n")
        f_blind.write(f"LABEL {n:03d}: \n\n")

        # Judge-facing file:
        # BUGGY needs ground-truth bug to distinguish SC vs SW.
        f_judge.write(
            f"=== ITEM {n:03d} | program-type: {ptype} ===\n"
        )

        if r["intended"] == "fail":
            f_judge.write(
                f"GROUND-TRUTH BUG: {r['truth']}\n"
            )

        f_judge.write(
            "DIAGNOSIS:\n"
            + r["diagnosis"].strip()
            + "\n\n"
        )

        f_key.write(json.dumps({
            "n": n,
            "model": r["model"],
            "arm": r["arm"],
            "id": r["id"],
            "intended": r["intended"],
        }) + "\n")

print("H21 blind dataset created")
print("items:", len(items))
print("seed:", SEED)
print("human:", BLIND)
print("judge:", JUDGE)
print("key:", KEY)
