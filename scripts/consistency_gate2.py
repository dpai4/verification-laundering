import json, re, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT / "data" / "verification")

def norm(code): return re.sub(r"\s+", "", code or "")

bank = {b["id"]: b for b in json.load(open("../verified_bank_v2.json"))}

# rebuild final presup labels: agreed grader labels overridden by human adjudications
def load(path):
    d = {}
    for line in open(path):
        m = re.match(r"\s*(\d+)\s*:\s*([A-Z]{1,2})", line)
        if m: d[int(m.group(1))] = m.group(2)
    return d
a, b_ = load("labels_a.txt"), load("all_labels.txt")
human = {}
for line in open("adjudicate_final.txt"):
    m = re.match(r"FINAL\s+(\d+)\s*:\s*([A-Z]{1,2})", line)
    if m: human[int(m.group(1))] = m.group(2)
key = {json.loads(l)["n"]: json.loads(l) for l in open("blind_key.jsonl")}
label = {}
for n, meta in key.items():
    if meta.get("arm") == "presup":
        resolved = human[n] if n in human else a.get(n)
        if resolved is not None:
            label[(meta["model"], meta["id"])] = resolved

rows = [json.loads(l) for l in open("h2_verified_write.jsonl")]
res = {"laundered_kept": 0, "laundered_caught": 0,
       "true_kept": 0, "true_caught": 0, "unmatched": 0}
caught_list = []
for r in rows:
    if r["gate"] != "PERSIST": continue
    lab = label.get((r["model"], r["id"]))
    if lab is None: res["unmatched"] += 1; continue
    same = norm(r["fix_code"]) == norm(bank[r["id"]]["code"])
    asserts_error = lab in ("F", "SW", "SC")
    discard = asserts_error and same
    if r["intended"] == "pass":
        if lab == "F":
            if discard: res["laundered_caught"] += 1; caught_list.append((r["model"], r["id"]))
            else: res["laundered_kept"] += 1
    else:
        if lab == "SC":
            if discard: res["true_caught"] += 1
            else: res["true_kept"] += 1

print(json.dumps(res, indent=2))
tot = res["laundered_caught"] + res["laundered_kept"]
if tot: print(f"\ncatch rate on persisted fabrications: {res['laundered_caught']}/{tot} = {res['laundered_caught']/tot:.0%}")
tt = res["true_caught"] + res["true_kept"]
if tt: print(f"true-lesson false-discard: {res['true_caught']}/{tt}")
print("caught:", caught_list)
