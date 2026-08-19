# Level-2 Addendum — structural and methylation convergence at the rs1421085 ortholog

**Status:** mechanistic narrowing, not mechanism resolution  
**Date:** 2026-08-19  
**Linked research:** `safal207/CAUSAL-DNA`, GAP-001

## Why this addendum exists

The original Issue 002 article established a narrow Level-1 computational result: the exact mouse ortholog of human rs1421085 sits in a rare but reproducible adult hypothalamic chromatin state with statistically structured neuronal-subclass accessibility and sparse independent same-nucleus compatibility with `Irx3` expression.

New analyses now narrow the missing molecular interval further.

The unresolved causal edge remains:

`rs1421085 T>C -> M? -> Irx3 up in adult male posterior hypothalamus`

No mediator has been identified and no causal edge is promoted in this addendum.

---

## 1. The SNP-containing contact bin has a published adult-hypothalamus contact to the Irx3 promoter bin

A targeted reanalysis of the published adult-hypothalamus H3K27ac+ PLAC-seq processed callset identifies one significant 10-kb interaction between:

- the bin containing the exact rs1421085 mouse ortholog: `chr8:91370000-91380000` (mm10);
- the `Irx3` promoter/TSS bin: `chr8:91800000-91810000`.

Primary processed-call statistics:

| Metric | Value |
|---|---:|
| observed contact count | 49 |
| expected | 12.6272643735288 |
| FDR | 2.8483024481983e-14 |

This is strong structural **compatibility** between the exact-ortholog-containing bin and the `Irx3` promoter region in adult hypothalamus.

### Why we do not call this a solved enhancer-target mechanism

The evidence has three load-bearing limits:

1. resolution is 10 kb, so the call does not prove that the exact 500-bp tile or SNP base is the contacting anchor;
2. the data are wild-type and do not compare T versus C alleles;
3. a secondary interaction-model table does not reproduce the primary call's exact count/expected/FDR tuple, while a separate Fed/Fasted 5-kb comparison does not show a significant state-dependent difference for the corresponding pair (`FDR = 1.0`).

The correct interpretation is therefore a **positive primary structural call with preserved cross-callset discordance**, not a causal contact claim.

---

## 2. The exact locus is surrounded by a reproducibly methylated CG environment

Three independent adult male hypothalamus WGBS replicates were queried at the dynamically lifted mm9 ortholog.

The wild-type ortholog base itself is T and cannot be methylated. The relevant question is whether methylatable cytosines exist immediately around it.

### mCG within +/-250 bp

| replicate | coverage-weighted mCG |
|---|---:|
| GSM2241593 | 95.918% |
| GSM2241594 | 97.222% |
| GSM2241595 | 93.103% |

A qualifying CG occurs just **1 bp upstream** of the ortholog in all three datasets:

| replicate | coverage | methylation at nearest CG |
|---|---:|---:|
| GSM2241593 | 11 | 100% |
| GSM2241594 | 6 | 83.33% |
| GSM2241595 | 6 | 83.33% |

### mCAC within +/-250 bp

mCAC is present but substantially lower and more variable:

- replicate 1: 12.903%;
- replicate 2: 25.974%;
- replicate 3: 13.043%.

The nearest qualifying CAC is +19 bp from the ortholog and has low/absent methylation at that individual position in these bulk datasets.

### Meaning

This does **not** prove a methylation-mediated rs1421085 mechanism.

It does establish a new constraint on the hypothesis space: the exact ortholog resides next to a strongly methylated CG substrate in adult male hypothalamus, making methylation-sensitive reader/chromatin-state mechanisms physically plausible rather than merely motif-derived speculation.

---

## 3. The convergent regulatory surface is getting smaller

The evidence can now be written as:

```text
exact rs1421085 mouse ortholog
        |
        +--> rare 500-bp adult hypothalamic accessibility
        |
        +--> replicate-prioritized neuronal subclass state
        |      LHA-AHN-PVH Otp Trh Glut
        |
        +--> sparse independent same-nucleus locus ATAC + Irx3 RNA
        |
        +--> 10-kb structural contact compatibility with Irx3 promoter
        |
        +--> strongly methylated adjacent CG substrate (3/3 WGBS)
        |
        v
      M remains unknown
        |
        v
Irx3 increase after exact T>C in vivo
```

The unknown mediator is no longer unconstrained. A defensible model now requires a mechanism that can operate in a rare adult neuronal chromatin state, at a sequence whose containing contact bin can physically access `Irx3`, in a locally methylated regulatory environment.

---

## 4. Current competing mechanistic families

### Classical exact-site reader branch

**ARID5B** and **CUX1** remain high-value because their exact-site allele-sensitive motif grammar is portable human-to-mouse under a strict same-motif/same-strand/same-offset criterion, both are feasible in adult `Irx3+` VPH cells, and both occur in the two sparse same-nucleus locus+/`Irx3+` Multiome nuclei.

The decisive missing datum is direct adult hypothalamic exact-site occupancy with an exact T-versus-C contrast.

### Methylation-sensitive / epigenetic-state branch

The reproducible adjacent mCG state materially strengthens this family as a plausible context.

Candidates retained by earlier motif/cell-context screens include `MECP2`, `TET1`, `KDM2B` and `DNMT1`, but none is established as the mediator.

A direct adult-hypothalamus MeCP2 ChIP/Input exact-locus analysis is still being resolved at the time of this addendum. It is intentionally not counted as positive evidence until its matched-input result is complete.

---

## 5. Novelty boundary after comparison with prior Fto-Irx work

This addendum does **not** claim the first Fto-region-to-Irx3 contact. Broader Fto-Irx regulatory architecture and functional hypothalamic CREs have already been reported.

The exact rs1421085 ortholog also does not overlap the previously perturbed `Fto-Irx::hibE1` element; after assembly reconciliation it lies about 13.9 kb away. Thus those CRE deletion experiments do not constitute a perturbation of the exact SNP-containing sequence.

The narrower computational contribution remains the integration of:

- an exact rs1421085-ortholog focus;
- reproducible rare 500-bp accessibility across the intended adult hypothalamus sample set;
- replicate-aware official neuronal-subclass enrichment;
- independent same-nucleus exact-locus/`Irx3` feasibility;
- a significant published 10-kb SNP-containing-bin/`Irx3`-promoter-bin PLAC call with preserved secondary-callset disagreement;
- reproducible local methylated-CG substrate in 3/3 adult male hypothalamus WGBS replicates.

---

## 6. What would move this from Level-2 narrowing to a mechanistic discovery

The decisive design remains an exact-allele, sex-stratified, cell-resolved adult posterior-hypothalamus experiment that measures in matched biological material:

1. `Irx3` expression;
2. exact-locus accessibility;
3. local methylation;
4. ARID5B/CUX1/top methylation-reader occupancy;
5. exact-element-to-`Irx3` contact;
6. mediator perturbation and rescue.

A molecular discovery claim requires the mediator layer to survive that intervention chain.

## Current verdict

`GAP-001 = OPEN`  
`cause_found = false`

**Level-1 computational discovery remains supported. Level-2 evidence has materially narrowed the regulatory surface, but the molecular mediator M is not yet identified.**
