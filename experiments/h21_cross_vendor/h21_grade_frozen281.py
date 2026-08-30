import json
import re
import time
from pathlib import Path
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def get_chat(prompt, model, temperature=0.0, max_tokens=5):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""

JUDGE = Path("h21_blind_items_judge.txt")
RUBRIC_PATH = Path("h21_rubric.txt")
OUT = Path("h21_labels_gpt41mini.jsonl")

MODEL = "gpt-4.1-mini"

rubric = RUBRIC_PATH.read_text().strip()
text = JUDGE.read_text()
blocks = text.split("=== ITEM ")[1:]

if len(blocks) != 281:
    raise SystemExit(f"REFUSING TO GRADE: expected 281 blind items, got {len(blocks)}")

done = {}
if OUT.exists():
    for line in OUT.open():
        if line.strip():
            r = json.loads(line)
            done[int(r["n"])] = r

print("items:", len(blocks))
print("already graded:", len(done))
print("remaining:", len(blocks) - len(done))
print("model:", MODEL)

def parse_label(raw, program_type):
    s = raw.strip().upper()

    # Exact/near-exact label extraction.
    toks = re.findall(r"\b(?:SC|SW|DC|CD|F|H)\b", s)

    if not toks:
        compact = re.sub(r"[^A-Z]", "", s)
        for lab in ["SC", "SW", "DC", "CD", "F", "H"]:
            if compact == lab:
                toks = [lab]
                break

    if len(set(toks)) != 1:
        return None

    lab = toks[0]

    allowed = (
        {"SC", "SW", "H", "DC", "CD"}
        if program_type == "BUGGY"
        else {"F", "DC", "CD", "H"}
    )

    return lab if lab in allowed else None


with OUT.open("a") as f:
    for idx, block in enumerate(blocks):
        n = int(block[:3])

        if n in done:
            continue

        m = re.search(r"program-type:\s*(BUGGY|CORRECT)", block)
        if not m:
            raise RuntimeError(f"Cannot determine program type for item {n:03d}")

        program_type = m.group(1)

        prompt = (
            rubric
            + "\n\n"
            + "Apply the frozen rubric to the item below. "
              "Respond with exactly one permitted label and nothing else.\n\n"
            + "=== ITEM "
            + block.strip()
        )

        last_raw = None
        lab = None

        for attempt in range(1, 4):
            raw = get_chat(
                prompt,
                model=MODEL,
                temperature=0.0,
                max_tokens=5,
            )
            last_raw = raw
            lab = parse_label(raw, program_type)

            if lab is not None:
                break

            print(
                f"retry item={n:03d} attempt={attempt} "
                f"type={program_type} raw={raw!r}",
                flush=True,
            )
            time.sleep(1)

        if lab is None:
            raise RuntimeError(
                f"Invalid grader output after retries for item {n:03d}: {last_raw!r}"
            )

        row = {
            "n": n,
            "program_type": program_type,
            "label": lab,
            "grader_model": MODEL,
            "temperature": 0.0,
            "max_tokens": 5,
        }

        f.write(json.dumps(row) + "\n")
        f.flush()

        print(f"{n:03d}: {program_type:7s} -> {lab}", flush=True)

print("done ->", OUT)
