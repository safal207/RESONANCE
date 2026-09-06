# RESONANCE Corrections + Version History Contract

**Verdict:** PASS

- Managed publications: **4**
- Managed routes: **10**
- Append-only history entries: **6**
- Diff gate: **checked**
- Changed managed routes in this diff: **0**
- New history entries in this diff: **1**

## Release invariants

- Registered published routes must exist and end at the version declared by the registry.
- Version transitions must form an unbroken chain from initial publication to the current version.
- Existing history entries are immutable and append-only once v0.5 exists on the base branch.
- A modified managed published page must be covered by a newly appended history entry in the same change.
- Every history entry records change type, claim impact, reason, affected versions and inspectable evidence URLs.
- Non-publication updates require RESONANCE GitHub evidence.

## Evidence boundary

Passing this contract proves publication-version bookkeeping, append-only history integrity and evidence linkage for registered routes. It does **not** prove that the correction itself is editorially or factually sufficient, and it makes no claim about unregistered pages.
