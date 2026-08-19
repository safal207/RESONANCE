# Open-data evidence for a rare adult hypothalamic state at the rs1421085 ortholog

**RESONANCE — Issue 002**  
**Article type:** computational discovery / open-data reanalysis  
**Status:** **narrow Level-1 discovery candidate**; molecular mechanism unresolved  
**Updated:** 19 August 2026

## Abstract

The obesity-associated non-coding variant `rs1421085` has experimentally established regulatory effects in several contexts, yet the molecular state connecting the exact homologous T>C substitution to increased `Irx3` in the adult male posterior hypothalamus remains unresolved. We reanalysed two independent public adult-mouse hypothalamus datasets at the exact mouse ortholog rather than at a broad FTO-region proxy.

A sequence-based coordinate gate resolves the ortholog at `mm10 chr8:91,374,372` (1-based; T>C). Independent UCSC liftOver maps the same base to `GRCm39 chr8:92,101,000` (1-based), inside `Fto`. This site is **not** the recently characterized `Fto-Irx::hibE1` enhancer: the exact ortholog lies 13,859 bp upstream of the GRCm39 hibE1 interval. This distinction matters because 2025 work in *Science* already established adult hypothalamic chromatin accessibility, H3K27ac-associated long-range contacts and causal knockout effects for several cis-elements in the Fto-Irx TAD. The present novelty claim is therefore deliberately narrower.

In GSE246791, an adult mouse-brain single-nucleus ATAC atlas, the 500-bp tile containing the exact ortholog showed rare raw accessibility across all eight intended male hypothalamus samples. The complete barcode evidence pack contains **83,321 nuclei and 154 target-tile-positive nuclei**. Exact joins to the authors' official cell metadata reveal non-uniform subclass structure. The most reproducible prioritized neuronal subclass, `LHA-AHN-PVH Otp Trh Glut`, contains **11/1,842 target-positive nuclei**, with signal in **6/8 biological samples** and a pooled enrichment of approximately **3.23×**. A sample-stratified Mantel-Haenszel analysis gives a common odds ratio of approximately **3.64** (95% CI **1.95–6.79**); the signal remains significant after Benjamini-Hochberg correction across the represented official subclasses (`q≈0.00137`). The effect is heterogeneous across samples (Breslow-Day `p≈0.032`), so it should not be interpreted as a uniform cell-class effect. `DMH-LHA Vgll2 Glut` shows a larger pooled enrichment (~5.67×) but occurs in only 3/8 samples and is therefore less reproducible.

In the independent paired hypothalamus Multiome dataset GSE226277, 2/4 biological pairs contain a filtered nucleus with both an ATAC fragment overlapping the same target interval and detectable `Irx3` RNA. Only two such nuclei were observed, making this sparse orthogonal support rather than evidence of regulation.

Together, these results identify a narrow, testable adult hypothalamic state at the exact rs1421085 ortholog. They do **not** show allele-specific accessibility, direct TF occupancy, target-interval-to-`Irx3` contact, enhancer activity or causal mediation. `GAP-001` therefore remains open.

---

## 1. The unresolved edge

The strongest known causal chain around rs1421085 is context-dependent.

In human adipocyte progenitors, the T>C risk allele disrupts an ARID5B repressor motif, increases enhancer activity, derepresses `IRX3/IRX5`, alters thermogenic programming and can be rescued experimentally. This is a useful positive-control mechanism, but it cannot be imported automatically into adult hypothalamic neurons.

The adult CNS question became sharper after an exact homologous T>C mouse model showed increased brain `Irx3`, including an allele-dose increase in the male posterior hypothalamus. Manipulating IRX3-positive posterior-hypothalamic neurons connected IRX3 abundance to neuronal activity, feeding and body weight. Yet the regulatory mediator between the exact DNA substitution and adult hypothalamic `Irx3` remained unresolved.

The open edge is therefore:

```text
rs1421085 T>C
      ↓
 adult posterior-hypothalamic molecular state M ?
      ↓
    Irx3 ↑
      ↓
IRX3+ neuronal activity ↓
      ↓
food intake / body weight ↑
```

This study asks only what existing public chromatin and paired RNA/ATAC data can establish about the exact locus before a mediator is claimed.

---

## 2. Coordinate identity is a causal prerequisite

Approximate locus matching is especially dangerous for non-coding variants: a biologically active neighboring enhancer can be mistaken for the exact SNP element.

CAUSAL-DNA therefore resolves the mouse ortholog from the published edit sequence against the chromosome reference. The published wild-type guide has a unique match in the mm10 chromosome 8 sequence, giving:

- `GRCm38/mm10 chr8:91,374,371–91,374,372` (0-based half-open);
- `chr8:91,374,372` (1-based);
- assembly-strand allele `T>C`.

A second, independent assembly cross-check uses the UCSC `mm10ToMm39` chain. It maps the exact base to:

- `GRCm39 chr8:92,100,999–92,101,000` (0-based half-open);
- `chr8:92,101,000` (1-based).

The associated 500-bp atlas tile maps from:

```text
mm10  chr8:91,374,000–91,374,500
```

to:

```text
mm39  chr8:92,100,628–92,101,128
```

The lifted exact site lies within the current GRCm39 `Fto` interval.

### 2.1 The exact site is not hibE1

The 2025 *Science* study of hibernation-associated Fto-Irx cis-elements is essential prior art. MGI annotates `Fto-Irx::hibE1` (`Rr695574`) at:

```text
GRCm39 chr8:92,114,859–92,119,641
```

The exact rs1421085 ortholog does not overlap hibE1. The interval-to-interval distance is:

- exact base to hibE1: **13,859 bp**;
- 500-bp target tile to hibE1: **13,731 bp**.

Thus hibE1 supplies strong evidence that the neighboring adult hypothalamic Fto-Irx regulatory landscape is functional and can contact `Irx3/Irx5`; it does not establish the regulatory behavior of the exact rs1421085 site.

---

## 3. Prior art changes the novelty boundary

A broad claim such as “adult hypothalamic Fto-Irx chromatin regulation has not been shown” would be wrong.

Steinwand and colleagues reported adult hypothalamic single-nucleus chromatin profiles, H3K27ac-associated PLAC-seq contacts and knockout experiments for five `Fto-Irx::hibE` cis-elements. These elements form long-range regulatory contacts in the Fto-Irx TAD, and individual deletions alter `Fto`, `Irx3` and/or `Irx5` expression and metabolic phenotypes in context-dependent ways. A companion *Science* study mapped hypothalamic gene-expression and chromatin programs across fed, fasted and refed states.

Accordingly, the present work makes a narrower, falsifiable novelty claim:

> **Public adult hypothalamic data support rare accessibility specifically at the 500-bp interval containing the exact rs1421085 mouse ortholog, with reproducible official neuronal-subclass structure, while an independent paired Multiome dataset contains sparse same-nucleus target-interval ATAC / `Irx3` RNA co-detection.**

This is not a claim of a new Fto-Irx TAD, a new generic adult hypothalamic enhancer landscape, or a solved rs1421085 mechanism.

---

## 4. Eight-sample exact-locus accessibility

GSE246791 is a large adult mouse-brain snATAC atlas. The processed H5ADs preserve a 500-bp tile matrix, raw insertion information and nucleus barcodes.

The target tile is not a strong constitutive catalogue element. It is absent from the thresholded atlas-wide union candidate-enhancer catalogue. However, querying the raw matrix at the exact ortholog-containing tile finds low-frequency signal across the intended adult male hypothalamic samples.

A provenance-safe recovery of the eighth sample, `GSM7876882 / CEMBA200520_9L`, resolved its exact processed H5AD filename directly from the official GEO SOFT record rather than from a guessed filename. That sample contained 10,314 filtered nuclei, including 21 target-tile-positive nuclei and 19 nuclei with an insertion within ±250 bp of the ortholog.

The frozen all-eight evidence pack now contains:

- biological samples: **8**;
- filtered nuclei: **83,321**;
- target-tile-positive nuclei: **154**;
- overall target-positive rate: **~0.1848%**.

The result is therefore neither “the locus is strongly open” nor “the adult locus is inaccessible.” A better description is:

```text
not a strong catalogue cCRE
        AND
not uniformly inaccessible
        ↓
rare / subthreshold adult accessibility
```

---

## 5. Official annotations reveal replicate-aware neuronal structure

Every target barcode was joined to the authors' official Supplementary Table 2 rather than re-annotated from sparse marker expression.

All **154/154** target-tile barcodes matched official sample/subclass metadata.

### 5.1 The most reproducible priority subclass

`LHA-AHN-PVH Otp Trh Glut` contains:

- target-positive nuclei: **11**;
- total nuclei: **1,842**;
- samples with target signal: **6/8**;
- pooled enrichment over the all-nucleus target rate: **~3.23×**.

Treating the biological sample as the replication stratum gives:

- Mantel-Haenszel common OR: **~3.64**;
- 95% CI: **~1.95–6.79**;
- null-test `p≈1.18×10⁻⁵`;
- BH-adjusted `q≈0.00137` after testing the represented official subclasses.

The Breslow-Day equal-odds test gives `p≈0.032`, indicating detectable between-sample heterogeneity. That heterogeneity is scientifically important: the signal is enriched but not uniform across dissections/replicates.

### 5.2 A stronger but less replicated enrichment

`DMH-LHA Vgll2 Glut` contains 4/382 target-positive nuclei, approximately **5.67×** pooled enrichment, and appears in **3/8** samples. Its sample-stratified common OR is ~5.70, but the smaller count and lower replicate coverage make it a secondary priority rather than the primary cell-state claim.

### 5.3 Glial abundance does not explain the target signal

Large glial subclasses remain depleted relative to the pooled target rate:

- `Astro-NT`: 12/13,546, ~0.48×;
- `Oligo`: 8/12,699, ~0.34×.

The observed target counts therefore do not simply track the most abundant populations.

### Statistical boundary

The subclass analysis is a prioritization layer, not proof of a causal cell of action. Rare counts, anatomical sampling and between-sample heterogeneity remain material limitations. Extreme enrichments seen in only one sample are not promoted merely because a p-value is small; replication coverage is part of the priority rule.

---

## 6. Independent same-nucleus Multiome support

GSE226277 was generated for a recurrent-hypoglycaemia study rather than obesity genetics, but it provides paired hypothalamic RNA and ATAC measurements.

Across four verified male wild-type hypothalamus RNA/ATAC pairs:

- 2/4 pairs contain a filtered nucleus with an ATAC fragment overlapping the rs1421085 target tile and detectable `Irx3` RNA;
- the total number of such nuclei is **two**.

Both rare `locus+ / Irx3+` nuclei also have detectable transcripts for `Arid5b`, `Cux1`, `Tet1` and `Kdm2b`; one has detectable `Mecp2`.

This does **not** rank those factors as mediators. RNA presence is availability, not occupancy. The useful result is orthogonal and narrower: the target interval can be accessible in the same adult hypothalamic nucleus in which `Irx3` is transcribed.

---

## 7. What the data change

The open mechanism space initially included several coarse alternatives:

1. the exact site is effectively closed in adulthood and the effect is entirely developmentally imprinted;
2. the site is broadly active and simply reuses the adipocyte ARID5B mechanism;
3. the exact site is available only in a rare adult cell state with context-specific molecular grammar;
4. the variant acts through a state-dependent long-range contact or chromatin configuration.

The present data weaken the simplest versions of models 1 and 2. Raw accessibility exists in adulthood, but it is rare and structured rather than ubiquitous.

The surviving high-information search space is closer to:

```text
exact rs1421085 sequence
        ×
adult hypothalamic neuronal state
        ×
metabolic / sex / developmental context
        ×
local chromatin and TF occupancy
        ×
3D Fto-Irx contact state
        ↓
Irx3 regulatory output
```

This still does not identify `M`. It makes `M` more local and testable.

---

## 8. The next decisive computational boundary

The strongest newly discovered prior art points directly to the next analysis: adult hypothalamic H3K27ac-associated PLAC-seq already demonstrates functional 3D architecture around neighboring Fto-Irx cis-elements.

The next question is therefore **exact-site**, not TAD-wide:

> Does the exact rs1421085 ortholog-containing interval itself participate in a detectable adult hypothalamic contact with the `Irx3` promoter, and is that contact cell-state or metabolic-state specific?

A positive wild-type contact would strengthen the 3D-contact hypothesis but would still not demonstrate allele dependence. A negative result would also be informative, subject to PLAC-seq resolution and power.

In parallel, exact-site ARID5B/CUX1 occupancy and allele-dependent accessibility remain load-bearing discriminators.

---

## 9. Claims explicitly not made

This article does **not** claim that:

- T>C causes the observed wild-type accessibility state;
- the 500-bp tile is itself a proven enhancer;
- hibE1 is the rs1421085 element;
- accessibility at the target tile causes `Irx3` expression;
- ARID5B, CUX1 or another candidate occupies the exact adult hypothalamic site;
- the two Multiome co-detections establish enhancer-to-`Irx3` regulation;
- a specific subclass is the causal cell of action;
- the male-specific genotype effect has been explained;
- `GAP-001` is solved.

Machine status remains:

```text
GAP-001 = OPEN
cause_found = false
```

---

## 10. Conclusion

The broad adult hypothalamic Fto-Irx regulatory landscape is no longer an open question: 2025 work established functional cis-elements, long-range contacts and metabolic-state-dependent regulation in this TAD.

The exact rs1421085 site remains different.

A sequence-anchored, assembly-cross-checked reanalysis places the ortholog inside `Fto` but 13.859 kb away from hibE1. Across eight adult male hypothalamus snATAC samples, the exact-site-containing tile shows rare accessibility with reproducible neuronal subclass structure. The `LHA-AHN-PVH Otp Trh Glut` signal persists across six samples and survives a replicate-stratified, multiple-testing-corrected analysis. Independent Multiome data add sparse same-nucleus evidence that target-interval accessibility can coexist with `Irx3` transcription.

That is sufficient for a **narrow Level-1 computational discovery candidate**, not for a molecular mechanism.

The next load-bearing question is now sharply defined:

```text
At the exact rs1421085 site,
what adult hypothalamic molecular state
links sequence to Irx3 —
and does T>C change it?
```

Until that edge is measured, the causal graph remains open by design.
