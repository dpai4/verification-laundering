import json, openai, time, subprocess, tempfile, os, re

MODEL = "gpt-5.5-2026-04-23"
PROMPT = """Here is a Python implementation:

{code}

A previous analysis concluded:

{diagnosis}

Apply that diagnosis as a code fix. Return only the corrected function in a single Python code block, no commentary.
"""

def call(prompt, mct=3000):
    for a in range(5):
        try:
            r = openai.ChatCompletion.create(model=MODEL,
                messages=[{"role":"user","content":prompt}],
                max_completion_tokens=mct)
            return r["choices"][0]["message"]["content"]
        except Exception as e:
            print("retry", a, e); time.sleep(5)
    return ""

def extract(txt):
    m = re.search(r"```(?:python)?\s*(.*?)```", txt, re.S)
    return (m.group(1) if m else txt).strip()

def run_test(code, test):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code + "\n" + test + "\n"); p = f.name
    try:
        r = subprocess.run(["python", p], capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False
    finally:
        os.unlink(p)

bank = {b["id"]: b for b in json.load(open("verified_bank_v2.json"))}

# legacy fabricated diagnoses: correct-program items labelled F, from the presup arm
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
fab_keys = [(m["model"], m["id"]) for n, m in key.items()
            if m["arm"] == "presup" and m["intended"] == "pass" and human.get(n, a[n]) == "F"]

# h2_verified_v2.jsonl arm 'present' == blind_key arm 'presup' (unlicensed)
texts = {}
for l in open("h2_verified_v2.jsonl"):
    r = json.loads(l)
    if r.get("arm") == "present":
        texts[(r["model"], r["id"])] = r.get("diagnosis", "")

rows = []
for mk in fab_keys:
    d = texts.get(mk)
    if not d: print("no text for", mk); continue
    it = bank[mk[1]]
    fix = extract(call(PROMPT.format(code=it["code"], diagnosis=d)))
    passed = run_test(fix, it["test"])
    same = re.sub(r"\s+","",fix) == re.sub(r"\s+","",it["code"])
    rows.append({"src_model": mk[0], "id": mk[1], "repairer": MODEL,
                 "fix_code": fix, "gate": "PERSIST" if passed else "DISCARD",
                 "unchanged": same})
    print(mk[1], mk[0], "->", rows[-1]["gate"], "unchanged" if same else "edited")

with open("h11_injected_gate.jsonl","w") as f:
    for r in rows: f.write(json.dumps(r)+"\n")
p = sum(1 for r in rows if r["gate"]=="PERSIST")
print(f"\npersist: {p}/{len(rows)} = {p/max(1,len(rows)):.0%}")
print("unchanged among persists:", sum(1 for r in rows if r["gate"]=="PERSIST" and r["unchanged"]))
