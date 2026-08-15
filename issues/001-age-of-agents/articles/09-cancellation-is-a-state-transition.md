# Cancellation Is a State Transition — почему остановка AI-агента должна оставлять доказуемую границу

**Article ID:** I001-RN-CDB  
**Deck:** Streaming делает часть работы AI-агента видимой раньше, чем она становится durable graph state. Cancel вскрывает этот разрыв. Правильный контракт — не превращать каждый токен в обычный checkpoint, а оставлять machine-readable terminal receipt, который связывает последний durable checkpoint, уже показанный пользователю stream, результат persistence boundary и допустимую политику resume.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · Cancellation Durability Boundary / Terminal Lifecycle Receipt / Resume Authority

---

## Signal

У AI-агентов появляется класс ошибок, который почти незаметен в обычном request/response software.

Пользователь уже **увидел состояние**, но система ещё не обязана считать это состояние **durable**.

Это особенно хорошо видно в streaming runtime:

```text
checkpoint N
    ↓
stream e1
    ↓
stream e2
    ↓
stream e3
    ↓
user presses Cancel
```

Для пользователя `e1..e3` уже существуют: они были показаны на экране, прочитаны, возможно повлияли на следующее решение.

Для backend они могут всё ещё принадлежать другой durability class: transient output, pending writes, partial task output или данные, которые ещё не стали полным checkpoint graph state.

Если после cancel клиент снова запрашивает authoritative history и получает только `checkpoint N`, возникает неприятный эффект:

> система молча возвращает authority более старому состоянию, хотя пользователь уже наблюдал более новое.

Именно этот конфликт обсуждается в публичном issue [`langchain-ai/langgraph#5672`](https://github.com/langchain-ai/langgraph/issues/5672) — *Run Cancellation Causes Loss of Streamed State Not Yet Persisted as a Checkpoint*.

Но за время обсуждения вопрос стал точнее.

Проблема уже не сводится к тезису:

> «LangGraph сохраняет состояние только в конце run».

Актуальная OSS-документация описывает checkpoints на super-step boundaries и отдельно pending writes на уровне node/task. Agent Server также имеет явные durability modes (`sync`, `async`, `exit`).

Поэтому более сильный вопрос выглядит так:

> **Что именно гарантированно известно о persistence boundary в тот момент, когда explicit cancellation объявлена завершённой?**

---

## The public thread moved from bug report to contract design

Исходный issue описывал UX failure: пользователь видит streamed output, отменяет run, затем новый message/history sync возвращает более старое checkpointed state и часть видимого вывода исчезает.

Дальше появились несколько независимых линий анализа.

Один участник указал на frontend/history branching path. Другой проследил возможную cancellation-cleanup границу через `AsyncBackgroundExecutor` и pending `aput/aput_writes`. Позже maintainer сообщил, что команда пересматривает streaming primitives.

Затем обсуждение стало архитектурным.

В треде появилась идея отделить:

```text
persisted application state
        ≠
terminal lifecycle receipt
```

и не считать partial state автоматически нормальным resumable checkpoint.

RESONANCE внесла в обсуждение следующий invariant:

> **no silent authority transfer from what the user already observed back to an older checkpoint**

То есть rollback к старому durable state может быть допустим как recovery policy — но он не должен происходить **молча**.

Позже независимый re-audit текущего OSS сузил возможный остаточный gap до boundary между Pregel cleanup и LangGraph Platform / Agent Server cancel semantics.

А свежий комментарий `atomicdjt` сформулировал ещё одну важную часть:

> streamed output и checkpointed graph state — разные durability classes.

И предложил моделировать cancellation как first-class terminal record вместо того, чтобы безусловно мутировать последний нормальный checkpoint.

Это и есть зрелая формулировка проблемы.

---

## False binary: checkpoint every token or lose everything

На первый взгляд есть только два варианта:

```text
A. persist every streamed token as graph state
B. accept that cancel loses everything after last checkpoint
```

Но это ложная бинарность.

Нормальный graph checkpoint несёт сильную семантику: completed transition / super-step boundary / resumable state.

Если мы автоматически складываем туда любой partial stream, появляется другая ошибка:

```text
visible partial output
        ↓
forced into normal checkpoint
        ↓
resume engine assumes transition completed
        ↓
partial execution masquerades as completed execution
```

Это опасно для tool-using agents, approval workflows и любых nodes с side effects.

Поэтому нужны как минимум **три разных факта**:

1. **Last durable graph checkpoint** — какое graph state действительно подтверждено runtime.
2. **User-visible stream frontier** — какой sequence уже был exposed клиенту.
3. **Terminal lifecycle receipt** — что произошло с промежутком между ними при cancel/failure/disconnect.

Схематично:

```text
D = last durable checkpoint
V = last visible stream event
T = terminal transition receipt

safe continuation requires reasoning over D + V + T
```

Нельзя автоматически заменить эту тройку одним blob.

---

## `wait=true` is the interesting synchronization boundary

Актуальная LangChain documentation для Agent Server описывает `interrupt` cancellation так:

- run получает статус `interrupted`;
- run record сохраняется;
- checkpoints run сохраняются;
- thread state сохраняется на последнем completed step.

Отдельно `wait=True` описан как режим, при котором cancel request блокируется, пока run не будет fully cancelled; это полезно, когда caller хочет узнать final state и созданные checkpoints.

Canonical docs:

- [How to cancel a run](https://docs.langchain.com/langsmith/cancel-run)
- [Cancel Run API](https://docs.langchain.com/langsmith/agent-server-api/thread-runs/cancel-run)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

Это не доказывает дополнительную гарантию «все streamed values durable после cancel» — такой вывод был бы сильнее документации.

Но `wait=true` создаёт естественную synchronization boundary.

Если caller ждёт завершения cancellation, runtime должен хотя бы иметь определённый ответ на вопрос:

> **Что стало durable, что осталось partial, а что было abandoned?**

RESONANCE предлагает следующий happens-before invariant как **design / conformance proposal**, а не как существующую vendor guarantee:

```text
cancel requested
  -> cancellation cleanup / pending-write drain attempted
  -> persistence outcome established
  -> terminal run state published
  -> history/state exposed to the caller
```

Ключевое слово — **outcome established**.

Оно не требует, чтобы outcome всегда был `durable`.

Допустимы:

```text
durable
partial
abandoned
```

Недопустим только четвёртый неявный вариант:

```text
unknown, but presented as if history were fully authoritative
```

---

## A terminal durability receipt

Минимальный machine-readable receipt может выглядеть так:

```yaml
run_id: ...
terminal_cause: explicit_cancel
terminal_status: interrupted

last_checkpoint_id: ...
last_stream_seq_emitted: 184
last_stream_seq_durable: 176

terminal_durability: partial
cleanup_attempted: true
cleanup_completed: false

resume_policy: reconcile
```

Более строгий вариант может добавить digests:

```yaml
durable_state_digest: H1
visible_state_digest_at_abort: H2
terminal_receipt_digest: H3
```

Тогда recovery logic получает сравнимые surfaces:

```text
H1 — что backend может доказать как durable graph state
H2 — что пользователь фактически успел увидеть
H3 — что runtime утверждает о переходе между ними
```

Это продолжает уже введённый в RESONANCE principle:

> **Meaning may change. Trace must not.**

И добавляет второй:

> **Visibility may outrun durability. The gap must remain inspectable.**

---

## Cancellation is not transport loss

В свежем продолжении `langchain-ai/langgraph#5672` появилась особенно важная граница: explicit user cancellation нельзя автоматически приравнивать к socket disconnect.

Agent Server API уже различает disconnect policy через `on_disconnect: cancel | continue`, а resumable streaming имеет отдельную настройку `stream_resumable`.

Canonical API reference:

- [Create Run, Stream Output](https://docs.langchain.com/langsmith/agent-server-api/thread-runs/create-run-stream-output)

Это подтверждает, что transport lifecycle и run lifecycle — связанные, но разные плоскости.

Семантически они ещё сильнее отличаются:

```text
explicit_cancel
= user/runtime intentionally asks execution to stop

transport_disconnect
= delivery channel disappeared
```

Если временная потеря сети автоматически получает семантику intentional cancellation, runtime рискует превратить случайный transport event в authoritative lifecycle decision.

Поэтому terminal cause должен быть явным:

```text
completed
explicit_cancel
transport_interrupted
failed
```

А recovery policy должна вычисляться уже из cause + durability result, а не из одного факта «stream закрылся».

---

## Resume authority

В Article 08 мы формализовали другой принцип:

> Correct knowledge does not imply current authority.

Cancellation boundary добавляет симметричный принцип:

> **Older durability does not automatically imply current resume authority.**

Представим:

```text
checkpoint N     = durable
stream N+delta   = visible
cancel           = partial
```

После reload backend действительно может знать только `checkpoint N` как полный graph checkpoint.

Но из этого не следует, что он имеет право **молча** продолжить conversation так, словно `N+delta` никогда не существовал.

Resume должен выбрать policy осознанно:

```text
ALLOW
  visible delta became durable

REPAIR / RECONCILE
  visible delta remains recoverable but is not normal completed graph state

RESTART
  caller explicitly accepts restart from last durable checkpoint

BLOCK
  continuation would erase or contradict newer user-visible state without reconciliation
```

Это не означает, что user-visible output всегда является truth.

Наоборот: streamed output может быть observational, tentative или incomplete.

Но факт его наблюдения уже становится частью provenance.

---

## The smallest falsifiable test

Вместо дискуссии о том, где «вообще» должен жить fix, issue можно свести к маленькому conformance test:

```text
1. start stateful run
2. stream e1..ek
3. explicit cancel(wait=true, action="interrupt")
4. fetch run
5. fetch thread history/state
6. inspect terminal persistence result
7. send next message
8. verify continuation policy
```

Test oracle:

```text
PASS if:
- terminal cause is unambiguous;
- durable frontier is knowable;
- visible/durable mismatch is detectable when it exists;
- next message does not silently erase a newer visible frontier;
- normal checkpoint invariants are not falsified by partial output.

FAIL if:
- cancel returns as complete while persistence boundary is unknowable;
- history silently presents an older checkpoint as if no newer visible state existed;
- transport disconnect is indistinguishable from explicit cancellation;
- partial node output is promoted to completed graph state without an explicit contract.
```

Этот тест одновременно помогает найти ownership.

```text
if OSS Pregel fails before Agent Server boundary
    -> OSS target

if OSS cleanup is correct but Platform publishes/reads terminal state too early
    -> Platform / Agent Server target
```

Именно такой framing был опубликован от `safal207` в issue:

- [conformance proposal / happens-before boundary](https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5300522182)

---

## Why this matters beyond LangGraph

Это не LangGraph-specific проблема.

Любая agent runtime с optimistic streaming может попасть в тот же класс failure:

```text
execution state
    ≠
stream delivery state
    ≠
durable state
    ≠
terminal lifecycle state
```

Пока агент только печатает текст, ошибка выглядит как UX rollback.

Когда агент:

- запускает tools;
- делает платежи;
- меняет документы;
- выполняет approval workflows;
- пишет в базы;
- оркестрирует другие agents;
- инициирует внешний side effect;

тот же gap становится проблемой recovery authority.

Например:

```text
agent emitted "transfer prepared"
        ↓
external side effect may already exist
        ↓
run cancelled before next checkpoint
        ↓
old checkpoint restored
        ↓
retry begins
```

Без terminal receipt система может потерять различие между:

```text
not executed
executed but not checkpointed
checkpointed but not acknowledged
acknowledged but client disconnected
explicitly cancelled after partial progress
```

Это напрямую соединяется с Engineering Signal 015:

> **commit ≠ acknowledgement ≠ retry permission**

Теперь можно добавить:

> **cancel acknowledgement ≠ proof that the visible frontier and durable frontier are identical.**

---

## Claims

| ID | Claim | Classification | Confidence | Evidence |
|---|---|---|---|---|
| C1 | LangGraph checkpoints graph state at super-step boundaries and also persists successful node/task writes used for pending-write recovery | Current official documentation | High | LangGraph Persistence docs, verified 2026-08-15 |
| C2 | Agent Server exposes run durability modes `sync`, `async`, `exit` | Current official documentation | High | Agent Server / Run API docs, verified 2026-08-15 |
| C3 | `interrupt` cancellation preserves run/checkpoints and thread state at the last completed step | Current official documentation | High | LangChain cancel-run docs, verified 2026-08-15 |
| C4 | `wait=True` blocks until the run is fully cancelled and is documented as useful for inspecting final state/checkpoints | Current official documentation | High | LangChain cancel-run docs, verified 2026-08-15 |
| C5 | The public issue contains reports of user-visible streamed output disappearing after cancellation/history resync | Public issue report | High for report existence; implementation cause not automatically proven | `langchain-ai/langgraph#5672` |
| C6 | The issue discussion has converged on separating partial/visible state from normal completed checkpoints and terminal lifecycle semantics | Public design discussion | High for discussion existence | comments in `#5672` |
| C7 | The proposed happens-before ordering from cancellation cleanup to terminal publication is a RESONANCE conformance proposal, not a documented LangGraph guarantee | Design proposal / scope limitation | High | `safal207` comment `5300522182` |
| C8 | Explicit cancellation and transport disconnect should remain semantically distinct in the terminal record | Design inference supported by current API separation | High | `on_disconnect` API + issue discussion |
| C9 | A durable/visible/terminal three-surface model can prevent silent resume authority transfer without forcing partial output into normal graph checkpoints | Architecture inference | High | causal analysis and conformance model in this article |

---

## A compact invariant

The article's core invariant is:

```text
resume_authority is valid only when

last durable graph state
+ last user-visible stream frontier
+ terminal lifecycle transition

can be compared under an explicit recovery policy
```

Or shorter:

> **Do not confuse what was visible, what was durable, and what is safe to resume.**

---

## What this changes in the Age of Agents

Early agent infrastructure treated cancellation as control flow:

```text
cancel -> stop coroutine / worker
```

Mature agent infrastructure must treat it as a **state transition**:

```text
cancel
  -> stop execution
  -> establish persistence frontier
  -> record terminal cause
  -> expose recovery policy
  -> only then resume, reconcile, restart or block
```

The difference is small in syntax and large in consequence.

A control-flow exception says:

> execution stopped.

A terminal durability receipt says:

> execution stopped **here**, this is what became durable, this is what the user saw beyond that point, this is why the run stopped, and these continuation choices remain admissible.

That is the level of evidence autonomous systems need when they begin to act in the world rather than merely produce text.

---

## Limits

This article does **not** claim that LangGraph currently violates the proposed happens-before invariant in every deployment or durability mode.

The public issue remains open, and the exact residual ownership between OSS Pregel and LangGraph Platform / Agent Server requires an integration reproduction against current versions.

It also does not claim that every streamed token should become durable graph state.

The opposite distinction is load-bearing:

> **persisted partial evidence is not automatically a completed checkpoint.**

The purpose of the proposal is to make the boundary falsifiable and machine-readable.

---

## Canonical references

- LangGraph issue: [`langchain-ai/langgraph#5672`](https://github.com/langchain-ai/langgraph/issues/5672)
- RESONANCE cancellation conformance comment: [`issuecomment-5300522182`](https://github.com/langchain-ai/langgraph/issues/5672#issuecomment-5300522182)
- LangChain docs — cancellation: <https://docs.langchain.com/langsmith/cancel-run>
- Agent Server API — cancel run: <https://docs.langchain.com/langsmith/agent-server-api/thread-runs/cancel-run>
- LangGraph OSS persistence: <https://docs.langchain.com/oss/python/langgraph/persistence>
- Agent Server stream API: <https://docs.langchain.com/langsmith/agent-server-api/thread-runs/create-run-stream-output>

A detailed evidence ledger is preserved in [`09-cancellation-is-a-state-transition.sources.md`](09-cancellation-is-a-state-transition.sources.md).

---

**RESONANCE — Issue 001: The Age of Agents**  
**Article 09 · Cancellation Durability Boundary**
