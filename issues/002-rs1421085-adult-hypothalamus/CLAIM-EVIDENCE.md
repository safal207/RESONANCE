# Claim → evidence matrix

**Publication state:** narrow Level-1 computational discovery candidate  
**Causal state:** `GAP-001 = OPEN`, `cause_found = false`

## C0 — exact coordinate identity survives assembly cross-check

**Claim:** The mouse rs1421085 ortholog used by the analysis is sequence-anchored and maps consistently across mouse assemblies.

**Evidence:** unique published-guide match at mm10 `chr8:91,374,371–91,374,372` (0-based); UCSC mm10→mm39 liftOver gives `chr8:92,100,999–92,101,000`; lifted site lies inside current GRCm39 `Fto`.

**Strength:** verified coordinate/provenance gate.

**Does not imply:** biological function or causality.

---

## C0b — exact rs1421085 site is not hibE1

**Claim:** The exact ortholog-containing interval is distinct from the 2025 Science `Fto-Irx::hibE1` element.

**Evidence:** MGI places hibE1 at GRCm39 `chr8:92,114,859–92,119,641`; exact site is 13,859 bp upstream; 500-bp target tile is 13,731 bp upstream. No overlap.

**Strength:** verified coordinate distinction.

**Importance:** prevents a false novelty/identity claim. Science 2025 already establishes functional adult hypothalamic Fto-Irx cis-regulatory architecture, but not the exact rs1421085 interval.

---

## C1 — exact adult locus has detectable rare accessibility

**Claim:** The 500-bp mm10 interval containing the exact mouse ortholog has detectable raw chromatin accessibility in adult male hypothalamic snATAC data despite not behaving as a strong constitutive catalogue element.

**Evidence:** GSE246791 all-eight frozen barcode pack; 83,321 nuclei; 154 target-tile-positive nuclei; raw insertion signal near the ortholog in individual samples.

**Strength:** supported descriptive observation across 8/8 intended samples.

**Does not imply:** allele dependence, enhancer function, target gene or causality.

---

## C2 — accessibility has replicate-aware neuronal subclass structure

**Claim:** Target-tile accessibility is non-uniform across official hypothalamic subclasses and includes a reproducible neuronal priority signal.

**Evidence:** all 154/154 target barcodes join to the authors' Supplementary Table 2. `LHA-AHN-PVH Otp Trh Glut`: 11/1,842 target-positive nuclei, signal in 6/8 biological samples, pooled enrichment ~3.23×. Sample-stratified Mantel-Haenszel common OR ~3.64 (95% CI ~1.95–6.79); BH-adjusted q ~0.00137 across represented official subclasses. Breslow-Day p ~0.032 preserves evidence of between-sample heterogeneity.

**Secondary evidence:** `DMH-LHA Vgll2 Glut`: 4/382, ~5.67× pooled enrichment, but only 3/8 samples.

**Negative/depletion evidence:** Astro-NT ~0.48×; Oligo ~0.34×.

**Strength:** statistically supported prioritization with replication, multiple-testing correction and explicit heterogeneity.

**Does not imply:** that `LHA-AHN-PVH Otp Trh Glut` is the causal cell of action.

---

## C3 — target accessibility and Irx3 RNA can coexist in one adult hypothalamic nucleus

**Claim:** An independent paired Multiome dataset contains rare filtered nuclei with an ATAC fragment overlapping the target interval and detectable `Irx3` RNA in the same nucleus.

**Evidence:** GSE226277; four official male WT hypothalamus RNA/ATAC pairs; 2/4 pairs positive; two nuclei total.

**Strength:** orthogonal same-nucleus feasibility support; extremely sparse.

**Does not imply:** enhancer-to-Irx3 regulation.

---

## C4 — existing public data narrow the mediator search

**Claim:** The evidence weakens simple models in which the adult exact site is uniformly closed or in which target signal is merely proportional to abundant glial populations. A rare/context-dependent neuronal-state model remains viable.

**Evidence:** C1–C3 plus all-eight subclass enrichment/depletion.

**Strength:** inference from convergent observations.

**Does not imply:** which TF, epigenetic state or 3D contact is causal.

---

## C5 — broad adult Fto-Irx regulatory architecture is prior art

**Claim:** Adult hypothalamic Fto-Irx chromatin regulation and functional long-range cis-elements were established before this reanalysis.

**Evidence:** Steinwand et al., Science 2025 (PMID 40743330) and Ferris et al., Science 2025 (PMID 40743333): adult hypothalamic chromatin/multiomics, H3K27ac-associated contacts, `hibE1-5`, knockout effects and metabolic-state programs.

**Strength:** established prior art.

**Consequence for novelty:** RESONANCE Issue 002 may claim only the exact-site targeted reanalysis, all-eight official subclass structure and independent same-nucleus convergence — not discovery of the Fto-Irx TAD or generic adult hypothalamic regulatory architecture.

---

## Claims explicitly NOT made

- `rs1421085 T>C` causes the observed accessibility state.
- hibE1 is the exact rs1421085 element.
- the 500-bp target interval is a proven functional enhancer.
- ARID5B, CUX1 or another candidate occupies the exact adult PH site.
- accessibility at the target interval causes `Irx3` expression.
- same-nucleus ATAC/RNA establishes a regulatory edge.
- a specific official subclass is the causal cell of action.
- the result explains the male-specific genotype effect.
- GAP-001 is solved.

## Promotion requirements

### Level 2

At least one load-bearing **exact-site / exact-context** layer, preferably one of:

- adult hypothalamic target-interval → `Irx3` contact with explicit resolution/provenance;
- allele-specific accessibility;
- direct ARID5B/CUX1/other TF occupancy at the exact site;
- exact-site methylation/histone-state evidence in the prioritized adult neuronal context.

A wild-type 3D contact would strengthen H4 but would not by itself establish allele dependence.

### Level 3

Exact-allele plus mediator perturbation/rescue in the relevant adult posterior-hypothalamic context, or equivalently strong causal identification.
