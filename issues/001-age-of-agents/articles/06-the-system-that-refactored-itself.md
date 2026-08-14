# The System That Refactored Itself — что FCRP нашёл, когда мы применили его к собственной AI trust infrastructure

**Article ID:** I001-RN-FCRP-SELF  
**Deck:** После публикации Fractal Causal Refactoring Protocol мы превратили его в исполняемый контракт и направили на собственные репозитории. Он начал находить не только дефекты кода, но и ошибки в доказательствах, времени, canonical state, provenance и границах semantic authority.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-14  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · FCRP / Self-Refactoring / Trust Infrastructure

---

## Signal

14 августа 2026 года RESONANCE опубликовал исходную модель **Fractal Causal Refactoring Protocol (FCRP)**: анализировать систему не от места симптома, а от её идеи, масштаба, истории и причинной траектории.

Следующий шаг был намеренно опаснее для самой гипотезы: не искать удобный внешний пример, а направить FCRP на инфраструктуру, в которой он создавался.

```text
RESONANCE idea
      ↓
FCRP executable core
      ↓
ContractGraph-QA self-test
      ↓
ProofPath
      ↓
CML
      ↓
LiminalDB
      ↓
RINSE
```

Результат оказался важнее первоначального ожидания.

FCRP начал находить расхождения не только внутри runtime logic. Несколько первых значимых divergence находились в других слоях:

```text
test evidence
repository canonicality
time semantics
contract identity
provenance strength
semantic authority
Git topology
```

Иными словами, система начала обнаруживать ошибки в **собственном представлении о том, что уже доказано, что является текущим и кто имеет право интерпретировать состояние**.

---

## Why it matters

Автономный engineering agent может написать корректный patch и всё равно принять неправильное решение.

Причина проста: локально зелёный результат может опираться на слабый тест, устаревший контракт, промежуточное состояние, branch-only capability или доказательство меньшей силы, чем предполагает агент.

Из этого следует более широкий объект проверки:

```text
code correctness
        ⊂
state-transition correctness
        ⊂
verification correctness
        ⊂
repository reality
        ⊂
system reality
```

Если AI-агенты будут самостоятельно рефакторить сложные системы, им потребуется уметь спрашивать не только:

> Этот fix работает?

но и:

> На какой версии реальности основан этот вывод, какой контракт считается каноническим, какой тип времени наблюдался, чем доказано состояние и не присвоил ли один слой полномочия другого?

---

## Claims

| ID | Claim | Classification | Confidence | Evidence |
|---|---|---|---|---|
| C1 | FCRP v0.1 существует как исполняемый machine-readable evaluator, а не только как статья | Verified fact | High | ContractGraph-QA PR #49 / merge `b87a8ada…` |
| C2 | Первый FCRP self-test обнаружил, что зелёный regression test мог доказывать не тот invariant, который заявлял | Verified repository result | High | FCRP-SELF-001 in ContractGraph-QA |
| C3 | В Gonka research FCRP отклонил локально успешный candidate fix после upward verification parent accounting invariant | Reproducible research result; not upstream defect claim | Medium | ContractGraph-QA PR #33 / FCRP-SELF-002 |
| C4 | В temporal Gonka probe FCRP обнаружил ошибку в нашем собственном wall-clock oracle до объявления upstream liveness defect | Reproducible research result; runtime follow-up ongoing | Medium | ContractGraph-QA PR #50 / FCRP-SELF-003/004 |
| C5 | ProofPath audit обнаружил Canonical Reality Drift между `main` и длинной branch-only capability chain и ввёл machine-readable promotion contract | Verified repository result | High | ProofPath PR #220 / merge `4a05ee31…` |
| C6 | CML self-audit показал, что историческое `verified` не эквивалентно current applicability + information quality | Verified repository result | High | CML PR #283 / merge `2a649903…` |
| C7 | LiminalDB self-audit отделил historical provenance identity от current semantic contract compatibility | Verified repository result | High | LiminalDB PR #117 / merge `dfd74ad9…` |
| C8 | RINSE audit консолидировал одну interpretation semantics и выявил gap между declared schema/provenance и реально enforced verification | Verified core result; domain projection follow-up ongoing | High / Medium | RINSE PR #23 / merge `fcf83417…`, PR #25 |

Эти результаты не доказывают, что FCRP является универсальным root-cause algorithm. Они показывают более узкий факт: один и тот же причинный контракт уже оказался полезен для нескольких разных классов self-verification внутри связанных репозиториев.

---

## Evidence

### Primary repository evidence

- [ContractGraph-QA PR #49 — provider evidence pack + FCRP self-verification core](https://github.com/safal207/ContractGraph-QA/pull/49)
- [ContractGraph-QA PR #33 — Gonka verification profile / FCRP-SELF-002](https://github.com/safal207/ContractGraph-QA/pull/33)
- [ContractGraph-QA PR #50 — G-004P/G-004Q temporal proof / FCRP-SELF-003/004](https://github.com/safal207/ContractGraph-QA/pull/50)
- [ProofPath PR #220 — FCRP-SELF-005 Canonical Reality Drift](https://github.com/safal207/ProofPath/pull/220)
- [CML PR #283 — FCRP-SELF-006 Temporal Contract Drift](https://github.com/safal207/Causal-Memory-Layer/pull/283)
- [LiminalDB PR #117 — FCRP-SELF-007 provenance vs compatibility](https://github.com/safal207/LiminalDB/pull/117)
- [RINSE PR #23 — consolidated reflection graph v0.2](https://github.com/safal207/rinse/pull/23)
- [RINSE PR #25 — FCRP-SELF-008 Career projection over one interpretation authority](https://github.com/safal207/rinse/pull/25)

### Canonical FCRP implementation

- [`contractgraph_qa/fcrp.py`](https://github.com/safal207/ContractGraph-QA/blob/main/contractgraph_qa/fcrp.py)
- [FCRP v0.1 protocol documentation](https://github.com/safal207/ContractGraph-QA/blob/main/docs/FRACTAL_CAUSAL_REFACTORING_PROTOCOL_V0_1.md)

### Origin article

- [Article 05 — Fractal Causal Refactoring](05-fractal-causal-refactoring.md)

---

## From idea to executable protocol

Исходная статья описывала пространство поиска:

```text
Scale × Time × Causality × Intent
```

Минимальный executable FCRP v0.1 не пытается автоматически угадать root cause. Он проверяет, что предложенное причинное объяснение не схлопывает разные понятия в одно.

```text
scope + idea
     ↓
past / present / future
     ↓
evidence
     ↓
causal path
     ↓
first meaningful divergence
     ↓
cause point
     ↓
refactor point
     ↓
navigation
     ↓
local verification
     ↓
upward verification
     ↓
PASS / BLOCK
```

Это принципиальное ограничение.

FCRP v0.1 пока является **causal case verifier**, а не автономным причинным оракулом.

---

## SELF-001 — когда тест доказывает не то, что написано в его названии

Первый self-test появился внутри самого ContractGraph-QA.

Цель regression test была простой: доказать, что отдельно переданный неверный external digest блокирует evidence pack.

Но fixture был невалиден раньше этого boundary.

```text
invalid fixture
     ↓
schema rejection
     ↓
test sees expected exception class
     ↓
GREEN
```

Проблема: тест мог остаться зелёным даже при исчезновении external-digest guard.

FCRP разложил три точки:

```text
symptom:
confidence in regression

cause:
invalid fixture

refactor point:
test construction
```

Ремонт оказался не в production verifier.

Новый proof требует:

```text
valid evidence pack
+ intentionally wrong external digest
+ exact external-digest mismatch
```

Первый урок:

> **Verification code тоже является системой, которую необходимо причинно проверять.**

---

## SELF-002 — local PASS может быть глобальным FAIL

В Gonka timeout/correlation исследовании локально привлекательный fix решал addressability:

```text
caller correlation id
→ use as canonical request id
→ timeout lookup works
```

Локальный тест переходил из FAIL в PASS.

Но FCRP выполнил `UP` и проверил parent accounting storage.

При повторном caller correlation две независимые logical operations могли схлопнуться в одну canonical accounting row.

```text
local addressability PASS
          ↓
zoom UP
          ↓
request accounting identity collision
          ↓
parent invariant FAIL
          ↓
BLOCK
```

Второй урок:

> **Локальный success — это наблюдение, а не разрешение на refactor.**

Важно: этот кейс является исследованием candidate remediation, а не заявлением о подтверждённой уязвимости Gonka.

---

## SELF-003 — иногда дефект находится в наших часах

Следующий Gonka probe выглядел тревожно:

```text
HTTP 200
request outcome = success
winner inference = pending
120 seconds later = still pending
reserve not released
```

Первичная гипотеза: возможный liveness/accounting defect.

FCRP заставил подняться к protocol semantics.

Оказалось, что `MsgFinishInference` проходит через отдельную protocol transition: публикация Finish и wall-clock ожидание сами по себе не доказывают, что следующий eligible diff уже применил state transition.

```text
wall-clock elapsed
        ≠
protocol state advanced
```

First Meaningful Divergence оказался в нашем verification oracle.

Вместо «подождать ещё дольше» новый G-004Q требует:

```text
retry pending
→ exact Finish visible / sequencing-ready
→ next eligible state advance
→ terminal state
→ reserve / actual / fee reconciliation
```

Третий урок:

> **В распределённой системе нужно идентифицировать не только время, но и тип времени.**

---

## SELF-005 — branch reality не равна canonical reality

ProofPath обнаружил другой класс расхождения.

В `main` существовала одна совокупность capabilities, а длинная цепочка PoCI → Deploy Guard → Evidence → Control Cloud → Governance жила в протестированных stacked PR.

С технической точки зрения код существовал.

Но вопрос FCRP был другим:

> Может ли downstream-система считать это capability обычной поверхностью ProofPath?

Ответ: нет.

Первой значимой divergence стал ранний branch-only PoCI contract, от которого начала расти зависимая архитектура.

Вместо mass merge был введён lifecycle contract:

```text
CANONICAL
PROPOSED
EXPERIMENTAL
SUPERSEDED
ARCHIVED
```

И consumer invariant:

```text
status = CANONICAL
AND
consumer_default_allowed = true
AND
canonical_commit = exact commit
```

Так появился новый класс:

### Canonical Reality Drift

```text
implemented somewhere
        ≠
canonical capability
```

---

## SELF-006 — historical verified не значит currently trusted

В CML Focus–Field experiment исторический anchor имел простую модель:

```text
verified: bool
+ evidence_refs
```

Но canonical CML к этому времени уже имел более сильные contracts:

- applicability to current repository / commit / environment;
- information-quality readiness;
- evidence binding;
- lineage/source semantics.

Старый `verified=true` мог пережить контекст, в котором он был получен.

FCRP нашёл Temporal Contract Drift:

```text
historically verified
       ≠
currently applicable
       ≠
ready for authority check
```

После refactor trusted continuation требует current gate outputs. Старая информация может оставаться полезной, но явно как exploratory context.

Четвёртый урок:

> **Доверие к памяти имеет временную область применимости.**

---

## SELF-007 — provenance identity не является semantic identity

LiminalDB дал почти обратный пример.

Первичная гипотеза была: старый import contract устарел, потому что `main` ушёл вперёд.

Но causal diff показал:

```text
historical repository commit changed
contract bytes unchanged
```

Старая модель использовала historical commit сразу в двух ролях:

```text
provenance identity
+
semantic compatibility identity
```

Это создавало ложную incompatibility.

Refactor разделил факты:

```text
historical commit
= provenance

current contract blob
= semantic compatibility
```

Если repository меняется, а потребляемый contract byte-identical — совместимость сохраняется.

Если contract bytes меняются — verifier fail closed.

Пятый урок:

> **То, откуда пришёл артефакт, и то, с чем он совместим сейчас, — разные доказательства.**

---

## SELF-008 — доменный слой не должен становиться вторым источником истины

RINSE развивал общий reflection graph и отдельно Career RINSE.

Оба направления были полезны, но topology позволила двум interpretation models эволюционировать параллельно.

Это создало риск:

```text
RINSE core interpretation authority
        ∥
Career-specific interpretation authority
```

Рефактор строится вокруг другой формы:

```text
one interpretation semantics
+ many domain adapters / projections
```

Career evidence нормализуется доменным слоем, затем создаётся shared RINSE reflection record, и только после этого строится Career projection.

Параллельно в core audit обнаружился отдельный assurance gap: JSON Schemas существовали, но workflow проверял лишь их синтаксическую валидность; часть provenance была записана в receipt, но не независимо проверялась этим CI.

После исправления:

```text
declared schema
→ executable schema validation

recorded provenance
→ explicitly distinguished from verified provenance
```

Шестой урок:

> **Записать доказательство и проверить доказательство — не одно действие.**

---

## Новые классы расхождений

Первые self-tests дали рабочую таксономию. Это пока внутренние инженерные названия, не отраслевой стандарт.

### 1. Verification Boundary Drift

Тест остаётся зелёным, но больше не доказывает заявленный boundary.

### 2. Local Success / Parent Invariant Failure

Fix улучшает локальный outcome, но нарушает более высокий системный invariant.

### 3. Clock-Semantics Drift

Verifier измеряет wall-clock там, где причинно значим protocol/event/state clock.

### 4. Canonical Reality Drift

Capability существует в ветках и обсуждениях, но не является canonical consumer surface.

### 5. Temporal Contract Drift

Историческое доказательство применяется как будто его validity window не изменился.

### 6. Provenance / Compatibility Conflation

Один identifier используется одновременно как история происхождения и критерий текущей совместимости.

### 7. Parallel Semantic Authority

Domain layer начинает самостоятельно определять meaning вместо projection через общий semantic contract.

### 8. Recorded / Verified Provenance Gap

Receipt содержит provenance claim, но текущий verification layer его не подтверждает и не маркирует как непроверенный.

---

## Causal model

Общий механизм self-refactoring оказался таким:

```text
Idea(system)
     ↓
Expected contract
     ↓
Canonical state
     ↓
Observed repository / test / runtime state
     ↓
First Meaningful Divergence
     ↓
choose navigation:
DOWN / UP / SIDEWAYS / TIME
     ↓
Refactor Point
     ↓
local proof
     ↓
parent / dependency proof
     ↓
canonical promotion
     ↓
repeat at next scale
```

Особенно важен новый переход:

```text
verification result
      ↓
verify the verifier
```

FCRP оказался рекурсивным не только по масштабу предметной системы, но и по масштабу **доказательства**.

### Alternative explanations

- Некоторые найденные проблемы могли быть обнаружены обычным тщательным code review без FCRP.
- Self-selected repositories и cases создают сильный selection bias.
- Формализация case после возникновения подозрения может ретроспективно делать причинный путь более чистым, чем он был в реальном исследовании.
- Несколько результатов являются repository-governance improvements, а не runtime defect discoveries.
- Gonka temporal experiments остаются research work; они не должны интерпретироваться как подтверждённый upstream security defect без terminal causal proof.

---

## Timeline

| Date | Event | Evidence |
|---|---|---|
| 2026-08-14 | Article 05 публикует FCRP как архитектурную модель | RESONANCE Article 05 |
| 2026-08-14 | FCRP Core v0.1 + SELF-001 merged в ContractGraph-QA | PR #49 / `b87a8ada…` |
| 2026-08-14 | SELF-002 блокирует локально успешный Gonka correlation candidate после upward accounting verification | ContractGraph-QA PR #33 |
| 2026-08-14 | SELF-003 переопределяет Gonka liveness oracle с wall-clock на protocol transition | ContractGraph-QA PR #50 |
| 2026-08-14 | SELF-005 capability canonicality contract merged в ProofPath | PR #220 / `4a05ee31…` |
| 2026-08-14 | SELF-006 current trust-gate reconciliation merged в CML | PR #283 / `2a649903…` |
| 2026-08-14 | SELF-007 provenance/compatibility separation merged в LiminalDB | PR #117 / `dfd74ad9…` |
| 2026-08-14 | RINSE v0.2 consolidated interpretation surface merged; SELF-008 Career projection reconciliation prepared | PR #23 / `fcf83417…`, PR #25 |

---

## What changed in the FCRP hypothesis

Исходная статья предполагала, что FCRP прежде всего поможет выбирать правильное место ремонта в сложной системе.

Self-tests расширили гипотезу.

Теперь объектом causal navigation является не только production system:

```text
runtime
code
contract
test
benchmark
workflow
repository
branch topology
capability lifecycle
provenance
semantic authority
```

Это приводит к более сильной формулировке:

> **FCRP должен уметь находить First Meaningful Divergence между идеей системы и любой машинно значимой формой её текущей реальности — включая доказательства и канонический статус самой системы.**

---

## FCRP v0.2 — что теперь просится в контракт

Executable v0.1 намеренно минимален. Self-refactoring показывает следующие естественные расширения.

### IdeaContract

```text
purpose
expectedOutcome
invariants[]
forbiddenOutcomes[]
dependencies[]
parentContract
```

### Typed time

```text
wall_clock
protocol_clock
logical_operation_time
repository_history
contract_validity_window
```

### Stronger stop conditions

Исходная статья содержала условие:

```text
causal propagation stopped
```

В минимальном v0.1 оно ещё не является отдельным machine-enforced field. Это кандидат для v0.2.

### Refactor candidates + simulation

```text
candidate
├ causal_leverage
├ invariant_restoration
├ downstream_benefit
├ future_alignment
└ change_risk
```

с будущим концептуальным score:

```text
RefactorScore =
    causal_leverage
  × invariant_restoration
  × downstream_benefit
  × future_alignment
  ÷ change_risk
```

### Evidence strength

```text
recorded
locally_recomputed
externally_anchored
independently_observed
```

### Capability lifecycle

```text
EXPERIMENTAL
PROPOSED
CANONICAL
SUPERSEDED
ARCHIVED
```

### Semantic authority

Каждый interpretation / decision layer должен явно отвечать:

```text
who may interpret?
who may authorize?
who may execute?
who may persist?
who merely observes?
```

---

## Uncertainty

FCRP ещё не доказал следующие вещи:

- автоматическое восстановление Idea из конфликтующих источников;
- автономное нахождение First Meaningful Divergence без заранее сформированного causal case;
- объективное ранжирование нескольких refactor candidates;
- качество simulation на больших distributed systems;
- переносимость результатов на независимые команды без участия авторов;
- снижение реального числа production regressions в контролируемом сравнении;
- оптимальный computational/time cost causal navigation.

Особенно важно: успешные self-tests могут показывать полезность дисциплины, но не доказывают универсальность алгоритма.

---

## Verification

- [x] Material repository claims bound to public PRs / commits
- [x] Merged results separated from ongoing draft research
- [x] External Gonka work not presented as confirmed vulnerability
- [x] FCRP v0.1 boundary kept explicit: verifier, not autonomous root-cause oracle
- [x] Alternative explanations included
- [x] New defect-class names labelled as working taxonomy
- [x] Canonical / proposed / experimental states distinguished where material
- [ ] Independent third-party replication completed
- [ ] Controlled comparison against non-FCRP debugging completed

---

## Implications

### First-order

FCRP уже можно рассматривать не только как debugging pattern, но как **repository and verification governance protocol**.

AI-agent system может проверять:

```text
What is wrong?
What proves it?
Is that proof current?
Is that capability canonical?
What clock defines completion?
What identity defines compatibility?
Who owns semantic authority?
```

### Second-order

Trust infrastructure для AI может потребовать отдельный causal control plane, соединяющий:

```text
RESONANCE  → intent / idea
CML        → history / applicability
FCRP       → divergence / navigation
LiminalOSAI→ authority
ContractGraph-QA → transition verification
ProofPath  → evidence / provenance
LiminalDB  → durable verified state
RINSE      → reinterpretation
```

Следующая проверка должна происходить уже не repository-by-repository, а на уровне **межрепозиторного end-to-end system contract**.

### Who wins / who loses

Выигрывают команды, которым важно отличать «код существует» от «capability канонична», «результат записан» от «результат проверен», и «локальный fix работает» от «система после него остаётся целостной».

Цена — дополнительная дисциплина и verification cost. Для тривиальных изменений полный causal pass по-прежнему может быть избыточен.

---

## What to watch next

1. FCRP-SELF-009 на authorization boundary в LiminalOSAI;
2. end-to-end `FCRP-SYSTEM-001` через несколько репозиториев;
3. machine-readable IdeaContract;
4. typed clock semantics;
5. explicit `causalPropagationStopped`;
6. evidence-bound impact simulation;
7. independent external cases;
8. сравнение regression-prevention rate с локальным fix-first workflow.

---

## Action

Для разработчиков agent infrastructure практический переход теперь выглядит так:

```text
Observe failure
→ locate scope
→ recover IdeaContract
→ identify relevant clock / history
→ build evidence-bound causal path
→ find First Meaningful Divergence
→ distinguish symptom / cause / refactor point
→ verify local candidate
→ verify parent / dependency invariants
→ verify evidence strength
→ verify canonical capability state
→ authorize separately
→ promote / change
→ preserve proof
```

Главное изменение — после каждого зелёного результата задавать ещё один вопрос:

> **Что именно этот green result доказывает — и на каком уровне системы это доказательство действительно действует?**

---

## Hot Question

> **Где в вашей engineering-системе сегодня существует самая опасная “ложная реальность”: зелёный тест, устаревший verified-флаг, branch-only capability, записанный-but-unverified provenance или локальный fix, который никто не проверяет на уровне родительского инварианта?**

### Workflow prompts

- **Observed state:** Что выглядит зелёным / валидным / готовым?
- **Hidden boundary:** Какой более высокий контракт может это опровергнуть?
- **Time:** Какой тип времени определяет, что состояние действительно финально?
- **Canonicality:** Это production/main capability или только branch/research state?
- **Evidence:** Что реально проверено, а что лишь записано?
- **Authority:** Кто имеет право превратить этот вывод в действие?

### CTA

**Дайте один реальный пример “локально всё правильно, но системе всё равно нельзя доверять” →**

---

## Corrections

| Date | Correction | Reason |
|---|---|---|
| 2026-08-14 | Initial publication | Field report created after first executable cross-repository FCRP self-tests |

---

**RESONANCE verification chain:**

**Signal → Claim → Source → Evidence → Cause → Timeline → Uncertainty → Verification → Implication → Action**

**FCRP self-refactoring chain:**

**Idea → Canonical Reality → Evidence → Divergence → Navigation → Refactor → Upward Verification → Promotion → Re-evaluate**
