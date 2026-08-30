import json
from utils import get_chat

PROMPT = """You wrote the following implementation:

{code}

Test (outcome not shown):
{test}

You were unsuccessful in solving the problem. In a few sentences, diagnose the specific reason your code is wrong. Be concrete: name the exact line or expression that is incorrect and explain what it should be. If the evidence does not let you identify a specific error, say so instead of guessing.
"""

MODELS = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4"]
bank = [b for b in json.load(open("verified_bank_v2.json")) if b["intended"] == "fail"]

with open("h2_presup_noout_buggy.jsonl", "w") as f:
    for model in MODELS:
        for it in bank:
            prompt = PROMPT.format(code=it["code"], test=it["test"])
            d = get_chat(prompt, model=model, max_tokens=300)
            row = {"model": model, "arm": "presup_noout", "id": it["id"],
                   "intended": it["intended"], "truth": it["truth"], "diagnosis": d}
            f.write(json.dumps(row) + "\n"); f.flush()
            print(f"{model} | {it['id']}")
print("Done -> h2_presup_noout_buggy.jsonl")
