# Authority Has a History — почему право AI-агента действовать тоже имеет причинное состояние

**Article ID:** I001-RN-ACI  
**Deck:** В multi-agent системе мало доказать, что агент знает актуальное состояние. Нужно доказать, что именно этот агент всё ещё имеет право его менять. Static ownership решает простые случаи, но work-stealing, failover, recovery и delegation превращают authority в собственную причинную state machine.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · The Age of Agents · Authority Causality / Dynamic Ownership / Causal CAS

---

## Signal

В публичном треде `anthropics/claude-code#24798` обсуждение inter-session coordination дошло до неожиданно фундаментального вопроса.

Один из участников, `deemwario`, описал production-подобный workaround для lost updates между несколькими loops: вместо общего compare-and-swap они заранее разделили key space так, чтобы один key мог иметь только одного writer.

```text
one loop
   ↓
one key
   ↓
one write authority
```

Пока ownership можно статически назначить заранее, это дешевле общего CAS: конкуренции за право записи просто не возникает.

Но автор сразу обозначил границу решения.

Когда ownership нельзя определить заранее — например, появляется dynamic work-stealing или «правильный» владелец зависит от runtime state — статическая партиция перестаёт быть достаточной.

И здесь возникает более общий вопрос:

> Если state имеет causal predecessor, почему authority считается вечным свойством actor?

В действительности право действовать тоже меняется во времени.

Оно может быть:

```text
assigned
transferred
delegated
revoked
expired
superseded
```

Значит, authority — не просто metadata возле агента.

**Authority itself has causal state.**

---

## Why it matters

Обычный optimistic concurrency control спрашивает:

> На каком состоянии основана эта запись?

Например:

```text
expected_previous_state_digest
        ↓
transition
        ↓
new_state_digest
```

Если два writers прочитали одну и ту же версию и одновременно пытаются изменить объект, второй конфликт можно обнаружить.

Но multi-agent системы добавляют второй независимый вопрос:

> Имеет ли этот writer право выполнять transition сейчас?

Эти вопросы нельзя сливать.

```text
Question 1:
is state predecessor current?

Question 2:
is authority predecessor current?
```

Агент может иметь абсолютно актуальные данные и при этом уже не иметь права на mutation.

Это происходит при:

- work-stealing;
- failover;
- lease expiration;
- delegation;
- revoke;
- restart;
- session recovery;
- context compaction;
- delayed retry;
- ownership migration между agents или lanes.

Отсюда появляется новый базовый принцип:

> **Correct knowledge does not imply current authority.**

---

## Claims

| ID | Claim | Classification | Confidence | Evidence |
|---|---|---|---|---|
| C1 | В `anthropics/claude-code#24798` описан практический ownership-per-key подход как способ исключить конкурирующих writers | Public reported implementation pattern | High for report existence | `deemwario`, issue comment `5300376905` |
| C2 | Сам автор ограничивает static ownership случаями, где key space можно заранее partition | Public reported design boundary | High | тот же comment |
| C3 | При dynamic work-stealing статическое ownership требует механизма безопасной передачи authority | Design inference | High | causal analysis of reported boundary |
| C4 | ACI-001 формализует authority state, `authority_epoch`, transfer/revoke и authority-bound mutation | Verified repository fact | High | `safal207/pythiaLabs#259` |
| C5 | Reference suite блокирует stale writer после ownership handoff 17→18 | Verified conformance result | High | ACI conformance run `31863547583` |
| C6 | ACI suite проходит 16/16 tests в GitHub Actions | Verified CI result | High | workflow run `31863547583` |
| C7 | ACI-001 — внешний research/prototype contract, а не встроенная функция Claude Code, Codex или другого vendor runtime | Scope limitation | High | repository boundary |

---

## From state CAS to authority CAS

Начнём с привычной модели.

### State CAS

```text
state S17
   ↓
read digest D17
   ↓
propose transition T
   ↓
CAS(expected=D17)
   ↓
state S18
```

Если к моменту записи state уже изменился, transition отклоняется.

Теперь добавим ownership.

```text
authority A17
owner = worker:A
epoch = 17
```

Во время выполнения системы work может быть передан другому worker:

```text
worker:A
   ↓ handoff
worker:B

epoch 17 → 18
```

После handoff старый worker может проснуться, закончить старый computation и попытаться записать результат.

Его local state может быть свежим.

Patch может быть корректным.

Но authority уже другая.

Поэтому появляется второй compare-and-swap:

```text
expected_previous_authority_digest
+
expected_previous_epoch
        ↓
transfer / delegate / revoke
        ↓
new_authority_digest
+
new_authority_epoch
```

И consequential mutation становится двухключевой:

```text
CAS(state)
AND
CAS(authority)
→ mutation admissible
```

Это не означает, что каждая система обязана всегда выполнять два дорогих distributed CAS.

Наоборот — важный вывод как раз в том, что coordination может быть адаптивной.

---

## The coordination ladder

Из обсуждения получилось три режима.

### Mode 1 — Static ownership

```text
key X → worker A
key Y → worker B
```

Если partition можно определить заранее и ownership не меняется, write-time arbitration почти не нужна.

Это дешёвая и сильная structural guarantee.

Не надо доказывать, кто победил гонку, если гонка архитектурно невозможна.

### Mode 2 — CAS ownership transfer

Когда workload становится динамическим:

```text
worker A owns key X @ epoch 17
        ↓
verified handoff
        ↓
worker B owns key X @ epoch 18
```

Не обязательно сразу CAS-ить каждую mutation.

Можно сначала сериализовать только изменение **права записи**.

Все последующие writes должны нести текущий `authority_epoch`.

### Mode 3 — Causal-CAS shared state

Если genuine concurrent mutation неизбежна, одной сериализации owner уже мало.

Тогда mutation должна доказывать одновременно:

```text
current authority predecessor
+
current state predecessor
```

Именно здесь появляется полный causal-CAS.

Получается лестница стоимости:

```text
static ownership
      ↓
CAS ownership transfer
      ↓
causal-CAS shared state
```

Чем меньше contention, тем дешевле coordination.

---

## `ownership_epoch` is not a timestamp

В ACI-001 authority получает `authority_epoch`.

Это число удобно интерпретировать неправильно.

Оно **не является временем**.

```text
resource X epoch 18
resource Y epoch 18
```

не означает, что эти состояния authority произошли одновременно или вообще сравнимы.

Epoch действует внутри causal history конкретного resource.

```text
X: 16 → 17 → 18
Y: 4 → 5
```

Он нужен для ответа на узкий вопрос:

> Не пытается ли writer действовать на основании authority, которая уже была superseded?

Поэтому правильная проверка:

```text
presented_authority_epoch == current_authority_epoch
```

а не:

```text
latest timestamp wins
```

---

## A stale worker can be perfectly informed

Это самый важный negative case.

Представим:

```text
T0
worker A owns key X
epoch = 17

T1
A reads current state

T2
scheduler transfers X to B
epoch = 18

T3
A finishes computation

T4
A attempts write
```

На T4 данные A могут быть актуальны.

Если проверять только state digest, mutation иногда даже может пройти.

Но authority proof показывает:

```text
presented epoch = 17
current epoch   = 18

17 != 18
→ BLOCKED
```

То есть correctness computation и admissibility action — разные свойства.

```text
correct result
≠
currently authorized result
```

Этот принцип важен далеко за пределами shared KV state.

Он применим к:

- code ownership;
- deployment lanes;
- payment authorization;
- agent wallets;
- approval chains;
- incident response;
- database migration leadership;
- distributed task queues;
- scientific verification tasks;
- autonomous infrastructure management.

---

## Revocation must beat memory

Особенно опасен recovery после interruption.

Агент может восстановить checkpoint:

```text
I own resource X
```

Но пока session была остановлена, authority могла быть revoked или transferred.

Если recovery pipeline просто доверяет durable memory, получается authority resurrection.

```text
old checkpoint
    ↓
restart
    ↓
stale ownership silently restored
```

ACI требует обратного:

```text
checkpoint says: owner A @ 17
current authority source says: owner B @ 18

current authority wins
→ A blocked
```

Это естественно продолжает линию Article 07 — Responsibility-Lane Continuity.

Там мы сформулировали:

> recovered state does not imply recovered responsibility topology.

Теперь появляется следующий слой:

> recovered responsibility topology does not imply that the recovered authority is still current.

---

## Responsibility lane and authority history are different things

Responsibility-Lane Continuity отвечает:

```text
Which lane owns this class of action?
```

Authority Causality отвечает:

```text
How did this actor/lane become the current owner?
```

Например:

```text
Lane: verification
scope: read + verify
```

может быть стабильной архитектурной сущностью.

Но конкретный verifier instance может меняться:

```text
verifier A @ epoch 8
      ↓ handoff
verifier B @ epoch 9
```

Поэтому lane identity и active authority identity не обязательно совпадают.

Композиция выглядит так:

```text
recover task state
        ↓
recover responsibility lane
        ↓
recover current authority state
        ↓
verify authority predecessor
        ↓
verify state predecessor
        ↓
execute bounded mutation
```

Это уже не просто memory recovery.

Это восстановление **causal permission graph**.

---

## Authority is a graph edge, not merely a role label

В простых ACL системах authority часто выглядит так:

```text
user Alice → can_write
```

Но для автономных multi-agent систем этого мало.

Нужно знать:

```text
who granted it
what it replaced
which resource it applies to
which scope it permits
which epoch is current
whether it was revoked
which action consumed it
```

То есть authority лучше представлять как часть графа переходов:

```text
AuthorityState(17)
      ↓ transfer
AuthorityState(18)
      ↓ authorizes
Mutation(42)
      ↓ produces
State(99)
```

Такое представление делает возможным аудит вопроса:

> Почему именно этот actor имел право создать этот state transition?

---

## ACI-001

После обсуждения границы static ownership мы зафиксировали executable contract **ACI-001 — Authority Causality Invariant** в `pythiaLabs`.

Он включает три machine-readable объекта.

### Authority State

```text
resource_ref
owner_ref
authority_epoch
status
scope
predecessor_digest
authority_digest
```

### Authority Transition

```text
kind
resource_ref
expected_previous_authority_digest
expected_previous_epoch
from_owner_ref
to_owner_ref
new_epoch
new_scope
```

### Mutation Request

```text
actor_ref
resource_ref
effect_ref
presented_authority_epoch
presented_authority_digest
expected_previous_state_digest
new_state_digest
```

Reference validator проверяет отдельно authority and state conditions.

---

## What the executable proof currently demonstrates

GitHub Actions run `31863547583` выполняет ACI conformance suite.

На момент публикации:

```text
16 tests
16 passed
0 failed
```

Проверяются, среди прочего:

- valid static owner;
- tamper-evident authority digest;
- valid transfer with exact predecessor;
- stale epoch rejection;
- wrong predecessor digest rejection;
- exact epoch increment;
- stale writer rejection after handoff;
- current owner acceptance;
- wrong actor rejection;
- mutation scope enforcement;
- revocation dominating cached context;
- split-authority detection;
- state-CAS success when both predecessors are current;
- state-CAS rejection with current authority but stale state;
- authority rejection with current state but stale authority.

Последние два теста особенно важны.

Они доказывают независимость двух осей:

```text
state proof PASS
+
authority proof FAIL
→ BLOCKED
```

и:

```text
authority proof PASS
+
state proof FAIL
→ BLOCKED
```

---

## Split authority is a first-class conflict

Ещё один неприятный failure mode:

```text
key X
├── worker A @ epoch 7 ACTIVE
└── worker B @ epoch 7 ACTIVE
```

Если система обнаруживает два разных active owners одного resource с одинаковым epoch, нельзя просто выбрать более свежий timestamp.

Это structural contradiction.

ACI-001 классифицирует его как conflict и требует fail closed.

Почему?

Потому что timestamp не объясняет causal legitimacy.

Одна запись может быть позднее по часам, но происходить из невалидной ветви authority history.

---

## Delegation is not the same as transfer

Transfer обычно означает:

```text
A stops owning
B starts owning
```

Delegation может быть сложнее:

```text
A retains parent authority
B receives bounded child scope
```

Текущая ACI-001 v0.1 намеренно не претендует на полную formal semantics hierarchical delegation.

Но causal principle остаётся тем же:

```text
delegated authority
must have
parent authority predecessor
+
explicit scope
+
revocation path
```

Иначе delegation превращается в вечный permission leak.

Это один из следующих frontier для стандарта.

---

## Evidence logistics for authority

Если proof сложный, недостаточно сохранить authority state где-то в storage.

Verifier должен быстро получить правильную цепочку:

```text
current mutation
      ↓
current authority state
      ↓
authority predecessor
      ↓
transfer / delegation evidence
      ↓
previous authority state
```

И отдельно:

```text
current mutation
      ↓
expected state predecessor
      ↓
current state evidence
```

Это снова приводит к evidence logistics.

Хорошая proof architecture должна доставлять **минимально достаточный causal slice**, а не весь исторический лог.

Например:

```text
mutation 42
needs:
  authority state 18
  authority predecessor digest 17
  transfer receipt 17→18
  state predecessor digest 98
  current state proof 98
```

Так verification остаётся дешёвым даже при длинной истории.

---

## The broader trust stack

Теперь несколько наших линий начинают складываться в последовательную architecture:

```text
Fractal Causal Refactoring
        ↓
find meaningful divergence

Responsibility-Lane Continuity
        ↓
recover who owns which responsibility boundary

Authority Causality Invariant
        ↓
prove how current execution authority became current

Causal CAS
        ↓
prove the mutation is based on current state

Evidence Logistics
        ↓
route minimum proof slice

ContractGraph-QA
        ↓
validate causal admissibility
```

Это важное изменение рамки.

Trust layer больше не выглядит как один permission check перед tool call.

Он превращается в проверяемую причинную систему.

---

## Failure taxonomy

ACI выделяет несколько разных классов отказа.

| Failure | State current? | Authority current? | Result |
|---|---:|---:|---|
| Normal mutation | yes | yes | admissible |
| Stale state | no | yes | blocked |
| Stale owner after handoff | yes | no | blocked |
| Stale state + stale owner | no | no | blocked |
| Revoked owner | maybe | no | blocked |
| Split authority | unknown | contradictory | blocked |
| Scope violation | yes | partially valid | blocked |

Главное: **state freshness и authority freshness — ортогональны**.

---

## Product implications

Если multi-agent runtimes начнут поддерживать native coordination, им может понадобиться больше, чем shared event bus.

Для dynamic ownership полезны primitives уровня:

```text
claim(resource)
transfer(resource, expected_epoch, new_owner)
revoke(resource, expected_epoch)
inspect_authority(resource)
mutate(resource, authority_epoch, expected_state)
```

При этом static partitioning должно оставаться дешёвым fast path.

Нельзя заставлять простую систему платить distributed-consensus cost только потому, что сложные workloads иногда его требуют.

---

## Security implications

Authority causal state близка к security capability, но не идентична обычному token.

Token может быть cryptographically valid и всё равно stale.

```text
signature valid
≠
authority current
```

Поэтому высокоуровневая проверка должна включать:

```text
identity proof
+
scope proof
+
causal-currentness proof
```

Это особенно важно для agent wallets, payments, deployment keys и machine-to-machine approvals.

---

## What ACI does not prove

ACI-001 v0.1 не доказывает:

- Byzantine consensus;
- globally linearizable distributed ownership;
- production-grade leases;
- cryptographic signer identity;
- cross-datacenter clocks;
- vendor-native integration;
- complete hierarchical delegation semantics;
- absence of bugs в reference implementation.

Он доказывает более узкую вещь:

> authority predecessor можно сделать first-class causal object и mechanically reject stale/split authority in a reference model.

Это deliberately small proof.

---

## The deeper principle

В autonomous systems мы привыкли считать state чем-то, что меняется, а authority — чем-то, что просто существует.

Но реальная система ведёт себя иначе.

Authority тоже имеет историю.

```text
who could act yesterday
≠
who may act now
```

И если agent architecture не хранит эту историю явно, она всё равно существует — только неформально, в scheduler state, human assumptions, stale memory, locks, tickets или timing.

Неявная authority history сложнее проверить и легче потерять.

Поэтому ACI предлагает сделать её наблюдаемой.

---

## Closing invariant

В Article 07 мы пришли к принципу:

> Recover the boundaries that make the work safe to continue.

Article 08 добавляет следующий вопрос:

> Are those boundaries still authorized by the current causal history?

И финальная формула становится такой:

```text
current knowledge
        ≠
current authority
```

Для consequential action нужно оба:

```text
current state predecessor
+
current authority predecessor
        ↓
causally admissible action
```

**Authority itself has causal state.**

Именно поэтому право AI-агента действовать должно быть не флагом, а доказуемой цепочкой переходов.
