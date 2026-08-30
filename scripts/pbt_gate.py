import json, re, os, sys, warnings, string
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT / "data" / "verification")
import hypothesis
from hypothesis import given, settings, strategies as st, HealthCheck, Phase
warnings.filterwarnings("ignore")

MAX_EX = int(os.environ.get("MAXEX", 200))
BACKEND = os.environ.get("BACKEND", "hypothesis")   # or "crosshair"

def norm(c): return re.sub(r"\s+", "", c or "")
def fname(code):
    m = re.search(r"def\s+(\w+)\s*\(", code or "")
    return m.group(1) if m else None

ints   = st.integers(min_value=-30, max_value=30)
ilists = st.lists(ints, min_size=0, max_size=10)
slists = st.lists(ints, min_size=0, max_size=10).map(sorted)
strs   = st.text(alphabet=string.ascii_letters, min_size=0, max_size=15)

STRAT = {
  "power":        st.tuples(st.integers(-6,6), st.integers(0,10)),
  "factorial":    st.tuples(st.integers(0,10)),
  "fib":          st.tuples(st.integers(0,25)),
  "gcd":          st.tuples(st.integers(1,300), st.integers(1,300)),
  "sum_evens":    st.tuples(ilists),
  "max_val":      st.tuples(st.lists(ints, min_size=1, max_size=10)),
  "max_subarray": st.tuples(st.lists(ints, min_size=1, max_size=10)),
  "count_vowels": st.tuples(strs),
  "length_of_longest": st.tuples(st.text(alphabet="abcdeABCDE", min_size=0, max_size=15)),
  "search":       st.tuples(slists, ints),
  "two_sum":      st.tuples(slists, ints),
  "remove_duplicates": st.tuples(slists),
  "subsets":      st.tuples(st.lists(st.integers(-5,5), min_size=0, max_size=5)),
  "merge":        st.tuples(st.lists(st.lists(st.integers(0,20), min_size=2, max_size=2).map(sorted),
                                     min_size=0, max_size=6)),
  "range_sum":    st.lists(ints, min_size=1, max_size=10).flatmap(
                      lambda xs: st.tuples(st.just(xs),
                                           st.integers(0, len(xs)-1)).flatmap(
                          lambda t: st.tuples(st.just(t[0]), st.just(t[1]),
                                              st.integers(t[1], len(t[0])-1)))),
}

import signal
class _TO(Exception): pass
def _h(sig, frm): raise _TO()
signal.signal(signal.SIGALRM, _h)

def call(fn, args):
    try:
        signal.setitimer(signal.ITIMER_REAL, 0.5)
        out = repr(fn(*json.loads(json.dumps(list(args)))))
        signal.setitimer(signal.ITIMER_REAL, 0)
        return ("ok", out)
    except _TO:
        return ("timeout", None)
    except Exception as e:
        signal.setitimer(signal.ITIMER_REAL, 0)
        return ("err", type(e).__name__)

def equivalent(orig, fix, name):
    strat = STRAT.get(name)
    if strat is None: return None, None
    ns1, ns2 = {}, {}
    try:
        exec(orig, ns1); exec(fix, ns2)
        f1, f2 = ns1[name], ns2[name]
    except Exception:
        return None, None
    counter = {}
    cfg = dict(max_examples=MAX_EX, deadline=None, database=None,
               suppress_health_check=list(HealthCheck))
    if BACKEND == "crosshair":
        cfg["backend"] = "crosshair"

    @settings(**cfg)
    @given(strat)
    def prop(args):
        a, b = call(f1, args), call(f2, args)
        if a != b:
            counter["args"] = args
        assert a == b

    try:
        prop(); return True, None
    except AssertionError:
        return False, counter.get("args")
    except Exception as e:
        return None, f"harness:{type(e).__name__}"

bank = {b["id"]: b for b in json.load(open("../verified_bank_v2.json"))}

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

fab_caught = fab_missed = true_kept = true_dropped = 0
skipped, missed_ids = [], []
for l in open("h2_verified_write.jsonl"):
    r = json.loads(l)
    if r["gate"] != "PERSIST": continue
    lab = label.get((r["model"], r["id"]))
    if lab is None: continue
    orig = bank[r["id"]]["code"]; nm = fname(orig)
    eq, info = equivalent(orig, r["fix_code"], nm)
    if eq is None:
        skipped.append((r["id"], info)); continue
    if r["intended"] == "pass" and lab == "F":
        if eq: fab_caught += 1
        else:  fab_missed += 1; missed_ids.append((r["model"], r["id"]))
    elif r["intended"] == "fail" and lab == "SC":
        if eq: true_dropped += 1
        else:  true_kept += 1

t = fab_caught + fab_missed
print(f"backend={BACKEND}  max_examples={MAX_EX}")
print(f"catch rate on persisted fabrications: {fab_caught}/{t} = {fab_caught/max(1,t):.0%}")
print(f"true fixes wrongly discarded: {true_dropped}/{true_dropped+true_kept}")
print("missed:", missed_ids)
print("skipped:", skipped)
