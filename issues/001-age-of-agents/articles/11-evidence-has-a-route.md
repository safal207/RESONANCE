# Evidence Has a Route — почему AI-агенту нужен не максимум проверки, а оптимальная логистика доказательств

**Article ID:** I001-RN-ELR  
**Deck:** Самый сильный verifier может быть неправильным выбором. Для автономной системы важно не проверять всё максимально тяжёлым способом, а доставлять достаточное, актуальное и проверяемое доказательство в нужную точку системы — в нужный момент, для нужного действия и по допустимой цене.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · Evidence Logistics / Contextual Proof Routing / Authorization Path Optimization

---

## Самый сильный verifier может быть неправильным выбором

Представим автономную систему, которая умеет проверять действие пятью способами.

```text
1. local synchronous policy check
2. cached evidence + freshness revalidation
3. independent verifier
4. human approval through DEFER / resolve
5. fresh external evidence + independent verification + human approval
```

Если мы спросим:

> Какой путь самый безопасный?

интуитивный ответ будет:

```text
5
```

Больше доказательств.
Больше независимых проверок.
Человек в контуре.
Свежие данные.

Но теперь действие меняется.

AI-агент хочет прочитать локальный конфигурационный файл.

И система снова выбирает путь №5.

Она:

- запрашивает свежую внешнюю аттестацию;
- будит человека;
- создаёт durable authorization;
- ждёт approval;
- запускает независимый verifier;
- повторно проверяет freshness;
- только после этого читает файл.

Формально система может быть очень осторожной.

Практически она перестаёт быть полезной.

Теперь другой край.

AI-агент хочет отправить необратимый платёж на крупную сумму.

Система выбирает путь №1, потому что он самый быстрый.

Это уже не эффективность.

Это недоказанная экономия на trust boundary.

Значит, вопрос поставлен неправильно.

Нужно спрашивать не:

> Какой verifier самый сильный?

И не:

> Какой путь самый дешёвый?

А:

> **Какой самый дешёвый путь остаётся допустимым для этого конкретного действия в этой конкретной точке состояния, времени, authority и риска?**

Это уже не просто authorization.

Это **логистика доказательств**.

---

## От sync vs async к более общей задаче

В обсуждении pre-tool authorization легко зафиксироваться на бинарном выборе:

```text
synchronous
vs
asynchronous
```

Синхронный путь прост:

```text
check
  ↓
ALLOW
  ↓
execute
```

Асинхронный путь нужен, когда решение должно пережить паузу:

```text
check
  ↓
DEFER
  ↓
external evidence / human / policy engine
  ↓
resolve
  ↓
revalidate
  ↓
consume authorization
  ↓
execute
```

После Article 10 — *Consent Has a Causal Lifetime* — мы добавили ещё одну границу:

```text
authorization occurrence
        ↓
consumption
        ↓
execution occurrence
```

И получили ACB — Authorization Consumption Boundary.

Но следующий вопрос оказался ещё интереснее.

Почему runtime вообще должен заранее решить, что определённый класс действий всегда synchronous или всегда asynchronous?

В реальной системе правильный маршрут зависит от контекста.

Одно и то же действие может требовать разных proof paths в разные моменты.

```text
same tool
same nominal operation
same agent
```

но:

```text
different state
new policy version
changed authority epoch
higher amount
different recipient
older evidence
network partition
recent human confirmation
new uncertainty
```

И admissible route меняется.

Отсюда более общий тезис:

> **Sync vs async — не обязательно policy decision само по себе. Это может быть execution-path choice, выбранный политикой под текущие proof obligations.**

---

## Evidence logistics

Логистика в обычном мире отвечает не на вопрос:

> Какой грузовик самый мощный?

Она отвечает:

> Как доставить нужный груз в нужную точку в нужное время с приемлемыми стоимостью, риском и ограничениями?

С доказательствами в agentic systems возникает похожая задача.

Нам нужен не максимальный объём verification.

Нам нужно:

```text
правильное доказательство
        ×
правильной свежести
        ×
правильной глубины
        ×
для правильного действия
        ×
в правильной точке causal graph
        ×
до пересечения side-effect boundary
```

Это можно назвать:

# Evidence Logistics Routing

или короче:

# Evidence Routing

---

## Доказательство тоже имеет маршрут

Вместо одной линейной цепочки представим граф.

```text
                              ┌→ local sync policy check ─────────────┐
                              │                                      │
Intent → proposed execution ─┼→ cached evidence + revalidate ───────┤
                              │                                      │
                              ├→ independent verifier ───────────────┤
                              │                                      │
                              ├→ human DEFER → resolve ──────────────┤
                              │                                      │
                              └→ fresh evidence → verifier → human ──┘
                                                                     ↓
                                                        authorization consume
                                                                     ↓
                                                                  execute
                                                                     ↓
                                                                  outcome
```

Все эти пути могут быть корректными.

Но не для каждого действия.

### Path A — дешёвый synchronous route

```text
local check
   ↓
consume
   ↓
execute
```

Подходит, например, если:

- риск низкий;
- действие обратимо;
- state стабилен;
- authority локальна и актуальна;
- нет необходимости во внешнем evidence;
- ошибка легко компенсируется.

### Path B — cached evidence + freshness check

```text
cached verified evidence
        ↓
cheap freshness predicate
        ↓
consume
        ↓
execute
```

Подходит, если сильное доказательство уже существует, а вопрос только в том, осталось ли оно применимым.

### Path C — independent verification

```text
proposed action
      ↓
independent verifier
      ↓
consume
      ↓
execute
```

Подходит, когда локальный policy engine не должен быть единственной точкой доверия.

### Path D — durable human authorization

```text
proposed action
      ↓
DEFER
      ↓
human approval
      ↓
revalidation
      ↓
one-shot consumption
      ↓
execution
```

Подходит для consequential actions, где human authority является частью policy.

### Path E — high-assurance route

```text
fresh external evidence
        ↓
independent verifier
        ↓
human authorization
        ↓
state + authority revalidation
        ↓
one-shot consumption
        ↓
execution
        ↓
outcome provenance
```

Нужен не потому, что он красивее.

А потому, что цена ошибки в конкретной точке достаточно высока.

---

## The first invariant

Из этого следует первое правило:

> **The strongest proof path is not automatically the best proof path.**

Но и обратное неверно:

> **The cheapest proof path is not automatically admissible.**

Поэтому целевой принцип такой:

> **Choose the lowest-cost admissible path that still satisfies the proof obligations of the current action, state, authority, time and risk.**

По-русски:

> **Выбирай самый дешёвый из допустимых маршрутов, но никогда не удешевляй маршрут ценой невыполненного доказательного обязательства.**

---

## Causal coordinates: где именно мы принимаем решение

Фраза «сейчас это безопасно» слишком размыта.

Решение должно быть привязано к координатам системы.

Условно:

```text
C = (
  scale,
  topology,
  state,
  time,
  authority,
  policy,
  risk
)
```

Здесь:

- `scale` — на каком уровне системы происходит действие;
- `topology` — в какой части causal / responsibility graph мы находимся;
- `state` — какое состояние реально наблюдается;
- `time` — насколько актуальны evidence и authorization;
- `authority` — кто имеет право действовать сейчас;
- `policy` — по какому набору правил принимается решение;
- `risk` — цена и обратимость возможной ошибки.

Это хорошо стыкуется с FCRP.

FCRP спрашивает:

> На каком масштабе и в какой причинной точке находится meaningful divergence?

Evidence Routing добавляет:

> Какой proof path уместен именно в этой причинной точке?

То есть доказательство тоже должно соответствовать масштабу и текущему causal context.

---

## Формально: constrained shortest proof path

Пусть есть граф доказательных операций:

```text
G = (V, E)
```

Каждая вершина может представлять:

```text
policy check
freshness check
human approval
external evidence acquisition
independent verification
authority validation
authorization consumption
execution boundary
```

Каждое ребро имеет стоимость, зависящую от текущего контекста.

Например:

```text
cost(e | C) = {
  latency,
  compute_cost,
  monetary_cost,
  human_coordination,
  evidence_freshness_decay,
  uncertainty,
  trust_boundary_crossings
}
```

Для action `A` в causal coordinates `C` существует набор обязательств:

```text
O(A, C)
```

Например:

```text
current authority must be proven
recipient binding must be fresh
policy version must match
independent verifier required
human approval required
one-shot consumption required
outcome provenance required
```

Тогда выбирается путь:

```text
P* = argmin J(P | C)
```

при жёстком ограничении:

```text
P satisfies O(A, C)
```

Это принципиально.

Risk-critical obligations не должны превращаться просто в маленький штраф внутри функции стоимости.

Иначе optimizer однажды сможет решить:

> Human approval дорогой. Давайте заплатим penalty и пропустим его.

Нет.

Если human approval является hard obligation, путь без него **не входит в множество допустимых маршрутов вообще**.

Сначала:

```text
filter admissible paths
```

Потом:

```text
optimize among them
```

Не наоборот.

---

## Не обязательно Dijkstra

Слово «оптимальный путь» легко заставляет сразу выбрать конкретный algorithm.

Это тоже преждевременно.

В разных системах могут быть уместны:

```text
Dijkstra
A*
constrained shortest path
multi-objective optimization
Pareto frontier selection
min-cost flow
policy search
bounded dynamic programming
```

Но RESONANCE здесь не предлагает один обязательный algorithm.

Нормативным является не способ поиска.

Нормативны свойства результата:

```text
1. path is admissible
2. required proof obligations are satisfied
3. selected evidence is current enough
4. authority remains current
5. route choice is inspectable
6. route can be invalidated when causal coordinates change
7. optimization cannot silently weaken hard safety constraints
```

---

## Route selection itself needs provenance

Как только runtime начинает оптимизировать proof path, появляется новый temptation:

```text
"optimizer said this route was enough"
```

Этого недостаточно.

Router не должен становиться новой скрытой authority.

Поэтому полезен отдельный record:

```yaml
proof_route_decision:
  route_id: route_019
  action_ref: action_77
  causal_context_ref: state_901
  router_version: elr-router-v0.1

  required_obligations:
    - authority_current
    - scope_bound
    - policy_current
    - one_shot_consumption

  selected_path:
    - local_policy_check
    - freshness_revalidation
    - authorization_consumption

  rejected_alternatives:
    - path: local_policy_check_only
      reason: missing_freshness_obligation

    - path: human_defer_independent_verify
      reason: admissible_but_dominated_on_cost

  cost_snapshot:
    latency_budget_ms: 250
    human_required: false

  valid_until:
    state_digest: sha256:...
    authority_epoch: 22
    policy_version: policy:v17
```

Так independent verifier может спросить не только:

> Path прошёл?

Но и:

> Почему именно этот path считался допустимым в тот момент?

---

## Routing is not authority

Критическая граница:

> **Choosing a proof route does not authorize the action.**

Router может только выбрать способ удовлетворения proof obligations.

Он не должен сам создавать отсутствующее permission.

```text
route selection
    !=
authorization
    !=
authorization occurrence
    !=
consumption
    !=
execution
```

Это сохраняет разделение, построенное в Articles 08–10.

```text
Article 08:
correct knowledge != current authority

Article 09:
older durable state != current resume authority

Article 10:
historical consent != current execution authorization

Article 11:
stronger verification != contextually better proof route
```

---

## Three kinds of waste

Evidence Logistics становится особенно понятной, если посмотреть на три вида потерь.

### 1. Under-verification waste

Система экономит миллисекунды и compute, но пропускает обязательную проверку.

```text
cheap path
   ↓
missing obligation
   ↓
unsafe execution
```

Это ложная экономия.

### 2. Over-verification waste

Система использует high-assurance pipeline для trivial reversible action.

```text
low-risk action
   ↓
human approval
   ↓
independent verification
   ↓
fresh external evidence
   ↓
minutes of latency
```

Это trust infrastructure, которая сама становится bottleneck.

### 3. Stale-route waste

Маршрут был правильным пять секунд назад.

Потом изменился context.

```text
route selected
      ↓
authority epoch changes
      ↓
old route still executes
```

Это уже не только inefficiency.

Это causal bug.

Поэтому route имеет собственную causal lifetime.

---

## Evidence route also has a lifetime

Как consent в Article 10, выбранный proof path не должен считаться вечным.

Маршрут строился при:

```text
state = S1
authority_epoch = 22
policy = v17
risk_profile = R4
```

Если система дошла до execution boundary уже при:

```text
state = S2
authority_epoch = 23
policy = v18
risk_profile = R7
```

старый route decision может быть неприменим.

Отсюда ещё один invariant:

> **A previously optimal proof route does not imply a currently admissible proof route.**

И operational rule:

```text
route validity must be re-evaluated
when bound causal coordinates materially change
```

---

## Sync and async as profiles, not religions

Теперь можно аккуратно вернуться к исходному вопросу.

### Sync profile

```text
DecisionEvent(E1): ALLOW
        ↓
atomic validate + consume
        ↓
Execution(X1)
```

Может быть лучшим route, если:

- нет ожидания внешнего actor;
- state достаточно стабилен;
- required obligations можно закрыть локально;
- risk не требует дополнительной независимости.

### Async profile

```text
DecisionEvent(E1)
        ↓
DEFER
        ↓
external actor / evidence
        ↓
resolve
        ↓
revalidate
        ↓
consume(E1, X1)
        ↓
Execution(X1)
```

Нужен, если obligation не может быть закрыто внутри текущего synchronous boundary.

### Hybrid profile

```text
cached strong evidence
        ↓
cheap live freshness check
        ↓
local consume
        ↓
execute
```

Это часто будет наиболее интересный маршрут.

Он использует уже оплаченное сильное доказательство, но не делает вид, что прошлое автоматически актуально сейчас.

---

## Example 1 — read a local file

```text
action: read config
risk: low
reversible: yes
external side effect: none
state volatility: low
```

Required obligations:

```text
scope allowed
actor allowed
```

Possible route:

```text
local policy check
      ↓
read
```

Запуск human DEFER здесь не добавляет пропорциональной ценности.

---

## Example 2 — medium-risk API mutation

```text
action: update customer metadata
risk: medium
reversible: mostly
state volatility: medium
```

Strong evidence уже было получено недавно.

Но customer state мог измениться.

Possible route:

```text
cached verified decision
        ↓
revalidate customer version
        ↓
revalidate authority
        ↓
one-shot consume
        ↓
PATCH
```

---

## Example 3 — high-value payment

```text
action: send payment
risk: high
reversible: no / expensive
recipient sensitivity: high
state volatility: high
```

Required obligations:

```text
fresh recipient binding
current authority
current balance/state
independent verification
human approval
one-shot consumption
settlement provenance
```

Possible route:

```text
fresh evidence
     ↓
independent verifier
     ↓
DEFER
     ↓
human approval
     ↓
revalidate recipient + state + authority
     ↓
consume exact authorization occurrence
     ↓
execute payment
     ↓
record settlement outcome
```

Здесь high-assurance route не является over-verification.

Он соответствует цене ошибки.

---

## Example 4 — same payment, different moment

Самое важное начинается, когда nominal action не меняется.

Пусть человек только что вручную подтвердил recipient и amount, authority state стабилен, а independent verifier уже выпустил свежий signed result.

Тогда следующий execution attempt может иметь другой оптимальный маршрут — **если** policy допускает reuse evidence и freshness predicates всё ещё hold.

```text
reuse verified evidence
        ↓
cheap freshness + authority check
        ↓
new bounded authorization occurrence
        ↓
consume
        ↓
execute
```

То есть даже одинаковый tool call не обязан иметь одинаковую логистику доказательств.

Контекст — часть задачи.

---

## Failure mode: optimizer as a safety bypass

Самая опасная реализация Evidence Routing будет выглядеть разумно:

```text
route score =
  0.5 * latency
+ 0.3 * compute_cost
+ 0.2 * safety_score
```

Проблема в том, что hard safety obligation превратилось в negotiable weight.

В плохом состоянии optimizer может выбрать:

```text
slightly unsafe
but much cheaper
```

Поэтому модель должна быть двухфазной:

```text
PHASE 1
construct / filter admissible routes

PHASE 2
optimize cost among admissible routes
```

Это один из главных falsification points статьи.

---

## Failure mode: evidence laundering

Cached evidence создаёт другую опасность.

```text
historically strong evidence
        ↓
route optimizer sees "verified"
        ↓
reuses forever
```

Так proof strength превращается в замену freshness.

Но:

> **Strong evidence about the past is not automatically adequate evidence about the present.**

Поэтому стоимость route должна учитывать не только наличие evidence, но и его applicability сейчас.

---

## Failure mode: route thrashing

Если каждый маленький state change заставляет optimizer полностью перестраивать route, runtime может начать oscillate:

```text
sync
→ async
→ sync
→ independent
→ async
```

Нужны:

- materiality thresholds;
- bounded re-planning;
- hysteresis where appropriate;
- explicit route invalidation reasons.

Иначе доказательная система превращается в scheduler, который тратит больше ресурсов на выбор проверки, чем на саму работу.

---

## Failure mode: invisible cost model

Если два runtime выбирают разные proof paths, но никто не знает их cost/constraint model, сравнение становится почти бессмысленным.

Поэтому route decision должен по возможности раскрывать:

```text
hard obligations
available paths
selected path
rejected paths
cost dimensions used
bound context
validity conditions
```

Не обязательно публиковать private policy internals.

Но causal explanation выбора должна быть проверяема настолько, насколько это допускает threat model.

---

## The evidence supply chain

В этот момент становится видно, что agentic trust infrastructure начинает напоминать supply chain.

```text
claim / intent
      ↓
evidence acquisition
      ↓
verification
      ↓
transport / reference
      ↓
freshness maintenance
      ↓
authorization binding
      ↓
consumption
      ↓
execution
      ↓
outcome observation
```

Каждый stage может:

- задержаться;
- устареть;
- потерять provenance;
- быть продублирован;
- приехать не в ту точку;
- быть слишком дорогим;
- оказаться недостаточным для current obligation.

Поэтому trust layer будущих agent systems — это не только cryptography, guardrails или policy.

Это ещё и **evidence logistics**.

---

## From proof storage to proof delivery

Большинство систем сегодня думает о доказательствах как о storage problem:

```text
Where do we store logs?
Where do we store receipts?
Where do we store approvals?
```

Но автономному runtime нужен другой вопрос:

> **Как нужное доказательство попадёт к нужному execution boundary до того, как действие станет реальным?**

Это уже delivery problem.

И delivery имеет:

```text
route
cost
freshness
SLA
failure modes
fallbacks
```

То есть proof infrastructure постепенно становится не архивом, а транспортной системой.

---

## A new three-layer stack

После Articles 08–11 можно увидеть компактный стек.

```text
ACI
Who may act now?

        ↓

ACB
Which exact permission may this execution consume?

        ↓

Evidence Routing
Which admissible proof path should be used here and now?
```

Это три разные задачи.

### ACI

Проверяет causal authority.

### ACB

Привязывает authorization occurrence к execution occurrence.

### Evidence Routing

Выбирает, каким допустимым способом закрыть необходимые proof obligations в текущих causal coordinates.

Ни один слой не должен поглощать остальные.

---

## The compact invariants

Article 11 предлагает шесть коротких правил.

> **1. The strongest proof path is not automatically the best proof path.**

> **2. The cheapest proof path is not automatically admissible.**

> **3. First filter by proof obligations; only then optimize cost.**

> **4. Sync vs async may be a contextual route choice rather than a universal policy category.**

> **5. A previously optimal proof route does not imply a currently admissible route.**

> **6. Route selection is not execution authority.**

И наиболее общая формула:

> **Evidence should be sufficient, current and proportionate — not maximal by default.**

---

## Smallest falsifiable routing suite

Если превратить идею в executable conformance, минимальный набор должен проверять не только happy path.

### Case 1 — low-risk local action

Expected:

```text
sync route admissible
unnecessary human route dominated by cost
```

### Case 2 — missing freshness obligation

```text
cheap cached route
```

должен быть BLOCKED, если freshness required и не доказана.

### Case 3 — high-risk irreversible action

Local-only route должен быть исключён из admissible set, если policy требует independent verification + human authorization.

### Case 4 — authority epoch changes after route selection

Old route decision invalidates.

### Case 5 — one-shot authorization already consumed

Retry должен либо получить новый authorization route, либо быть BLOCKED.

### Case 6 — same semantic action, different risk coordinates

Optimizer должен иметь возможность выбрать другой допустимый path.

### Case 7 — cheapest route violates hard obligation

Optimizer обязан выбрать более дорогой admissible route или BLOCK.

### Case 8 — no admissible route exists

Correct result:

```text
BLOCKED
```

а не:

```text
best-effort execution
```

---

## What would falsify the thesis?

Эта статья не должна быть защищена от критики определением.

Модель станет слабее или потребует пересмотра, если окажется, что:

1. route optimization создаёт больше скрытой complexity, чем экономит;
2. proof obligations невозможно достаточно стабильно формализовать;
3. cost models слишком manipulable и становятся новым attack surface;
4. dynamic routing ухудшает auditability относительно фиксированных profiles;
5. route re-planning создаёт небезопасные race conditions;
6. простая небольшая система получает больше пользы от fixed policy, чем от graph routing;
7. независимые реализации не могут согласиться даже на минимальный definition of admissibility.

Если такие counterexamples воспроизводимы, Evidence Routing должен сужать scope, а не объявлять их неправильными.

---

## Reader poll — согласен, частично или нет?

Эта статья специально заканчивается не выводом, а голосованием.

Тезис под голосование:

> **The strongest authorization / verification path is not automatically the best path. A runtime should select the lowest-cost admissible evidence route that still satisfies the proof obligations of the current action, state, authority, time and risk.**

### Голосовать

- [✅ **Agree** — согласен с основной моделью](https://github.com/safal207/RESONANCE/issues/58#issuecomment-5301268390)
- [🟡 **Partially agree** — идея полезна, но в модели не хватает важного ограничения](https://github.com/safal207/RESONANCE/issues/58#issuecomment-5301268556)
- [❌ **Disagree** — считаю саму модель маршрутизации ошибочной или опасной](https://github.com/safal207/RESONANCE/issues/58#issuecomment-5301268783)

Откройте выбранный вариант и поставьте ему 👍.

Полный poll thread:

https://github.com/safal207/RESONANCE/issues/58

Если выбираете `Partially` или `Disagree`, особенно полезен короткий counterexample.

### Что означает голосование

Ничего из этого не является доказательством корректности статьи.

```text
100 Agree votes
    !=
formal proof
```

и:

```text
1 reproducible counterexample
    may be more valuable than
100 Agree votes
```

Poll нужен для другого:

- найти missing constraints;
- собрать реальные implementation contexts;
- увидеть, где abstraction ломается;
- отделить широкое согласие от проверяемой correctness.

---

## The shift

Сначала казалось, что проблема — выбрать между synchronous и asynchronous authorization.

Потом оказалось, что consent имеет causal lifetime.

Затем появилась граница consumption.

Теперь следующий сдвиг выглядит так:

```text
authorization is not only a decision

proof is not only an artifact

verification is not only a gate

all three participate in a route
through a changing causal system
```

То есть будущая trust infrastructure может оптимизировать не только действия агента.

Она будет оптимизировать **путь самого доказательства к действию**.

И если этот путь выбран правильно, система не будет ни слепо доверять дешёвому route, ни парализовать себя максимальной проверкой в каждой точке.

Она будет делать то, что делает хорошая логистика:

> **доставлять ровно то доказательство, которое нужно, туда, где оно нужно, тогда, когда оно ещё действительно.**

---

## Next experiment

Следующий falsifiable шаг — executable **Evidence Routing Conformance** поверх ACI + ACB:

```text
causal context
      ↓
required proof obligations
      ↓
admissible route set
      ↓
constrained path selection
      ↓
route validity binding
      ↓
ACI
      ↓
ACB
      ↓
execution
      ↓
outcome provenance
```

Главный вопрос verifier-а будет уже не только:

> Было ли действие разрешено?

И не только:

> Какое разрешение оно потребило?

Но ещё:

> **Можем ли мы доказать, что выбранный proof path был допустимым и уместным именно в той причинной точке, где действие стало реальным?**
