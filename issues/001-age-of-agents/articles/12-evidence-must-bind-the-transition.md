# Evidence Must Bind the Transition — почему AI-системе недостаточно доказательства, если оно не связано с конкретным переходом

**Article ID:** I001-RN-EBT  
**Deck:** Два независимых публичных треда — CrewAI о use-time revalidation и LangGraph о cancellation durability — пришли к одной и той же архитектурной границе. Проверка может быть корректной, persistence outcome может быть известен, порядок событий может быть правильным — и всё равно система остаётся небезопасной, если consequential transition не связан с конкретным evidence occurrence, которое его разрешило или сделало его terminal claim доказуемым.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · Evidence-Bound Transition / Execution Binding / Terminality Binding / Receipt Causality

---

## Signal

За один день в двух разных agent-system discussions проявился один и тот же failure shape.

В CrewAI-thread вопрос был об authorization и use-time freshness:

```text
historical verification
        ↓
current revalidation
        ↓
execution
```

В LangGraph-thread вопрос был о cancellation и persistence:

```text
cancellation accepted
        ↓
persistence outcome established
        ↓
terminal interrupted state
```

На поверхности это разные темы.

Одна — о том, можно ли выполнить действие после проверки.

Другая — о том, можно ли объявить run терминально interrupted после cancel.

Но обе сводятся к одной более общей проблеме:

> **Доказательство может существовать отдельно от перехода, который на него опирается.**

Именно этот разрыв создаёт класс ошибок, который можно назвать **unbound evidence transition**.

Система знает правильный факт.

Но не может доказать, что **именно этот факт** был тем evidence occurrence, на основании которого **именно этот state transition** был разрешён, потреблён или опубликован.

Отсюда основной инвариант Article 12:

> **A consequential state transition must be causally bound to the evidence occurrence that authorizes, validates, or settles that transition.**

Короткая форма:

> **Evidence must bind the transition.**

---

## Correct evidence can still be operationally unsafe

Обычная verification-модель часто заканчивается на таком утверждении:

```text
verify(x) == PASS
```

В static software этого нередко достаточно.

Но agent runtime живёт во времени.

Между:

```text
PASS
```

и:

```text
ACT
```

могут измениться:

- state;
- authority;
- policy;
- arguments;
- selected route;
- external resource version;
- cancellation status;
- execution attempt;
- ownership;
- durable frontier;
- observable world.

Поэтому верное утверждение в момент `T1` не является автоматически действующим authorization fact в `T2`.

Это уже появлялось в Issue 001 в разных формах:

```text
correct knowledge != current authority
historically valid consent != current execution authority
historically verified != currently applicable
```

Article 12 добавляет ещё один слой:

```text
valid evidence != evidence bound to this transition
```

Даже если evidence остаётся valid, система должна знать **какой переход его потребляет**.

---

## CrewAI: from historical validity to execution binding

В публичном discussion `crewAIInc/crewAI#4877` участники последовательно сузили authorization boundary.

Сначала важным стало различие между historical verification и use-time validity.

Реализация, обсуждаемая в треде, сохранила `verify_receipt()` как историческую проверку и добавила отдельную use-time revalidation path, которая повторно проверяет выбранные edges против `current_context`.

Публичный комментарий `babyblueviper1` сообщает, что он отдельно проверил exact head, green conformance CI, тестовые файлы и непосредственно прочитал `revalidate_receipt_for_use()`. Его вывод: freshness primitive действительно стала reachable и проверяется в use-time path, а не только описана на уровне design.

Это закрывает один gap:

```text
receipt was valid when created
        ↓
world changed
        ↓
old receipt reused blindly
```

Но почти сразу появился следующий.

Даже если система делает:

```text
revalidate(receipt, current_context) == PASS
```

между revalidation и реальным side effect может снова пройти время.

Получается новый TOCTOU:

```text
T1: context version = N
T2: revalidation PASS against N
T3: context version becomes N+1
T4: execution proceeds using PASS from T2
```

На T2 verdict был корректен.

На T4 его operational authority уже не доказана.

Поэтому в треде появился следующий proposed invariant:

### ELR-I9 — Execution Binding

```text
A successful use-time revalidation
may authorize only the specific execution occurrence/context
it was bound to.
```

Практическая форма:

```text
read version N
        ↓
validate against N
        ↓
issue use_token(context_digest=N)
        ↓
consume only if context still N
```

Если version/context сдвинулся:

```text
reject
  -> revalidate again
```

Это очень похоже на optimistic concurrency / compare-and-swap.

Но здесь CAS применяется не только к данным.

Он применяется к **праву использовать verification result**.

Отсюда сильная формулировка:

> **A verified fact is not necessarily a valid permission to act.**

---

## LangGraph: happens-before is necessary, but not sufficient

В `langchain-ai/langgraph#5672` обсуждается другой класс failure: пользователь видит streamed output, отменяет run, а durable graph state и terminal lifecycle могут находиться на другой границе.

Article 09 уже отделил:

```text
user-visible frontier
        !=
durable checkpoint frontier
        !=
terminal lifecycle state
```

Свежий комментарий `atomicdjt` предложил сделать cancellation boundary testable через happens-before:

```text
C = cancellation accepted
P = bounded persistence/drain outcome established
T = terminal interrupted state published

assert C < P < T
```

Это важный инвариант.

Другой client не должен наблюдать `T`, пока система ещё не знает persistence consequence cancellation.

Причём `P` не обязано означать полный успех.

Оно может честно сказать:

```text
durable
partial
abandoned
```

Смысл не в том, чтобы сохранить всё.

Смысл в том, чтобы **не публиковать terminal certainty раньше persistence knowledge**.

Но порядок `C < P < T` всё ещё оставляет один вопрос.

Представим, что recovery видит:

```text
P17 = partial
P18 = durable
T9  = interrupted
```

Какой именно persistence outcome делает `T9` доказуемым?

Одного timestamps/happens-before недостаточно.

Между событиями может быть concurrency, retry, duplicated delivery, восстановление после crash или несколько cancellation occurrences.

Поэтому следующая граница — **Terminality Binding**:

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

Теперь `T` не просто случилось после какого-то `P`.

`T` ссылается на **конкретный P**, который делает terminal claim meaningful.

---

## Ordering is not causality

Это центральное различие.

Пусть события произошли так:

```text
E1 < E2 < E3
```

Из этого ещё не следует:

```text
E3 was authorized by E2
```

или:

```text
E3 was settled by E2
```

Temporal order отвечает:

> что произошло раньше?

Causal binding отвечает:

> какой конкретный факт является основанием для этого конкретного перехода?

Для distributed/agent systems нужны оба слоя.

```text
happens-before
        +
explicit evidence reference
        +
identity / version binding
        =
inspectable transition causality
```

Timestamp сам по себе не является permission.

Ближайший предыдущий receipt сам по себе не является permission.

Последний известный PASS сам по себе не является permission.

Нужна явная edge:

```text
Evidence occurrence E
        ───────────────▶
Consequential transition X
```

---

## The general model: Evidence-Bound Transition

Назовём consequential transition любое изменение, после которого система, пользователь или внешний мир получают новое значимое состояние.

Примеры:

```text
execute tool
send payment
publish terminal state
resume run
commit mutation
approve external action
release escrow
change authority
retry side effect
promote evidence to accepted state
```

Минимальная модель:

```yaml
transition_id: X42
transition_kind: execute_tool
logical_operation_id: O7
execution_id: E12

predecessor_state_ref: S91
result_state_ref: S92

required_evidence:
  - role: authorization
    receipt_id: A17
  - role: freshness
    receipt_id: F31

context_digest: H(N)
transition_status: committed
```

Для terminal cancellation другой набор ролей:

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

Важно: Article 12 не утверждает, что каждый transition обязан иметь одинаковое число receipts.

Наоборот.

Evidence roles зависят от типа перехода.

Но если safety/recovery semantics требуют доказательства, оно должно быть **addressable and bound**, а не существовать где-то рядом в журнале.

---

## Four evidence roles that should not be collapsed

Одна из повторяющихся ошибок agent infrastructure — складывать разные epistemic/causal роли в один универсальный `verified=true`.

Полезно различать хотя бы четыре класса.

### 1. Authorization evidence

Отвечает:

> было ли действие разрешено?

Примеры:

```text
human approval
policy allow
capability grant
preflight authorization
```

### 2. Freshness / admissibility evidence

Отвечает:

> остаётся ли ранее разрешённое действие допустимым сейчас?

Примеры:

```text
context_digest still matches
resource version unchanged
authority epoch unchanged
revalidate_if predicates unchanged
```

### 3. Settlement / durability evidence

Отвечает:

> что система может доказать о результате перехода?

Примеры:

```text
commit durable
persistence partial
write abandoned
external settlement confirmed
```

### 4. Observation / outcome evidence

Отвечает:

> кто и с какой vantage наблюдал фактический outcome?

Это линия Article 04: decision provenance и outcome provenance не должны сливаться.

Один receipt иногда может закрывать несколько ролей, если контракт это явно гарантирует.

Но система не должна предполагать такое совпадение автоматически.

---

## Execution Binding and Terminality Binding are the same shape

Теперь можно положить CrewAI и LangGraph рядом.

### CrewAI shape

```text
historical receipt
        ↓
use-time revalidation F31
        ↓
execution X42

required edge:
F31 ──authorizes-current-context──▶ X42
```

### LangGraph shape

```text
cancel C4
        ↓
persistence outcome P18
        ↓
terminal transition T9

required edge:
P18 ──settles-terminal-claim──▶ T9
```

Семантика edges разная.

Структура одинаковая:

```text
meaningful evidence occurrence
        ↓ explicit causal binding
consequential state transition
```

Именно поэтому проблема уже не выглядит framework-specific.

Она похожа на общий architecture invariant для autonomous systems.

---

## Crash recovery becomes much cleaner

Explicit binding особенно полезен после crash.

Без binding recovery часто делает inference:

```text
"последний PASS был рядом — наверное, он относится к этому action"
```

или:

```text
"terminal state уже записан — наверное, persistence успел завершиться"
```

Это опасные предположения.

С explicit evidence IDs crash cases становятся механическими.

### Cancellation boundary

```text
C exists
P missing
T missing
```

Результат:

```text
indeterminate / recovery required
not terminal
```

---

```text
C exists
P exists
T missing
```

Результат:

```text
recovery may publish T idempotently
using the exact P reference
```

---

```text
T exists
referenced P missing
```

Результат:

```text
invalid terminal state
```

---

### Execution boundary

```text
F31 validates context N
use_token bound to N
context becomes N+1
X42 attempts consumption
```

Результат:

```text
reject stale binding
revalidate
```

---

```text
F31 already consumed by X42
X43 attempts replay
```

Если authorization policy one-shot:

```text
reject replay
```

Если reusable:

```text
require explicit reusable semantics
not accidental reuse
```

Таким образом recovery перестаёт угадывать intent по близости событий.

Он следует causal references.

---

## This is TOCTOU at the level of meaning

Классический TOCTOU:

```text
check file
        ↓
file changes
        ↓
use file assuming old state
```

Agent systems добавляют более широкий вариант:

```text
check meaning / authority / admissibility / durability
        ↓
world changes or execution occurrence changes
        ↓
use old proof as if it still referred to this transition
```

Это можно назвать **semantic TOCTOU**.

Объектом race становится не только byte state.

Race может происходить между:

- approval и execution;
- verification и consumption;
- cancellation и terminal publication;
- commit и acknowledgement;
- authority check и mutation;
- evidence selection и action;
- route validation и route execution;
- visible state и resume authority.

Общий антидот не всегда транзакция.

Во внешнем мире atomic transaction может быть невозможна.

Но даже без полной atomicity система может сделать boundary **explicit, versioned, rejectable and recoverable**.

Это намного сильнее, чем просто надеяться, что промежуток маленький.

---

## A receipt is not a magic token

Важно не превратить эту идею в культ receipts.

Наличие `receipt_id` ничего не доказывает само по себе.

Плохой дизайн:

```text
transition.evidence_ref = "something-pass-like"
```

Хороший contract должен определить:

```text
identity
scope
issuer / producer
semantic role
context/version binding
lifetime / supersession rules
consumption semantics
failure behavior
recovery behavior
```

Например, `use_token` полезен только если consumption проверяет:

```text
token.context_digest == current_context_digest
```

а не просто наличие token.

`persistence_receipt_id` полезен только если terminal transition ссылается на receipt того же cancellation occurrence/run boundary.

Иначе мы просто добавили ещё один string field.

---

## Fail closed on ambiguity, not on history

Evidence-bound design не требует стирать старые receipts.

Наоборот, historical records должны сохраняться.

Проблема не в том, что старый PASS существует.

Проблема в том, что старый PASS может получить **неявную текущую authority**.

Поэтому хороший runtime разделяет:

```text
historically valid
currently admissible
bound to this execution
consumed by this execution
superseded
revoked
settled
```

А при ambiguity:

```text
E1 and E2 both match semantic decision D
execution cites only D
```

нельзя выбирать первый/последний occurrence по удобству.

Нужно либо:

```text
resolve exact occurrence
```

либо:

```text
surface ambiguity / fail closed
```

Это продолжает линию Article 10: semantic identity и occurrence identity отвечают на разные вопросы.

---

## Conformance: test the edges, not the labels

Article 12 предлагает небольшой cross-runtime falsification suite.

### EB-1 — stale-after-revalidation

```text
validate context N
mutate context to N+1
attempt execution with token for N
```

Expected:

```text
BLOCK or explicit revalidation
```

### EB-2 — execution occurrence mismatch

```text
revalidate for execution X1
attempt to consume for X2
```

Expected:

```text
BLOCK unless contract explicitly authorizes transferable/reusable consumption
```

### EB-3 — replayed one-shot evidence

```text
consume authorization occurrence A1 with X1
retry X2 with same A1
```

Expected:

```text
BLOCK for one-shot policy
```

### EB-4 — terminal without settlement evidence

```text
persist terminal T
remove / never create referenced persistence P
restart
```

Expected:

```text
T is invalid / unreconciled
never silently authoritative
```

### EB-5 — settlement without terminal publication

```text
C
P
crash before T
restart
```

Expected:

```text
recovery can complete T idempotently from exact C/P pair
```

### EB-6 — wrong persistence occurrence

```text
C1 -> P1
C2 -> P2
T2 cites P1
```

Expected:

```text
BLOCK / invalid causal binding
```

### EB-7 — transport is not explicit cancel

```text
network disconnect
partial stream exists
```

Expected:

```text
transport lifecycle remains distinct
no automatic promotion to intentional cancellation history
```

### EB-8 — historical evidence remains inspectable

After supersession/rejection:

```text
old receipt still queryable
but no longer grants current transition authority
```

Expected:

```text
history preserved
operational authority denied
```

Этот suite специально проверяет **edges**, а не поля вроде `verified=true`.

---

## The transition graph

Если собрать Articles 04, 08, 09, 10, 11 и 12 вместе, agent action начинает выглядеть не как один function call, а как небольшой causal graph.

```text
intent
  ↓
authority state
  ↓
authorization occurrence
  ↓
evidence route
  ↓
use-time freshness receipt
  ↓
execution occurrence
  ↓
external / internal outcome
  ↓
outcome observation
  ↓
settlement / durability receipt
  ↓
terminal or resumable state
```

Не каждая система обязана материализовать каждый node.

Но опасно смешивать их семантически, когда failure modes зависят от различия.

Например:

```text
authorization occurrence
!=
execution occurrence
```

```text
execution occurrence
!=
outcome observation
```

```text
outcome observation
!=
settlement proof
```

```text
settlement proof
!=
terminal publication
```

```text
verification PASS
!=
execution-bound authorization
```

Эти различия и создают recoverable system вместо optimistic story.

---

## Why this matters for payments and irreversible tools

Чем дороже side effect, тем меньше можно полагаться на proximity и implicit state.

Представим agent payment:

```text
policy check PASS
        ↓
wallet balance / policy epoch changes
        ↓
agent retries
        ↓
old PASS reused
```

Или:

```text
payment submitted
        ↓
client disconnects
        ↓
local run state is ambiguous
        ↓
retry assumes nothing happened
```

В обоих случаях central question один:

> **Какой evidence occurrence разрешает следующий переход?**

Для execution это может быть fresh authorization binding.

Для retry — authoritative settlement/idempotency evidence.

Для terminal state — durability receipt.

Для recovery — exact predecessor and settlement chain.

Поэтому evidence-bound transitions естественно соединяются с предыдущими RESONANCE signals:

```text
commit != acknowledgement != retry permission
```

и:

```text
idempotency identity belongs to the logical operation
```

Receipt causality не заменяет idempotency.

Она показывает, **какое доказательство позволяет решить, можно ли делать следующий шаг**.

---

## Relationship to Articles 08–11

Article 12 не заменяет предыдущие contracts.

Он связывает их.

### Article 08 — Authority Has a History

```text
correct knowledge != current authority
```

Article 12 спрашивает:

```text
какой authority/freshness evidence occurrence связан с этой mutation?
```

### Article 09 — Cancellation Is a State Transition

```text
visible state != durable state != terminal lifecycle state
```

Article 12 добавляет:

```text
terminal lifecycle transition must cite the persistence outcome that settles it
```

### Article 10 — Consent Has a Causal Lifetime

```text
semantic decision != authorization occurrence != execution occurrence
```

Article 12 добавляет general form:

```text
authorization/freshness occurrence -> explicit edge -> execution transition
```

### Article 11 — Evidence Has a Route

```text
select sufficient/current/proportionate proof path
```

Article 12 добавляет финальную discipline:

```text
selected evidence route is not enough;
its resulting evidence must be bound to the transition that uses it
```

Именно поэтому Article 12 — не ещё один verification layer.

Это **binding layer между verification и change**.

---

## A compact protocol

Самая короткая operational form:

```text
1. Identify the consequential transition X.
2. Determine which evidence roles X requires.
3. Resolve exact evidence occurrences, not only semantic labels.
4. Bind evidence to X + relevant context/version.
5. Re-check freshness at the last meaningful use boundary.
6. Consume / commit under the declared usage semantics.
7. Record the result and settlement evidence separately.
8. Publish terminal/recovery state only from explicit causal references.
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

Historical verification semantics MUST remain stable and should not silently become time-dependent merely to solve freshness.

### EBT-I2 — Freshness Separation

Use-time admissibility MUST be represented separately when the world may change after historical verification.

### EBT-I3 — Execution Binding

A successful use-time check MUST NOT authorize an unrelated execution occurrence or materially changed context unless the contract explicitly permits that transfer.

### EBT-I4 — Terminality Binding

A terminal state whose meaning depends on persistence/settlement MUST reference the concrete persistence/settlement occurrence that supports it.

### EBT-I5 — Ambiguity Rejection

If multiple evidence occurrences could satisfy a semantic reference and the exact occurrence matters, the system MUST surface ambiguity rather than silently choose one.

### EBT-I6 — Supersession Without Erasure

Superseded evidence SHOULD remain inspectable but MUST NOT silently retain current transition authority.

### EBT-I7 — Recovery from References

Crash recovery SHOULD reconstruct admissible transitions from explicit causal references rather than timestamps, adjacency or “latest PASS” heuristics alone.

---

## The deeper pattern

Agent infrastructure постепенно переходит от хранения объектов к хранению **отношений между доказуемыми событиями**.

Недостаточно знать:

```text
there was an approval
there was a verification
there was a persistence event
there was a terminal state
```

Нужно знать:

```text
this approval authorized this execution
this freshness check was consumed by this execution
this persistence outcome settled this cancellation
this settlement receipt justified this terminal publication
```

То есть trust layer становится не таблицей флагов.

Он становится **causal evidence graph**.

И здесь появляется очень простой принцип:

> **The system may forget convenience. It must not forget why a consequential transition was allowed to become real.**

---

## Non-claims

Article 12 не утверждает:

- что CrewAI официально принял `ELR-I9`;
- что LangGraph официально принял Terminality Binding;
- что описанные community proposals являются vendor guarantees;
- что every agent transition обязан использовать cryptographic receipt;
- что causal references дают distributed transaction atomicity;
- что timestamps бесполезны;
- что one-shot consumption подходит для любого authorization model;
- что explicit binding устраняет все race conditions;
- что любой partial state должен быть сохранён как normal checkpoint;
- что transport disconnect и explicit cancel должны иметь одинаковую recovery policy.

Узкий claim статьи:

> **Когда consequential transition зависит от конкретного authorization, freshness, durability или settlement evidence, система должна уметь доказать связь между exact evidence occurrence и exact transition occurrence. Порядок событий и наличие PASS рядом с переходом сами по себе этой связи не доказывают.**

---

## Closing

В ранних agent systems trust часто выглядел как фильтр:

```text
check
  ↓
allow / deny
```

Теперь становится видно, что real-world autonomy требует более длинной цепи:

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
evidence-bound terminal / recovery state
```

Каждый переход между этими слоями — потенциальный seam.

И два независимых публичных треда показали один и тот же урок с разных сторон.

В одном случае PASS нельзя отпускать свободно от execution.

В другом terminal state нельзя отпускать свободно от persistence receipt.

Поэтому следующий trust primitive — не ещё один verifier.

Это **causal binding**.

> **A verified fact is not necessarily permission to act.**

> **A terminal label is not necessarily proof that the transition settled.**

> **Evidence becomes operational only when the system can show which transition it belongs to.**

---

**RESONANCE — Issue 001: The Age of Agents**  
**Article 12 — Evidence Must Bind the Transition**
