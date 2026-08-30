# Verification Laundering

> **A passing test shows that a repair passes. It does not necessarily show that the diagnosis behind the repair was correct.**

This repository contains the code and data for **“Verification Laundering: When Execution Evidence Fails to Verify Agent Diagnoses.”**

## Main results

* Execution gating accepts **44/45 correct diagnoses** and **24/27 fabricated diagnoses**.
* With a stronger repair model, **25/27 known-false diagnoses** still pass the execution gate.
* A simple program-change check rejects **4/24** persisted fabrications.
* Random differential testing, property-based testing, and symbolic checking each reject **20/24**, while rejecting **0/34** applicable true fixes.
* The remaining cases change behavior only outside the intended task specification.

## Repository structure

```text
config/       prompts and experiment settings
data/         programs, generations, grading, and results
scripts/      generation, verification, and analysis code
figures/      paper figures
paper/        paper source
```

## Run the checks

```bash
python scripts/verify_claims.py
```

This checks the main reported results using the included data.

## Reproducibility

See:

```text
REPRODUCIBILITY.md
```

for model settings, grading details, and instructions for rerunning the experiments.

## Environment

Install dependencies with:

```bash
pip install -r requirements.txt
```

API-based generation scripts require access to the corresponding model providers.
