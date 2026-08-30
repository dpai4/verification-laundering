# Verification Laundering

Code and frozen experimental artifacts for:

**Verification Laundering: When Passing a Test Certifies a False Agent Reflection**

## Core idea

A successful repair verifies that the repaired artifact passes a test.
It does not necessarily verify that the diagnosis which motivated the
repair was true.

We call the resulting failure **verification laundering**.

## Main results

- 44/45 true lessons preserved.
- Approximately 89% of fabricated lessons also preserved.
- 25/27 known-false diagnoses passed with a current reasoning repairer.
- Behavioral comparison caught 20/24 persisted false diagnoses.
- Random testing, property-based testing, and symbolic analysis caught the same 20 cases.
- After H21 adjudication, 127/127 completed buggy cases were specific-correct.
- H23: false-lesson following increased from 25.9% to 37.0%; paired McNemar p = 0.25.

## Scope

The central claim is conditional:

> Given a false diagnosis, successful execution of a repair does not establish
> that the diagnosis was true.

The project does not claim that current frontier models universally fabricate diagnoses.
