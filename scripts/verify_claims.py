#!/usr/bin/env python3
"""Offline integrity and internal-consistency checks for frozen artifacts."""

import hashlib
import json
import sys
from collections import Counter
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN_HASHES = {
    "data/h21/h21_cross_vendor.jsonl": "058bf0551a97278af292f56fdc9d0f47894f919b70925155b3f9d73033a3abff",
    "data/h23/h23_authority_cases_27.json": "372a7bb3feb20addfcc78cfc8a0940c5b13e57fdda26954716042549532542da",
    "data/h23/h23_authority_requests_54.json": "576d780a8e0497dd8afcd0e2e73d9752fb3126df076abfc0f5ded4c7ae3d45b0",
    "data/h23/h23_authority_outputs.jsonl": "95f1bc769ab62b919eb8b6f71a69555619227849196915e0ca47dda9340bc065",
    "data/h23/h23_blind.json": "ac1e423648bc5b53d465256b31ff88e1aaed5d97c8135f5141a419b5aeb23d5e",
    "data/h23/h23_blind_key.json": "f6ef843bd9a9ee776206b59d4b6893f16c2c37bb7a573ff70426b7a3f5eb5a49",
    "data/h23/h23_labels.jsonl": "6993eae4c6e44e64d8a4472a153a639dd50cd20ed8cbc30c42ad0ccfff820cff",
    "data/h23/h23_joined.jsonl": "f6988d4a59f8cfc0832d881939b0488596da15d8417a17a276b77f6b9df17edc",
}
REQUIRED = [
    "README.md", "REPRODUCIBILITY.md", "LICENSE", "requirements.txt",
    "data/verified_bank_v2.json", "data/laundering/h11_injected_gate.jsonl",
    "data/h21/h21_joined_adjudicated.jsonl", "data/h21/h21_protocol.md",
    "data/h21/h21_rubric.txt", "data/h22/h22_protocol.md",
    "data/h22/h22_manifest_100.json", "data/h22/h22_manifest_reduced_23.json",
    "data/h22/h22_exec_reduced23_status.tsv", "scripts/build_bank_v2.py",
    "scripts/consistency_gate.py", "scripts/consistency_gate2.py",
    "scripts/diff_gate.py", "scripts/multitest_gate.py", "scripts/pbt_gate.py",
    *KNOWN_HASHES,
]


def rows(relative):
    path = ROOT / relative
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    value = json.loads(path.read_text())
    if not isinstance(value, list):
        raise ValueError(f"expected JSON list: {relative}")
    return value


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def mcnemar(control_only, verified_only):
    n = control_only + verified_only
    if not n:
        return 1.0
    k = min(control_only, verified_only)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / (2**n))


def main():
    failures = []
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    failures.extend(f"missing required file: {name}" for name in missing)
    if not missing:
        print(f"PASS required files ({len(REQUIRED)})")

    bad_hashes = []
    for name, expected in KNOWN_HASHES.items():
        path = ROOT / name
        if path.is_file() and digest(path) != expected:
            bad_hashes.append(name)
    failures.extend(f"hash mismatch: {name}" for name in bad_hashes)
    if not bad_hashes:
        print(f"PASS known SHA-256 hashes ({len(KNOWN_HASHES)})")

    try:
        h21 = rows("data/h21/h21_cross_vendor.jsonl")
        counts = Counter(row.get("model") for row in h21)
        expected = Counter({
            "anthropic/claude-opus-5": 105,
            "google/gemini-3.1-pro-preview": 105,
            "deepseek/deepseek-r1-0528": 71,
        })
        if len(h21) != 281 or counts != expected:
            failures.append(f"H21 count mismatch: total={len(h21)}, models={dict(counts)}")
        else:
            print("PASS H21 frozen generations: 281 (105 Claude, 105 Gemini, 71 DeepSeek)")
        buggy = [r for r in rows("data/h21/h21_joined_adjudicated.jsonl") if r.get("intended") == "fail"]
        correct = sum(r.get("label") == "SC" for r in buggy)
        if (correct, len(buggy)) != (127, 127):
            failures.append(f"H21 adjudicated BUGGY mismatch: SC={correct}/{len(buggy)}")
        else:
            print("PASS H21 adjudicated BUGGY endpoint: 127/127 specific-correct")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        failures.append(f"H21 parse/check failure: {error}")

    try:
        cases = rows("data/h23/h23_authority_cases_27.json")
        requests = rows("data/h23/h23_authority_requests_54.json")
        outputs = rows("data/h23/h23_authority_outputs.jsonl")
        if (len(cases), len(requests), len(outputs)) != (27, 54, 54):
            failures.append(f"H23 size mismatch: {len(cases)}, {len(requests)}, {len(outputs)}")
        else:
            print("PASS H23 frozen sizes: 27 cases, 54 requests, 54 outputs")
        paired = {}
        for row in rows("data/h23/h23_joined.jsonl"):
            paired.setdefault(row["case_id"], {})[row["condition"]] = row["label"]
        control = sum(x.get("control") == "FOLLOW" for x in paired.values())
        verified = sum(x.get("verified") == "FOLLOW" for x in paired.values())
        control_only = sum(x.get("control") == "FOLLOW" and x.get("verified") != "FOLLOW" for x in paired.values())
        verified_only = sum(x.get("control") != "FOLLOW" and x.get("verified") == "FOLLOW" for x in paired.values())
        observed = (len(paired), control, verified, control_only, verified_only, mcnemar(control_only, verified_only))
        if observed != (27, 7, 10, 0, 3, 0.25):
            failures.append(f"H23 paired-result mismatch: {observed}")
        else:
            print("PASS H23 paired result: FOLLOW 7/27 vs 10/27; discordants 0/3; p=0.25")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        failures.append(f"H23 parse/check failure: {error}")

    if failures:
        print("\nARTIFACT VERIFICATION FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("\nARTIFACT VERIFICATION PASSED (offline; no API calls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
