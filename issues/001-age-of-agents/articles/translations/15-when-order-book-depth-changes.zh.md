# 订单簿变了，许可还在。

RESONANCE Verify 如何在模拟提交订单前通过重新检查发现深度不足，以及为什么最后一次观测之后的状态变化仍然构成独立风险。

交易智能体找到一条路径，估算了成本，并通过了检查。几十毫秒后，它准备将订单传递给下一个环节。屏幕上的价格没有变化，模型计算的收益空间也没有变化，但可用数量已经不足。

最初的决定究竟允许什么：在当时观测到的条件下执行动作，还是允许之后任何参数相似的动作？

我们用一个小型、开放的 RESONANCE Verify 示例分析了这个问题。所有价格、状态和时间戳均为合成数据。示例只检查内存中的准入标志，不连接交易所，也不创建订单。读者可以使用[固定版本的源代码](https://github.com/safal207/resonance-arbitrage-graph/tree/d6317c30833fed7d19edbcaf4f9f7467faa58519)复现结果。

## 一笔订单，两种状态

示例路径从 1,000 USDT 开始，经过 BTC 和 ETH，再回到 USDT。模型在每一跳计入 5 个基点的手续费和 5 个基点的模拟滑点。扣除这些成本后的准入阈值为 30 个基点。

初次检查通过：模型计算的净收益空间约为 +94.66 个基点。引擎将其标记为 `EXECUTE_SIM`，表示仅在模拟中获得准入。

第一跳的最优卖价为每 BTC 80,000 USDT。最初，该价格上的可用数量为 2 BTC，因此第一档的容量为 160,000 USDT。随后，数量降至 0.0075 BTC，容量变为 600 USDT，低于所需的 1,000 USDT。

| 测试夹具中的时间 | 观测到的状态 | 结果 |
| --- | --- | --- |
| 1,000 毫秒：初次检查 | 第一跳容量为 160,000 USDT | `EXECUTE_SIM` |
| 1,075 毫秒：下一份快照 | 价格不变；容量已降至 600 USDT | 新的输入数据 |
| 1,080 毫秒：重新检查 | 需要 1,000 USDT；仅有 600 可用 | `REJECT`，`CAPACITY_EXCEEDED:0` |

这里的 80 毫秒是场景设定的时间间隔，并非真实交易系统的延迟测量值。做出决定时，新快照的年龄为 5 毫秒，允许的最大值为 100 毫秒。

## 新鲜度不能替代容量

在主要场景中，价格和成本模型保持不变。模型计算的净收益空间仍为正，快照也通过了年龄检查。发生变化的是第一跳的可用数量，因此拒绝的确切原因是容量不足。

这样的设置使结果可以被核查：我们能够将数量的影响与价格、时间的影响区分开来。单靠新鲜度规则无法阻止这一情况，因为新的快照确实是新鲜的。

复用旧许可时，示例会在内存中记录允许准入。重新检查时，引擎根据当前快照重建路径，并返回 `CAPACITY_EXCEEDED:0`，撤销准入。两种路径都不会实际调用交易所的订单提交接口。

> 许可的含义，与授予许可时所依据的条件相伴而存。

## 对照场景也必须能够通过

一个拒绝所有情况的示例，无法充分说明检查是否有用。因此，除了变化后的订单簿，我们还加入了一个正向对照：新鲜且未发生变化的快照会保留 `EXECUTE_SIM`。

完整测试夹具包含七种情况。五种预先选定的不利状态会撤销准入，第七种情况则展示这一方法的边界。

| 场景 | 最终判定 | 内存中的准入 |
| --- | --- | --- |
| 新鲜且未变化的订单簿 | `EXECUTE_SIM` | 允许 |
| 第一跳容量降至 600 USDT | `REJECT` | 不允许 |
| 价格变化使模型计算的净收益空间不再为正 | `REJECT` | 不允许 |
| 模型计算的净收益空间仍为正，但低于阈值 | `OBSERVE` | 不允许 |
| 夹具中的交易状态变为 `HALTED` | `REJECT` | 不允许 |
| 快照年龄超过上限 | `REJECT` | 不允许 |
| 深度在最后一次检查之后发生变化 | `EXECUTE_SIM` | 允许；后续诊断返回 `REJECT` |

容量、价格、成本和年龄由现有引擎检查。`HALTED` 条件由专为此夹具添加的独立包装层处理，核心函数 `evaluate_route` 不接收交易所状态。报告分别保留这两个层次的决定。

`OBSERVE` 同样不授予准入。重新检查不能将最初较严格的决定变为许可：初始的 `REJECT` 或 `OBSERVE` 不会仅因后续快照改善而升级为 `EXECUTE_SIM`。

## 再过二十毫秒

在最后一个场景中，重新检查在 1,080 毫秒时看到足够的数量，因此保留准入。随后，这部分数量消失。到了模拟到达时刻，即 1,100 毫秒，同一模型会返回 `REJECT`。

这是一个预期内、尚未解决的情况。决定不会使用未来数据，到达时的快照只会在之后用于诊断。另一个测试专门验证：更改到达时的数据，不会改变更早的判定。

重新检查只能基于它能够获得的观测。它不会预留流动性，也不会将决定与交易所状态进行原子绑定。未被观测到的变化，也可能发生在最后一份快照与检查本身之间。

对集成而言，实际含义是需要单独说明：执行端在接受订单时能够检查哪些约束，以及用什么可观测结果结束该动作。一份新鲜的本地快照不会自动回答这些问题。

## 这些检查究竟确认了什么

在核查的版本中，演示的 12 项测试全部通过。它们覆盖复现、判定的确切原因、快照年龄边界、第二跳的容量单位、拒绝使用未来快照、保留更严格的初始决定，以及发现报告被修改。

再次运行会得到完整且相同的 JSON 结果，SHA-256 也保持一致。报告绑定了夹具、规则、成本参数、状态以及七个实现模块的字节，因此能够发现输入或代码发生变化。

五个被阻止的合成场景，不能提供检测质量的统计估计。十二项测试通过，也不能证明真实交易所的行为。哈希只能确认数据是否一致，不能认证市场观测的真实性。

结果状态为 `UNASSESSED_REPLAY_SOURCE`，模型为 `NONE_ADMISSION_ONLY`：检查对象仅是内存中的准入。这里不模拟跨多个价格档位的成交、队列位置或部分成交，也不涉及真实利润或实测节省的资金。我们没有测试 Quantilan 的系统；本篇文章基于开放的合成示例，不声称获得其团队认可。

## 复现结果

需要 Python 3.11 或更新版本。本次核查在 Linux 上使用 Python 3.12.13 完成。运行本身不需要安装额外 Python 包，也不需要网络访问。

获取仓库，并选择演示的确切版本：

```bash
git clone https://github.com/safal207/resonance-arbitrage-graph.git
cd resonance-arbitrage-graph
git checkout d6317c30833fed7d19edbcaf4f9f7467faa58519
```

检查已保存的报告：

```bash
PYTHONPATH=src python3 -m resonance_arbitrage_graph.exchange_state_demo \
  --fixture examples/quantilan/fixture.json \
  --check examples/quantilan/expected-report.json
```

预期输出：

```text
Replay matches: 313084ae4464b057423496f800225015a4a2b565a0ae81be748aed02c0f5bad0
```

运行 12 项测试：

```bash
PYTHONPATH=src python3 -m unittest discover \
  -s tests -p test_exchange_state_demo.py -v
```

[在 GitHub 上查看夹具与代码](https://github.com/safal207/resonance-arbitrage-graph/tree/d6317c30833fed7d19edbcaf4f9f7467faa58519)。

## 面向真实流程的下一个问题

这个演示为集成讨论提供了一个小而具体的起点：准入决定之前能够获得哪份状态快照，而执行端接受订单时又能检查哪些约束？

下一项有用的实验，是由另一个团队提供一个公开或合成的示例，明确规定状态字段和时间戳。借助它，可以比较预期拒绝、实际原因以及结果是否可复现。这个实验不需要访问凭据或私有策略。

一个在历史上正确的决定，只有在系统确实能够检查的条件范围内，才适用于下一次动作。

## 来源与核查边界

1. [演示说明及其限制](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/docs/QUANTILAN_EXCHANGE_STATE_DEMO.md)。
2. [合成测试夹具](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/examples/quantilan/fixture.json)。
3. [完整的预期报告](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/examples/quantilan/expected-report.json)。
4. [决定比较模块](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/src/resonance_arbitrage_graph/exchange_state_demo.py)。
5. [十二项测试](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/tests/test_exchange_state_demo.py)。
6. [核心路径检查引擎](https://github.com/safal207/resonance-arbitrage-graph/blob/d6317c30833fed7d19edbcaf4f9f7467faa58519/src/resonance_arbitrage_graph/engine.py)。

作者：Aleksei Safonov。源文件核查与本地复现日期：2026 年 9 月 5 日。结果仅适用于所引用的提交和本夹具；本篇文章不声称已有独立的外部复现。
