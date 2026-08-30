import json
from collections import Counter
from math import comb

key = {r["n"]:r for r in json.load(open("h23_blind_key.json"))}
labs = {
    r["n"]:r
    for r in (
        json.loads(x)
        for x in open("h23_labels.jsonl")
        if x.strip()
    )
}

assert len(key)==54
assert len(labs)==54

rows=[]
for n,k in key.items():
    rows.append({**k, **labs[n]})

print("N =", len(rows))

for condition in ["control","verified"]:
    xs=[r for r in rows if r["condition"]==condition]
    c=Counter(r["label"] for r in xs)
    print(condition, "N=",len(xs), dict(c))

ctrl=sum(r["label"]=="FOLLOW" for r in rows if r["condition"]=="control")
ver=sum(r["label"]=="FOLLOW" for r in rows if r["condition"]=="verified")

pc=ctrl/27
pv=ver/27
delta=pv-pc

print()
print(f"CONTROL FOLLOW = {ctrl}/27 = {pc:.3f}")
print(f"VERIFIED FOLLOW = {ver}/27 = {pv:.3f}")
print(f"DELTA = {delta:.3f}")

by={}
for r in rows:
    by.setdefault(r["case_id"],{})[r["condition"]]=r

both=ctrl_only=ver_only=neither=unclear=0

for cid,p in sorted(by.items()):
    c=p["control"]["label"]
    v=p["verified"]["label"]

    if "UNCLEAR" in (c,v):
        unclear += 1
    elif c=="FOLLOW" and v=="FOLLOW":
        both += 1
    elif c=="FOLLOW" and v!="FOLLOW":
        ctrl_only += 1
    elif c!="FOLLOW" and v=="FOLLOW":
        ver_only += 1
    else:
        neither += 1

print()
print("PAIRED TABLE")
print("both_follow =",both)
print("control_only =",ctrl_only)
print("verified_only =",ver_only)
print("neither_follow =",neither)
print("pairs_with_unclear =",unclear)

n=ctrl_only+ver_only
if n:
    k=min(ctrl_only,ver_only)
    p=min(1.0, 2*sum(comb(n,i) for i in range(k+1))/(2**n))
else:
    p=1.0

print(f"EXACT McNEMAR p = {p:.6f}")

print()
print("DISCORDANT CASES")
for cid,p in sorted(by.items()):
    c=p["control"]["label"]
    v=p["verified"]["label"]
    if c != v:
        print(
            cid,
            p["control"]["id"],
            "control=",c,
            "verified=",v,
            "src=",p["control"]["src_model"]
        )

with open("h23_joined.jsonl","w") as f:
    for r in rows:
        f.write(json.dumps(r)+"\n")
