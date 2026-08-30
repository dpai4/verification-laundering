import json, re, random, string, signal, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT / "data" / "verification")
from collections import defaultdict

import os
N_INPUTS = int(os.environ.get("NIN", 200))
random.seed(11)

def norm(c): return re.sub(r"\s+", "", c or "")

# input generators by function name; each returns a tuple of args
def ints(n=8, lo=-20, hi=20): return [random.randint(lo, hi) for _ in range(random.randint(1, n))]
GEN = {
  "power":        lambda: (random.randint(-5, 5), random.randint(0, 8)),
  "factorial":    lambda: (random.randint(0, 8),),
  "fib":          lambda: (random.randint(0, 20),),
  "gcd":          lambda: (random.randint(1, 200), random.randint(1, 200)),
  "sum_evens":    lambda: (ints(),),
  "max_val":      lambda: (ints() or [0],),
  "max_subarray": lambda: (ints(),),
  "count_vowels": lambda: ("".join(random.choice(string.ascii_letters) for _ in range(random.randint(1, 12))),),
  "length_of_longest": lambda: ("".join(random.choice("abcde") for _ in range(random.randint(1, 12))),),
  "search":       lambda: (sorted(ints()), random.randint(-20, 20)),
  "two_sum":      lambda: (sorted(ints()), random.randint(-20, 20)),
  "remove_duplicates": lambda: (sorted(ints()),),
  "range_sum":    lambda: None,   # needs coupled indices, handled below
  "subsets":      lambda: (ints(4, -5, 5),),
  "merge":        lambda: ([sorted([random.randint(0, 20), random.randint(0, 20)]) for _ in range(random.randint(1, 5))],),
}
def gen_range_sum():
    nums = ints(); n = len(nums)
    l = random.randint(0, n - 1); r = random.randint(l, n - 1)
    return (nums, l, r)

def fname(code):
    m = re.search(r"def\s+(\w+)\s*\(", code or "")
    return m.group(1) if m else None

class TO(Exception): pass
def handler(s, f): raise TO()
signal.signal(signal.SIGALRM, handler)

def run(code, args):
    ns = {}
    try:
        exec(code, ns)
        fn = ns[fname(code)]
        signal.alarm(1)
        out = fn(*[json.loads(json.dumps(a)) for a in args])
        signal.alarm(0)
        return ("ok", repr(out))
    except TO:
        return ("timeout", None)
    except Exception as e:
        signal.alarm(0)
        return ("err", type(e).__name__)

def equivalent(c1, c2, name):
    g = gen_range_sum if name == "range_sum" else GEN.get(name)
    if g is None: return None, 0
    tried = 0
    for _ in range(N_INPUTS):
        try: args = g()
        except Exception: continue
        tried += 1
        if run(c1, args) != run(c2, args): return False, tried
    return True, tried

bank = {b["id"]: b for b in json.load(open("../verified_bank_v2.json"))}

def load(p):
    d = {}
    for line in open(p):
        m = re.match(r"\s*(\d+)\s*:\s*([A-Z]{1,2})", line)
        if m: d[int(m.group(1))] = m.group(2)
    return d
a = load("labels_a.txt")
human = {}
for line in open("adjudicate_final.txt"):
    m = re.match(r"FINAL\s+(\d+)\s*:\s*([A-Z]{1,2})", line)
    if m: human[int(m.group(1))] = m.group(2)
key = {json.loads(l)["n"]: json.loads(l) for l in open("blind_key.jsonl")}
label = {}
for n, meta in key.items():
    if n >= 270: continue
    if meta.get("arm") == "presup":
        label[(meta["model"], meta["id"])] = human.get(n, a[n])

res = defaultdict(int); skipped = []; caught = []; missed = []
for line in open("h2_verified_write.jsonl"):
    r = json.loads(line)
    if r["gate"] != "PERSIST": continue
    lab = label.get((r["model"], r["id"]))
    if lab is None: continue
    orig = bank[r["id"]]["code"]; name = fname(orig)
    eq, tried = equivalent(orig, r["fix_code"], name)
    if eq is None: skipped.append(r["id"]); continue
    if r["intended"] == "pass" and lab == "F":
        if eq: res["fab_caught"] += 1; caught.append((r["model"], r["id"]))
        else:  res["fab_missed"] += 1; missed.append((r["model"], r["id"]))
    elif r["intended"] == "fail" and lab == "SC":
        if eq: res["true_wrongly_discarded"] += 1
        else:  res["true_kept"] += 1

print(f"inputs per item: {N_INPUTS} (uniform ints -20..20, lists len 1-8; strings len 1-12 from letters; sorted where the signature requires it)")
print(json.dumps(dict(res), indent=2))
t = res["fab_caught"] + res["fab_missed"]
if t: print(f"\nbehavioral catch rate on persisted fabrications: {res['fab_caught']}/{t} = {res['fab_caught']/t:.0%}")
tt = res["true_wrongly_discarded"] + res["true_kept"]
if tt: print(f"true fixes wrongly discarded: {res['true_wrongly_discarded']}/{tt}  (should be 0; nonzero = generator too weak)")
print(f"skipped, no generator: {sorted(set(skipped))}")
print("caught:", caught)
print("missed:", missed)
