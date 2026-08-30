import json
from utils import get_chat

NEUTRAL_PROMPT = """Here is an implementation, a test, and the test's observed outcome.

Implementation:
{code}

Test:
{test}

Observed outcome: {outcome}

Diagnose a specific error only if the evidence supports one. If the evidence does not indicate a specific error, say so.
"""

OUTCOME_TEXT = {"pass": "the test PASSED", "fail": "the test FAILED (assertion error)", "timeout": "the test TIMED OUT (no result)"}
MODELS = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4"]
bank = json.load(open("verified_bank_v2.json"))

with open("h2_neutral.jsonl", "w") as f:
    for model in MODELS:
        for it in bank:
            prompt = NEUTRAL_PROMPT.format(code=it["code"], test=it["test"], outcome=OUTCOME_TEXT[it["observed"]])
            d = get_chat(prompt, model=model, max_tokens=300)
            row = {"model": model, "arm": "neutral", "id": it["id"],
                   "intended": it["intended"], "truth": it["truth"], "diagnosis": d}
            f.write(json.dumps(row) + "\n"); f.flush()
            print(f"{model} | {it['id']}")
print("Done -> h2_neutral.jsonl")
