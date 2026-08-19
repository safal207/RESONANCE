# Sources and provenance — RESONANCE Issue 002 / Article 01

## Primary literature

1. **Claussnitzer M et al. (2015). FTO Obesity Variant Circuitry and Adipocyte Browning in Humans.** New England Journal of Medicine. PMID: 26287746. DOI: 10.1056/NEJMoa1502214.  
   Role: exact `rs1421085 T>C` adipocyte-progenitor ARID5B mechanism; endogenous editing/rescue positive control.

2. **Smemo S et al. (2014). Obesity-associated variants within FTO form long-range functional connections with IRX3.** Nature. PMID: 24646999. DOI: 10.1038/nature13138.  
   Role: long-range FTO obesity interval -> IRX3 relationship, including adult mouse-brain interaction evidence.

3. **Sobreira DR et al. (2021). Extensive pleiotropism and allelic heterogeneity mediate metabolic effects of IRX3 and IRX5.** Science. PMID: 34083488. DOI: 10.1126/science.abh2683.  
   Role: FTO-region enhancer complexity and developmental/tissue context.

4. **Laber S et al. (2021).** PMID: 34290091. PMCID: PMC8294759.  
   Role: published mouse rs1421085 regulatory-element sequence/guide used for exact ortholog coordinate anchoring; broader deletion supplies negative/tension evidence for bulk hypothalamic Irx3/Irx5 effects.

5. **Zhang et al. (2023). The rs1421085 variant within FTO promotes brown fat thermogenesis.** Nature Metabolism. PMID: 37460841. DOI: 10.1038/s42255-023-00847-2.  
   Role: exact homologous mouse T>C in another tissue context; demonstrates that rs1421085 target/mechanism can be context-dependent rather than universally ARID5B→IRX3/5.

6. **Sullivan et al. (2025). Mice harboring the obesity-associated SNP rs1421085 exhibit increased body weight and reveal an IRX3 neuronal circuit regulating body weight.** Molecular Metabolism. PMID: 40835181. DOI: 10.1016/j.molmet.2025.102234. PMCID: PMC12419104.  
   Role: exact homologous T>C mouse edit; adult posterior-hypothalamic Irx3 increase; sex dependence; IRX3-positive neuronal circuit and phenotype.

7. **Zu S et al. (2023). Single-cell analysis of chromatin accessibility in the adult mouse brain.** Nature 624:378–389. PMID: 38092917. DOI: 10.1038/s41586-023-06824-9.  
   Role: GSE246791 2.3-million-nucleus adult mouse brain snATAC atlas and official sample/barcode/subclass annotations.

8. **Steinwand S et al. (2025). Conserved noncoding cis elements associated with hibernation modulate metabolic and behavioral adaptations in mice.** Science 389:501–507. PMID: 40743330. PMCID: PMC12403242. DOI: 10.1126/science.adp4701.  
   Role: critical prior art. Establishes adult hypothalamic Fto-Irx cis-elements (`hibE1-5`), cell-state accessibility, H3K27ac-associated regulatory contacts and causal knockout effects on Fto/Irx3/Irx5/metabolic phenotypes. This paper prevents any broad novelty claim for adult hypothalamic Fto-Irx regulatory architecture.

9. **Ferris E et al. (2025). Genomic convergence in hibernating mammals elucidates the genetics of metabolic regulation in the hypothalamus.** Science 389:494–500. PMID: 40743333. PMCID: PMC12434793. DOI: 10.1126/science.adp4025.  
   Role: companion adult hypothalamic fed/fasted/refed chromatin and regulatory-program prior art.

10. **Disrupted hypothalamic transcriptomics and proteomics in a mouse model of type 2 diabetes exposed to recurrent hypoglycaemia.** PMID: 38017352. DOI: 10.1007/s00125-023-06043-x.  
   Role: source context for GSE226277. The present analysis uses paired hypothalamus Multiome data only as a wild-type same-nucleus feasibility resource.

## Coordinate references

### Exact ortholog

CAUSAL-DNA resolves the published mouse edit sequence uniquely on mm10:

- mm10/GRCm38: `chr8:91,374,371–91,374,372` (0-based half-open)
- 1-based exact base: `chr8:91,374,372`
- allele on assembly strand: `T>C`

Independent UCSC `mm10ToMm39` liftOver gives:

- mm39/GRCm39: `chr8:92,100,999–92,101,000` (0-based half-open)
- 1-based exact base: `chr8:92,101,000`
- lifted 500-bp tile: `chr8:92,100,628–92,101,128`

NCBI Gene 26383 places current GRCm39 `Fto` at `chr8:92,039,995–92,395,061`; the lifted exact site lies inside this interval.

### hibE1 is a neighboring element, not the exact SNP site

MGI:8245447 (`Rr695574`, `Fto-Irx::hibE1`) is annotated at GRCm39 `chr8:92,114,859–92,119,641` and regulates `Fto`, `Irx3`, and `Irx5`.

CAUSAL-DNA assembly cross-check:

- exact site overlaps hibE1: **false**
- target 500-bp tile overlaps hibE1: **false**
- exact-site distance to hibE1: **13,859 bp**
- target-tile distance to hibE1: **13,731 bp**

Verified workflow run: `32242283795` — SUCCESS.

## GSE246791 all-eight evidence

Frozen evidence pack:

`CAUSAL-DNA/discovery/CDNA-001-GSE246791-target-barcodes-all8.json`

Samples:

- GSM7877104 — CEMBA200312_6H
- GSM7877105 — CEMBA200319_6H
- GSM7877102 — CEMBA200305_7J
- GSM7877103 — CEMBA200520_7J
- GSM7877106 — CEMBA200312_8K
- GSM7877107 — CEMBA200319_8K
- GSM7876880 — CEMBA200305_9L
- GSM7876882 — CEMBA200520_9L

The eighth sample was recovered by resolving the processed H5AD filename from the official GSM7876882 GEO SOFT record rather than guessing it. Repair run `32238756696`: SUCCESS.

All-eight totals:

- samples: **8**
- nuclei: **83,321**
- target-tile-positive nuclei: **154**
- all 154 target barcodes join to official Supplementary Table 2 metadata

Priority subclass after all-eight join:

- `LHA-AHN-PVH Otp Trh Glut`: 11/1,842
- signal in 6/8 samples
- pooled enrichment ~3.23×
- sample-stratified Mantel-Haenszel OR ~3.64
- 95% CI ~1.95–6.79
- BH q ~0.00137 across represented official subclasses
- Breslow-Day equal-odds p ~0.032, so between-sample heterogeneity is preserved rather than hidden

Secondary high-enrichment subclass:

- `DMH-LHA Vgll2 Glut`: 4/382, ~5.67×, 3/8 samples

Large glial subclasses remain depleted:

- Astro-NT: 12/13,546, ~0.48×
- Oligo: 8/12,699, ~0.34×

## GSE226277 paired Multiome

Four verified paired hypothalamus RNA/ATAC combinations:

- RH1: GSM7070456 RNA + GSM7070464 ATAC
- AH1: GSM7070457 RNA + GSM7070465 ATAC
- RH2: GSM7070458 RNA + GSM7070466 ATAC
- AH2: GSM7070459 RNA + GSM7070467 ATAC

Same-nucleus exact-target result:

- verified run `32237141430`
- four pair jobs: SUCCESS
- positive pairs: 2/4
- total `target-locus+ / Irx3+` nuclei: 2

These are wild-type data and do not provide an rs1421085 allele contrast.

## Claim boundary

The current package supports a **narrow Level-1 computational discovery candidate** only:

> exact rs1421085-ortholog target-tile accessibility in adult hypothalamus has reproducible official neuronal-subclass structure, with sparse orthogonal same-nucleus target-interval ATAC / Irx3 RNA support.

It does not establish:

- allele-specific adult-hypothalamic accessibility;
- direct ARID5B/CUX1/other TF occupancy;
- target-interval -> Irx3 3D contact;
- enhancer activity of the exact 500-bp tile;
- a causal mediator;
- the causal cell of action;
- a molecular explanation for the male-specific genotype effect.

`GAP-001 = OPEN`  
`cause_found = false`
