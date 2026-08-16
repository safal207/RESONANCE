# FCRP Credential Boundary Rollout Ledger

**Date:** 2026-08-14  
**Routing source:** RESONANCE Signal 013  
**Canonical provider:** [ContractGraph-QA](https://github.com/safal207/ContractGraph-QA)  
**Exact provider head:** `cc1d1e227bbb1a25776819e6f2829bfb7a66ee58`

This is an append-only operational record, not execution authority. It records what was verified, what was rejected, and what remains scoped for a later transition.

## Contract

Each covered repository calls:

```yaml
uses: safal207/ContractGraph-QA/.github/workflows/credential-boundary-reusable.yml@cc1d1e227bbb1a25776819e6f2829bfb7a66ee58
with:
  scanner-ref: cc1d1e227bbb1a25776819e6f2829bfb7a66ee58
```

The two pins are intentionally identical. A caller branch or repository head is not capability identity. The provider workflow checks out the caller with read-only contents permission, checks out the canonical scanner at the explicit `scanner-ref`, and never prints matched values.

## Covered wave

32 draft caller PRs are open; **32/32 FCRP Credential Boundary runs passed** on their current exact heads.

| Repository | Review | State |
|---|---:|---|
| `safal207/RESONANCE` | [#49](https://github.com/safal207/RESONANCE/pull/49) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/rinse` | [#26](https://github.com/safal207/rinse/pull/26) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/LiminalDB` | [#120](https://github.com/safal207/LiminalDB/pull/120) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/LiminalOSAI` | [#194](https://github.com/safal207/LiminalOSAI/pull/194) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/Causal-Memory-Layer` | [#285](https://github.com/safal207/Causal-Memory-Layer/pull/285) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/ProofPath` | [#221](https://github.com/safal207/ProofPath/pull/221) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/T-Trace` | [#13](https://github.com/safal207/T-Trace/pull/13) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/resonance-arbitrage-graph` | [#40](https://github.com/safal207/resonance-arbitrage-graph/pull/40) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/transition-intelligence-protocol` | [#7](https://github.com/safal207/transition-intelligence-protocol/pull/7) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/SearchProof-SEO-Evidence` | [#16](https://github.com/safal207/SearchProof-SEO-Evidence/pull/16) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/CaPU` | [#88](https://github.com/safal207/CaPU/pull/88) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/LiminalQAengineer` | [#130](https://github.com/safal207/LiminalQAengineer/pull/130) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/L-THREAD-Liminal-Thread-Secure-Protocol-LTP-` | [#522](https://github.com/safal207/L-THREAD-Liminal-Thread-Secure-Protocol-LTP-/pull/522) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/pythiaLabs` | [#257](https://github.com/safal207/pythiaLabs/pull/257) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/ttm-db` | [#6](https://github.com/safal207/ttm-db/pull/6) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/DRP` | [#23](https://github.com/safal207/DRP/pull/23) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/DMP-decision-memory-protocol` | [#13](https://github.com/safal207/DMP-decision-memory-protocol/pull/13) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/Access-Orientation-Protocol` | [#4](https://github.com/safal207/Access-Orientation-Protocol/pull/4) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/LRE-Core` | [#19](https://github.com/safal207/LRE-Core/pull/19) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/guardian-layer` | [#8](https://github.com/safal207/guardian-layer/pull/8) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/DIF` | [#42](https://github.com/safal207/DIF/pull/42) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/ProofTask` | [#17](https://github.com/safal207/ProofTask/pull/17) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/osoznanie-ai` | [#71](https://github.com/safal207/osoznanie-ai/pull/71) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/Living-Relational-Identity-LRI` | [#76](https://github.com/safal207/Living-Relational-Identity-LRI/pull/76) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/Liminal-Presence-Interface-LPI` | [#97](https://github.com/safal207/Liminal-Presence-Interface-LPI/pull/97) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/Scale-Descent-Protocol-SDP` | [#7](https://github.com/safal207/Scale-Descent-Protocol-SDP/pull/7) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/ibex-agent-verification` | [#75](https://github.com/safal207/ibex-agent-verification/pull/75) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/QALim` | [#1](https://github.com/safal207/QALim/pull/1) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/LS` | [#933](https://github.com/safal207/LS/pull/933) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/typeScript-7-rc-qa-benchmark` | [#14](https://github.com/safal207/typeScript-7-rc-qa-benchmark/pull/14) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/typescript-go-qa-findings` | [#16](https://github.com/safal207/typescript-go-qa-findings/pull/16) | Draft · FCRP green · pin `cc1d1e2…` |
| `safal207/DI` | [#10](https://github.com/safal207/DI/pull/10) | Draft · FCRP green · pin `cc1d1e2…` |

Liminal has a separate security PR [#126](https://github.com/safal207/Liminal/pull/126), currently draft. Its caller run #4 passed on exact head `61503c412686209a4f50936de36f418dd23bbaf5`. Merge remains blocked until historical credentials are revoked/rotated provider-side.

## Finding history preserved

- Initial rollout exposed five BLOCK clusters: 31 RESONANCE benchmark fixture lines; one CML deterministic demo signing fixture; three LTP deterministic reference-fixture assignments; one LiminalQAengineer local compose credential set; and one LS CI fixture plus one LS local compose credential set.
- The first provider action pin was rejected after a native Actions setup failure; it was superseded by resolvable pinned v4 action revisions.
- The scanner was then tightened with an explicit `# fcrp: fixture` marker. Marker lines suppress only literal-assignment findings; provider/private-key token shapes still block. Unmarked runtime/dev defaults remain blocked.
- All five consumer remediation clusters were re-run and passed.

## Explicit exclusions

- `ContractGraph-QA` — provider repository; canonical workflow is merged.
- `safal207` — profile repository, not a runtime consumer.
- `TachTachAI` — default-head resolution unavailable during the audit; no mutation attempted.
- Forks kept outside this owner rollout: `linkedin-api-mcp`, `crewAI-upstream`, `trashnet`, `terra_ai`.

## Review queue

The remaining non-fork repositories were inventoried but not mutated in this wave. They require an explicit scope decision before adding a workflow; dormant or non-runtime repositories should not receive a blind caller just because they exist.

- `safal207/typescript-7-rc-qa-benchmark` — REVIEW_QUEUE / scope before mutation
- `safal207/robys-coffee-house-demo` — REVIEW_QUEUE / scope before mutation
- `safal207/DAO_lim` — REVIEW_QUEUE / scope before mutation
- `safal207/GardenLiminal` — REVIEW_QUEUE / scope before mutation
- `safal207/fediverse-portability-test-kit` — REVIEW_QUEUE / scope before mutation
- `safal207/Vajra-Space-Evidence-Lab` — REVIEW_QUEUE / scope before mutation
- `safal207/temporal-market-intelligence` — REVIEW_QUEUE / scope before mutation
- `safal207/smart-market-data-gateway` — REVIEW_QUEUE / scope before mutation
- `safal207/land_plf` — REVIEW_QUEUE / scope before mutation
- `safal207/Kairos-Gate-for-X-Cell` — REVIEW_QUEUE / scope before mutation
- `safal207/IPO-Quality-Score` — REVIEW_QUEUE / scope before mutation
- `safal207/lotus-private-relocation` — REVIEW_QUEUE / scope before mutation
- `safal207/Codex-Adoption-Lab` — REVIEW_QUEUE / scope before mutation
- `safal207/ai-cafe-network` — REVIEW_QUEUE / scope before mutation
- `safal207/crewAI` — REVIEW_QUEUE / scope before mutation
- `safal207/Proto-liminal` — REVIEW_QUEUE / scope before mutation
- `safal207/KuponGo` — REVIEW_QUEUE / scope before mutation
- `safal207/liminal-voice-core` — REVIEW_QUEUE / scope before mutation
- `safal207/nexus-sales` — REVIEW_QUEUE / scope before mutation
- `safal207/SOMA-Self-Organizing-Modular-Architecture` — REVIEW_QUEUE / scope before mutation
- `safal207/L-EDGE-Liminal-Edge-OS` — REVIEW_QUEUE / scope before mutation
- `safal207/cybernetics-of-care` — REVIEW_QUEUE / scope before mutation
- `safal207/Lifetra` — REVIEW_QUEUE / scope before mutation
- `safal207/liminal-thread-book` — REVIEW_QUEUE / scope before mutation
- `safal207/Universe-E` — REVIEW_QUEUE / scope before mutation
- `safal207/web4-liminal` — REVIEW_QUEUE / scope before mutation
- `safal207/noosphere-city` — REVIEW_QUEUE / scope before mutation
- `safal207/finanalytics-core` — REVIEW_QUEUE / scope before mutation
- `safal207/voice-to-evidence` — REVIEW_QUEUE / scope before mutation
- `safal207/self-creation-protocol` — REVIEW_QUEUE / scope before mutation
- `safal207/CareerOS` — REVIEW_QUEUE / scope before mutation
- `safal207/nexus-ecosystem` — REVIEW_QUEUE / scope before mutation
- `safal207/qa-fintech-api-python-course` — REVIEW_QUEUE / scope before mutation
- `safal207/Awakening` — REVIEW_QUEUE / scope before mutation
- `safal207/liminal-you` — REVIEW_QUEUE / scope before mutation
- `safal207/students` — REVIEW_QUEUE / scope before mutation
- `safal207/English-Liminal-` — REVIEW_QUEUE / scope before mutation
- `safal207/trashcoin` — REVIEW_QUEUE / scope before mutation
- `safal207/agi-consciousness-safety` — REVIEW_QUEUE / scope before mutation
- `safal207/Neurolab` — REVIEW_QUEUE / scope before mutation
- `safal207/Liminal-2.0.-For-people` — REVIEW_QUEUE / scope before mutation
- `safal207/liminal-shelter` — REVIEW_QUEUE / scope before mutation
- `safal207/Garder-2d` — REVIEW_QUEUE / scope before mutation
- `safal207/test_qorer_f` — REVIEW_QUEUE / scope before mutation
- `safal207/mweb3waves` — REVIEW_QUEUE / scope before mutation
- `safal207/noosphere-server` — REVIEW_QUEUE / scope before mutation

## Next transition

Use this ledger plus Article 05 → Article 06 → Signals 011/012/013 before the SYSTEM-004 ProofPath → LiminalDB lane. Reuse existing causal, provenance, replay, exact-head, authority-negative and LTP trace lanes; create no new skill until an invariant gap is proven with a negative regression.
