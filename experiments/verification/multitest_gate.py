import json, re, os, random, string, subprocess, tempfile, signal
from collections import defaultdict

K = int(os.environ.get("K", 5))
random.seed(int(os.environ.get("SEED", 5)))

def norm(c): return re.sub(r"\s+", "", c or "")
def fname(code):
    m = re.search(r"def\s+(\w+)\s*\(", code or "")
    return m.group(1) if m else None

def ints(n=6, lo=-15, hi=15): return [random.randint(lo,hi) for _ in range(random.randint(1,n))]
GEN = {
 "power": lambda: (random.randint(-4,4), random.randint(0,6)),
 "factorial": lambda: (random.randint(0,7),),
 "fib": lambda: (random.randint(0,15),),
 "gcd": lambda: (random.randint(1,120), random.randint(1,120)),
 "sum_evens": lambda: (ints(),),
 "max_val": lambda: (ints() or [0],),
 "max_subarray": lambda: (ints(),),
 "count_vowels": lambda: ("".join(random.choice(string.ascii_letters) for _ in range(random.randint(1,10))),),
 "length_of_longest": lambda: ("".join(random.choice("abcdeABCDE") for _ in range(random.randint(1,10))),),
 "search": lambda: (sorted(ints()), random.randint(-15,15)),
 "two_sum": lambda: (sorted(ints()), random.randint(-15,15)),
 "remove_duplicates": lambda: (sorted(ints()),),
 "subsets": lambda: (ints(4,-4,4),),
 "merge": lambda: ([sorted([random.randint(0,15),random.randint(0,15)]) for _ in range(random.randint(1,4))],),
}
def gen_range_sum():
    xs = ints(); n = len(xs)
    l = random.randint(0,n-1); r = random.randint(l,n-1)
    return (xs, l, r)

class TO(Exception): pass
signal.signal(signal.SIGALRM, lambda s,f: (_ for _ in ()).throw(TO()))

def run(code, args):
    ns = {}
    try:
        exec(code, ns); fn = ns[fname(code)]
        signal.setitimer(signal.ITIMER_REAL, 0.5)
        out = fn(*json.loads(json.dumps(list(args))))
        signal.setitimer(signal.ITIMER_REAL, 0)
        return ("ok", out)
    except TO: return ("timeout", None)
    except Exception as e:
        signal.setitimer(signal.ITIMER_REAL, 0); return ("err", type(e).__name__)

def make_tests(ref_code, name, k):
    """k assertions whose expected values come from the reference implementation."""
    g = gen_range_sum if name == "range_sum" else GEN.get(name)
    if g is None: return None
    tests, seen, tries = [], set(), 0
    while len(tests) < k and tries < k*20:
        tries += 1
        try: args = g()
        except Exception: continue
        key = repr(args)
        if key in seen: continue
        st, val = run(ref_code, args)
        if st != "ok": continue
        seen.add(key)
        tests.append(f"assert {name}({', '.join(repr(a) for a in args)}) == {val!r}")
    return tests or None

def passes_all(code, tests):
    src = code + "\n" + "\n".join(tests) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(src); p = f.name
    try:
        return subprocess.run(["python", p], capture_output=True, timeout=15).returncode == 0
    except Exception: return False
    finally: os.unlink(p)

bank = {b["id"]: b for b in json.load(open("verified_bank_v2.json"))}

def load(p):
    d = {}
    for line in open(p):
        m = re.match(r"\s*(\d+)\s*:\s*([A-Z]{1,2})", line)
        if m: d[int(m.group(1))] = m.group(2)
    return d
a = load("labels_a.txt"); human = {}
for line in open("adjudicate_final.txt"):
    m = re.match(r"FINAL\s+(\d+)\s*:\s*([A-Z]{1,2})", line)
    if m: human[int(m.group(1))] = m.group(2)
key = {json.loads(l)["n"]: json.loads(l) for l in open("blind_key.jsonl") if json.loads(l)["n"] < 270}
label = {(m["model"], m["id"]): human.get(n, a[n]) for n, m in key.items() if m["arm"] == "presup"}

persist = caught = 0
skipped = []
for l in open("h2_verified_write.jsonl"):
    r = json.loads(l)
    if r["gate"] != "PERSIST" or r["intended"] != "pass": continue
    if label.get((r["model"], r["id"])) != "F": continue
    ref = bank[r["id"]]["code"]; nm = fname(ref)
    tests = make_tests(ref, nm, K)
    if not tests: skipped.append(r["id"]); continue
    if passes_all(r["fix_code"], tests): persist += 1
    else: caught += 1; print("CAUGHT:", r["model"], r["id"])

tot = persist + caught
print(f"K={K} tests per item")
print(f"fabrications still persisting: {persist}/{tot} = {persist/max(1,tot):.0%}")
print(f"caught by the multi-test gate:  {caught}/{tot} = {caught/max(1,tot):.0%}")
print("skipped (no generator):", sorted(set(skipped)))
