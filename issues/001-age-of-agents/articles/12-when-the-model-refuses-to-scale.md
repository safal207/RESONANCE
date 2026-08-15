# When the Model Refuses to Scale — почему честный FAIL важнее красивой гипотезы

**Article ID:** I001-RN-WMRS  
**Deck:** Самый опасный момент исследовательского AI-агента наступает не тогда, когда эксперимент падает, а когда локальный успех начинает превращаться в глобальную историю. На примере COSMIC ORGANICS / MORPHOS мы прошли путь от красивой идеи programmable matter до воспроизводимого 2D Pareto-эффекта — а затем заморозили модель и увидели, что она не переносится на 7×7 и 9×9 без изменения архитектуры. Этот FAIL оказался не концом гипотезы, а указателем на следующий причинный уровень.  
**By:** RESONANCE Editorial  
**Status:** Published  
**Last verified:** 2026-08-15  
**Languages:** RU  
**Canonical identity:** Issue 001 · Scientific Agent Generalization / Negative Evidence / Scale-Aware Architecture

---

## Самая удобная ошибка — поверить собственному успеху

Есть простой способ сделать исследовательский проект убедительным.

Найти конфигурацию, которая работает.

Показать красивую метрику.

Сравнить её с простым baseline.

Назвать результат новым принципом.

А потом больше никогда не задавать вопрос:

> **Что произойдёт, если мы перестанем подстраивать систему под эксперимент?**

Для человеческого исследователя это старая проблема.

Для автономного исследовательского агента она становится инфраструктурной.

Потому что агент умеет очень быстро:

```text
сгенерировать гипотезу
        ↓
написать модель
        ↓
запустить sweep
        ↓
найти удачную конфигурацию
        ↓
объяснить, почему она логична
        ↓
создать следующую версию
        ↓
получить ещё один локальный успех
```

Если в этой цепи нет механизма, который заставляет систему **заморозить собственную победу и попытаться её уничтожить**, агент может стать идеальной машиной подтверждения самого себя.

Именно поэтому отрицательный результат — не побочный продукт научного процесса.

В agentic research он должен быть **first-class state transition**.

---

## От «космической органики» к вычислимой гипотезе

COSMIC ORGANICS начался с гораздо более широкой идеи.

Если материя может существовать в разных состояниях — аморфном, смешанном, кристаллическом, органическом, ионном, фотонном — можно ли рассматривать переход между состояниями не только как физический эффект, но и как вычисление?

Вместо классической схемы:

```text
Data + Instructions
        ↓
      CPU
        ↓
     Result
```

мы сформулировали другую:

```text
Material State
      +
Interaction
      +
Constraint
      +
Stimulus / Energy
      +
Time
      ↓
State Transition
      ↓
Function
```

В предельно короткой форме:

> **Состояние среды может быть не только памятью программы. Сам переход состояния может быть частью вычисления.**

Это стало MORPHOS Protocol.

Но протокол сам по себе ничего не доказывает.

Поэтому первым принципом проекта стало разделение:

```text
VERIFIED
HYPOTHESIS
HORIZON
```

И первый исполняемый слой — MORPHOS-0 — был намеренно игрушечным.

Три состояния:

```text
A — amorphous
M — mixed
C — crystalline / ordered
```

Локальная связь.

Пороговый переход.

Детерминированный state digest.

Никаких заявлений о новом материале.

Никаких заявлений о новом физическом процессоре.

Только вопрос:

> Может ли управляемая структурная динамика демонстрировать полезное вычислительное поведение?

---

## Первый хороший результат был недостаточно хорош

MORPHOS-0 быстро показал пространственный эффект.

Локальная связь могла исправлять структурный дефект лучше, чем uncoupled-версия той же модели.

Это выглядело обещающе.

Но temporal benchmark сразу показал провал.

Повторяющиеся импульсы ниже порога не накапливались.

```text
0.2
0.2
0.2
0.2
0.2
```

при пороге:

```text
0.35
```

оставляли систему без нужного перехода.

Вместо того чтобы поменять benchmark, мы зафиксировали этот FAIL.

Следующий слой — MORPHOS-T1 — добавил retained activation:

\[
a_{t+1}=\lambda a_t+d_t
\]

После этого прежний failing input стал проходить.

Но это ещё ничего не означало.

Поэтому рядом появились negative controls:

```text
zero input
isolated subthreshold pulse
alternating +/- pulse
```

Новая память должна была решать исходную проблему, не создавая самопроизвольных переходов.

Так возник первый важный pattern проекта:

> **Новая способность считается улучшением только если она чинит зафиксированный failure и одновременно сохраняет старые инварианты.**

---

## Потом мы спросили: а это вообще устойчиво?

Одна удачная точка параметров ничего не говорит о системе.

Поэтому следующий шаг был не «улучшить модель», а прогнать robustness map:

```text
memory_decay
× threshold
× coupling
× pulse amplitude
```

Всего:

\[
400
\]

конфигураций.

Требовалось одновременно пройти пять ворот:

```text
subthreshold accumulation
defect repair
zero-input stability
isolated-pulse decay
alternating-pulse cancellation
```

Полный PASS дали только:

```text
20 / 400
```

то есть:

\[
5\%
\]

пространства параметров.

Это уже меняет язык результата.

Не:

> MORPHOS устойчив.

А:

> **У MORPHOS существует воспроизводимая, но узкая область устойчивого поведения в объявленной сетке параметров.**

Для исследовательского агента разница огромна.

Первое предложение превращает локальное наблюдение в свойство системы.

Второе сохраняет границу доказательства.

---

## А потом внешний baseline уничтожил первую красивую историю

До этого момента мы сравнивали MORPHOS в основном с абляциями MORPHOS.

Но если новая архитектура делает что-то лучше собственной урезанной версии, это ещё не значит, что она вообще нужна.

Поэтому появились простые внешние алгоритмы:

```text
nearest-neighbor Majority CA
Leaky Three-State accumulator
```

И они повторили наши положительные toy tasks.

Результат:

```text
MORPHOS wins:   0
Baseline wins:  0
Ties:           3
```

Первая версия истории:

> local coupling создаёт вычислительное преимущество

перестала быть допустимой.

Более точная версия стала такой:

> local coupling создаёт полезное поведение относительно uncoupled ablation, но текущие задачи не показывают алгоритмической уникальности относительно простых внешних baseline.

Это не ухудшение исследования.

Это его очищение.

---

## State capacity нашёл настоящий дефект архитектуры

Следующий вопрос был уже не:

> Может ли система решить задачу?

А:

> Сколько различных состояний она вообще способна удерживать?

Для 7 бинарных ячеек существует:

\[
2^7=128
\]

возможных A/C паттернов.

При сильной связи, которая хорошо исправляла прежний дефект, MORPHOS-T1 устойчиво удерживал только:

```text
2 / 128
```

то есть около:

\[
1\ bit
\]

эффективной бинарной ёмкости на выбранном тесте.

Majority CA сохранял существенно больше устойчивых состояний.

А после одиночной ошибки у MORPHOS проявился новый failure mode:

# Mixed-State Dead Zone

Ячейка попадала в промежуточное состояние `M`, но локального drive уже не хватало ни для перехода к `A`, ни для перехода к `C`.

Система не разрушалась.

Она **застревала между решениями**.

Это важнее, чем просто плохая метрика.

Потому что появилась причинная мишень.

Не «MORPHOS плохо восстанавливает ошибки».

А:

> **Промежуточное состояние становится поглощающей областью при определённой комбинации coupling, threshold и temporal accumulation.**

Вот это уже можно рефакторить.

---

## T2 починил механизм — и всё равно не победил

MORPHOS-T2 получил отдельный relaxation threshold для `M`.

То есть мы не стали глобально снижать порог всей системы.

Мы спросили точнее:

> Можно ли изменить только динамику промежуточного состояния?

Был прогнан новый grid из:

```text
243 configurations
```

Часть конфигураций действительно убрала dead zone.

Некоторые повысили recovery.

Некоторые сохранили capacity.

Но ни одна не доминировала Majority CA одновременно по:

```text
capacity
recovery
transition cost
```

И это было очень полезно.

Потому что ещё один scalar threshold перестал быть перспективной точкой дальнейшего поиска.

FCRP-язык здесь звучит почти буквально:

```text
мы вошли на уровень параметра
        ↓
нашли divergence
        ↓
починили локальный механизм
        ↓
поднялись уровнем выше
        ↓
родительский invariant всё ещё не улучшился
```

Значит, refactor point находился уже не там.

---

## Геометрия изменила Pareto frontier

Следующий эксперимент поменял не коэффициент, а топологию системы.

Появился MORPHOS-2D-H:

```text
5 × 5 lattice
four-neighbor topology
checkerboard heterogeneity
anchor cells
adaptive cells
```

Теперь разные ячейки имели разные локальные свойства.

На discovery-наборе это выглядело интересно.

Поэтому кандидат **заморозили до confirmation**.

Это принципиальная граница.

После freeze запрещено менять параметры потому, что новый набор данных оказался неудобным.

На отдельном 256-input SHA-256 confirmation corpus кандидат показал:

```text
binary fixed attractors:
MORPHOS     200
Majority CA 147

observed capacity:
MORPHOS     7.6439 bits
Majority CA 7.1997 bits

one-bit recovery:
MORPHOS     58.80%
Majority CA 65.90%

recovery transition cost:
MORPHOS      2.4586
Majority CA 38.8052
```

Впервые появился новый Pareto-регион.

MORPHOS удерживал больше наблюдаемых бинарных attractor’ов и делал переходы гораздо дешевле по algorithmic transition count.

Но восстанавливал ошибки хуже.

Поэтому корректный вывод был не:

> MORPHOS победил Majority CA.

А:

> **2D heterogeneity создаёт воспроизводимую Pareto-недоминируемую точку в объявленном сравнении.**

Это уже интересный результат.

Но именно здесь начинается самый опасный момент.

Потому что теперь очень хочется написать:

> Архитектурный принцип найден.

---

# Generalization Gate

Вместо этого мы сделали противоположное.

Кандидат заморозили.

И атаковали.

Без retuning.

Generalization Gate включил:

```text
multiple unseen 5×5 seeds
7×7 transfer
9×9 transfer
mask ablations
neighborhood ablations
1/2/3-bit corruption
local recurrent threshold baselines
```

Именно здесь модель отказалась поддерживать красивую историю.

---

## По новым seed’ам эффект жив

На пяти новых 5×5 корпусах направление tradeoff повторилось.

В среднем:

```text
observed capacity delta: +0.3143 bits
one-bit recovery delta:  -8.56 percentage points
seed transition cost:     0.3785× baseline
```

То есть локальный 5×5 Pareto-эффект не был случайностью одного confirmation seed.

Это важно.

Но потом изменился размер системы.

---

## 5×5 → 7×7 → 9×9

Те же параметры.

Та же логика.

Никакой size-specific настройки.

Результат по observed capacity delta относительно Majority CA:

```text
5×5   +0.2801 bits
7×7   -0.1520 bits
9×9   -0.7063 bits
```

Знак изменился.

Это и есть момент, ради которого нужен Generalization Gate.

Локальное свойство не стало автоматически масштабным свойством.

И теперь мы знаем намного больше, чем если бы просто продолжили улучшать 5×5.

---

# Fixed coupling is not scale invariance

Главный причинный вывод эксперимента можно записать так:

\[
\boxed{\text{fixed local coupling} \not\Rightarrow \text{scale-invariant behavior}}
\]

Почему?

Потому что при изменении размера меняется не только число ячеек.

Меняются:

```text
distribution of local motifs
boundary / interior ratio
path lengths
attractor landscape
error propagation distances
cluster geometry
effective interaction topology
```

Даже если локальное правило формально не меняется, **контекст его действия меняется**.

Значит, архитектура, которая хочет переноситься между масштабами, возможно, должна учитывать масштаб как часть причинного состояния.

Не обязательно явным числом `N`.

Но через нормализованные свойства:

```text
local degree
relative neighborhood density
hierarchical region
boundary class
local entropy
distance scale
cluster size
multi-scale coupling
```

Иначе мы пытаемся применять локальную константу как универсальный закон.

---

## Это тот же FCRP, только теперь над исследованием

Fractal Causal Refactoring Protocol говорит:

```text
выбери правильный масштаб
        ↓
восстанови идею этого уровня
        ↓
сравни проект и фактическое состояние
        ↓
найди first meaningful divergence
        ↓
выбери refactor point
        ↓
проверь родительские invariants
```

В MORPHOS мы сначала думали, что divergence находится в локальном threshold.

Потом — в temporal memory.

Потом — в mixed-state relaxation.

Но каждый следующий тест поднимал нас выше.

```text
cell threshold
      ↓
temporal state
      ↓
intermediate-state dynamics
      ↓
heterogeneous topology
      ↓
scale transfer
```

После Generalization Gate first meaningful divergence уже выглядит иначе:

> **Не конкретная ячейка ведёт себя неправильно. Архитектура не определяет, как локальная связь должна преобразовываться при изменении масштаба.**

Это другой уровень проблемы.

И другой уровень процессора.

---

# MORPHOS-S1

Следующая гипотеза поэтому не должна быть:

> найдём ещё лучший coupling для 7×7.

Это было бы просто новой подгонкой.

Следующий кандидат должен решать более общий контракт:

# Scale-Invariant Structural Dynamics

Условно:

\[
c_i=f(
local\ geometry,
local\ degree,
region\ scale,
hierarchy,
state\ context
)
\]

вместо:

\[
c_i=constant
\]

Возможная архитектура:

```text
cell
 ↓
local neighborhood
 ↓
mesoscopic cluster
 ↓
region
 ↓
global lattice
```

И на каждом уровне действует собственная структурная связь.

Не центральный контроллер.

Не один глобальный weight.

А композиция локальных взаимодействий, нормализованных относительно уровня.

Это уже ближе к тому, что COSMIC ORGANICS изначально пытался выразить:

> функция возникает не из одной идеальной части, а из организации взаимодействий между разными состояниями и масштабами.

---

## Multi-bit noise тоже не дал нам удобной победы

При corruption в 1, 2 и 3 бита MORPHOS сохранял тот же характер tradeoff.

Recovery оставался ниже Majority CA.

Но transition cost оставался намного ниже.

Примерно:

```text
1 bit  cost ratio ≈ 0.066×
2 bit  cost ratio ≈ 0.134×
3 bit  cost ratio ≈ 0.203×
```

Это важно не как доказательство физической энергоэффективности.

Transition count — только алгоритмический proxy.

Но это показывает, что архитектура остаётся отдельной точкой пространства свойств.

Она не превращается в Majority CA при усложнении шума.

---

## Более сильный recurrent baseline тоже не закрыл вопрос

Generalization Gate добавил локальный recurrent threshold challenge.

15 параметрических точек схлопнулись в три различимых поведенческих режима.

И результат снова оказался неудобно хорошим для науки.

Ни один recurrent regime не доминировал замороженный MORPHOS одновременно по наблюдаемой capacity, one-bit recovery и seed transition cost.

Но MORPHOS тоже не доминировал весь recurrent frontier.

То есть:

```text
не победа
не поражение
не эквивалентность
```

А отдельная Pareto-точка.

Это гораздо полезнее громкого benchmark headline.

Потому что теперь вопрос становится:

> **Какое физически или вычислительно полезное ограничение соответствует именно этой точке?**

Если реальный substrate очень дорого переключать, но дёшево хранить состояние, низкий transition count может быть важен.

Если критична максимальная коррекция ошибок — возможно, нет.

Но до физической калибровки это остаётся гипотезой.

---

# Что должен уметь исследовательский AI-агент

Из этой истории вытекает более общий контракт.

Agentic science не должна быть просто системой, которая быстро строит модели.

Она должна уметь управлять **жизненным циклом гипотезы**.

Минимальная цепь выглядит так:

```text
HYPOTHESIS
    ↓
smallest falsifiable model
    ↓
locked benchmark
    ↓
negative controls
    ↓
external baseline
    ↓
robustness map
    ↓
freeze candidate
    ↓
separate confirmation
    ↓
generalization attack
    ↓
PASS / FAIL / PARTIAL
    ↓
causal refactor target
```

И здесь есть несколько жёстких правил.

---

## Rule 1 — Не удаляй старый провал после новой версии

Если T1 исправил failure T0, failure T0 должен остаться в истории.

Иначе невозможно понять, что именно новая архитектура решила.

```text
failure ≠ мусор
failure = predecessor state гипотезы
```

---

## Rule 2 — Freeze before confirmation

Если кандидат можно менять после просмотра confirmation data, это не confirmation.

Это следующая итерация discovery.

Поэтому:

```text
candidate identity
parameters
benchmark identity
confirmation generator
```

должны быть связаны до запуска.

---

## Rule 3 — Baseline должен быть внешним достаточно рано

Победа над собственной абляцией полезна для causal diagnosis.

Но она не доказывает необходимость новой архитектуры.

Нужен вопрос:

> Какой самый простой другой механизм воспроизводит тот же эффект?

Если воспроизводит — гипотеза должна стать уже.

---

## Rule 4 — Generalization FAIL не разрешает немедленный retuning

Если 5×5 работает, а 9×9 нет, следующий шаг — не обязательно оптимизировать параметры 9×9.

Сначала надо спросить:

> Почему invariant не переносится?

И найти уровень расхождения.

Иначе мы строим семейство отдельных моделей, а потом называем его одним принципом.

---

## Rule 5 — Оптимизируй архитектуру только после локализации причинного уровня

Это прямое продолжение FCRP.

Не менять всё сразу.

Не добавлять complexity потому, что «может помочь».

А определить:

```text
какой parent invariant сломан
на каком масштабе
какая зависимость отсутствует
какой минимальный новый механизм её выражает
```

Для MORPHOS после Generalization Gate ответ сейчас выглядит так:

```text
missing relationship:
local interaction ↔ system scale
```

Поэтому следующий эксперимент должен быть scale-aware.

---

# Evidence must survive the narrative

У AI есть особая способность.

Он очень хорошо объясняет результат.

Это полезно.

И опасно.

Потому что почти любой outcome можно встроить в красивую post-hoc narrative.

```text
метрика выросла → подтверждение
метрика упала → tradeoff
не масштабируется → emergent boundary
baseline лучше → complementary regime
```

Каждая отдельная фраза может быть разумной.

Но вместе они могут создать систему, в которой гипотеза никогда не умирает.

Поэтому evidence architecture должна быть сильнее narrative architecture.

То есть машина должна хранить не только объяснение.

Она должна хранить:

```text
what was frozen
what was tested
what failed
what passed
what baseline won
which metric reversed sign
which claim became inadmissible
what new hypothesis replaced it
```

Именно здесь RESONANCE становится не просто журналом.

Он становится operational memory исследования.

---

# Publication must not promote a hypothesis to truth

Это правило уже появлялось в нашей trust infrastructure.

Здесь оно приобретает научную форму.

Публикация может зафиксировать интерпретацию.

Она не должна повышать её статус автоматически.

Для MORPHOS корректная лестница сейчас такая:

```text
VERIFIED externally:
physical stateful materials and neuromorphic devices exist as research fields

HYPOTHESIS supported computationally:
heterogeneous structural-state dynamics can occupy a distinct Pareto region
on declared finite toy-model corpora

FAILED generalization claim:
the frozen 5×5 parameterization does not transfer as a scale-invariant advantage
on 7×7 and 9×9

NEXT HYPOTHESIS:
scale-aware / hierarchical coupling may preserve the useful tradeoff across size

HORIZON:
physical MORPHOS processor
biohybrid morphogenesis
organ-scale applications
quantum-biological mechanisms
```

Такой журнал сложнее читать, чем манифест.

Но намного полезнее строить по нему систему.

---

# The Research Agent Invariant

Из всей истории можно вынести один главный invariant:

> **A research agent must be able to make its own previous claim less true.**

Если новый эксперимент не может сузить, понизить или опровергнуть старый вывод, система не занимается проверкой.

Она занимается производством подтверждений.

По-русски:

> **Исследовательский агент должен уметь не только усиливать гипотезу, но и доказуемо уменьшать область, в которой она допустима.**

В нашем случае область уменьшилась так:

```text
"MORPHOS может иметь преимущество"
        ↓
"не на простых toy tasks — baseline их повторяет"
        ↓
"T2 чинит dead zone, но не доминирует"
        ↓
"2D heterogeneity создаёт новый Pareto point"
        ↓
"эффект повторяется по 5×5 seeds"
        ↓
"но не переносится на 7×7 / 9×9 без изменения архитектуры"
```

Это не деградация идеи.

Это превращение идеи в объект исследования.

---

# Следующий вопрос

После этого нам уже неинтересно искать ещё одну удачную пару threshold/coupling.

Следующий вопрос гораздо сильнее:

> **Можно ли определить локальные структурные взаимодействия так, чтобы их вычислительный смысл сохранялся при изменении масштаба системы без size-specific retuning?**

Если нет — MORPHOS останется интересной семейством локальных dynamical systems.

Если да — появится основание говорить о более общем архитектурном принципе.

Следующий кандидат:

# MORPHOS-S1 — Scale-Invariant Structural Dynamics

Его первый контракт должен быть жёстким:

```text
same architectural rule
        ↓
5×5
7×7
9×9
        ↓
no size-specific parameter tuning
        ↓
predeclared external baselines
        ↓
predeclared generalization metrics
        ↓
exact evidence
```

И если S1 снова не масштабируется — это тоже результат.

Потому что правильная исследовательская система не обещает нам победу.

Она обещает более точную карту реальности.

---

## Evidence boundary

Текущая статья опирается на воспроизводимые computational artifacts COSMIC ORGANICS.

Ключевые этапы:

```text
MORPHOS foundation
        ↓
P1 falsification
        ↓
T1 temporal memory
        ↓
400-point robustness map
        ↓
external baselines
        ↓
state-capacity / dead-zone analysis
        ↓
T2 repair grid
        ↓
2D heterogeneous frozen confirmation
        ↓
Generalization Gate
```

Канонические GitHub surfaces на момент публикации:

- COSMIC ORGANICS repository: https://github.com/safal207/COSMIC-ORGANICS
- 2D heterogeneous confirmation — PR #8: https://github.com/safal207/COSMIC-ORGANICS/pull/8
- Generalization Gate — PR #9: https://github.com/safal207/COSMIC-ORGANICS/pull/9

Generalization Gate evidence summary digest:

```text
sha256:953e38a05958f970386bd256b964ade1d9240b3ff134da696bf8d9942e9850c0
```

Граница утверждения остаётся load-bearing:

> **Это computational toy-model research. Наблюдаемая capacity основана на конечных sampled attractor corpora. Transition count является algorithmic cost proxy, а не измеренной физической энергией. Результаты не доказывают новый материал, физический процессор, биологическую технологию или quantum mechanism.**

---

## Final principle

Самая ценная модель — не та, которая однажды показала красивый результат.

И не та, которую можно бесконечно улучшать до победы.

А та, у которой есть граница, за которой она перестаёт работать — и система умеет эту границу найти, доказать и превратить в следующий вопрос.

```text
local success
    ↓
freeze
    ↓
attack
    ↓
FAIL
    ↓
find causal level
    ↓
new architecture
```

В эпоху автономных исследовательских агентов это может оказаться одним из главных механизмов научной честности.

Потому что интеллект, который умеет только находить ответы, полезен.

Но интеллект, который умеет **доказать, где заканчивается его собственный ответ**, — уже способен участвовать в исследовании.

---

**RESONANCE Issue 001 — THE AGE OF AGENTS**  
**Article 12 — When the Model Refuses to Scale**