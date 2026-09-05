# Evidence Time Machine — a working evidence-revision demo

A read-only GitHub observation, a commit applicability boundary, and the published
conditional-withdrawal reproducer. This is **not an LLM benchmark result**.

## Reproduce

From a checkout of this repository:

```sh
cd benchmarks/evidence-time-machine-v0.1
python -m unittest -v test_adapter
python study.py --out reproduced-results.json
python adapter.py replay
python adapter.py replay --sha d3f79f9e192b2df3a745fa123e0d24f2be2444fa
```

Python 3.12+; the offline path uses only the standard library. It imports the two
previously published policies from `../temporal-evidence-interim-2026-09-05/`.
The last two commands demonstrate `SUPPORTED` for the exact captured PR-head SHA
and `UNKNOWN` for the different, real merge SHA. Neither permits an action.

The public application is `../../site/evidence-time-machine.en.html`. It is a
self-contained, offline-capable interactive replay with its own claim-only
JavaScript implementation of both policies. It recomputes verdicts in the browser;
it is not a static screenshot or an LLM impersonation.

## Source and measured scope

`source_observation.json` projects one check run from a connected GitHub read that
returned eight runs. The field projection was transcribed from the tool response;
it is not represented as a raw signed HTTP export. `recorded_at` is when this
immutable local observation was recorded, **not** the check's completion time.
The observation concerns GitHub Actions run/check `101291849079`, pinned to commit
`0bf8f4095a8048d9a2ee145d71c10c9214d72a8c` in the author's own repository.

Local results: 32/32 adapter development tests; five matching queries sharing one
source observation; re-executed published synthetic audit 7/12 original vs 12/12
candidate; 240 order checks. The five query examples overlap with unit tests:
**do not sum these counters as independent tasks**. Four of the previous synthetic
cases expose the same root defect; the cycle case specifies a rejection boundary.

The load probe uses 0, 1,000 and 10,000 artificial distractors in one synthetic
scenario. Seven local repetitions at each size include the full deterministic
query and fingerprint. Construction/validation costs are reported separately.
There is no population accuracy estimate, speedup claim, or LLM latency result.

## Fresh connector read

```sh
# Optional GITHUB_TOKEN with read access may be supplied through the environment.
# No credential is printed or stored; no remote resource is mutated.
python adapter.py capture --out fresh-github-observation.json
python study.py --input fresh-github-observation.json --out fresh-results.json
```

This path is GET-only with bounded pagination and no redirects. A fresh observation
will have a new knowledge timestamp and fingerprint. It selects the same historical
check ID: it does not ask whether the newest commit is safe to deploy. Snapshot
collection is not atomic across pages; inconsistent/incomplete counts are rejected.
A GitHub Actions workflow performs this smoke read and stores its observation.
Its successful execution must be confirmed separately before claiming a live
end-to-end run. Local direct HTTPS was unavailable in the authoring environment;
the initial real observation came through the connected GitHub tool.

## Browser verification

With Playwright and an already installed Chromium:

```sh
python browser_smoke.py --chromium /usr/bin/chromium
```

The local run cross-checked 34 Python/JavaScript verdicts and 24 interface states
(three scenarios, two checkpoints, two widths, two themes), verified the JSON
download, and observed zero page errors or outbound page requests. The browser
rendered the authored HTML with `set_content` because file navigation was not
available in this environment. This is not a hosted-site or cross-browser test.

## Boundaries

- A historical success for one check ID is not the repository's required-check
  policy, current release readiness, deployment evidence, or merge authority.
- Accepted app metadata comes from the observation. This prototype neither verifies
  source signatures nor proves completeness, independence, or external truth.
- The conditional-withdrawal case is synthetic, not a GitHub incident or a newly
  discovered third-party vulnerability. Unconditional administrative withdrawals
  remain effective under the published toy policy.
- 0 comparative LLM runs, 0 independent scientific reviewers, 0 external customer
  deployments, and no claimed commercial traction. AI-assisted implementation.

Next: an independent reproduction of the pinned case and policy review in issue
[#74](https://github.com/safal207/RESONANCE/issues/74), followed by a budget-matched
R4/R5 × flat/graph experiment on genuinely new episodes.
