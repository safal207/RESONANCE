# Fractal Causal Refactoring — как AI-агенту искать не ошибку, а точку расхождения системы с её идеей

**Article ID:** I001-RN-FCRP  
**Deck:** Новый класс AI-агента должен уметь выбирать правильный масштаб проблемы, восстанавливать идею системы во времени, находить первое причинное расхождение и доказывать, что локальное исправление не разрушает целое.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-14  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · Causal Reasoning / Refactoring

---

## Signal

Большинство AI-агентов для разработки работают по короткому циклу:

```text
ошибка → файл → функция → исправление → тест
```

Но место, где проявилась проблема, не обязательно является местом, где она возникла.

Сбой в нижнем слое может быть следствием решения, принятого несколькими уровнями выше. И наоборот: локальный компонент может быть реализован идеально, но выполнять неверную задачу, потому что ошибка появилась на уровне продукта, архитектуры или исходного замысла.

Из этого следует другой вопрос для автономного агента:

> Не «где сломалось?», а «где траектория системы впервые перестала соответствовать её идее?»

Эта статья вводит **Fractal Causal Refactoring Protocol (FCRP)** — фрактальный протокол причинного рефакторинга.

---

## Why it matters

Чем больше прав получает AI-агент, тем опаснее стратегия «нашёл симптом → придумал fix → применил fix».

Если агент меняет код, инфраструктуру, политики, данные или финансовые state transitions, ему недостаточно знать локальный дефект. Он должен понимать:

- на каком уровне системы находится проблема;
- зачем этот уровень существует;
- как он пришёл в текущее состояние;
- где впервые возникло причинное расхождение;
- какое изменение даст максимальный эффект при минимальном риске;
- как доказать сохранение целостности родительской системы после ремонта.

Это превращает AI-агента из локального исполнителя в **навигатора сложных систем**.

---

## Claims

| ID | Claim | Classification | Confidence | Evidence |
|---|---|---|---|---|
| C1 | Место наблюдаемого сбоя и место возникновения причины могут находиться на разных уровнях системы | Engineering principle / inference | High | Причинная модель и иллюстративные примеры статьи |
| C2 | Один и тот же причинный цикл можно рекурсивно применять к вложенным уровням системы | Proposed protocol | Medium | FCRP model |
| C3 | Root cause и оптимальная точка рефакторинга не обязаны совпадать | Engineering hypothesis | Medium | Refactor-point model |
| C4 | После локального изменения агенту нужна восходящая проверка затронутых родительских инвариантов | Safety design principle | High | FCRP verification rule |

Ключевые положения статьи являются архитектурной моделью и инженерной гипотезой, а не утверждением о завершённой эмпирической валидации FCRP как стандарта.

---

## Масштаб как первая координата

Представим иерархию:

```text
Вселенная
└── Галактика
    └── Солнечная система
        └── Планета
            └── Экосистема
                └── Организм
                    └── Клетка
                        └── Молекула
```

Программная система может быть представлена аналогично:

```text
Business
└── Product
    └── Project
        └── Service
            └── Module
                └── Component
                    └── Function
                        └── State Transition
```

Каждый уровень — самостоятельная система с собственным смыслом, контрактами, инвариантами, историей и зависимостями.

Поэтому агент не обязан начинать анализ с верхнего уровня.

Он должен найти **минимальную систему, которая полностью содержит наблюдаемую проблему**.

Если проблема находится на уровне Солнечной системы, сначала исследуется идея Солнечной системы.

Если нарушение локализовано на Земле — агент спускается до Земли.

Если объяснение требует уровня бактерии — тот же причинный цикл запускается для бактерии.

---

## Idea как точка входа

Для выбранного уровня `L` агент сначала восстанавливает:

```text
Idea(L)
```

Он должен ответить минимум на пять вопросов:

```text
WHY does L exist?
WHAT must L accomplish?
WHAT must never happen?
WHO depends on L?
WHAT does parent(L) expect from L?
```

Из этого формируются:

- Purpose;
- Expected Outcome;
- Invariants;
- Boundaries;
- Parent Contract.

Например, для платёжного исполнения идея может выглядеть так:

```text
одна логическая покупка
→ максимум одно экономическое списание
→ повтор безопасен
→ отказ не мутирует ledger
→ результат доказуем
```

Это значительно сильнее, чем просто изучить текущую функцию `executePayment()`.

---

## Вторая координата — время

Текущий код — только один кадр фильма.

FCRP рассматривает исследуемый объект сразу через четыре модели:

```text
IDEA
PAST
PRESENT
FUTURE
```

То есть:

```text
Past ←──── Present ────→ Future
             ↑
            Idea
```

**Past** отвечает на вопрос, какие решения привели систему сюда.

**Present** показывает, что реально существует сейчас.

**Future** задаёт траекторию, к которой система должна прийти.

**Idea** позволяет понять, не потерялся ли сам смысл объекта по дороге.

Это создаёт причинно-временной diff, а не обычное сравнение ожидаемого и фактического состояния.

---

## First Meaningful Divergence

После восстановления Idea, Past, Present и Future агент строит причинный граф:

```text
Idea
  ↓
Architecture
  ↓
Decision
  ↓
Implementation
  ↓
Runtime behavior
  ↓
Outcome
```

Главный объект поиска — **First Meaningful Divergence**: первая значимая точка, где реальная траектория перестала соответствовать ожидаемой.

Например:

```text
Idea
 ↓
API contract
 ↓
retry design       ← divergence
 ↓
worker
 ↓
payment provider
 ↓
ledger
 ↓
duplicate payment  ← symptom
```

Двойное списание видно в ledger.

Но если расхождение возникло в retry design, исправление ledger может убрать симптом и сохранить причину.

---

## Recursive Causal Zoom

FCRP делает навигацию рекурсивной.

Если текущий уровень объясняет симптом, но не механизм причины, агент идёт вниз:

```text
ZoomDown()
```

Если локальный механизм корректен, но его задача или контракт неверны, агент идёт вверх:

```text
ZoomUp()
```

Если причинный сигнал ведёт в соседнюю систему или dependency:

```text
FollowDependency()
```

Получается пространство движения:

```text
            ↑ CONTEXT
            │
DEPENDENCY ←●→ DEPENDENCY
            │
            ↓ MECHANISM
```

А поверх него существует временная ось:

```text
Past ←──── NOW ────→ Future
```

Поэтому пространство поиска можно выразить как:

```text
Scale × Time × Causality × Intent
```

---

## Фрактальность протокола

Один и тот же цикл применяется независимо от масштаба:

```text
FCRP(level):

    idea     = recover_idea(level)
    past     = reconstruct_history(level)
    present  = observe_current_state(level)
    future   = derive_future_target(level)

    gap = causal_diff(idea, past, present, future)

    if cause_is_below(level):
        return FCRP(relevant_child(level))

    if cause_is_above(level):
        return FCRP(parent(level))

    if cause_is_external(level):
        return FCRP(relevant_dependency(level))

    refactor_point = select_refactor_point(gap)
    simulate(refactor_point)
    authorize(refactor_point)
    apply(refactor_point)
    verify(level)
    verify_affected_parents(level)
```

Именно это делает подход фрактальным: алгоритм не меняется, меняется только масштаб исследуемой системы.

---

## Root cause ещё не означает Refactor Point

Даже если первопричина найдена, она не обязательно является лучшим местом для изменения.

FCRP отделяет:

```text
symptom_location
causal_location
refactor_location
```

Например:

```text
A → B → C → D → ERROR
```

Ошибка проявляется в `D`.

Неправильное решение возникло в `B`.

Но оптимальная точка ремонта может находиться между `B` и `C`, если там можно восстановить инвариант с меньшим риском для системы.

Кандидатов можно оценивать концептуально:

```text
Refactor Score =
    causal leverage
  × invariant restoration
  × downstream benefit
  × future alignment
  ÷ change risk
```

Цель:

> Минимальное изменение с максимальным причинным воздействием.

---

## Сначала симуляция, потом изменение

Автономный агент не должен переходить напрямую от объяснения к редактированию.

Перед изменением он моделирует последствия:

```text
Candidate Fix
     ↓
simulate
     ├── child effects
     ├── sibling effects
     ├── parent effects
     ├── dependencies
     ├── invariants
     └── future architecture
```

Безопасный цикл выглядит так:

```text
Observe
  ↓
Understand
  ↓
Explain
  ↓
Simulate
  ↓
Authorize
  ↓
Change
  ↓
Verify
```

Это разделяет способность агента **понимать изменение** и его право **внести изменение**.

---

## Анализируй локально, проверяй глобально

Представим, что проблема найдена на уровне бактерии.

Исправление бактерии само по себе ещё не доказывает безопасность ремонта.

Необходимо проверить затронутые родительские уровни:

```text
Bacteria ✓
    ↑
Cell ✓
    ↑
Organism ✓
    ↑
Ecosystem ✓
```

Но агенту не нужно каждый раз проверять всю Вселенную.

Восходящую проверку можно остановить, когда одновременно выполнены условия:

```text
parent invariants preserved
AND
no affected cross-boundary dependency
AND
causal propagation stopped
AND
explanation complete
```

Отсюда следует один из базовых принципов FCRP:

> **Анализируй локально. Проверяй глобально настолько далеко, насколько распространяется причинный эффект изменения.**

---

## Causal model

Базовый механизм FCRP:

```text
problem
  ↓
locate scale
  ↓
recover idea
  ↓
reconstruct past / observe present / model future
  ↓
causal diff
  ↓
first meaningful divergence
  ↓
zoom down / zoom up / follow dependency
  ↓
select refactor point
  ↓
simulate impact
  ↓
authorize change
  ↓
repair
  ↓
local verification
  ↓
upward system verification
  ↓
evidence
```

### Alternative explanations

- Для многих локальных дефектов обычного root-cause analysis достаточно; FCRP может быть избыточен.
- Идея системы может быть неоднозначной, конфликтующей или плохо документированной, поэтому `Idea(L)` иногда приходится выводить из контрактов, истории и наблюдаемого поведения.
- First Meaningful Divergence не всегда единственна: сложные системы могут иметь несколько независимых причинных ветвей.
- Симуляция будущего состояния остаётся моделью, а не доказательством отсутствия всех возможных регрессий.

---

## Timeline

| Date | Event | Evidence |
|---|---|---|
| 2026-08-14 | Сформулирована рекурсивная модель анализа через Idea → Past → Present → Future | RESONANCE working model |
| 2026-08-14 | Добавлены Scale × Time × Causality × Intent и First Meaningful Divergence | FCRP v0.1 |
| 2026-08-14 | Модель оформлена как Fractal Causal Refactoring Protocol | This article |

---

## Uncertainty

FCRP v0.1 — проектируемый протокол, а не завершённый отраслевой стандарт.

Открытые вопросы:

- как машинно восстанавливать `Idea(L)` при конфликтующих источниках;
- как измерять causal leverage без чрезмерно дорогой симуляции;
- как выбирать глубину ZoomDown и границу ZoomUp;
- как формально определять момент остановки восходящей проверки;
- как доказательно отделять корреляцию в истории изменений от причинного расхождения;
- как оценивать несколько competing refactor points.

Сильнейшее подтверждение модели должно прийти не из красивой схемы, а из повторяемых benchmark cases, где FCRP находит более раннюю причинную точку и предотвращает регрессию лучше локального fix-first подхода.

---

## Verification

- [x] Causal language reviewed
- [x] Protocol claims separated from empirical facts
- [x] Alternative explanations included
- [x] Examples labelled as conceptual / illustrative
- [x] Timeline checked
- [x] No synthetic example presented as market evidence
- [ ] FCRP benchmark suite implemented
- [ ] Cross-project empirical validation completed

---

## Implications

### First-order

AI coding agents могут получить отдельный этап **scope localization + causal navigation** перед изменением кода.

### Second-order

Если модель работает, evidence layer для AI engineering должен хранить не только diff и test result, но также:

- выбранный уровень анализа;
- Idea / invariants этого уровня;
- causal ancestors;
- First Meaningful Divergence;
- alternative refactor points;
- impact simulation;
- границу восходящей проверки.

### Who wins / who loses

Выигрывают системы, где цена неправильного локального исправления высока: финансовые state machines, distributed systems, autonomous agents, policy engines, critical infrastructure и сложные multi-service продукты.

Проигрывает скорость в тех случаях, где проблема тривиальна и дополнительный causal pass не даёт полезной информации. Поэтому FCRP должен включаться адаптивно, а не превращаться в обязательный ритуал для каждой опечатки.

---

## What to watch next

Следующие сигналы для проверки гипотезы:

1. benchmark cases, где symptom location и causal location различаются;
2. случаи, где root cause и лучший refactor point различаются;
3. измерение числа предотвращённых downstream-регрессий;
4. стоимость causal navigation по времени и вычислениям;
5. качество автоматического восстановления Idea и invariants;
6. переносимость протокола между кодом, инфраструктурой, agent workflows и финансовыми state transitions.

---

## Action

Практический следующий шаг для разработчиков agent infrastructure:

```text
Problem
→ Locate Scope
→ Recover Idea
→ Past / Present / Future
→ Causal Diff
→ First Meaningful Divergence
→ Refactor Point
→ Simulate
→ Authorize
→ Change
→ Verify Upward
→ Evidence
```

Не заменяйте существующие тесты этим циклом.

Используйте его как слой, который отвечает на более фундаментальный вопрос: **что именно мы собираемся чинить и почему это правильное место вмешательства?**

---

## Hot Question

> **Если завтра автономный AI-агент получит право самостоятельно рефакторить вашу production-систему, что он должен доказать перед изменением: только наличие локального бага — или ещё то, что он нашёл правильный причинный уровень и понимает последствия ремонта для всей системы?**

### Workflow prompts

- **Actor / agent:** Что агент может менять самостоятельно?
- **Failure:** Какой локально корректный fix способен повредить систему целиком?
- **Impact:** Какова цена неправильного уровня рефакторинга?
- **Current workaround:** Как команда сегодня ищет такие причины?
- **Trust condition:** Что должно быть доказано до того, как агенту разрешат применить fix?

### CTA

**Опишите один реальный workflow, где баг проявился в одном месте, а причина находилась на другом уровне системы →**

---

**RESONANCE verification chain:**

**Signal → Claim → Evidence → Cause → Timeline → Uncertainty → Verification → Implication → Action**

**FCRP chain:**

**Scale → Idea → Past → Present → Future → Divergence → Refactor → Simulation → Change → System Verification → Evidence**

---

## Implementation Update — 2026-08-14

После исходной публикации FCRP был реализован как минимальный machine-readable protocol в ContractGraph-QA и начал применяться к собственной инфраструктуре.

Canonical implementation:

- [ContractGraph-QA PR #49 — FCRP Core v0.1 + SELF-001](https://github.com/safal207/ContractGraph-QA/pull/49)
- merge commit: `b87a8ada5eefef975e551262b112440ea7a0aec4`
- [`contractgraph_qa/fcrp.py`](https://github.com/safal207/ContractGraph-QA/blob/main/contractgraph_qa/fcrp.py)
- [FCRP v0.1 protocol documentation](https://github.com/safal207/ContractGraph-QA/blob/main/docs/FRACTAL_CAUSAL_REFACTORING_PROTOCOL_V0_1.md)

Executable v0.1 сейчас machine-enforces:

```text
scope + idea
→ past / present / future
→ evidence refs
→ causal path
→ symptom point
→ First Meaningful Divergence
→ cause point
→ selected Refactor Point
→ UP / DOWN / SIDEWAYS / STOP
→ local verification
→ upward verification
→ explicit stop conditions
→ PASS / BLOCK
```

При этом исходная статья сознательно шире текущего executable core.

Пока остаются концептуальными или частично реализованными:

```text
full IdeaContract
├ purpose
├ expected outcome
├ invariants
├ forbidden outcomes
├ dependencies
└ parent contract

autonomous causal discovery
Refactor Score
impact simulation
separate authorization integration
cross-project causal propagation
typed time semantics
```

### Важная разница между статьёй и v0.1

В исходной модели остановка ZoomUp требует:

```text
parent invariants preserved
AND
no affected cross-boundary dependency
AND
causal propagation stopped
AND
explanation complete
```

Минимальный executable v0.1 пока проверяет отдельно:

```text
parentInvariantsPreserved
crossBoundaryEffectsAbsent
causalExplanationComplete
```

`causalPropagationStopped` ещё не является отдельным machine-enforced field. Это один из прямых кандидатов для FCRP v0.2.

### Что уже произошло после публикации

FCRP был применён к нескольким уровням собственной системы:

```text
SELF-001 — verification test proved the wrong boundary
SELF-002 — local PASS, parent invariant FAIL → BLOCK
SELF-003 — wall-clock oracle confused with protocol-time → BLOCK + reframe
SELF-005 — ProofPath Canonical Reality Drift
SELF-006 — CML historical verified ≠ current applicability
SELF-007 — LiminalDB provenance identity ≠ semantic compatibility identity
SELF-008 — RINSE domain interpretation ≠ shared semantic authority
```

Часть этих результатов уже promoted в canonical `main`, часть остаётся исследовательской и поэтому не представляется как завершённая внешняя валидация.

Текущий статус исходных verification goals:

- [x] Minimal executable FCRP core implemented
- [x] Repeatable self-benchmark cases implemented
- [x] Cross-repository self-validation started and produced canonical repository changes
- [ ] Independent third-party replication completed
- [ ] Controlled comparison against non-FCRP debugging completed
- [ ] Autonomous root-cause discovery demonstrated

Полный field report с evidence и новыми классами divergence опубликован отдельно:

**[Article 06 — The System That Refactored Itself](06-the-system-that-refactored-itself.md)**

Это сохраняет Article 05 как origin document и одновременно делает видимой эволюцию гипотезы:

```text
Article 05
conceptual FCRP
      ↓
executable v0.1
      ↓
self-tests
      ↓
repository-wide causal governance
      ↓
Article 06
field evidence + FCRP v0.2 directions
```
