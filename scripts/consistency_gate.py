import json, re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "verification"

def normalize(code):
    return re.sub(r"\s+", "", code or "")

rows = [json.loads(l) for l in (DATA / "h2_verified_write.jsonl").open()]

# Gate rule: diagnosis asserts a specific error AND extracted fix == original code -> DISCARD
# We already have per-row: intended, persisted (execution gate), fix_code, orig_code, fabricated label where known
res = {"correct": {"laundered": 0, "caught": 0, "kept_true": 0},
       "buggy": {"true_kept": 0, "true_discarded": 0}}

for r in rows:
    same = normalize(r.get("fix_code")) == normalize(r.get("orig_code"))
    asserts_error = r.get("asserts_error", None)
    if asserts_error is None:
        # fallback heuristic: diagnosis that was labeled F/SW/SC asserts an error
        asserts_error = r.get("label") in ("F", "SW", "SC")
    gate_discard = asserts_error and same
    if r["intended"] == "pass":
        if r.get("persisted"):
            if gate_discard: res["correct"]["caught"] += 1
            else: res["correct"]["laundered"] += 1
    else:
        if r.get("persisted"):
            if gate_discard: res["buggy"]["true_discarded"] += 1
            else: res["buggy"]["true_kept"] += 1

print(json.dumps(res, indent=2))
c = res["correct"]
tot = c["caught"] + c["laundered"]
if tot: print(f"\ncatch rate on laundered fabrications: {c['caught']}/{tot} = {c['caught']/tot:.0%}")
b = res["buggy"]
print(f"true-lesson false-discard rate: {b['true_discarded']}/{b['true_discarded']+b['true_kept']}")
