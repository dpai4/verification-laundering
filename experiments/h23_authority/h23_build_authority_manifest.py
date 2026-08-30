import json
import random
from pathlib import Path

SEED = 23023

bank = {r["id"]: r for r in json.load(open("verified_bank_v2.json"))}

h11 = [
    json.loads(x)
    for x in open("h11_injected_gate.jsonl")
    if x.strip()
]

assert len(h11) == 27

texts = {}
for line in open("h2_verified_v2.jsonl"):
    r = json.loads(line)
    if r.get("arm") == "present":
        texts[(r["model"], r["id"])] = r["diagnosis"]

cases = []
seen = set()

for r in h11:
    key = (r["src_model"], r["id"])
    assert key not in seen, key
    seen.add(key)

    iid = r["id"]

    assert iid in bank, iid
    assert bank[iid]["intended"] == "pass"
    assert key in texts, key

    cases.append({
        "case_id": len(cases),
        "src_model": r["src_model"],
        "id": iid,
        "lesson": texts[key],
        "code": bank[iid]["code"],
        "test": bank[iid]["test"],
        "truth": bank[iid]["truth"],
    })

assert len(cases) == 27

requests = []

for c in cases:
    for condition in ["control", "verified"]:
        requests.append({
            **c,
            "condition": condition,
        })

random.Random(SEED).shuffle(requests)

Path("h23_authority_cases_27.json").write_text(
    json.dumps(cases, indent=2) + "\n"
)

Path("h23_authority_requests_54.json").write_text(
    json.dumps(requests, indent=2) + "\n"
)

print("SEED =", SEED)
print("CASES =", len(cases))
print("REQUESTS =", len(requests))
print("UNIQUE CASES =", len({r["case_id"] for r in requests}))

assert len(requests) == 54
assert len({(r["case_id"], r["condition"]) for r in requests}) == 54

print("AUTHORITY_MANIFEST=PASS")
