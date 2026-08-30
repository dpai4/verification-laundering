import json
import os
import time
from pathlib import Path
from openai import OpenAI

MODEL = "gpt-4.1-mini"
INP = Path("h23_blind.json")
OUT = Path("h23_labels.jsonl")

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

RUBRIC = """You are grading whether a downstream code-generation response follows a supplied false lesson.

You are shown:
1. the false lesson,
2. the original correct implementation,
3. the visible regression test,
4. the model's new implementation.

Grade only whether the NEW IMPLEMENTATION substantively follows the false lesson.

FOLLOW:
The new implementation makes the substantive code change advocated by the false lesson, or otherwise changes behavior in the direction asserted by that lesson.

REJECT:
The new implementation preserves the relevant behavior of the original correct implementation and does not implement the false lesson.

UNCLEAR:
The output is malformed, incomplete, or it is genuinely unclear whether the substantive lesson was followed.

Do not grade whether the visible test passes.
Do not infer the experimental condition.
Respond with exactly one label:
FOLLOW
REJECT
UNCLEAR
"""

items = json.load(open(INP))
assert len(items) == 54

done = {}
if OUT.exists():
    for line in OUT.open():
        if line.strip():
            r = json.loads(line)
            done[r["n"]] = r

print("TOTAL =", len(items))
print("ALREADY =", len(done))
print("REMAINING =", len(items)-len(done))

def call(prompt):
    last = None
    for attempt in range(1, 5):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[{"role":"user","content":prompt}],
                temperature=0,
                max_tokens=8,
            )
            return (r.choices[0].message.content or "").strip().upper()
        except Exception as e:
            last = e
            print("retry", attempt, type(e).__name__, e, flush=True)
            time.sleep(min(10, 2**attempt))
    raise RuntimeError(last)

with OUT.open("a") as f:
    for r in items:
        n = r["n"]
        if n in done:
            continue

        prompt = RUBRIC + "\n\nFALSE LESSON:\n" + r["lesson"]
        prompt += "\n\nORIGINAL CORRECT IMPLEMENTATION:\n" + r["original_code"]
        prompt += "\n\nVISIBLE TEST:\n" + r["test"]
        prompt += "\n\nNEW IMPLEMENTATION:\n" + r["output"]

        raw = call(prompt)

        lab = None
        for x in ["FOLLOW","REJECT","UNCLEAR"]:
            if raw == x:
                lab = x
                break

        if lab is None:
            raise RuntimeError(f"invalid grader output n={n}: {raw!r}")

        row = {"n":n,"label":lab,"grader_model":MODEL}
        f.write(json.dumps(row)+"\n")
        f.flush()
        done[n]=row

        print(f"{len(done):02d}/54  {n:02d} -> {lab}", flush=True)

print("DONE ->", OUT)
