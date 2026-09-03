# Engineering Signal 020 — Repository-Owned Windows Proof Without Moving the Reviewed Heads

**Status:** DRAFT — participant attribution review required before publication

**Observed:** 2026-09-03

**Article:** `What Counts as Windows Proof?`

**Authority:** public execution evidence only; this signal grants no merge, release, deployment, endorsement, commercial, credential, or external-action authority

## Signal

Two Windows-specific repairs had already passed in a contributor fork, but the repository-owned workflows attached to the reviewed pull requests were Ubuntu-only.

That left a precise gap:

```text
source boundary reviewed
        +
supporting fork execution passed
        +
upstream Windows branch not executed
        ↓
HOLD / NOT_RUN
```

The gap was closed with one temporary workflow in the repository that checked out two literal commit SHAs on `windows-latest`, asserted the checked-out identity before and after execution, ran only the affected verification surface, and retained bounded artifacts.

> A green run becomes decision-relevant only when the runner, subject revision, command, result and authority boundary belong to the same evidence packet.

## Exact subjects

| PR | Expected and observed head | Windows branch under test |
|---|---|---|
| [`safal207/pythiaLabs#265`](https://github.com/safal207/pythiaLabs/pull/265) | `70d4a98a4801884b1c75df0166154e2d6d28853b` | Windows `mix.cmd` discovery, platform-native `PATH` delimiter and Windows-only shell launch for the fixed command |
| [`safal207/pythiaLabs#266`](https://github.com/safal207/pythiaLabs/pull/266) | `e62820c8f3a22ec6f26b027805e2a0ff1a73f509` | selection and execution of Cargo's `solver_port.exe` output |

The temporary workflow definition was held separately in draft PR [`#269`](https://github.com/safal207/pythiaLabs/pull/269) at:

`ddf622d859bde5de4dca815a5d288735f66628c5`

It did not modify either implementation PR head.

## Smallest verification

The repository-owned workflow run was [`33766318986`](https://github.com/safal207/pythiaLabs/actions/runs/33766318986).

### PR #265 — MCP process boundary

```text
runner:       Windows
head-before:  70d4a98a4801884b1c75df0166154e2d6d28853b
command:      node integrations/mcp/smoke.mjs
result:       14 assertions passed; exit 0
head-after:   70d4a98a4801884b1c75df0166154e2d6d28853b
```

This execution reached the Windows-only branches that create a discoverable `mix.cmd`, join `PATH` with `path.delimiter`, and enable the command shell only when `process.platform === "win32"`. Caller-controlled JSON remained on child stdin; the executable and argument remained fixed.

### PR #266 — worker executable boundary

```text
runner:       Windows
head-before:  e62820c8f3a22ec6f26b027805e2a0ff1a73f509
build:        solver_port.exe produced
command:      mix test test/port_worker_test.exs
result:       3 tests, 0 failures; exit 0
head-after:   e62820c8f3a22ec6f26b027805e2a0ff1a73f509
```

The targeted suite opened the Windows executable through the same `@worker_binary` selection introduced by the reviewed change and exercised three packet-framed worker interactions.

## Artifact integrity

The two GitHub Actions artifacts were downloaded and checked against GitHub's reported archive digests:

| Artifact | GitHub artifact ID | ZIP SHA-256 | Result |
|---|---:|---|---|
| `pr-265-windows-exact-head` | `9897659571` | `1be6e23525275d0c51d765a480fda70d5a415d6b51b57921f8cc963fb1c7457b` | MATCH |
| `pr-266-windows-exact-head` | `9897711320` | `2e4b25cc1e109b68bdc9e77fa80c03a4a790a6b0f095d0628ac1116844652bb3` | MATCH |

The artifacts expire on 2026-09-10. A text extraction, closed manifest and the original archive digests are retained under [`evidence/pythialabs-ota-windows-exact-head-2026-09-03/`](../evidence/pythialabs-ota-windows-exact-head-2026-09-03/).

Archive integrity proves the downloaded ZIP bytes match the provider-reported digest. It does not independently prove GitHub runner integrity or the semantic completeness of the tests.

## What changed in the verdict

Before run `33766318986`:

```text
Windows-specific execution gate = NOT_RUN
advisory status                = HOLD
```

After the run, artifact inspection and final PR-head recheck:

```text
#265 bounded Windows gate = PASS at 70d4a98a4801884b1c75df0166154e2d6d28853b
#266 bounded Windows gate = PASS at e62820c8f3a22ec6f26b027805e2a0ff1a73f509
```

This is a change in one evidence dimension. It is not a scalar approval of either pull request.

## What this does not prove

The run does **not** establish:

- merge approval for PR #265, #266 or #269;
- Ota adoption or repository-global execution governance;
- production Windows compatibility outside the two exercised surfaces;
- credentialed provider calls, deployment or multi-repository lifecycle behavior;
- absence of unrelated defects;
- commercial endorsement by PythiaLabs, Ota or either participant.

## Reusable pattern

```text
expected immutable subject
        ↓
repository-owned workflow
        ↓
literal-SHA checkout on affected platform
        ↓
initial identity assertion
        ↓
smallest causal test
        ↓
raw log + exit status + runner identity
        ↓
final identity assertion
        ↓
artifact digest check
        ↓
bounded verdict
```

The important design choice is not the number of jobs. It is refusing to let evidence from one repository, platform, revision or authority context silently satisfy a gate defined in another.

## Collaboration and attribution boundary

This draft describes a public, bounded PythiaLabs × Ota collaboration. Bobai, founder of Ota, proposed the pressure-test package and agreed to keep the reviewed implementation heads unchanged while the repository-owned Windows gap was closed.

That attribution is included for participant review. The article must not be published, distributed or presented as an endorsement until Bobai has approved the attribution boundary in writing.

## Open question

> When CI replays code from another branch, fork or workflow, what exact identity and authority context must the evidence bind before it may influence a merge decision?

A useful answer should name one result that looks green but must still remain `HOLD`, `NOT_RUN`, `STALE` or `INCOMPLETE`.
