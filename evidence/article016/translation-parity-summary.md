# RESONANCE Translation Parity Contract

**Verdict:** PASS

| Managed group | Profile | Outline tokens EN/RU/ZH | CTA links EN/RU/ZH | Source links EN/RU/ZH | Verdict |
|---|---|---:|---:|---:|---|
| article016 | article-semantic | 12/12/12 | 3/3/3 | 8/8/8 | PASS |
| article015 | article-semantic | 10/10/10 | 1/1/1 | 2/2/2 | PASS |
| homepage | locale-shell | shell | n/a | n/a | PASS |
| article004 | article-semantic | 21/21/21 | 2/2/2 | 5/5/5 | PASS |
| article005 | article-semantic | 23/23/23 | 2/2/2 | 4/4/4 | PASS |

## Release invariants

- EN / RU / zh-CN managed siblings must all exist and declare the correct `html lang`.
- Canonical and reciprocal `hreflang` mappings must point to the same managed triplet.
- The visible language switcher must contain EN / RU / zh-CN and mark only the current locale with `aria-current="page"`.
- Article siblings must preserve the same shell controls/rail count and the same major semantic outline: heading levels plus evidence, trajectory, market-question, distribution and source blocks.
- Article identity, critical IDs, CTA destinations, primary/evidence source URLs and runtime script set must not drift across translations.

## Evidence boundary

Passing this contract proves structural/destination parity for the managed triplets. It does **not** prove that translated prose is linguistically excellent, complete in nuance, or semantically equivalent sentence by sentence.
