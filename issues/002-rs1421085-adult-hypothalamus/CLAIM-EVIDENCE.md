# Claim → evidence matrix

## C1 — exact adult locus has detectable rare accessibility

**Claim:** The 500-bp mm10 interval containing the exact mouse ortholog of human rs1421085 has detectable raw chromatin accessibility in adult male hypothalamic snATAC data despite absence from the thresholded union candidate-enhancer catalogue.

**Evidence:** GSE246791 processed H5AD raw 500-bp tile/insertion matrices; exact-coordinate gate; target-positive nuclei in seven provenance-complete hypothalamic samples.

**Strength:** supported descriptive observation.

**Does not imply:** allele dependence, enhancer function, target gene or causality.

---

## C2 — the accessibility signal has neuronal subclass structure

**Claim:** Target-tile accessibility is non-uniform across officially annotated hypothalamic subclasses and includes reproducible neuronal enrichment.

**Evidence:** 133/133 target barcodes joined to the authors' Supplementary Table 2. Seven-sample overall target rate ~0.182%. `LHA-AHN-PVH Otp Trh Glut`: 9/1,800 nuclei, ~2.74x pooled enrichment, target detected in 5/7 samples. Several other hypothalamic neuronal classes exceed background; Astro-NT and Oligo are depleted.

**Strength:** reproducible descriptive prioritization; inferential statistics still limited by rarity and one pending sample.

**Does not imply:** that a specific subclass mediates the variant phenotype.

---

## C3 — target-interval accessibility and Irx3 RNA can coexist in the same adult hypothalamic nucleus

**Claim:** An independent paired Multiome dataset contains rare filtered nuclei with an ATAC fragment overlapping the target interval and detectable `Irx3` RNA in the same nucleus.

**Evidence:** GSE226277, four official male WT hypothalamus RNA/ATAC pairs; 2/4 pairs positive; two nuclei total.

**Strength:** orthogonal same-nucleus feasibility support; extremely sparse.

**Does not imply:** enhancer-to-Irx3 regulation.

---

## C4 — current public-data evidence narrows the mechanism search

**Claim:** The data weaken the simple alternatives “the adult locus is uniformly closed” and “target-tile signal is merely proportional to abundant glial populations,” motivating a rare/context-dependent neuronal regulatory-state model.

**Evidence:** C1–C3 plus official subclass enrichment/depletion.

**Strength:** inference from convergent observations.

**Does not imply:** which TF, methylation state or 3D contact is causal.

---

## Claims explicitly NOT made

- `rs1421085 T>C` causes the observed accessibility state.
- ARID5B, CUX1, TET1, KDM2B, MECP2, DNMT1 or CXXC1 is the adult PH mediator.
- the 500-bp interval is a functional enhancer in the observed nuclei.
- accessibility at this interval causes `Irx3` expression.
- the result explains the male-specific genotype effect in the 2025 mouse study.
- GAP-001 is solved.

`GAP-001 = OPEN`  
`cause_found = false`

## Promotion requirements

### Level 2

At least one load-bearing exact-context layer such as allele-specific ATAC, direct TF occupancy, methylation/histone state, or target-interval -> Irx3 contact in the prioritized adult hypothalamic neurons.

### Level 3

Exact-allele plus mediator perturbation/rescue in the relevant adult PH cell context, or equivalently strong causal identification.
