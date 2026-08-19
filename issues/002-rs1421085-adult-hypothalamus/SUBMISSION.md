# External submission plan

## Current recommendation

### 1. bioRxiv — **appropriate once the manuscript bundle is finalized**

Recommended category: **Genomics** or **Neuroscience**.  
Article category: **New Results**.

Why: the manuscript reports a new open-data result in life science and explicitly separates computational evidence from causal validation. A preprint is the right first public timestamp and creates a venue for community feedback while the mechanism remains under investigation.

Before upload:

- incorporate the recovered eighth GSE246791 hypothalamus sample if technically available;
- add a compact figure set;
- freeze CAUSAL-DNA commit/workflow provenance;
- add author names, affiliations, ORCID and contribution statement;
- run one final primary-literature novelty search.

## Journal strategy by evidence level

### Current Level 1

**Cell Genomics — plausible editorial target after replicate completion and figures.**

Rationale: its stated scope spans research, resources, methods and technology for characterizing, interpreting and functionally interrogating genomes. The manuscript is an integrative single-cell reanalysis of a disease-associated non-coding locus.

Risk: current evidence is sparse and observational. Editorial interest will depend on whether the exact-locus cell-state result is considered sufficiently general and biologically important.

### PLOS Genetics — **not the first target at the current evidence level**

The topic fits PLOS Genetics sections covering human genetic variation/disease, epigenetics, gene regulation, single-cell genomics and integrative omics. However, its current journal information explicitly lists descriptive genomic/epigenomic studies without follow-up experimental investigation among common reasons for rejection without external review.

Recommendation: submit here after adding at least one stronger load-bearing layer: exact-allele accessibility, direct occupancy, locus-to-Irx3 contact, or another genuinely independent replication.

### Genome Biology / similar high-selectivity genomics journals

Treat as a Level-2 target rather than a present recommendation. The result would need a broader or more mechanistic contribution than a single-locus descriptive discovery.

### Nature Genetics

Not appropriate for the present Level-1 claim. Reconsider only if the project reaches a broad, experimentally supported mechanism with exact-allele and mediator evidence.

## External-submission abstract

**Background:** The obesity-associated non-coding variant `rs1421085` has a defined adipocyte-progenitor mechanism and an exact homologous T>C mouse model increases `Irx3` in adult male posterior hypothalamus, yet the intervening adult neural regulatory state is unresolved.

**Results:** We mapped the exact mouse ortholog to `mm10 chr8:91,374,372` and reanalysed two independent public adult-mouse hypothalamus datasets. In the 2.3-million-nucleus GSE246791 snATAC atlas, the 500-bp interval containing the ortholog was absent from the thresholded union cCRE catalogue but exhibited rare raw accessibility. Exact barcode joins to official cell annotations identified a non-uniform hypothalamic subclass distribution. Among seven currently provenance-complete samples, `LHA-AHN-PVH Otp Trh Glut` showed target signal in five samples (9/1,800 nuclei; ~2.74-fold pooled enrichment), whereas abundant astrocyte and oligodendrocyte subclasses were depleted. In the independent GSE226277 paired hypothalamus Multiome dataset, two of four biological pairs contained a filtered nucleus in which an ATAC fragment overlapping the target interval co-occurred with detectable `Irx3` RNA.

**Conclusions:** Adult hypothalamic accessibility at the rs1421085 ortholog is detectable but rare, is not captured by a simple strong-cCRE model, and has a neuronal cell-state structure. The result identifies a restricted adult context in which allele-specific chromatin, TF occupancy and enhancer-to-`Irx3` coupling can now be tested. It does not establish allele-specific accessibility or causal mediation.

## Cover-letter draft — adaptable for Cell Genomics / genetics journals

Dear Editors,

We submit the manuscript **“Open-data evidence for a rare adult hypothalamic chromatin state at the rs1421085 ortholog.”**

The obesity-associated FTO locus is among the best-studied non-coding disease loci, yet a key mechanistic gap remains. The exact `rs1421085 T>C` substitution has a well-supported adipocyte mechanism and an exact-edit mouse model recently connected the variant to increased adult posterior-hypothalamic `Irx3` and an IRX3-positive neuronal circuit. The native adult neural regulatory state between the exact variant and `Irx3`, however, has not been resolved.

Using provenance-preserving reanalysis of two independent public single-nucleus datasets, we identify rare adult hypothalamic chromatin accessibility at the exact mouse-ortholog interval, resolve its distribution with the authors' official cell-subclass annotations, and obtain orthogonal same-nucleus ATAC/RNA evidence that accessibility at the interval can coexist with `Irx3` transcription. The central result is deliberately presented as a computational cell-state discovery rather than a causal enhancer claim.

We believe the work is useful because it converts a broad unresolved mechanism into a specific, falsifiable adult neuronal context for exact-allele accessibility, TF occupancy and chromatin-contact experiments. All analysis code, provenance rules, negative results and workflow outputs are openly reproducible through the CAUSAL-DNA repository.

We would be grateful for your consideration.

Sincerely,

[Authors / affiliations / corresponding author to be completed before external submission]

## Required package before actual external submission

- manuscript converted to journal/preprint format;
- figures and legends;
- author/affiliation/ORCID information;
- author contributions;
- conflict-of-interest and funding statements;
- data/code availability statement;
- exact CAUSAL-DNA release/tag or archival DOI;
- final novelty audit;
- eighth-sample status and replicate-aware enrichment table.
