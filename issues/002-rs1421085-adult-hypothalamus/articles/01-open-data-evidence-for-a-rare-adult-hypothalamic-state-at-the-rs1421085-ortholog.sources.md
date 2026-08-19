# Sources and provenance — RESONANCE Issue 002 / Article 01

## Primary literature

1. **Claussnitzer M et al. (2015). FTO Obesity Variant Circuitry and Adipocyte Browning in Humans.** New England Journal of Medicine. PMID: 26287746. DOI: 10.1056/NEJMoa1502214.  
   Role: exact `rs1421085 T>C` adipocyte-progenitor ARID5B mechanism; endogenous editing/rescue positive control.

2. **Smemo S et al. (2014). Obesity-associated variants within FTO form long-range functional connections with IRX3.** Nature. PMID: 24646999. DOI: 10.1038/nature13138.  
   Role: long-range FTO obesity interval -> IRX3 regulatory relationship, including adult mouse-brain interaction evidence.

3. **Sobreira DR et al. (2021). Extensive pleiotropism and allelic heterogeneity mediate metabolic effects of IRX3 and IRX5.** Science. PMID: 34083488. DOI: 10.1126/science.abh2683.  
   Role: multiple FTO-region enhancers, brain/adipose effects and temporal restriction; developmental hypothalamic context.

4. **Laber S et al. (2021).** PMID: 34290091. PMCID: PMC8294759.  
   Role: deletion spanning the rs1421085 regulatory element; negative/tension evidence for bulk hypothalamic Irx3/Irx5 expression.

5. **Sullivan et al. (2025). Mice harboring the obesity-associated SNP rs1421085 exhibit increased body weight and reveal an IRX3 neuronal circuit regulating body weight.** Molecular Metabolism. PMID: 40835181. DOI: 10.1016/j.molmet.2025.102234. PMCID: PMC12419104.  
   Role: exact homologous T>C mouse edit, adult posterior-hypothalamic Irx3 increase, sex dependence, IRX3-positive neuronal circuit and phenotype.

6. **Zu S et al. (2023). Single-cell analysis of chromatin accessibility in the adult mouse brain.** Nature 624:378–389. PMID: 38092917. DOI: 10.1038/s41586-023-06824-9.  
   Role: source publication for GSE246791, 2.3-million-nucleus adult mouse brain snATAC atlas and official cell annotations.

7. **Disrupted hypothalamic transcriptomics and proteomics in a mouse model of type 2 diabetes exposed to recurrent hypoglycaemia (2023/2024).** PMID: 38017352. DOI: 10.1007/s00125-023-06043-x.  
   Role: source study/data context for GSE226277. The present reanalysis uses the paired hypothalamus Multiome files only as a wild-type same-nucleus feasibility resource.

## Public datasets

### GSE246791

- organism: mouse
- assay: snATAC-seq
- adult whole brain
- processed sample H5AD files retain raw fragments and 500-bp tile matrices
- official Supplementary Table 2 provides `Sample + Barcode -> L4/Subclass`
- exact CAUSAL-DNA target: `mm10 chr8:91,374,000-91,374,500`
- exact ortholog base within tile: `chr8:91,374,372` 1-based / `91,374,371` 0-based

Seven provenance-complete samples currently used in the article:

- GSM7877104 — CEMBA200312_6H
- GSM7877105 — CEMBA200319_6H
- GSM7877102 — CEMBA200305_7J
- GSM7877103 — CEMBA200520_7J
- GSM7877106 — CEMBA200312_8K
- GSM7877107 — CEMBA200319_8K
- GSM7876880 — CEMBA200305_9L

Pending recovery:

- GSM7876882 — 9L,rep2. The accession is official; the workflow is being repaired to resolve the exact supplementary filename from the official GSM SOFT record instead of guessing it.

### GSE226277

Four verified paired hypothalamus Multiome combinations:

- RH1: GSM7070456 RNA + GSM7070464 ATAC
- AH1: GSM7070457 RNA + GSM7070465 ATAC
- RH2: GSM7070458 RNA + GSM7070466 ATAC
- AH2: GSM7070459 RNA + GSM7070467 ATAC

All are male WT hypothalamus in the source study. They do not provide an rs1421085 genotype contrast.

## CAUSAL-DNA reproducibility anchors

Repository: `safal207/CAUSAL-DNA`  
Branch: `agent/causal-dna-001-bootstrap`  
Draft PR: #1 — open/unmerged.

Key discovery passes:

- exact mouse ortholog coordinate gate
- GSE246791 raw locus accessibility scan
- official barcode -> subclass annotation join
- Nature 2026 motif-codebook scan and strict human/mouse motif-placement gate
- GSE146692 adult VPH Irx3/candidate transcript feasibility screen
- GSE226277 paired Multiome manifest
- GSE226277 same-nucleus target-locus/RNA scan
- discovery pass 07: adult hypothalamic exact-locus convergence + publication-gate decision

Verified same-nucleus workflow:

- GSE226277 run `32237141430`
- four pair jobs: SUCCESS
- aggregate: SUCCESS
- `locus+ / Irx3+` pairs: 2/4
- total `locus+ / Irx3+` nuclei: 2

## Claim boundary

These sources support a Level-1 computational observation only. They do not support:

- allele-specific adult-hypothalamic accessibility;
- direct TF occupancy;
- a proven enhancer-to-Irx3 edge;
- a causal mediator;
- a molecular explanation for the male-specific genotype effect.
