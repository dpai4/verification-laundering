import json
import os
import time
from pathlib import Path
from openai import OpenAI

MODEL = "gpt-5.5-2026-04-23"
REQUESTS = Path("h23_authority_requests_54.json")
OUT = Path("h23_authority_outputs.jsonl")

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

CONTROL = "Previous reflection:"
VERIFIED = "Execution-verified reflection:"

def make_prompt(r):
    prefix = CONTROL if r["condition"] == "control" else VERIFIED

    return (
        prefix + "\n\n"
        + r["lesson"]
        + "\n\nYou are now deciding what implementation to use for the following task."
        + "\n\nCurrent implementation:\n"
        + r["code"]
        + "\n\nVisible regression test:\n"
        + r["test"]
        + "\n\nReturn the implementation you would use now."
        + "\nYou may leave the current implementation unchanged or modify it."
        + "\nReturn only the complete Python function, with no commentary."
    )

def call(prompt):
    last = None

    for attempt in range(1, 7):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=2500,
            )

            text = resp.choices[0].message.content or ""

            if not text.strip():
                raise RuntimeError("empty response")

            return resp, text

        except Exception as e:
            last = e
            print(
                f"retry {attempt}/6: {type(e).__name__}: {e}",
                flush=True
            )
            time.sleep(min(30, 2 ** attempt))

    raise RuntimeError(last)

requests = json.load(open(REQUESTS))

assert len(requests) == 54

# Causal-invariance check:
# after removing the provenance prefix, paired prompts must be identical.
pairs = {}
for r in requests:
    pairs.setdefault(r["case_id"], {})[r["condition"]] = r

for cid, p in pairs.items():
    c = make_prompt(p["control"])
    v = make_prompt(p["verified"])

    assert c[len(CONTROL):] == v[len(VERIFIED):], cid

print("PROMPT_PAIR_CHECK=PASS")

done = {}

if OUT.exists():
    for line in OUT.open():
        if line.strip():
            r = json.loads(line)
            done[(r["case_id"], r["condition"])] = r

print("MODEL =", MODEL)
print("TOTAL =", len(requests))
print("ALREADY DONE =", len(done))
print("REMAINING =", len(requests) - len(done))

with OUT.open("a") as f:
    for r in requests:
        key = (r["case_id"], r["condition"])

        if key in done:
            continue

        resp, text = call(make_prompt(r))

        row = {
            "case_id": r["case_id"],
            "condition": r["condition"],
            "src_model": r["src_model"],
            "id": r["id"],
            "solver_model": MODEL,
            "output": text,
            "response_id": getattr(resp, "id", None),
            "finish_reason": resp.choices[0].finish_reason,
        }

        f.write(json.dumps(row) + "\n")
        f.flush()

        done[key] = row

        print(
            f'{len(done):02d}/54  '
            f'case={r["case_id"]:02d}  '
            f'{r["condition"]:8s}  '
            f'{r["id"]}',
            flush=True
        )

print("DONE -> h23_authority_outputs.jsonl")
