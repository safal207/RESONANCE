# Consent Has a Causal Lifetime — почему approval AI-агента должно иметь доказуемую границу потребления

**Article ID:** I001-RN-CCL  
**Deck:** Самая опасная кнопка в автономной системе — не `Execute`, а `Approve`, если runtime не может доказать, что именно это разрешение было выдано для именно этого действия, осталось актуальным к моменту исполнения и было потреблено ровно тем execution occurrence, который реально совершил side effect.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · Causal Consent / Authorization Occurrence / Consumption Boundary

---

## Самая опасная кнопка — `Approve`

Представим простой интерфейс.

AI-агент хочет выполнить действие:

```text
send_payment(amount=100, recipient=B)
```

Система показывает человеку запрос.

Человек нажимает:

```text
APPROVE
```

На первый взгляд всё закончено.

Есть человек.
Есть разрешение.
Есть действие.

Но между нажатием кнопки и реальным side effect может пройти минута, час или сутки.

За это время:

- изменились аргументы;
- изменился recipient;
- изменилась policy;
- изменился account state;
- authority была revoked;
- операция была retried;
- старый worker восстановился после crash;
- появился новый execution attempt;
- первоначальное разрешение уже было использовано;
- тот же semantic decision был выпущен повторно как отдельное signed occurrence.

И вот здесь возникает вопрос, который обычная модель `ALLOW | DENY` почти не задаёт:

> **Что именно человек разрешил — смысл действия, конкретный authorization event или конкретное исполнение?**

Это три разных объекта.

Если система их не различает, кнопка `Approve` может незаметно превратиться из разрешения на одно действие в переносимую фразу:

> «Когда-то действие такого типа было разрешено».

Для автономной системы этого недостаточно.

**Consent is not a timeless boolean. Consent has a causal lifetime.**

---

## Signal

В публичном треде `crewAIInc/crewAI#4877` изначально обсуждался компактный provider-agnostic контракт для pre-tool-call authorization.

Базовая форма была простой:

```text
before_tool_call
    ↓
ALLOW | DENY
```

Затем обсуждение упёрлось в human approval.

Если решение требует человека или внешнего policy engine, нельзя держать coroutine или процесс открытым часами только ради ожидания.

`atomicdjt` предложил более durable модель:

```text
before_tool_call
  -> ALLOW | DENY | DEFER(decision_id, continuation_descriptor)

DEFER
  -> durable pending authorization
  -> typed tool_deferred outcome
  -> dependent work remains unsatisfied

external resolver
  -> resolve(decision_id, allow|deny)
  -> enqueue fresh continuation/replay
```

Это важный архитектурный сдвиг.

Human approval перестаёт быть паузой процесса и становится **durable workflow fact**.

Но тот же комментарий добавил более опасный failure mode:

```text
approve action A
        ↓
world changes
        ↓
framework later executes materially different A'
        ↓
stale consent reused
```

Предлагаемая защита — bind pending decision к digest как минимум от:

```text
tool_name
normalized_args
agent / crew identity
policy version
relevant state / version
```

и повторно проверять binding при resolve.

Почти одновременно `babyblueviper1` проследил другой seam в реальном ledger implementation, обсуждаемом в том же треде: semantic `decision_ref` мог соответствовать нескольким различным signed decision events.

По его публичному отчёту, один semantic decision identifier не позволял независимо доказать, **какое именно occurrence** было тем authorization event, к которому относится outcome.

Отсюда появился второй принцип:

```text
semantic decision identity
        !=
signed decision occurrence
```

А существующий AG2 proposal `ag2ai/ag2#3156` уже отделял:

```text
logical_operation_id
        !=
execution_id
```

и содержал `revalidate_if`: явные условия, изменение которых делает preflight verdict непригодным для исполнения даже до формального expiry.

Эти три линии сходятся в одну более общую модель.

---

## The missing object: authorization consumption

Большинство authorization systems умеют ответить хотя бы на часть следующих вопросов:

```text
1. Что было разрешено?
2. Кто разрешил?
3. Когда разрешил?
4. По какой policy?
```

Но для autonomous execution появляется пятый вопрос:

> **Какое конкретное execution occurrence потребило это разрешение?**

Это не bookkeeping detail.

Это последняя causal edge между permission и side effect.

Рассмотрим:

```text
decision_ref = D
```

`D` может означать:

```text
ALLOW tool=X args=Y under policy=P
```

Но один и тот же semantic decision может быть выпущен дважды:

```text
E1 -> decision_ref D
E2 -> decision_ref D
```

Одинаковый смысл.

Разные signed events.

Теперь появляется execution:

```text
X7 -> side effect
```

Если audit record хранит только:

```text
X7 cites D
```

независимый verifier не всегда может доказать:

```text
E1 authorized X7
```

а не:

```text
E2 authorized X7
```

или вообще:

```text
D merely describes a compatible semantic decision
```

Поэтому одного semantic ref недостаточно.

Нужен отдельный causal edge:

```text
authorization occurrence
        ↓
consumed by
        ↓
execution occurrence
```

---

## Three identities that must not collapse

Минимальная модель должна различать три identity classes.

### 1. Semantic decision identity

Отвечает:

> Что означает решение?

Например:

```text
decision_ref = hash(
  intent,
  policy_version,
  verdict,
  bounded context
)
```

Это удобно для deduplication, recomputation и сравнения одинаковых logical decisions.

Но semantic identity не обязана быть уникальной во времени.

---

### 2. Authorization occurrence identity

Отвечает:

> Какое конкретное решение было фактически выпущено?

Например:

```text
decision_event_id
issued_at
issuer / signer
signature
precedence anchor
```

Два occurrence могут иметь один `decision_ref`.

```text
E1.semantic_ref = D
E2.semantic_ref = D
E1 != E2
```

Это не collision в смысле ошибки hash function.

Это нормальное различие между:

```text
same meaning
```

и:

```text
same historical event
```

---

### 3. Execution occurrence identity

Отвечает:

> Какое конкретное исполнение произошло?

```text
logical_operation_id = L
execution_id = X1
```

Retry может породить:

```text
logical_operation_id = L
execution_id = X2
```

То есть:

```text
logical operation identity
        !=
execution occurrence identity
```

И теперь полный invariant становится:

> **Semantic identity != authorization occurrence != execution consumption.**

---

## Approval is not execution authority forever

Самая простая implementation mistake выглядит так:

```text
if approval.status == ALLOW:
    execute()
```

Но `ALLOW` — это исторический факт.

Execution требует текущего admissibility proof.

Между ними существует время.

А значит, существует drift.

```text
T0 proposal created
T1 authorization issued
T2 authorization deferred
T3 human resolves allow
T4 freshness revalidated
T5 tool executes
T6 side effect becomes observable
T7 outcome recorded
```

На любом участке может измениться мир.

Поэтому вопрос:

```text
Was it approved?
```

слабее вопроса:

```text
Was this exact execution still authorized at the moment its effect crossed the execution boundary?
```

---

## The hidden TOCTOU seam

`DEFER + resolve` убирает необходимость держать long-lived suspension.

`execution_scope_digest` может защитить от изменения tool name / arguments / actor / policy / relevant state.

`revalidate_if` может потребовать повторную проверку freshness-sensitive predicates.

Но даже после этого остаётся классический TOCTOU window:

```text
resolve approval
      ↓
verify digest
      ↓
revalidate state
      ↓
          WORLD CHANGES
      ↓
execute tool
```

Это означает:

> revalidation is not automatically equivalent to execution-time authorization.

Если revalidation и effect crossing — разные несвязанные операции, stale consent всё ещё может просочиться через последний промежуток.

Поэтому появляется отдельная boundary.

---

## Authorization Consumption Boundary

Назовём её **Authorization Consumption Boundary (ACB)**.

Это точка, в которой runtime должен fail-close подтвердить одновременно:

```text
1. exact authorization occurrence is known
2. semantic decision still matches proposed action
3. execution scope digest still matches
4. freshness predicates still hold
5. authority/policy state is still admissible
6. authorization has not already been consumed/revoked/superseded
7. this execution occurrence is the one consuming it
```

Концептуально:

```text
resolve approval
      ↓
resolve exact decision_event_id
      ↓
recompute execution_scope_digest
      ↓
revalidate freshness predicates
      ↓
consume authorization fail-closed
      ↓
execute tool
      ↓
record execution occurrence
```

В идеальной implementation consumption и начало irreversible effect находятся в одной transactional / compare-and-swap / capability-use boundary настолько близко, насколько позволяет конкретный runtime.

Это не означает, что все frameworks обязаны реализовать distributed transaction.

Это означает, что **разрыв должен быть явным и проверяемым**, а не скрытым за одним boolean `allow=True`.

---

## Consent as a state machine

Approval удобнее моделировать не boolean, а state transition system.

Например:

```text
PROPOSED
   ↓
DEFERRED
   ↓
RESOLVED_ALLOW
   ↓
REVALIDATED
   ↓
CONSUMED
```

Terminal / competing states:

```text
DENIED
EXPIRED
STALE
REVOKED
SUPERSEDED
CANCELLED
CONSUMED
```

Ключевое свойство:

```text
CONSUMED
```

не равно:

```text
ALLOW forever
```

Для one-shot authorization повторное consumption должно fail-close.

```text
E1 consumed by X1

retry X2 attempts to use E1
        ↓
BLOCKED
```

Если product действительно хочет reusable authorization, это должно быть отдельным явным contract:

```text
usage_policy:
  mode: reusable
  max_uses: 5
  scope: ...
  expires_at: ...
```

А не случайным свойством отсутствия поля `consumed_by`.

---

## Consent is a capability, not a memory

Полезная mental model:

```text
approval record
```

не должен вести себя как passive memory.

Он ближе к bounded capability.

Capability описывает не просто прошлую мысль человека или policy engine.

Она отвечает:

```text
who may do what
under which state
until when
how many times
for which execution scope
```

Тогда human approval становится не строкой:

```text
"approved": true
```

а machine-checkable object.

Например:

```yaml
decision_ref: sha256:...
decision_event_id: evt_...
status: resolved_allow

issuer_ref: human:42
policy_version: policy:v17

execution_scope_digest: sha256:...
logical_operation_id: op_...

revalidate_if:
  - account_balance_changed
  - recipient_binding_changed
  - policy_version_changed
  - authority_epoch_changed

usage_policy:
  mode: one_shot

consumed_by_execution_id: null
```

После execution:

```yaml
status: consumed
consumed_by_execution_id: exec_019
consumed_at: ...
```

Теперь audit trail может отвечать не только:

> Был ли approve?

но и:

> **Какой approve был использован каким execution, при каких still-valid conditions?**

---

## `DEFER` becomes ordinary workflow state

Это особенно хорошо сочетается с идеей `atomicdjt`.

Вместо special-case pause:

```text
agent coroutine waiting for human
```

получаем:

```text
ToolNode
   ↓
DEFERRED authorization
   ↓
durable unsatisfied dependency
```

Зависимый branch:

```text
requires(tool_result)
        ↓
NOT RUNNABLE
```

Независимый branch:

```text
no dependency on deferred result
        ↓
CAN CONTINUE
```

После deny:

```text
DENIED outcome
        ↓
dependency resolved explicitly as denied
```

После allow:

```text
fresh continuation
        ↓
ACB verification
        ↓
execution or fail-close
```

Human approval перестаёт быть необычной магией внутри guardrail hook.

Он становится нормальным stateful edge workflow graph.

---

## The stale-consent matrix

Чтобы контракт был полезным, его надо пытаться сломать.

### Case 1 — arguments changed after approval

```text
approved:
transfer(100, B)

execute:
transfer(1000, B)
```

Expected:

```text
execution_scope_digest mismatch
→ BLOCKED
```

---

### Case 2 — recipient changed

```text
approved:
recipient=B

execute:
recipient=C
```

Expected:

```text
BLOCKED
```

---

### Case 3 — same semantic decision, different signed occurrence

```text
E1 -> D
E2 -> D

outcome cites only D
```

Expected read-side behavior:

```text
occurrence ambiguous
```

not:

```text
pick first event silently
```

A consumable authorization should name the exact occurrence used.

---

### Case 4 — policy changed after human approval

```text
approved under policy v17
current policy v18
```

Expected depends on policy contract, but must be explicit:

```text
revalidate / supersede / block
```

never accidental reuse.

---

### Case 5 — authority revoked

```text
human approved
agent authority epoch = 17

later:
authority epoch = 18
owner changed
```

Even unchanged arguments are insufficient.

From Article 08:

> Correct knowledge does not imply current authority.

Here:

> **Valid historical consent does not imply current execution authority.**

---

### Case 6 — approval consumed once, retry occurs

```text
E1 consumed by execution X1
X1 acknowledgement lost
runtime retries as X2
```

The worst implementation does:

```text
approval == allow
→ execute again
```

A safer implementation asks independently:

```text
Did X1 already cross the side-effect boundary?
Was E1 already consumed?
Is retry authorized as a new execution occurrence?
```

This connects directly to the broader invariant:

```text
commit != acknowledgement != retry permission
```

---

### Case 7 — cancellation after approval, before execution

```text
approval resolved
        ↓
run cancelled
        ↓
old continuation wakes up
```

Article 09 established cancellation as a state transition rather than mere transport disappearance.

Therefore cancel may supersede pending execution authority.

Recovery must not silently resurrect the old approval path.

---

## A minimal framework-neutral contract

The goal is not to prescribe CrewAI internals.

A compact neutral model could look like:

```python
@dataclass
class AuthorizationOccurrence:
    decision_ref: str
    decision_event_id: str
    status: Literal[
        "deferred",
        "resolved_allow",
        "denied",
        "expired",
        "stale",
        "revoked",
        "superseded",
        "consumed",
    ]

    issuer_ref: str
    policy_version: str

    logical_operation_id: str
    execution_scope_digest: str
    revalidate_if: list[str]

    usage_mode: Literal["one_shot", "reusable"] = "one_shot"
    max_uses: int | None = 1

    consumed_by_execution_id: str | None = None
```

Execution proposal:

```python
@dataclass
class ProposedExecution:
    logical_operation_id: str
    execution_id: str
    tool_name: str
    normalized_args: dict
    actor_ref: str
    authority_ref: str | None
    relevant_state_refs: list[str]
```

Then the boundary can be expressed as:

```text
scope(execution) == authorization.execution_scope_digest
AND
freshness predicates hold
AND
authorization occurrence is current
AND
usage policy permits consumption
AND
execution has not been cancelled/superseded
```

Only after that:

```text
consume -> execute
```

---

## Why `decision_id` belongs even on synchronous allow/deny

The deferred case makes this obvious, but the principle generalizes.

A synchronous deny should be a fact.

A synchronous allow should be a fact.

A defer should be a fact.

```text
no execution happened
```

не означает автоматически:

```text
deny occurred
```

Точно так же:

```text
execution happened
```

не должно означать автоматически:

```text
some valid authorization must have existed
```

Поэтому `GuardrailDecision` выигрывает от stable:

```text
decision_id
status
policy / provenance metadata
```

даже когда всё произошло за миллисекунды.

Это делает authorization inspectable after the fact и не привязывает framework к конкретному policy engine или approval UI.

---

## The PLF-shaped shift: from permission to provenance

В начале кажется, что задача — просто добавить human approval.

Потом кажется, что задача — научиться ждать его без busy-wait.

Потом — bind arguments digest.

Но настоящая смена модели происходит позже.

Проблема не в том, чтобы **получить разрешение**.

Проблема в том, чтобы сохранить причинную цепочку от разрешения до effect:

```text
intent
  ↓
semantic decision
  ↓
authorization occurrence
  ↓
deferred/resolved state
  ↓
revalidation
  ↓
authorization consumption
  ↓
execution occurrence
  ↓
observed outcome
```

Именно тогда approval перестаёт быть UI feature.

Он становится частью verifiable execution protocol.

---

## Relationship to the previous RESONANCE articles

Article 07 сформулировал:

```text
recovered state
!=
recovered responsibility topology
```

Article 08 добавил:

```text
correct knowledge
!=
current authority
```

Article 09 добавил:

```text
older durable state
!=
automatic resume authority
```

Article 10 добавляет:

```text
historically valid consent
!=
current execution authorization
```

Вместе:

```text
recover state
      ↓
recover responsibility boundaries
      ↓
recover current authority
      ↓
resolve exact authorization occurrence
      ↓
revalidate execution scope + freshness
      ↓
consume authorization
      ↓
execute
      ↓
observe outcome independently
```

Это уже можно рассматривать как causal permission graph.

---

## Causal Permission Graph

Обычный audit log часто выглядит как список:

```text
12:01 approval
12:04 execution
12:05 success
```

Но timestamp proximity не доказывает causality.

Более сильная модель:

```text
Intent(I7)
   ↓ evaluated as
DecisionSemantic(D3)
   ↓ issued as
DecisionEvent(E11)
   ↓ resolves
DeferredAuthorization(A8)
   ↓ revalidated against
State(S19) + AuthorityEpoch(22)
   ↓ consumed by
Execution(X41)
   ↓ produced
Outcome(O9)
   ↓ observed by
Observer(V4)
```

Каждая edge отвечает на отдельный вопрос.

Если две identity случайно объединить, audit становится короче — и слабее.

---

## What should fail closed

Минимальный contract должен блокировать execution, если:

- `decision_event_id` отсутствует там, где semantic ref ambiguous;
- semantic decision не соответствует current execution scope;
- normalized args изменились;
- actor / crew / agent identity изменились вне разрешённой policy;
- policy version требует revalidation;
- relevant state version изменилась;
- authority была revoked / transferred / superseded;
- authorization expired;
- one-shot authorization уже consumed;
- cancellation superseded continuation;
- required provenance cannot be recovered;
- resolver говорит `allow`, но runtime не может доказать, что это тот pending decision, который относится к текущему execution.

Fail-close здесь не означает «всегда навсегда deny».

Он означает:

```text
cannot prove current authorization
        ↓
do not silently execute
```

Runtime может:

```text
re-request approval
revalidate
create new decision occurrence
repair provenance
surface ambiguity
```

Но не должен подменять отсутствие proof предположением.

---

## What this does not require

Этот model не требует:

- держать process suspended до human response;
- встроить конкретный policy engine в CrewAI;
- использовать blockchain;
- подписывать каждую локальную allow decision;
- делать distributed transaction вокруг каждого tool call;
- превращать every approval в one-shot независимо от product semantics;
- запрещать retries;
- запрещать reusable delegated capabilities.

Он требует только одного:

> **Если authorization используется для оправдания consequential execution, связь между конкретным authorization occurrence и конкретным execution occurrence должна оставаться проверяемой.**

---

## Smallest falsifiable conformance test

```text
1. Freeze action A with normalized args and relevant state refs.
2. Produce semantic decision D.
3. Issue concrete authorization occurrence E1 for D.
4. Defer it.
5. Resolve E1 = allow.
6. Revalidate all declared freshness conditions.
7. Consume E1 with execution X1.
8. Record outcome O1.
9. Attempt to reuse E1 with execution X2.
10. Mutate one bound field and attempt X3.
11. Issue E2 with the same semantic D and verify E1/E2 remain distinguishable.
```

PASS if:

```text
X1 admissible
X2 blocked for one-shot reuse
X3 blocked for scope mismatch
E1 and E2 independently addressable
O1 can prove which authorization occurrence X1 consumed
```

FAIL if:

```text
semantic D alone is treated as sufficient occurrence identity
or
approval remains replayable merely because decision == allow
or
freshness is checked but the consumed authorization is not bound to X1
```

---

## The larger consequence

Human-in-the-loop is often described as a safety mechanism.

Но human approval без causal binding может создать ложное чувство безопасности.

Человек действительно нажал `Approve`.

Лог действительно содержит `ALLOW`.

Tool действительно был вызван.

И всё это может быть правдой одновременно — при том, что система не умеет доказать, что разрешение относилось именно к этому execution occurrence в момент side effect.

Поэтому следующий уровень agent governance — не больше approval dialogs.

Он выглядит так:

```text
less implicit permission
more causal permission
```

---

## Core invariants

> **Consent has a causal lifetime.**

> **Semantic identity != authorization occurrence != execution consumption.**

> **Valid historical consent does not imply current execution authority.**

> **An approval should authorize a bounded execution occurrence under bound conditions, not become an indefinitely replayable statement that an action was once approved.**

И наконец:

> **A system should be able to prove not only why an action was allowed, but which exact permission was consumed when the action became real.**

---

## What comes next

Следующий естественный шаг — executable conformance layer, который проверяет связку:

```text
DEFER
→ exact authorization occurrence
→ scope digest
→ freshness revalidation
→ one-shot consumption
→ execution occurrence
→ outcome provenance
```

Если такая цепочка становится portable между frameworks, human approval перестаёт быть framework-specific UI mechanic.

Он становится interoperable evidence primitive для autonomous systems.

И тогда вопрос будущей agent infrastructure меняется ещё раз.

Не:

> Кто нажал Approve?

А:

> **Можем ли мы независимо доказать, какое разрешение пересекло execution boundary вместе с этим действием?**

Именно с этого момента consent становится не обещанием безопасности, а проверяемой частью системы.
