import json
import random
from pathlib import Path

SEED = 23024

cases = {
    r["case_id"]: r
    for r in json.load(open("h23_authority_cases_27.json"))
}

outs = [
    json.loads(x)
    for x in open("h23_authority_outputs.jsonl")
    if x.strip()
]

assert len(outs) == 54
assert len({(r["case_id"], r["condition"]) for r in outs}) == 54

items = []

for r in outs:
    c = cases[r["case_id"]]

    items.append({
        "case_id": r["case_id"],
        "condition": r["condition"],
        "id": r["id"],
        "src_model": r["src_model"],
        "lesson": c["lesson"],
        "original_code": c["code"],
        "test": c["test"],
        "output": r["output"],
    })

rng = random.Random(SEED)
rng.shuffle(items)

blind = []
key = []

for n, r in enumerate(items):
    blind.append({
        "n": n,
        "lesson": r["lesson"],
        "original_code": r["original_code"],
        "test": r["test"],
        "output": r["output"],
    })

    key.append({
        "n": n,
        "case_id": r["case_id"],
        "condition": r["condition"],
        "id": r["id"],
        "src_model": r["src_model"],
    })

Path("h23_blind.json").write_text(json.dumps(blind, indent=2) + "\n")
Path("h23_blind_key.json").write_text(json.dumps(key, indent=2) + "\n")

print("SEED =", SEED)
print("BLIND N =", len(blind))
print("KEY N =", len(key))
print("BLINDING=PASS")
