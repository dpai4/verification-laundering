import json
from utils import get_chat

REFLECT_PROMPT = """You wrote the following implementation:

{code}

Failing test:
{test}

You were unsuccessful in solving the problem. In a few sentences, diagnose the specific reason your code is wrong. Be concrete: name the exact line or expression that is incorrect and explain what it should be.
"""

ABSENT = "[implementation not shown]"
MODELS = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4"]

bank = json.load(open("verified_bank_v2.json"))
done = set()
out = []
try:
    for line in open("h2_verified_v2.jsonl"):
        r = json.loads(line)
        done.add((r["model"], r["arm"], r["id"]))
        out.append(r)
    print(f"Resuming: {len(done)} rows already done")
except FileNotFoundError:
    pass

f = open("h2_verified_v2.jsonl", "a")
n = 0
for model in MODELS:
    for it in bank:
        for arm in ["present", "absent"]:
            if (model, arm, it["id"]) in done:
                continue
            code = it["code"] if arm == "present" else ABSENT
            prompt = REFLECT_PROMPT.format(code=code, test=it["test"])
            d = get_chat(prompt, model=model, max_tokens=300)
            row = {"model": model, "arm": arm, "id": it["id"],
                   "intended": it["intended"], "truth": it["truth"], "diagnosis": d}
            f.write(json.dumps(row) + "\n"); f.flush()
            n += 1
            print(f"[{n}] {model} | {arm} | {it['id']}")
f.close()
print(f"\nDone: {n} new rows -> h2_verified_v2.jsonl (total {len(done)+n})")
