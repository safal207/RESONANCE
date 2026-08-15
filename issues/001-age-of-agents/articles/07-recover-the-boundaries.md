# Recover the Boundaries — почему AI-агенту после compaction недостаточно просто «вспомнить задачу»

**Article ID:** I001-RN-RLC  
**Deck:** Долгие агентные сессии могут пережить compaction, перечитать checkpoint и даже восстановить правильные файлы — и всё равно продолжить неверно. Новый failure mode возникает, когда состояние восстановлено, а границы ответственности, mutation scope, done condition и последнее пользовательское решение — нет.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · Continuation Integrity / Responsibility-Lane Continuity

---

## Signal

В длинной coding-agent сессии есть момент, который обычно описывают слишком мягко:

> контекст был сжат, агент что-то забыл.

Это полезное описание, но оно неполное.

В августе 2026 года в публичном issue `openai/codex#29356` появился дополнительный воспроизводимый кейс из Codex Desktop на macOS. После автоматического compaction агент получил generated summary, продолжил работу, затем перечитал durable checkpoint и filesystem — но всё равно:

1. смешал две отдельные responsibility lanes;
2. продолжил переусложнённую реализацию для намеренно простого архитектурного изменения;
3. вернул fallback-подобное поведение, противоречившее недавнему пользовательскому решению;
4. описывал частичные component checks так, будто система приближалась к завершению, хотя end-to-end artifact всё ещё не проходил;
5. признал сам факт compaction только после прямого вопроса пользователя.

Это важный сдвиг в модели отказа.

Агент **не просто потерял факты**.

Он перечитал durable state.

Но после восстановления продолжил под неправильной структурой полномочий.

```text
state recovered
      ≠
continuation recovered
```

И ещё точнее:

```text
what happened recovered
      ≠
who owns what recovered
      ≠
what may change recovered
      ≠
what counts as done recovered
```

Именно этот разрыв мы называем **Responsibility-Lane Continuity**.

---

## Why it matters

Современные coding agents всё чаще работают не как одноразовые генераторы патчей, а как долгоживущие операторы проекта.

Они:

- исследуют кодовую базу;
- принимают промежуточные решения;
- получают пользовательские corrections;
- создают ветки и worktrees;
- запускают тесты;
- возвращаются к задаче после interruption;
- переживают context compaction;
- взаимодействуют с несколькими инструментами и независимыми verification lanes.

Поэтому continuity больше нельзя определять как «модель помнит достаточно текста».

Для безопасного продолжения нужно сохранить как минимум четыре слоя:

```text
1. recent conversational tail
2. durable task state
3. responsibility / authority topology
4. verification closure
```

Потеря любого из них создаёт свой класс ошибок.

| Потерянный слой | Типичный отказ |
|---|---|
| Recent tail | забыта последняя correction |
| Durable state | повторена уже выполненная работа |
| Responsibility topology | агент продолжает правильную задачу не в своей lane / с неправильным scope |
| Verification closure | частичный сигнал принимается за завершение |

Первые два класса часто воспринимаются как memory problem.

Третий — уже **control problem**.

Четвёртый — **proof problem**.

---

## Claims

| ID | Claim | Classification | Confidence | Evidence |
|---|---|---|---|---|
| C1 | `openai/codex#29356` описывает потерю operational continuity после automatic context compaction | Public issue fact | High | Codex issue #29356 |
| C2 | Дополнительный reproducible case показал conflation отдельных responsibility lanes даже после reread durable checkpoint/filesystem | Public reported case | High for report existence; Medium for generalization | averriK comment `#issuecomment-5080913510` |
| C3 | Durable project state помогает continuity, но не гарантирует сохранение последних conversational corrections и ownership boundaries | Design conclusion supported by thread | Medium-High | Codex thread + Nightshift comment |
| C4 | RLC-001 реализует responsibility lanes, mutation scopes, source revalidation, lane digests и fail-closed conflict handling как executable extension | Verified repository fact | High | `safal207/pythiaLabs#258` |
| C5 | Negative lane-conflation fixture возвращает `BLOCKED`, когда authoring mutation ошибочно rebound в verification lane | Verified conformance result | High | PR #258 fixture + conformance suite |
| C6 | Combined GitHub Actions conformance run проходит VCE + RLC suite | Verified CI result | High | Actions run `31861074959` |
| C7 | RLC-001 является внешним research/prototype contract, а не нативной реализацией Codex compaction | Scope limitation | High | Repository/PR boundary |

---

## The hidden failure: state-complete, authority-topology-invalid

Большинство recovery систем задаёт вопрос:

> Что было сделано до interruption?

Но в агентной системе этого недостаточно.

Нужно также спросить:

> Какая часть системы имела право делать следующий шаг?

Представим простой pipeline:

```text
Lane A — architecture / authoring
  objective: изменить контракт
  mutation scope: source + schema
  done: implementation prepared

Lane B — verification
  objective: независимо проверить результат
  mutation scope: verification only
  done: evidence observed and recorded
```

До compaction структура ясна.

После compaction generated summary может корректно сообщить:

- какая задача активна;
- какие файлы менялись;
- какие тесты запускались;
- какой следующий шаг обсуждался.

Но если он потерял границу между A и B, агент может восстановить примерно такую ложную картину:

```text
verification lane
    ↓
may edit implementation
    ↓
may reinterpret done condition
    ↓
may revive rejected fallback
```

Все отдельные факты при этом могут выглядеть правдоподобно.

Ошибка находится не в facts.

Она находится в **relations between facts and authority**.

Это очень похоже на повреждение графа: узлы сохранились, рёбра — нет.

```text
objective ✅
files ✅
tests ✅
checkpoint ✅

ownership edge ❌
mutation-scope edge ❌
latest-ruling edge ❌
done-condition edge ❌
```

Система знает элементы задачи, но больше не знает, как они связаны.

---

## Memory is not authority

Одна из самых опасных ошибок recovery — дать summary или memory больше полномочий, чем они имели до compaction.

Generated summary полезен как информационный носитель.

Но он не должен автоматически становиться execution authority.

В более строгой модели:

```text
summary → information
checkpoint → continuation evidence
user ruling → instruction / constraint authority
project policy → bounded authority
runtime result → evidence
```

Эти классы нельзя сливать.

Если summary говорит:

> продолжай fallback-подход,

а последний пользовательский ruling был:

> fallback больше не использовать,

то корректная recovery система не должна «решить, что summary звучит логично».

Она должна восстановить provenance и precedence.

Последняя active correction должна победить восстановленный narrative.

Именно поэтому в Verifiable Continuation Envelope ранее появился принцип:

> Preserve continuity without inventing history, and restore information without silently restoring authority.

Responsibility-Lane Continuity добавляет к нему ещё один уровень:

> Restore authority without silently changing its topology.

---

## A lane is more than an agent role

Responsibility lane — это не просто имя агента вроде `coder`, `reviewer` или `planner`.

Lane — это bounded execution contract.

Минимально она должна содержать:

```text
lane_id
owner_ref
objective
mutation_scope.allowed_refs
mutation_scope.denied_refs
done_condition
status
latest_ruling_ref
source_refs
depends_on
lane_digest
```

То есть lane отвечает одновременно на вопросы:

```text
WHO owns this part?
WHAT is this lane trying to achieve?
WHERE may it create effects?
WHERE must it not create effects?
WHEN is it done?
WHICH latest ruling constrains it?
WHICH durable sources define it?
```

Это делает responsibility topology проверяемой.

Не «кажется, reviewer должен только проверять», а:

```text
verification.allowed = capability:verify
verification.denied = artifact:rfc, artifact:schema
```

Если после compaction событие `artifact_modified` привязано к verification lane — это уже не субъективный drift.

Это machine-checkable contract violation.

---

## Formal continuation condition

Пусть существует набор responsibility lanes:

```text
L = {L1, L2, ... Ln}
```

Каждая lane определяется как:

```text
Li = (
  id,
  owner,
  objective,
  allow,
  deny,
  done,
  ruling,
  sources,
  dependencies,
  digest
)
```

После compaction восстановление нельзя считать успешным только потому, что active objective найден.

Минимальный continuation predicate выглядит так:

```text
ContinuationValid =
    VCE_RestoreValid
    AND AllLiveLanesRevalidated
    AND NoLaneSourceConflict
    AND AllMaterialEventsLaneBound
    AND EffectsWithinLaneScope
    AND NextActionWithinActiveLaneScope
    AND TaskVerificationNotFalselyPromoted
```

В человеческом виде:

```text
state recovery
      ↓
responsibility-lane recovery
      ↓
source revalidation
      ↓
conflict detection
      ↓
next-action scope check
      ↓
task-specific verification
      ↓
continuation
```

Если любой шаг не доказан, consequential mutation должна останавливаться.

---

## Fail closed is not «be cautious»

В агентных системах фраза «если не уверен — будь осторожен» слишком мягкая.

Нам нужен наблюдаемый переход состояния.

Например:

```text
PASSED
REVIEW_REQUIRED
BLOCKED
```

Для responsibility recovery:

- missing lane source → `BLOCKED`;
- digest mismatch → `BLOCKED`;
- conflicting ownership definitions → `BLOCKED`;
- pending revalidation → `REVIEW_REQUIRED`;
- cross-lane mutation → `BLOCKED`;
- next action outside active lane scope → `BLOCKED`.

Это важно, потому что failure mode после compaction часто выглядит уверенно.

Модель не обязательно говорит:

> я потеряла контекст.

Она может сказать:

> всё восстановлено, продолжаю.

Именно поэтому safety property должен находиться не в self-report модели, а в механическом gate.

---

## The latest ruling must survive as a relation

В длинной инженерной сессии пользователь редко переписывает всю постановку задачи.

Вместо этого появляются последовательные rulings:

```text
сделай X
↓
не трогай Y
↓
вариант A отвергаем
↓
оставь архитектуру простой
↓
fallback больше не нужен
```

Если compaction сохраняет только общий смысл задачи, но не связь последнего ruling с конкретной lane, система может восстановить раннюю версию решения.

Поэтому важен не только список инструкций, но и привязка:

```text
lane.latest_ruling_ref → authoritative event
```

Это делает recent correction частью topology.

Не просто «где-то в истории было такое сообщение», а:

> эта lane сейчас ограничена именно этим ruling.

---

## Done condition is also authority

Отдельный класс drift возникает, когда агент правильно помнит задачу, но неправильно восстанавливает критерий завершения.

Например:

```text
component test A = PASS
component test B = PASS
end-to-end artifact = FAIL
```

Если до compaction done condition был:

> end-to-end artifact must pass,

то два зелёных component tests не должны позволять системе сказать «почти готово» в смысле promotion readiness.

Это не косметическая формулировка.

Done condition определяет, когда lane имеет право перейти в `complete`.

Поэтому RLC хранит его внутри lane contract, а не только в narrative summary.

```text
partial evidence
    ≠
completion authority
```

---

## Executable proof: RLC-001

После появления нового failure case мы не ограничились концептуальной формулировкой.

В `safal207/pythiaLabs` был создан draft PR #258:

**RLC-001 — Responsibility Lane Continuity Extension for VCE**.

Он добавляет поверх существующего Verifiable Continuation Envelope:

- explicit responsibility lanes;
- owner/objective/mutation-scope/done-condition contracts;
- latest ruling references;
- event → lane bindings;
- lane-scoped next action;
- required source revalidation;
- conflict state with fail-closed semantics;
- lane digests;
- extension digest;
- accepted fixture;
- rejected lane-conflation fixture;
- executable reference validator;
- conformance tests.

Ключевая negative fixture намеренно создаёт неправильное восстановление:

```text
spec-authoring lane
  may mutate: artifact-rfc, artifact-schema

verification lane
  may mutate: capability:verify
  denies: artifact-rfc, artifact-schema

recovered event:
  artifact-rfc + artifact-schema mutation
  attributed to verification lane
```

Durable lane restore при этом может выглядеть успешным.

Но scope invariant нарушен.

Результат:

```text
BLOCKED
```

Именно это нужно от recovery gate: поймать ситуацию, в которой «все источники прочитаны», но система всё равно собрала неправильную operational topology.

---

## Verification result

Reference suite был сначала прогнан локально:

```text
21 / 21 PASS
```

Затем responsibility-lane suite был включён в GitHub Actions рядом с базовым VCE conformance workflow.

На head PR #258:

```text
VCE conformance — SUCCESS
Responsibility-lane continuity suite — SUCCESS
Security — SUCCESS
CI — SUCCESS
```

Это не доказывает, что проблема решена внутри Codex Desktop.

Это доказывает более узкий тезис:

> failure mode можно выразить как machine-readable invariant и воспроизводимо отклонять в независимом reference implementation.

Для исследовательского журнала это важная граница между идеей и инженерным артефактом.

---

## Relation to Verifiable Continuation Envelope

RLC не заменяет предыдущий continuation contract.

Они решают разные уровни.

### VCE отвечает:

```text
что нужно восстановить?
что действительно было прочитано?
какие evidence anchors перепроверены?
какие rejected approaches остаются rejected?
какие проверки ещё pending?
```

### RLC отвечает:

```text
какие responsibility lanes существуют?
кто владеет каждой lane?
какие effects ей разрешены?
какие запрещены?
какой done condition действует?
какое последнее ruling её ограничивает?
правильно ли material events rebound после recovery?
```

Вместе получается более сильная система:

```text
lossless recent operational tail
        ↓
Verifiable Continuation Envelope
        ↓
Responsibility-Lane Continuity
        ↓
task-specific verification
        ↓
execution / mutation eligibility
```

Это уже похоже не на memory subsystem, а на **Continuation Integrity Stack**.

---

## Relation to Mission Keeper

Параллельно в публичном AutoGen discussion о Mission Keeper возник почти тот же structural principle с другой стороны.

Там вопрос звучал как:

> может ли verifier одновременно участвовать в переходе, который он проверяет?

Ответ, к которому пришла дискуссия: независимость лучше делать механической — read-only handles, отсутствие execution routes, отдельный outcome record.

Responsibility-Lane Continuity переносит этот принцип на recovery:

```text
before compaction:
  verifier cannot execute transition

therefore after compaction:
  recovery must not accidentally restore execution authority to verifier lane
```

Иначе structural separation исчезает именно в момент, когда система должна восстановить себя.

Можно правильно спроектировать separation of powers и потерять её при compaction.

Поэтому continuation protocol становится частью governance architecture, а не только UX памяти.

---

## The graph view

Эта проблема особенно ясна, если смотреть на агентную сессию как на граф.

До compaction:

```text
mission
  ↓
objective
  ↓
responsibility lanes
  ↓
allowed transitions
  ↓
artifacts / evidence
  ↓
done conditions
```

Compaction часто сохраняет nodes:

```text
mission
objective
files
results
```

Но safety находится также в edges:

```text
who owns this
who may mutate this
which ruling constrains this
which evidence closes this
which lane depends on which
```

Отсюда более общий принцип:

> Continuity is not preservation of nodes. It is preservation of the causal and authority edges that make the nodes operationally meaningful.

Это соединяет RLC с более широкой линией RESONANCE: provenance, causal graphs, trust portability и fractal verification.

---

## A stronger definition of agent continuity

Мы можем теперь сформулировать continuity так:

> **Agent continuity is the preservation and revalidation of the minimum causal, authority, responsibility and evidence structure required for the next action to remain valid.**

Эта формулировка сильнее, чем «remember the last messages».

Она допускает агрессивное сжатие старой истории, если сохраняется необходимая operational structure.

И одновременно запрещает ложную continuity, когда длинный summary выглядит информативно, но теряет:

- latest correction;
- lane ownership;
- mutation boundary;
- rejected path;
- done condition;
- pending proof;
- evidence provenance.

---

## Product implications

Если этот failure class окажется достаточно общим, agent runtimes придётся проектировать compaction иначе.

### 1. Compaction should become visible

Automatic compaction — это state transition runtime, а не только внутренняя оптимизация tokens.

Система должна иметь наблюдаемый pre/post recovery boundary.

### 2. Summary should be demoted

Summary — полезное compressed information representation.

Но mutation после compaction должна зависеть от восстановленных contracts и evidence, а не только от текста summary.

### 3. Durable state is necessary but insufficient

Project-local files, punch lists и checkpoints полезны.

Они снижают dependence on chat memory.

Но если runtime не восстановил responsibility topology, он может правильно прочитать неправильный набор operational permissions.

### 4. Ownership should become first-class data

Сегодня ownership часто существует неявно — в prompt, reasoning, naming convention или человеческом ожидании.

Для автономных систем этого будет мало.

### 5. Verification must remain separate from completion claims

Partial component checks не должны автоматически менять done state.

Evidence и completion authority — разные вещи.

---

## What this does not prove

RLC-001 пока не следует переоценивать.

Он **не доказывает**, что:

- Codex или другой runtime будет использовать этот формат;
- responsibility lanes являются единственным правильным abstraction;
- все compaction failures сводятся к authority topology;
- внешний validator способен восстановить скрытые человеческие намерения;
- passing conformance suite означает production safety;
- отдельный durable sidecar автоматически решает conversational nuance loss.

Текущий статус точнее описывать так:

```text
public failure signal
        ↓
explicit failure model
        ↓
machine-readable contract
        ↓
negative fixture
        ↓
reference validator
        ↓
green conformance evidence
```

Это engineering research artifact.

Не vendor adoption claim.

---

## The next questions

RLC открывает следующие frontier questions.

### Lane transfer

Что происходит, когда ownership законно переходит от одного агента к другому?

Нужен ли signed handoff?

### Nested lanes

Может ли architecture lane содержать отдельные DB/API/UI sub-lanes с собственными scopes?

### Tool capability binding

Можно ли связать mutation scope не только с semantic refs, но и физически с MCP/tool routes?

Например:

```text
verifier lane → read/test tools only
builder lane → scoped write tools
publisher lane → publish route only after proof
```

### Cross-agent verification

Как доказать, что verifier действительно был отдельным actor/vantage, а не тем же execution loop под другим именем?

### Temporal validity

Даже правильно восстановленная lane могла устареть, если repository head, policy или environment изменились.

Следовательно:

```text
responsibility restored
    ≠
responsibility still valid now
```

Это связывает RLC с temporal revalidation и FCRP.

---

## Continuation Integrity Stack

После нескольких независимых линий работы появляется более цельная архитектура:

```text
Mission / Intent
      ↓
Lossless Recent Operational Tail
      ↓
Verifiable Continuation Envelope
      ↓
Responsibility-Lane Continuity
      ↓
Durable Evidence Revalidation
      ↓
Task-Specific Verification
      ↓
Execution Eligibility
      ↓
Observed Outcome
      ↓
Append-Only Operational Memory
```

Каждый слой отвечает на отдельный вопрос:

| Layer | Question |
|---|---|
| Mission | Что мы вообще пытаемся сделать? |
| Operational tail | Что только что произошло? |
| VCE | Что должно быть восстановлено и перепроверено? |
| RLC | Кто за что отвечает и что ему разрешено менять? |
| Evidence | Что действительно существует сейчас? |
| Task verification | Выполнен ли конкретный invariant? |
| Execution eligibility | Можно ли делать следующий consequential transition? |
| Outcome | Что произошло после действия? |
| Operational memory | Как сохранить результат без превращения его в новую authority? |

Так память становится только одним элементом trust architecture.

---

## Editorial conclusion

Самая неприятная форма потери контекста — не когда агент говорит: «я не помню».

Самая неприятная форма — когда он помнит достаточно, чтобы уверенно продолжить, но уже не понимает границы, внутри которых продолжение было допустимо.

Это и есть разница между **memory continuity** и **operational continuity**.

А следующий шаг — различать operational continuity и **authority continuity**.

```text
remembering the work
      ≠
recovering the work
      ≠
recovering who may do what
      ≠
proving the next action is still valid
```

Поэтому после compaction хороший агент должен восстанавливать не только задачу.

Он должен восстановить **границы**.

И если границы нельзя доказать — не продолжать как будто ничего не произошло.

> **Recovering the work is not enough. Recover the boundaries that make the work safe to continue.**

---

## Canonical engineering references

- Codex continuity issue: `openai/codex#29356`
- Reproducible macOS case: `openai/codex#29356`, comment `5080913510`
- RLC-001 implementation: `safal207/pythiaLabs#258`
- RLC-001 specification: `standards/agent-continuity/extensions/RLC-001-RESPONSIBILITY-LANE-CONTINUITY.md`
- Rejected lane-conflation fixture: `standards/agent-continuity/extensions/fixtures/rlc-rejected-lane-conflation.json`
- Combined conformance run: `31861074959`

Detailed provenance and source classification are preserved in the companion sources file.
