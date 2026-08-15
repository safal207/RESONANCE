# Evidence Must Bind the Transition — почему AI-системе недостаточно доказательства, если оно не связано с конкретным переходом

**Article ID:** I001-RN-EBT  
**Deck:** CrewAI use-time revalidation и LangGraph cancellation durability независимо пришли к одной архитектурной границе: корректный PASS, известный persistence outcome и правильный happens-before ещё не доказывают, что именно это evidence occurrence относится именно к этому consequential transition. Следующий trust primitive — explicit causal binding между доказательством и изменением состояния.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · Evidence-Bound Transition / Execution Binding / Terminality Binding / Receipt Causality

---

## Signal

В двух независимых публичных discussion за один день проявился один и тот же failure shape.

В `crewAIInc/crewAI#4877` граница выглядела так:

```text
historical verification
        ↓
use-time revalidation
        ↓
execution
```

В `langchain-ai/langgraph#5672` — так:

```text
cancellation accepted
        ↓
persistence outcome established
        ↓
terminal interrupted state
```

На поверхности это разные проблемы: authorization против cancellation/recovery.

Но структурно они одинаковы.

Система может иметь **правильное доказательство**, а затем использовать его для перехода, к которому оно уже не относится или никогда не было явно привязано.

Отсюда основной invariant Article 13:

> **A consequential state transition must be causally bound to the evidence occurrence that authorizes, validates, or settles that transition.**

Коротко:

> **Evidence must bind the transition.**

---

## Valid evidence is not enough

Обычная verification-модель часто заканчивается на:

```text
verify(x) == PASS
```

Но agent runtime существует во времени.

Между `PASS` и `ACT` могут измениться:

- state;
- authority;
- policy;
- tool arguments;
- resource version;
- cancellation state;
- selected execution occurrence;
- ownership epoch;
- durable frontier;
- external world.

Поэтому:

```text
valid at T1
!=
automatically authorized at T2
```

Issue 001 уже накопил несколько близких правил:

```text
correct knowledge != current authority
historically valid consent != current execution authority
historically verified != currently applicable
```

Article 13 добавляет ещё одно:

```text
valid evidence != evidence bound to this transition
```

Даже если evidence всё ещё корректно, runtime должен знать, **какой конкретный transition occurrence имеет право его потребить**.

---

## CrewAI: ELR-I9 — Execution Binding

В публичном `crewAIInc/crewAI#4877` `babyblueviper1` сообщил, что проверил exact head, green conformance CI, тестовые файлы и непосредственно прочитал `revalidate_receipt_for_use()`.

По его отчёту, `verify_receipt()` остался историческим, а новая use-time path реально перепроверяет выбранные edges через current context.

Это закрывает старый seam:

```text
receipt valid when created
        ↓
world changes
        ↓
old receipt reused blindly
```

Но сразу появляется следующий TOCTOU:

```text
T1: context = version N
T2: revalidation PASS against N
T3: context becomes N+1
T4: execution proceeds using PASS from T2
```

На T2 verdict был корректным.

На T4 его operational authority уже не доказана.

Поэтому в треде был предложен следующий invariant:

### ELR-I9 — Execution Binding

> A successful use-time revalidation may authorize only the specific execution occurrence/context it was bound to.

Практическая форма:

```text
read version N
        ↓
validate against N
        ↓
issue use_token(context_digest=N)
        ↓
consume only if current context is still N
```

Если version сдвинулся:

```text
BLOCK
  -> revalidate again
```

Это structurally похоже на optimistic concurrency / compare-and-swap, но объектом CAS становится не только data state.

Объектом проверки становится **право использовать verification result**.

Отсюда сильная формула:

> **A verified fact is not necessarily a valid permission to act.**

---

## LangGraph: `C < P < T` is necessary but not sufficient

В `langchain-ai/langgraph#5672` cancellation обсуждается как граница между user-visible stream state, durable state и terminal lifecycle state.

`atomicdjt` предложил testable happens-before:

```text
C = cancellation accepted
P = bounded persistence/drain outcome established
T = terminal interrupted state published

assert C < P < T
```

Это важный контракт.

Другой client не должен увидеть terminal `T`, пока persistence consequence cancellation остаётся неизвестным.

`P` при этом не обязано означать идеальный flush.

Оно может честно быть:

```text
durable
partial
abandoned
```

Но temporal ordering оставляет дополнительный вопрос.

Представим recovery state:

```text
P17 = partial
P18 = durable
T9  = interrupted
```

Какой именно `P` делает `T9` доказуемым?

Одного факта `P < T` недостаточно при concurrency, retries, duplicate delivery или нескольких cancellation occurrences.

Поэтому появляется более строгий primitive:

### Terminality Binding

```text
CancellationReceipt {
  cancellation_id
  cause
  persistence_outcome
  last_visible_seq
  last_durable_seq
  persistence_receipt_id
}

TerminalTransition {
  state: interrupted
  cancellation_id
  persistence_receipt_id
}
```

Теперь `T` не просто произошло после какого-то `P`.

`T` **ссылается на конкретный persistence occurrence**, который делает terminal claim meaningful.

---

## Ordering is not causality

Если:

```text
E1 < E2 < E3
```

это ещё не доказывает:

```text
E2 authorized E3
```

или:

```text
E2 settled E3
```

Temporal order отвечает:

> что случилось раньше?

Causal binding отвечает:

> какой конкретный fact является основанием для этого конкретного transition?

Для agent/distributed systems нужны оба слоя:

```text
happens-before
        +
explicit evidence reference
        +
identity/version binding
        =
inspectable transition causality
```

Timestamp не является permission.

«Последний PASS» не является permission.

Ближайший предыдущий receipt не является settlement proof автоматически.

Нужна явная edge:

```text
Evidence occurrence E
        ─────────────▶
Transition occurrence X
```

---

## Evidence-Bound Transition

Назовём **Evidence-Bound Transition (EBT)** consequential transition, для которого runtime явно хранит evidence occurrences, необходимые для его текущей семантики.

Пример execution:

```yaml
transition_id: X42
transition_kind: execute_tool
logical_operation_id: O7
execution_id: E12
predecessor_state_ref: S91

required_evidence:
  - role: authorization
    receipt_id: A17
  - role: freshness
    receipt_id: F31

context_digest: H(N)
transition_status: committed
```

Пример terminal cancellation:

```yaml
transition_id: T9
transition_kind: publish_terminal_interrupted

required_evidence:
  - role: cancellation
    receipt_id: C4
  - role: persistence_settlement
    receipt_id: P18

terminal_status: interrupted
```

Article 13 не требует одинакового набора receipts для каждого transition.

Evidence roles зависят от transition type.

Но если safety/recovery semantics зависят от evidence, оно должно быть **addressable and bound**, а не просто находиться где-то рядом в audit log.

---

## Evidence roles should remain distinct

Полезно разделять хотя бы четыре роли.

### Authorization evidence

Отвечает:

> разрешено ли действие?

Примеры: human approval, policy allow, capability grant, preflight authorization.

### Freshness / admissibility evidence

Отвечает:

> остаётся ли ранее допустимое действие допустимым сейчас?

Примеры: current context digest, authority epoch, state version, `revalidate_if` predicates.

### Settlement / durability evidence

Отвечает:

> что runtime может доказать о завершении/устойчивости перехода?

Примеры: durable commit, partial persistence, abandoned write, external settlement confirmation.

### Outcome observation evidence

Отвечает:

> кто и с какой vantage наблюдал реальный outcome?

Это линия Article 04: decision provenance и outcome provenance — разные вопросы.

Один artifact может закрывать несколько ролей только если контракт **явно** это гарантирует.

---

## Execution Binding and Terminality Binding are one shape

CrewAI:

```text
use-time freshness F31
        ↓
execution X42

F31 ──authorizes-current-context──▶ X42
```

LangGraph:

```text
persistence outcome P18
        ↓
terminal transition T9

P18 ──settles-terminal-claim──▶ T9
```

Semantics разные.

Structure одна:

```text
specific evidence occurrence
        ↓ explicit causal binding
specific consequential transition
```

Именно поэтому это уже выглядит не как framework-specific fix, а как более общий agent-runtime invariant.

---

## Crash recovery becomes mechanical

Explicit references уменьшают количество recovery-guessing.

### Cancellation

```text
C exists
P missing
T missing
```

=> `indeterminate/recovery`, не terminal.

```text
C exists
P exists
T missing
```

=> recovery может idempotently опубликовать `T`, ссылаясь на exact `C/P`.

```text
T exists
referenced P missing
```

=> invalid/unreconciled terminal state.

### Execution

```text
F31 validates context N
context becomes N+1
X42 consumes token bound to N
```

=> stale binding, BLOCK/revalidate.

```text
A1 consumed by X1
X2 replays A1
```

=> BLOCK при one-shot policy; reusable semantics должны быть explicit, а не случайными.

Recovery перестаёт выбирать «ближайший подходящий PASS» и начинает идти по causal references.

---

## Semantic TOCTOU

Классический TOCTOU:

```text
check state
state changes
use stale result
```

Agent systems расширяют его:

```text
check meaning / authority / admissibility / durability
        ↓
world or occurrence identity changes
        ↓
use old proof as if it still referred to this transition
```

Race может жить между:

- approval и execution;
- revalidation и tool call;
- cancellation и terminal publication;
- commit и acknowledgement;
- authority check и mutation;
- evidence routing и evidence consumption;
- visible state и resume authority.

Не каждый такой seam можно сделать глобально atomic — особенно при external side effects.

Но даже без полной atomicity runtime может сделать boundary:

```text
explicit
versioned
rejectable
recoverable
```

Это намного сильнее, чем надеяться, что race window «достаточно маленький».

---

## A receipt is not magic

Наличие `receipt_id` само по себе ничего не доказывает.

Хороший contract должен определять:

```text
identity
scope
semantic role
context/version binding
lifetime/supersession
consumption semantics
failure behavior
recovery behavior
```

`use_token` полезен только если consumption реально сравнивает его binding с current context.

`persistence_receipt_id` полезен только если terminal transition проверяет, что receipt относится к тому же run/cancellation occurrence.

Иначе это просто новый string field.

---

## Conformance: test edges, not labels

Минимальный falsification suite:

### EBT-1 — stale after revalidation

```text
validate context N
mutate to N+1
consume token for N
```

Expected: BLOCK/revalidate.

### EBT-2 — wrong execution occurrence

```text
bind evidence to X1
consume from X2
```

Expected: BLOCK unless explicit transfer/reuse semantics.

### EBT-3 — one-shot replay

```text
consume A1 with X1
reuse A1 with X2
```

Expected: BLOCK under one-shot policy.

### EBT-4 — terminal without settlement

```text
T references P
P missing
restart
```

Expected: T is invalid/unreconciled.

### EBT-5 — settlement before crash

```text
C -> P -> crash before T
```

Expected: recovery can publish T idempotently from exact references.

### EBT-6 — wrong settlement occurrence

```text
C1 -> P1
C2 -> P2
T2 cites P1
```

Expected: invalid causal binding.

### EBT-7 — transport is not cancel

Network disconnect must not silently become an intentional cancellation transition.

### EBT-8 — supersession without erasure

Old evidence remains inspectable but no longer grants current transition authority.

---

## Relationship to Articles 08–12

Article 08:

```text
correct knowledge != current authority
```

Article 09:

```text
visible state != durable state != terminal lifecycle state
```

Article 10:

```text
semantic decision != authorization occurrence != execution occurrence
```

Article 11:

```text
proof obligations -> admissible evidence routes -> route selection
```

Article 12:

```text
recorded owner/relation != operationally reachable/executable relation
```

Article 13 связывает эти линии:

```text
evidence selected or produced
        ↓
exact evidence occurrence
        ↓
explicit causal binding
        ↓
exact consequential transition
```

То есть Article 13 — не ещё один verifier.

Это **binding layer between proof and change**.

---

## Compact protocol

```text
1. Identify consequential transition X.
2. Determine evidence roles required by X.
3. Resolve exact evidence occurrences, not only semantic labels.
4. Bind evidence to X + relevant version/context.
5. Re-check freshness at the last meaningful use boundary.
6. Consume/commit under explicit usage semantics.
7. Record outcome and settlement evidence separately.
8. Publish terminal/recovery state from explicit causal references.
9. Preserve superseded/rejected evidence as history without granting it current authority.
```

В одной строке:

```text
prove -> bind -> consume -> settle -> publish
```

Не:

```text
prove once -> carry PASS forever
```

---

## Core invariants

### EBT-I1 — Historical Separation
Historical verification semantics should remain stable rather than silently becoming time-dependent to solve freshness.

### EBT-I2 — Freshness Separation
Current admissibility should be explicit when relevant state can drift after historical verification.

### EBT-I3 — Execution Binding
A successful use-time check must not silently authorize a different execution occurrence or materially changed context.

### EBT-I4 — Terminality Binding
A terminal state whose meaning depends on persistence/settlement must reference the concrete settlement occurrence supporting it.

### EBT-I5 — Ambiguity Rejection
If exact occurrence matters and multiple evidence occurrences match one semantic reference, ambiguity must be surfaced rather than silently resolved.

### EBT-I6 — Supersession Without Erasure
Superseded evidence should remain inspectable but must not retain implicit current authority.

### EBT-I7 — Recovery from References
Recovery should prefer explicit causal references over timestamps, adjacency and “latest PASS” heuristics.

---

## Non-claims

Article 13 does not claim:

- official CrewAI adoption of `ELR-I9`;
- official LangGraph adoption of Terminality Binding;
- that community proposals are vendor guarantees;
- that every transition requires cryptographic receipts;
- that evidence binding provides distributed transaction atomicity;
- that one-shot authorization is universal;
- that causal references eliminate all race conditions;
- that timestamps are useless;
- that partial streamed output should become a normal checkpoint;
- that transport disconnect and explicit cancel should share lifecycle semantics.

The narrow claim is:

> **When a consequential transition depends on a specific authorization, freshness, durability or settlement fact, the system should be able to prove which exact evidence occurrence belongs to which exact transition occurrence. Temporal proximity and an unbound PASS are not equivalent to that proof.**

---

## Closing

Early trust layers looked like filters:

```text
check
  ↓
ALLOW / DENY
```

Autonomous systems need a longer chain:

```text
historical truth
        ↓
current admissibility
        ↓
execution-bound authorization
        ↓
consequential transition
        ↓
settlement evidence
        ↓
evidence-bound terminal/recovery state
```

CrewAI exposed the danger of letting a successful revalidation float free from execution.

LangGraph exposed the danger of letting a terminal state float free from persistence outcome.

Это одна и та же архитектурная форма.

> **A verified fact is not necessarily permission to act.**

> **A terminal label is not necessarily proof that the transition settled.**

> **Evidence becomes operational only when the system can show which transition it belongs to.**

---

**RESONANCE — Issue 001: The Age of Agents**  
**Article 13 — Evidence Must Bind the Transition**
