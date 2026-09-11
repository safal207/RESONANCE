# Graph–Field Dynamics v0.1

Status: **experimental / advisory**  
Scope: work graphs, agent routing, maintenance and causal investigation  
Non-claim: this is **not** a physical field theory or a theory of consciousness.

## 1. Purpose

Graph-oriented agent systems are good at representing what exists and which transitions are structurally reachable. They are weaker at answering a prior question:

> Where should attention go next?

Graph–Field Dynamics (GFD) adds an advisory field over a bounded work graph. The graph describes structure; the field describes time-local pressure, uncertainty, opportunity and actionability over that structure.

The canonical invariant is:

> **Field proposes. Graph constrains. Authority permits. Evidence verifies.**

A high field score is never authority to execute, merge, deploy, spend, mutate production state, or escalate privileges.

## 2. Unit of analysis

The primary node is a **work node or transition**, not necessarily a repository.

Examples:

- `measure trust-spine cost/latency`;
- `resolve one compatibility frontier`;
- `triage a proposed-memory queue`;
- `obtain an external witness`;
- `repair one persistence boundary`.

A repository may contain several low-pressure proven regions and one high-pressure unproven transition. Scoring the repository as a single node would hide that distinction.

## 3. Local field components

Each component is normalized to `[0,1]` and must be attached to explicit evidence or declared as a heuristic estimate.

| Component | Meaning | Weight |
|---|---|---:|
| `divergence` | gap between intended/proven state and current state | 0.25 |
| `uncertainty` | unresolved ambiguity or missing discriminating evidence | 0.20 |
| `blast_radius` | expected dependency reach / system centrality | 0.20 |
| `freshness_gap` | risk that evidence, pins or assumptions are stale | 0.15 |
| `open_pressure` | unresolved active work, queue or dependency pressure | 0.10 |
| `opportunity` | expected information gain or useful leverage | 0.10 |

Local tension:

```text
T(v) = 0.25D + 0.20U + 0.20B + 0.15F + 0.10P + 0.10O
```

## 4. Tension is not actionability

Some important nodes are currently blocked by an external dependency, missing authority, required human decision, unavailable witness, or another prerequisite.

`blockedness ∈ [0,1]`

```text
A(v) = T(v) × (1 - 0.70 × blockedness(v))
```

This intentionally preserves a blocked hotspot as visible tension while reducing its rank as the next executable target.

A highly important `HOLD` should remain visible instead of being fabricated into an `ACCEPT`.

## 5. One-hop field coupling

GFD v0.1 supports bounded one-hop diffusion through declared work-graph edges.

For node `v`:

```text
N(v) = mean(edge_weight(v,u) × T(u))
Φ(v) = min(1, A(v) + α × N(v))
```

Default `α = 0.10`.

Edges are treated as undirected contextual coupling in v0.1. Directional diffusion, decay over time and learned coefficients are deliberately deferred.

## 6. Focus

Focus is an **observation/allocation operator**, not evidence of truth.

Repeated attention may reveal more evidence and therefore legitimately update field components, but attention intensity itself must not be used to prove that a hypothesis is correct.

This prevents a self-reinforcing loop:

```text
attention → higher score → more attention → “therefore true”
```

The valid loop is:

```text
focus → observation → new evidence → recompute field
```

## 7. Human / presence boundary

When a graph contains a human `SELF` or presence-related node, intrinsic human worth is outside the optimization objective.

A negative outcome may update:

- strategy;
- confidence in a hypothesis;
- evidence;
- next transition;
- requested support.

It must not be converted into a machine claim that the person has lower intrinsic value.

This is compatible with the Self-creation Protocol distinction between observable behavior and a Presence Space that must not be optimized.

In practical terms, the earlier “self-love” idea becomes a systems invariant:

> **Failure updates the model of action, not the worth of the actor.**

## 8. Output contract

A GFD orientation pass returns, for every node:

- `tension`;
- `blockedness`;
- `actionability`;
- `diffusion_bonus`;
- `field_score`;
- evidence references;
- `next_safe_transition`.

The output is advisory only and must explicitly state:

```text
mode = ADVISORY_ONLY
authority_granted = false
```

## 9. Operating loop

```text
intent
→ bound the work graph
→ collect current evidence
→ score local field
→ apply bounded diffusion
→ separate tension from actionability
→ rank hotspots
→ causal zoom on the top actionable node
→ hand off to an authority-aware execution path
→ observe outcome
→ update evidence
→ recompute field
```

## 10. Falsification criteria

GFD is useful only if it beats simpler routing baselines.

For repeated maintenance/research cycles compare GFD against:

1. FIFO / oldest-open-first;
2. repository-level activity ranking;
3. raw risk-only ranking;
4. human-selected next task.

Measure at minimum:

- useful findings per unit cost;
- time to first meaningful divergence;
- avoided work on blocked nodes;
- false-hotspot rate;
- stale-evidence catches;
- downstream rework after the selected transition.

If GFD does not improve routing under frozen evaluation criteria, reduce or discard the model rather than protecting the concept.

## 11. Relationship to Neo Resonance

GFD is an orientation layer, not a seventh proof stage.

The existing trust spine remains:

```text
intent → ProofPath → CML → LiminalDB → RINSE → ContractGraph-QA
```

GFD decides where to inspect next. It does not replace causal memory, evidence, durability, reflection, verification, or authority boundaries.

CaPU remains an adjacent execution-control boundary. A GFD score cannot grant CaPU, or any other component, semantic or execution authority.
