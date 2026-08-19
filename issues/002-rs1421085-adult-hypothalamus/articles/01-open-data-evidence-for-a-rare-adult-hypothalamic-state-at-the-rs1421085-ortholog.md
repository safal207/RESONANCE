# Open-data evidence for a rare adult hypothalamic chromatin state at the rs1421085 ortholog

**RESONANCE — Issue 002**  
**Article type:** computational discovery / open-data reanalysis  
**Status:** Level-1 discovery candidate; causal mechanism unresolved

## Abstract

The obesity-associated non-coding variant `rs1421085` lies within the first intron of `FTO` and has been linked experimentally to long-range regulation of `IRX3` and `IRX5`. In adipocyte progenitors, the risk allele disrupts an ARID5B repressor motif and alters thermogenic programming. More recently, the exact homologous T>C substitution was introduced into mice and shown to increase `Irx3` expression in the adult male posterior hypothalamus; increased IRX3 in posterior-hypothalamic neurons was sufficient to alter feeding and body weight. The molecular regulatory state connecting the exact substitution to adult hypothalamic `Irx3`, however, remains unresolved.

We used an evidence-first open-data workflow to interrogate the exact mouse ortholog (`mm10 chr8:91,374,372`, T>C) in two independent adult-mouse hypothalamus datasets. In the 2.3-million-nucleus GSE246791 single-nucleus ATAC atlas, the 500-bp interval containing the ortholog was absent from the thresholded union candidate-enhancer catalogue yet showed rare raw accessibility in hypothalamic dissections. Exact barcode-to-subclass joins against the authors' official metadata mapped 133 target-tile-positive nuclei across seven provenance-complete samples. The signal was not uniform across cell classes: several hypothalamic neuronal subclasses were enriched relative to the overall target-tile rate, while abundant astrocyte and oligodendrocyte subclasses were depleted. The most reproducible enriched signal among the current seven samples was `LHA-AHN-PVH Otp Trh Glut` (9/1,800 nuclei; approximately 2.74-fold pooled enrichment; target signal in 5/7 samples).

We then queried an independent paired hypothalamus Multiome dataset, GSE226277. In 2/4 biological pairs, an ATAC fragment overlapping the same 500-bp interval occurred in a filtered nucleus with detectable `Irx3` RNA. Only two such nuclei were observed, making the result sparse, but the paired measurement provides orthogonal evidence that accessibility at the target interval and `Irx3` transcription can coexist in the same adult hypothalamic nucleus.

These observations do not establish allele-specific accessibility, enhancer activity, TF occupancy, enhancer-to-`Irx3` contact or causal mediation. They instead identify a previously unresolved adult hypothalamic cell-state surface on which the `rs1421085 -> Irx3` mechanism can be tested directly.

---

## 1. The missing adult regulatory edge

The FTO obesity-risk locus is unusual because several pieces of its causal story are already experimentally strong while one central edge remains open.

Long-range interaction studies established that obesity-associated sequences in the first intron of `FTO` belong to a regulatory landscape that can contact `IRX3`. Claussnitzer and colleagues subsequently identified a concrete mechanism in human adipocyte progenitors: `rs1421085 T>C` disrupts an ARID5B repressor motif, increases enhancer activity, derepresses `IRX3/IRX5`, suppresses thermogenesis and promotes lipid storage. That branch includes endogenous editing and rescue and therefore provides a valuable positive-control mechanism.

But tissue context is part of a causal claim. A mechanism established in adipocyte progenitors cannot simply be copied into adult posterior-hypothalamic neurons.

This became especially important after the 2025 exact-edit mouse study. Mice carrying the homologous T>C substitution recapitulated obesity-related phenotypes under obesogenic conditions. `Irx3` increased in the brain, with a notable allele-dose effect in male posterior hypothalamus. Raising IRX3 in posterior-hypothalamic IRX3-positive neurons increased feeding and body weight, while the neuronal physiology experiments linked IRX3 abundance to reduced excitability and activity.

Those results sharpen the unresolved edge to:

```text
rs1421085 T>C
      ↓
 adult posterior-hypothalamic regulatory state ?
      ↓
    Irx3 ↑
      ↓
IRX3+ neuronal activity ↓
      ↓
food intake / body weight ↑
```

The present analysis asks a deliberately narrower question: **what can existing adult single-cell chromatin data tell us about the state of the exact locus before we claim a mediator?**

---

## 2. A provenance-first coordinate gate

A common failure mode in non-coding-variant analysis is to move from a human SNP to an approximate mouse region and then treat any nearby signal as evidence at the variant.

We therefore made coordinate identity an explicit gate.

Using the exact sequence context of the published mouse edit, the homologous position was resolved as:

- genome: `mm10`
- chromosome: `chr8`
- 1-based coordinate: `91,374,372`
- reference/alternate: `T>C`
- zero-based coordinate: `91,374,371`

The single-nucleus ATAC atlas stores a 500-bp tile matrix. The tile containing the exact ortholog is:

```text
chr8:91,374,000–91,374,500
```

This distinction matters. An early independent cross-check using a broader published FTO-region fosmid mapped more than 13 kb away. Rather than silently accepting the broad interval, the workflow rejected it as an exact-coordinate source and used the published edit sequence as authority.

---

## 3. The locus is neither simply closed nor a strong constitutive peak

GSE246791 is a comprehensive adult-mouse brain single-nucleus ATAC atlas containing approximately 2.3 million nuclei from 117 anatomical dissections and 1,482 cell populations.

At first glance, the target interval appears unremarkable: it is absent from the atlas-wide thresholded union candidate-enhancer/cCRE catalogue. If analysis stopped at the peak catalogue, the natural interpretation would be that the region is inaccessible in the adult brain.

Raw matrices gave a different answer.

The processed H5AD files retain both a 500-bp binary/count matrix and raw insertion information. Querying the exact target tile showed low-frequency accessibility in adult hypothalamic dissections. In an initial 6H sample, for example, the target tile was non-zero in 17 of 10,615 nuclei, and raw Tn5 insertions occurred within ±250 bp of the ortholog, including positions within tens of bases of the exact SNP.

This created a third state between the two naive alternatives:

```text
not a strong catalogue cCRE
        AND
not uniformly inaccessible
        ↓
rare / subthreshold adult accessibility
```

That state is biologically interesting precisely because it can be lost by peak-thresholding.

---

## 4. Official cell annotations reveal neuronal structure

A rare accessibility signal is not useful unless we know which cells carry it.

Rather than re-annotating sparse nuclei from markers, we joined the exact target-tile barcodes to the authors' official Supplementary Table 2, which contains `Sample`, `Barcode`, hierarchical cluster labels and `Subclass` for the 2.3 million snATAC nuclei.

Seven hypothalamic samples currently have complete target-barcode provenance in the analysis:

- two 6H samples;
- two 7J samples;
- two 8K samples;
- one 9L sample.

The second 9L replicate is a technical recovery item: the GEO accession is known, but an earlier workflow guessed the processed filename and failed. A repair workflow now resolves the filename directly from the official GEO sample record. The results below therefore remain explicitly seven-sample results until that recovery is incorporated.

Across the seven samples:

- 73,007 nuclei were present in the official metadata;
- 133 nuclei were positive in the exact 500-bp target tile;
- all 133/133 target barcodes matched an official subclass annotation;
- the overall target-tile-positive rate was about 0.182%.

### 4.1 Pooled subclass enrichment

For descriptive prioritization, we calculated:


a subclass target rate divided by the overall seven-sample target rate.

Several neuronal subclasses had higher rates than the pooled background. Examples include:

| Subclass | Target / total | Pooled enrichment | Samples with target signal |
|---|---:|---:|---:|
| DMH-LHA Vgll2 Glut | 4 / 322 | 6.82x | 3/7 |
| BST-MPN Six3 Nrgn Gaba | 8 / 1,192 | 3.68x | 3/7 |
| **LHA-AHN-PVH Otp Trh Glut** | **9 / 1,800** | **2.74x** | **5/7** |
| TU-ARH Otp Six6 Gaba | 7 / 1,603 | 2.40x | 4/7 |
| AHN-RCH-LHA Otp Fezf1 Glut | 6 / 1,515 | 2.17x | 4/7 |
| PVpo-VMPO-MPN Hmx2 Gaba | 8 / 2,831 | 1.55x | 6/7 |

The largest enrichment estimate belongs to `DMH-LHA Vgll2 Glut`, but it is based on only four target nuclei and is therefore fragile. We regard `LHA-AHN-PVH Otp Trh Glut` as the more defensible current prioritization signal because target accessibility occurs in five of seven available samples and the pooled estimate remains above background.

By contrast, the large glial subclasses were depleted relative to the overall target rate:

- `Astro-NT`: 9/11,640, ~0.42x;
- `Oligo`: 7/11,060, ~0.35x.

Thus the raw target counts cannot be explained simply by abundant glial populations. The locus-containing tile has a measurable hypothalamic neuronal structure.

These enrichments are descriptive, not a substitute for replicate-aware inferential statistics. The individual biological samples remain the unit of replication.

---

## 5. An independent Multiome dataset supplies orthogonal support

A second dataset was used to ask a different question.

GSE226277 contains paired RNA/ATAC Multiome measurements from male WT mouse hypothalamus collected in a recurrent-hypoglycaemia study. It is not an obesity-variant experiment and contains no `rs1421085` genotype contrast. Its value here is orthogonal: RNA and ATAC are measured from paired nuclei.

Official GEO metadata identified four hypothalamus RNA/ATAC pairs: two acute-hypoglycaemia and two recurrent-hypoglycaemia replicates.

The ATAC fragment files are approximately 1–2 GB each and do not provide `.tbi` indexes. To avoid converting a targeted question into a multi-gigabyte download, the analysis streams each chromosome-sorted fragment file only until it passes the exact chr8 interval, preserving all overlapping barcodes. Those barcodes are then intersected with the paired filtered RNA matrix.

### 5.1 Same-nucleus result

Two of four biological pairs contained a filtered nucleus with both:

1. an ATAC fragment overlapping `chr8:91,374,000–91,374,500`; and
2. detectable `Irx3` RNA.

The total number of such nuclei was only **two**.

That sparsity prevents a strong quantitative claim. But it provides something the first atlas cannot: direct paired evidence that an accessible fragment at the target interval and `Irx3` transcription can coexist in the same adult hypothalamic nucleus.

The two `locus+ / Irx3+` nuclei both also contained transcripts for `Arid5b`, `Cux1`, `Tet1` and `Kdm2b`; one contained `Mecp2`; neither contained detected `Dnmt1` or `Cxxc1`. With n=2, these observations must not be used as a mediator ranking.

---

## 6. Why this changes the search for the mediator

Before this analysis, several broad adult-PH models remained compatible with the published literature:

1. the site is effectively closed in adult hypothalamus and the T>C phenotype is developmentally imprinted;
2. the site is broadly active and reuses the adipocyte ARID5B mechanism;
3. a rare adult cell state exposes the locus to a different regulatory grammar;
4. an allele-dependent chromatin state or long-range contact exists only in a specific neuronal context.

The new data weaken the simplest version of model 1: raw accessibility is detectable in adult hypothalamus and has reproducible neuronal structure. They also weaken the simplest version of model 2: the site is not a strong ubiquitous adult-brain cCRE.

The surviving high-information model is therefore closer to:

```text
exact sequence
    ×
rare adult hypothalamic cell state
    ×
chromatin / methylation state
    ×
TF availability or occupancy
    ↓
Irx3 regulatory output
```

This does not identify the missing mediator `M`; it shrinks the space in which `M` must operate.

---

## 7. Candidate TFs remain hypotheses, not conclusions

A separate scan using the 2026 human transcription-factor motif codebook evaluated allele-sensitive motif grammar at the exact T>C position and then tested strict portability to the mouse sequence context.

Several candidates remain compatible with both sequence and adult `Irx3+` transcript availability, including the established ARID5B positive-control hypothesis and alternatives involving CUX1 and epigenetic regulators. However, motif scores report sequence compatibility, not occupancy, and transcript presence reports availability, not binding.

The present article therefore deliberately does not name a causal TF.

The decisive next measurements are:

- exact-allele accessibility in the prioritized adult hypothalamic neuronal subclasses;
- ARID5B/CUX1/epigenetic-factor occupancy at the exact site;
- methylation or histone state at the locus;
- cell-state-specific contact between the FTO interval and `Irx3`;
- mediator perturbation/rescue in the relevant adult PH context.

---

## 8. Novelty boundary

The relevant primary literature already establishes several adjacent facts:

- FTO obesity-associated sequences can interact with and regulate `IRX3`;
- `rs1421085 T>C` has a causal adipocyte-progenitor mechanism through ARID5B;
- the broader FTO interval has developmental and tissue-dependent effects on `IRX3/IRX5`;
- an exact T>C mouse model shows increased adult male posterior-hypothalamic `Irx3` and an IRX3-positive neuronal circuit affecting feeding/body weight;
- adult mouse-brain single-cell chromatin atlases exist.

A targeted search of the indexed primary literature did not identify a paper reporting the specific combination reconstructed here: **adult exact-ortholog raw accessibility resolved to hypothalamic subclasses together with independent same-nucleus target-interval ATAC / `Irx3` RNA co-detection.**

This is a bounded novelty statement. It should be rechecked during formal manuscript preparation and peer review.

---

## 9. Limitations

The most important limitation is also the central scientific boundary: both public datasets used here are wild-type with respect to the engineered T>C comparison.

Therefore this study cannot infer that the risk allele creates or increases the accessibility state.

Additional limitations include:

- the primary snATAC signal is a 500-bp tile containing the exact ortholog, not single-base accessibility;
- target-positive nuclei are rare;
- one of the eight intended GSE246791 hypothalamus samples is awaiting provenance-safe processed-file recovery;
- pooled subclass enrichment is descriptive and should be supplemented by replicate-aware inference;
- the independent Multiome support consists of only two `locus+ / Irx3+` nuclei across four pairs;
- GSE226277 was generated for a hypoglycaemia study, not obesity genetics;
- same-nucleus co-detection does not imply a regulatory edge between the locus and `Irx3`;
- motif compatibility, transcript expression and chromatin accessibility do not establish TF occupancy.

These limitations set the ceiling of the present claim at a **computational discovery candidate**, not a molecular mechanism.

---

## 10. Conclusion

The adult posterior-hypothalamic mechanism of `rs1421085` remains open, but the missing state is now less abstract.

Public single-cell chromatin data show that the exact ortholog-containing interval is not simply closed in the adult hypothalamus. Its accessibility is rare, subthreshold to standard catalogue calling, and structured across hypothalamic neuronal subclasses. An independent paired Multiome dataset provides sparse but direct same-nucleus evidence that accessibility at the same interval can coexist with `Irx3` transcription.

The result points away from a binary “enhancer open versus enhancer closed” model and toward a context-dependent adult regulatory state.

The next discovery target is no longer merely:

```text
What binds rs1421085?
```

It is:

```text
In which adult posterior-hypothalamic neuronal state
is the rs1421085 ortholog accessible,
what molecular grammar occupies it,
and does T>C change that state in a way that raises Irx3?
```

That is the load-bearing experiment separating the present computational discovery from a causal molecular mechanism.
