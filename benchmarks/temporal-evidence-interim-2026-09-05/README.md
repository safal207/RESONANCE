# Temporal evidence: interim policy audit

**2026-09-05 · Open synthetic development cases · Not an LLM benchmark result.**

A reproducible counterexample to our own earlier reference function: a conditional withdrawal can take effect even when its declared premise has expired, comes from an unaccepted source, has been withdrawn, or transitively depends on expired evidence. All four variants share one root cause. A separate cyclic-justification case introduces an explicit rejection boundary, not a claimed solution to cyclic inference.

## Reproduce the public subset

Python 3.10+; standard library only; no network, model key, external action or production service.

```sh
cd benchmarks/temporal-evidence-interim-2026-09-05
python audit.py --out /tmp/temporal-evidence-results.json
```

The command generates all 12 declared cases, compares baseline and candidate, checks 600 seeded record-order variants and 24 historical-release invariants, and exits nonzero if the candidate fails an expectation. Do not run Python with `-O`: the audit uses assertions for invariants.

| File | Purpose |
|---|---|
| `baseline.py` | Frozen original `temporal_bench.py`; known limitation preserved for comparison. |
| `hardening.py` | Experimental acyclic candidate; conditional withdrawals require active premises. |
| `audit.py` | All 12 synthetic fixtures and reproducible checks. |
| `results.json` | Saved case-level output of the actual local run. |
| `summary.json` | Additional original-package integrity and compatibility checks. |

The public runner is **audit.py**. The inherited CLI in baseline.py expects the separate v0.2 dataset and is not the public subset entrypoint. `summary.json` also records a local 68/68 baseline rerun, 68/68 with the candidate and unchanged results for 36 prior checkpoints. The full original 68-test conversation archive is NOT included here; its fingerprint is published so this subset cannot be mistaken for the full archive.

The saved Python version is an environment field, not a controlled performance measurement. Reproduction on another supported version may differ in that field. All verdicts and episode fingerprints should match. No model latency, temperature, token usage or cost was measured.

## Evidence boundary

- `SUPPORTED` means support under the declared toy policy. It is not truth, authentication, production readiness, or permission to act.
- Unconditional administrative withdrawals remain effective. This experiment does not justify restoring revoked real-world permissions.
- `known_at` releases only then-available records; validity uses a half-open interval. Query context has four exact dimensions. No hidden transfer between environments is inferred.
- Conditional dependencies must remain applicable at query time. This is an explicit chosen policy, not a universal definition of withdrawal.
- Circular justification/invalidation is rejected. Derivation from a withdrawal record is also unsupported. The candidate is not a general non-monotonic inference engine.
- The author designed the cases and candidate. 7/12 versus 12/12 is not a population accuracy estimate. 600 order checks are not 600 independent tasks. LLM runs and independent reviewers both remain zero.

Original module SHA-256: `43223dc69c148e0e637b01994bca2cff3d85b192ab1d518cc21a718663350936`.

[Full Russian methodological note](../../reports/science/temporal-evidence-interim-2026-09-05.md) · [Journal page](https://safal207.github.io/RESONANCE/reconsideration-needs-evidence.ru.html)

AI assistance was used for code, fixtures and text. This is an interim note in the project's own journal, not independent endorsement. Next: independent policy review, then R4/R5 × flat/graph with identical facts, declared whole-process budgets and new held-out episodes.
