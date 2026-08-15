# A Diagnostic Nobody Can See Is Not a Signal

## Почему ownership, reachability и causal awareness нельзя сжимать в один статус

**RESONANCE — Issue 001: THE AGE OF AGENTS**  
**Article ID:** `I001-RN-DNS`  
**Status:** Published  
**Date:** 2026-08-15

---

Самые опасные ошибки распределённых AI-систем часто выглядят не как ошибка.

Задача имеет владельца.  
Состояние записано.  
Процесс формально существует.  
Диагностическая команда даже умеет показать, кто сейчас активен.

И всё же работа никуда не движется.

Почему?

Потому что система знает факт, который **не входит в причинный путь решения**.

И в этот момент возникает правило, которое кажется почти тривиальным, пока не посмотришь на реальные multi-agent traces:

> **A diagnostic nobody is told about is not a signal.**

Диагностика может существовать внутри системы и при этом практически отсутствовать для того агента, который принимает решение.

Это не проблема observability в привычном смысле.

Это проблема **causal visibility**.

---

# 1. Один handoff, который выглядел завершённым

В публичной дискуссии вокруг межсессионной координации Claude Code мы обсуждали несколько возможных failure modes.

Один из участников решил не спорить теоретически и проверил собственные логи.

И нашёл живой случай.

Задача была передана новой сессии:

```text
ball passed
owner set
fresh activity recorded
```

По durable state всё выглядело нормально.

Но новая сессия не работала.

Watcher для неё отсутствовал.

Следовательно, handoff существовал как запись — но не существовал как реально доставляемый переход.

До ручного запуска получателя задача была фактически недостижима.

Особенно интересно другое: механизм проверки reachability уже существовал. Watcher inventory мог показать, способен ли конкретный участник сейчас принять сигнал.

Проблема была не в отсутствии диагностики.

Проблема была в том, что отправители **не знали, что эта диагностика является частью handoff protocol**.

Отсюда более точная формула:

```text
diagnostic exists
        !=
operational signal exists
```

---

# 2. Ownership не означает reachability

Мы часто используем поле `owner` как будто оно содержит больше информации, чем оно действительно содержит.

```text
owner = agent:B
```

может означать:

> B является текущим логическим владельцем этой responsibility lane.

Но оно не означает:

```text
B is running
B is listening
B is addressable
B saw the handoff
B accepted the handoff
B can act now
```

Это отдельные факты.

Поэтому:

> **Ownership does not imply reachability.**

И ещё строже:

> **A handoff is not complete merely because a new owner was named.**

Если система сначала записывает нового owner, а только потом когда-нибудь обнаруживает, что получить работу некому, она создала причинный разрыв.

Durable state утверждает больше, чем реально произошло.

---

# 3. Но второй предполагаемый failure mode не воспроизвёлся

Именно здесь история становится особенно полезной.

Вторая гипотеза касалась concurrent status writes и необходимости CAS — compare-and-swap по predecessor.

Проверка логов не дала красивого подтверждения.

В исследованной low-concurrency среде участник просмотрел **372 status-setting messages**.

Он нашёл 13 переходов, автор которых не видел предыдущий transition.

Три оказались отдельной timestamp-проблемой.

Из оставшихся десяти только один имел seconds-range gap — и обе записи исходили из одной сессии во время собственного теста.

Остальные были разделены минутами или даже днём.

То есть это были в основном не гонки.

Это были случаи другого класса:

> **writer wrote without reading the thread to the end.**

И это важная коррекция нашей модели.

CAS не исправляет того, кто вообще не читал predecessor.

---

# 4. Read basis и CAS — разные доказательства

На первый взгляд достаточно сделать:

```text
expected_predecessor_id = E42
CAS(E42 → E43)
```

Но откуда взялся `E42`?

Если writer реально прочитал E42, а потом между чтением и записью появился E43, это классический optimistic-concurrency conflict.

```text
writer observes E42
        ↓
other writer creates E43
        ↓
CAS(expected=E42, current=E43)
        ↓
CONFLICT
```

Но есть совсем другая ситуация:

```text
writer last observed E40
        ↓
thread already contains E41, E42
        ↓
writer proposes a transition anyway
```

Это не тот же самый failure.

У writer нет корректного causal basis для предлагаемого predecessor.

Поэтому нам нужны два значения:

```text
observed_through_event_id
expected_predecessor_id
```

И два независимых теста:

```text
observed_through_event_id == expected_predecessor_id
```

отвечает:

> действительно ли proposal основан на том predecessor, который writer утверждает ожидаемым?

А:

```text
expected_predecessor_id == current_head_event_id
```

отвечает:

> остаётся ли этот predecessor текущим сейчас?

Получаются два разных результата:

```text
BLOCKED_UNREAD_PREDECESSOR
```

и:

```text
BLOCKED_CAS_CONFLICT
```

Это принципиально разные причины отказа.

---

# 5. Causal visibility

Обычная observability отвечает:

> можно ли где-нибудь в системе узнать этот факт?

Но autonomous coordination требует более строгого вопроса:

> был ли этот факт доступен и обязателен именно в той точке, где агент принимал решение?

Назовём это **causal visibility**.

Например:

```text
watcher inventory exists
```

не достаточно.

Нужно:

```text
handoff protocol
    ↓ requires
reachability_surface_ref
    ↓ resolves
current reachability signal
```

Только тогда diagnostics становится частью proof path.

Поэтому:

> **Detectability without discoverability is not operational observability.**

И ещё точнее:

> **A fact outside the decision path cannot protect the decision.**

---

# 6. Handoff должен быть двухфазным

Из этого естественно появляется другая модель передачи ownership.

Не:

```text
owner = B
DONE
```

а:

```text
current owner = A
        ↓
A proposes handoff H43 to B
        ↓
check surfaced reachability(B)
        ↓
HANDOFF_DELIVERABLE
        ↓
B acknowledges exact H43
        ↓
HANDOFF_COMMIT_ALLOWED
        ↓
ownership_epoch 4 → 5
owner A → B
```

До последнего шага A остаётся текущим owner.

Это позволяет избежать странного промежуточного состояния:

```text
owner = B
B cannot receive anything
A believes responsibility is gone
```

Такое состояние выглядит согласованным в database и сломано в реальном мире.

---

# 7. Ownership epoch

Простого `owner_ref` недостаточно, если ownership может переходить между агентами.

Нужен causal identity самого владения:

```text
owner_ref = agent:B
ownership_epoch = 5
```

Теперь старый writer с epoch 4 не может продолжать mutation только потому, что когда-то был владельцем.

Получается разделение:

```text
ownership check
= who may write?

causal-basis check
= what did the writer actually observe?

CAS check
= is that predecessor still current?

reachability check
= can the target receive the handoff now?

ack check
= did the exact target accept the exact occurrence?
```

Ни один из этих вопросов не заменяет остальные.

---

# 8. Executable contract: HRC-001

Чтобы эта модель не осталась очередной красивой схемой, мы превратили её в executable reference contract:

**HRC-001 — Handoff Reachability & Causal Basis**

Implementation:

https://github.com/safal207/pythiaLabs/pull/262

Exact head:

```text
f38d45a67430c393f040702b1c1c360dbf3b9343
```

Canonical exact-head conformance:

```text
workflow: HRC conformance
run:      31876678326
event:    pull_request
result:   SUCCESS
```

https://github.com/safal207/pythiaLabs/actions/runs/31876678326

Reference suite: **24 falsification tests**.

Контракт отдельно проверяет:

- current owner;
- ownership epoch;
- unread predecessor;
- true CAS conflict;
- lane mismatch;
- missing reachability;
- recipient mismatch;
- diagnostic-surface mismatch;
- future reachability signal;
- expired reachability;
- known unavailable recipient;
- exact ownership-epoch increment;
- deliverable-but-unacknowledged handoff;
- wrong recipient ACK;
- wrong handoff occurrence ACK;
- wrong target epoch ACK;
- stale predecessor at ACK;
- exact acknowledged handoff commit;
- published JSON Schemas.

Главное здесь — не число тестов.

Главное, что теперь два внешне похожих failure mode имеют разные executable identities:

```text
never read predecessor
        !=
read predecessor, then lost race
```

---

# 9. Non-reproduction — это тоже evidence

Очень легко было бы написать статью так:

> мы нашли concurrency race, поэтому нужен CAS.

Но реальные данные этого не показали.

Именно поэтому мы не должны так писать.

В проверенной low-concurrency среде предполагаемый race не воспроизвёлся как систематический класс.

Это не означает:

```text
CAS races do not exist
```

И не означает:

```text
CAS races will happen everywhere
```

Это означает только:

> **в этой наблюдаемой среде найденный failure был преимущественно failure of causal awareness, а не concurrency collision.**

Такая отрицательная информация чрезвычайно полезна.

Она говорит нам, **куда не надо преждевременно направлять архитектуру**.

---

# 10. Координационный стек становится глубже

Раньше мы могли представить multi-agent handoff почти линейно:

```text
state
  ↓
owner
  ↓
write
```

Теперь видно больше слоёв:

```text
Responsibility Lane
        ↓
Ownership Epoch
Who currently owns it?
        ↓
Causal Read Basis
What has the writer actually observed?
        ↓
Predecessor CAS
Is that basis still current?
        ↓
Reachability
Can the target receive work now?
        ↓
Recipient ACK
Did that exact target accept this exact handoff?
        ↓
Ownership Commit
```

Это уже не message bus.

Это **causal coordination protocol**.

---

# 11. Более общий принцип

Этот класс ошибок существует далеко за пределами AI-agent sessions.

Он появляется в:

- distributed workers;
- incident ownership;
- human approvals;
- on-call rotations;
- workflow engines;
- delivery systems;
- payment authorization;
- orchestration queues;
- replicated control planes.

Везде, где запись:

```text
assigned
approved
owned
sent
ready
```

может быть исторически истинной, но операционно бесполезной.

Поэтому полезно помнить:

> **A recorded relation is not necessarily an executable relation.**

Чтобы отношение стало операционным, система должна доказать не только его наличие, но и пригодность в текущей причинной точке.

---

# 12. Голосование — и приглашение сломать модель

Статья имеет живой reader-falsification poll:

https://github.com/safal207/RESONANCE/issues/60

Варианты:

- [✅ Agree](https://github.com/safal207/RESONANCE/issues/60#issuecomment-5301568445)
- [🟡 Partially agree](https://github.com/safal207/RESONANCE/issues/60#issuecomment-5301568676)
- [❌ Disagree](https://github.com/safal207/RESONANCE/issues/60#issuecomment-5301569018)

Но количество голосов не является доказательством.

Особенно ценны:

```text
counterexample
trace
log shape
protocol failure
negative reproduction
```

Потому что именно такой ответ уже однажды сделал предыдущую модель сильнее.

---

# 13. Финальная формула

Multi-agent system недостаточно знать:

> кто владеет задачей?

Она должна уметь ответить:

```text
Who owns it?
Who may mutate it now?
What predecessor did the writer actually observe?
Is that predecessor still current?
Can the next owner be reached?
Was reachability visible to the sender?
Did the recipient accept this exact handoff?
```

И только после этого:

```text
ownership may move
```

Потому что:

> **Ownership does not imply reachability.**

> **CAS does not repair a missing read.**

> **A diagnostic nobody is told about is not a signal.**

И, возможно, самое общее:

> **A fact may exist in the system and still be causally absent from the decision that needed it.**

---

*RESONANCE — Issue 001: THE AGE OF AGENTS*  
*Article 12 — A Diagnostic Nobody Can See Is Not a Signal*
