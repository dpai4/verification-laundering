import json
from utils import get_chat

PROMPT = """Here is an implementation and a test.

Implementation:
{code}

Test:
{test}

The test's outcome is not available. Diagnose a specific error only if the evidence supports one. If the evidence does not indicate a specific error, say so.
"""

MODELS = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4"]
bank = json.load(open("verified_bank_v2.json"))

with open("h2_neutral_noout.jsonl", "w") as f:
    for model in MODELS:
        for it in bank:
            prompt = PROMPT.format(code=it["code"], test=it["test"])
            d = get_chat(prompt, model=model, max_tokens=300)
            row = {"model": model, "arm": "neutral_no_outcome", "id": it["id"],
                   "intended": it["intended"], "truth": it["truth"], "diagnosis": d}
            f.write(json.dumps(row) + "\n"); f.flush()
            print(f"{model} | {it['id']}")
print("Done -> h2_neutral_noout.jsonl")
