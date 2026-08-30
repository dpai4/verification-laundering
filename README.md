# Verification Laundering

Anonymous code and frozen artifacts for the double-blind workshop submission
**“Verification Laundering: When Passing a Test Certifies a False Agent Reflection.”**

> **A passing test is evidence that a repair passes. It is not necessarily evidence that the diagnosis which motivated the repair was true.**

Successful execution verifies a repair, not necessarily the explanation that produced it. We call the resulting failure mode **verification laundering**.

## Scientific scope

The study separates three stages that should not be conflated:

1. **Fabrication:** Does a model generate an unsupported diagnosis? This is model-dependent; the paper does not claim that frontier models generally hallucinate bugs or fail end to end at high rates.
2. **Laundering:** Conditional on a false diagnosis existing, does a verification gate certify it? This is the core architectural mechanism studied here.
3. **Authority:** Does describing a lesson as “verified” make a later agent more likely to follow it? The current evidence is preliminary and underpowered.

## Main frozen results

- The historical execution gate preserves 44/45 true lessons and approximately 89% of fabricated lessons.
- With a current reasoning model as the repairer, 25/27 (93%) injected known-false diagnoses pass the execution gate.
- Simple repair self-consistency catches 4/24 persisted fabrications.
- Behavioral comparison catches 20/24 (83%), with 0/34 observed tested true-fix false discards. This is not a claim that verification laundering or specification conformance is solved.
- Random differential testing, property-based testing, and symbolic analysis identify the same 20 cases and miss the same four. In this artifact, symbolic analysis refers to the CrossHair backend exposed by `pbt_gate.py`; it is not a separate general-purpose symbolic verifier. The four residual cases change behavior while broadening the assumed task specification.
- H21 contains 281 frozen generations: Claude Opus 5, 105/105; Gemini 3.1 Pro, 105/105; DeepSeek R1-0528, 71/105 (a partial exploratory sample). After five automated-grading corrections, all 127 completed H21 BUGGY diagnoses are specific-correct.
- In the H23 authority pilot, FOLLOW is 7/27 (25.9%) for control and 10/27 (37.0%) for execution-verified framing. Discordant pairs are 0 control-only and 3 verified-only; exact McNemar \(p=0.25\). This is directional, preliminary evidence, not statistical confirmation.
- H22 is an incomplete external-validity extension and does not support a headline empirical result.

## Repository layout

```text
config/prompts/     exact prompts retained for the included experiments
data/               frozen banks, outputs, grading, protocols, and gate inputs
scripts/            generation and analysis code
figures/            reserved for submission figures
paper/              reserved for anonymous paper sources
```

`data/historical/` contains the historical reflection/framing runs, `data/laundering/` the injected-diagnosis run, `data/verification/` frozen inputs used by stronger gates, and `data/h21/`–`data/h23/` the later studies.

## Artifact verification

The reviewer-facing, offline entry point is:

```bash
python scripts/verify_claims.py
```

It makes no network or API calls. It checks required files, the published SHA-256 values, H21 completion counts and adjudicated endpoint, and H23 manifest/output sizes and paired authority result.

This command verifies the integrity and internal consistency of the included artifact. It does **not** rerun model generation, recreate historical environments, or establish one-command end-to-end reproduction. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the boundary between artifact verification, frozen-output analysis, and API-dependent reruns.

## Environment

The core verifier uses only the Python standard library. Historical generation scripts used the pinned packages in `requirements.txt`; some provider-dependent scripts also require provider SDKs, credentials supplied through environment variables, and model access that may no longer be identical. No credentials are included.

## Double-blind status

This working tree intentionally contains no author list, affiliation, personal contact information, identifying citation metadata, or author-named copyright. Repository history must also be anonymized before release; a clean anonymous history is recommended rather than publishing the current development history.
