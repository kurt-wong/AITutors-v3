# PREPROCESSING-V3-CONTRACT v0.2 — DRAFT SKELETON

> **状态**：**已被取代，不进入正式历史**（工作区保留稿）。用途由 `PREPROCESSING-V3-CONTRACT-BLOCKER-ANALYSIS.md` 接替。
> **勘误**：本稿 §CB-3 相关行含两处已更正的错误事实（candidate 层落 `composite_unit`、四消费点/三处互相矛盾）。正确形态 = 两层矛盾 + candidate 零落库 + 静默失败掩盖。权威更正落点：`PREPROCESSING-V3-CONSUMER-GAP-MAP.md` §0 E-1。**勿以本稿 CB-3 事实为准。**
> **性质**：v0.2 起草骨架 = 问题分类与裁决槽位，**不是契约正文**，不含条款措辞。
> **用途**：供 Owner 按类裁决后，再据裁决结果撰写 v0.2 正文。
>
> **输入基线（亲验 2026-09-16）**：
> | 输入 | 仓 / commit | 说明 |
> |---|---|---|
> | Consumer Review v0.2 | AITutors-v3 @ `938535d` | 7 PASS / 3 BLOCK |
> | DSH Closure Plan v1 | preprocessing @ `4fdbb70` | A/B/C 分类 + unit_type 事实档 + figure 草案 + flags 需求 |
> | 被继承契约 | preprocessing `INTEGRATION/PREPROCESSING-INTEGRATION-CONTRACT.md` @ `1fbaf5e` | `git diff 1fbaf5e 4fdbb70 -- INTEGRATION/` → **空**，未改 |
> | DQE 报告 | preprocessing @ `4d78513` | 四重点测量 |
>
> **本骨架不改 preprocessing、不改 V3 adapter、不冻结契约。**

---

## 0. 两份输入的口径调和（必须先读）

Consumer Review v0.2 与 Closure Plan v1 对「什么阻塞冻结」给出**看似相反**的判定：

| 来源 | 判定 | 范围 |
|---|---|---|
| Closure Plan §1-A | 必须修复才能冻结 = **0 项** | **数据卫生项** |
| Consumer Review v0.2 | 阻塞冻结 = **3 项**（B1/B2/B3） | **接口/契约项** |

**两者不矛盾——各自在其范围内成立。** DSH 的 A 类问的是「脏数据是否阻塞冻结」，答案是否（契约冻结对象 = 实测值域 + fail-closed 消费条款，不是清洁数据）。V3 的 BLOCK 问的是「契约承诺在 V3 消费路径上是否可验证」，答案否（传输层/hash/unit_type 三项不可验证）。

**但有两处 DSH 陈述预设了 V3 不存在的消费路径**，须在 v0.2 中调和（见 CB-1、CB-3）：

| DSH 陈述 | 位置 | 预设 | V3 实况 |
|---|---|---|---|
| 「V3 对账必须用 IR provenance 或独立重算源 sha」 | Closure Plan §1-C-4 | V3 有 IR 消费能力或可用的独立重算 | V3 全仓 **0 命中** IR 消费；自算 hash 两路均对不上（Review §A.3） |
| 「非闭集值 → PENDING 通道，不静默消费，**fail-closed 生效中**」 | Closure Plan §2 影响节 | 消费侧隔离已实现 | V3 四消费点**零隔离**，三处解释互相矛盾（Review §B.2） |

**这两处不是意见分歧，是跨仓事实错误**（FACT-030/032/033）。v0.2 正文措辞必须以 V3 实况为准，或请 DSH 更正陈述。

---

## 1. Contract blocker（影响接口冻结）

> 判定标准：**阻碍契约 §3 required 清单与 §4 跨边界约束在 V3 消费路径上可验证**。
> 三项共同根因 = **CB-1 传输层未定**；CB-2 依赖 CB-1 才有对账落点；CB-3 依赖 CB-1 才有统一隔离执行面。

### CB-1 · source identity transport（根因）

| 项 | 内容 |
|---|---|
| **事实** | 契约 §2「V3 消费以 IR 为准」；V3 实读 manifest（`Grep resolver_ir|source_sha256` @ `backend/` = **0 命中**；`manifest_reader.py:44-75`）。IR 层 71/71 有 `source_sha256`；manifest 层 **0/166** 有 sha（DQE §4）。 |
| **阻塞什么** | 契约 §3.1 required 清单按 IR 层编写，§4.2「一一对应」主张无处落地——required 承诺在 V3 当前消费路径上**无数据可验证**。 |
| **契约层问题** | 消费载体（IR / manifest / 双载体显式分层）**未在契约中裁定**。 |
| **裁决槽位** | □ Owner 裁定传输层：__________ <br> □ 据此修订契约 §2 措辞：__________ <br> □ 据此修订 §3.1 required 清单归属层：__________ |
| **状态** | **NOT DECIDED** — 修复方向不属本骨架（任务禁止项） |

### CB-2 · hash agreement

| 项 | 内容 |
|---|---|
| **事实** | producer `source_sha256` = 源 md **原始字节** SHA-256（契约 §1.1）。V3 自算两路均对不上：`sha256_hex` 经 canonical_json 引号包裹 → **永远 DIFFER**（`hashing.py:60-62`）；`body_hash` 经 splitlines 规范化 → CRLF/尾随换行文件**漂移**（v0.1 实测 **6/12 DIFFER**；`source_loader.py:43-46`）。 |
| **阻塞什么** | 契约 §1.2「V3 义务：独立重算 sha 比对，不一致 → 阻断」当前**无法执行**——不是机制缺失，是 hash 输入定义不一致（原始字节 vs 规范化文本 vs canonical_json 包裹）。 |
| **契约层问题** | 跨系统对账的 hash **输入定义未在契约中统一约定**。 |
| **裁决槽位** | □ Owner 裁定对账 hash 输入定义：__________ <br> □ 契约 §1.1/§1.2 增补该定义：__________ <br> □ DSH 确认 producer 侧计算输入口径（handoff 007 B2 已请求）：__________ |
| **状态** | **NOT DECIDED** |

### CB-3 · unit_type semantics

| 项 | 内容 |
|---|---|
| **事实** | 非标准值恰 1 例 `andalone_question`（DQE §1，batch-C 可消费面内，IR 忠实携带）。V3 `manifest_reader.py:52` 不校验闭集；四消费点解释**互相矛盾**：annotation 当 standalone（`annotation_adapter.py:101-104`）／span 当 composite（`resolved_span_adapter.py:78`）／Track B 当 composite（`runner_b2.py:117`）／candidate 落 `composite_unit`（`runner_b2.py:252`）。**零隔离。** |
| **阻塞什么** | 契约 §3.3-6 要求隔离进 PENDING，**未实现**；且 DQE §1-A 与 Closure Plan §2 均称「已生效／fail-closed 生效中」——**与代码不符**（FACT-033）。 |
| **契约层问题** | (a) 隔离执行面未定（依赖 CB-1：隔离在哪一层做取决于消费载体）；(b) DSH 侧陈述需更正，否则 v0.2 写入的是错误事实基线。 |
| **裁决槽位** | □ Owner 裁定隔离执行面：__________ <br> □ 请 DSH 更正 DQE §1-A / Closure Plan §2 陈述（handoff 007 B3 已请求）：__________ <br> □ 契约 §3.3-6 措辞是否需按 V3 实况调整：__________ |
| **状态** | **NOT DECIDED** |

**CB 小结**：三项全部 **NOT DECIDED**。CB-1 为根因——未定则 CB-2 无对账落点、CB-3 无统一隔离面。**v0.2 冻结前置 = CB-1~3 裁决完毕。**

---

## 2. Data hygiene（不影响接口冻结）

> 判定标准：**不阻碍契约条款在 V3 消费路径上可验证**——契约 v0.1 已如实披露，配 fail-closed 消费条款即成立。
> 本类**不进冻结前置**。全部执行动作等 Owner 逐项批准（Closure Plan §5）。

| # | 项 | 现状事实 | 契约 v0.1 披露处 | Closure Plan 对应 |
|---|---|---|---|---|
| DH-1 | **figure recovery** | 70,838 引用；悬空 **27,240 处 / 1,396 份**，全部未恢复 `imgs/` 形态；已改写形态悬空=0；源 PDF 在位 1,394/1,396（99.86%）；R50 基线交集恰 2 份已隔离；无 PDF 恰 2 份单列 | §2.4（形态）；**资产在位性未写入** → 见 §4-N1 | §3 恢复计划草案 |
| DH-2 | **flags registry** | 值域天然闭合 2 值（`answer_table_unresolved` 502 单元/596 槽位；`answer_number_mismatch` 91 单元）；`rule_registry.md` **零注册** | §3.2（空值语义）+ §3.2 特别条款（禁静默默认） | §4 登记需求 |
| DH-3 | **historical cleanup** | BUG-14-DATA：D5-A ✅ / D5-B ✅ 70/70 / D5-C·D5-D 待跑 / D5-E 🔒 / **6 份 needs_ruling 待裁定**；72 collisions 零裁定 | 不涉契约条款 | §1-B 清洗序 B4~B6 |

**与契约的关系**：三项均为「如实描述脏数据 + 规定如何 fail-closed」。**数据清洁度不阻塞契约冻结**（Closure Plan §1-A 判定，V3 侧同意此范围内的判定）。

**唯一需契约侧动作**：DH-1 的资产在位性现状（27,240 悬空）契约 §2.4 只写了引用形态、**未声明资产缺口**。建议 v0.2 补一句如实披露（措辞归 Owner/DSH）。见 §4-N1。

---

## 3. Owner decisions（需要业务裁决）

> 判定标准：**超出接口/数据范畴、须业务判断**。本骨架只列裁决槽位，不预填结论。

### OD-1 · baseline 迁移（unit_type 修复路线二选一）

**裁决内容**（Closure Plan §1-A 唯一近 A 项 + §2 snapshot 硬事实）：

| 路线 | 内容 | 代价（Closure Plan 实测） |
|---|---|---|
| **披露路线** | 数据不动；契约 §2.1 已含异常注记 | 消费面永远带 1 个 PENDING 单元 |
| **清洁路线** | 冻结前执行 unit_type 单点修复 | **该 manifest 是 R50_input_baseline 成员**（356 之一，pin sha `58058c4f…`）→ 原地修复必致 `audit_integrity verify` 报 **DRIFT**，须配对再冻结决策或接受旧基线退役 |

**硬事实**：修复范围虽为「单点」（1 文件内 1 JSON 字段），但**破坏历史 snapshot 是硬事实**——不得只改数据不改基线（制造隐性 drift）。

**裁决槽位**：
- □ Owner 选路：□ 披露路线 / □ 清洁路线
- □ 若清洁路线：R50 基线处置 = □ 再冻结新基线（新 audit_id + 血统注记）/ □ 旧基线退役
- □ 与 CB-3 的耦合裁定（隔离面未定前，修复与否不改变 V3 当前零隔离的事实）：__________

### OD-2 · historical repair（figure 批跑范围与批次）

**裁决内容**（Closure Plan §3）：

- 批跑范围：1,394 份（排除 2 份 R50 基线交集 + 2 份无 PDF 单列）
- 批次切分与冻结清单时点（daemon 持续产出，清单须时点冻结）
- 2 份无 PDF 件（`(1)(1)` 重复 stem 家族）人工裁定，**不猜**

**裁决槽位**：
- □ Owner 批范围：__________
- □ 批次令：__________
- □ 2 份无 PDF 件裁定：__________
- □ 2 份 R50 交集件隔离归属（与 OD-1 基线决策同族）：__________

### OD-3 · 其余 Closure Plan 待批项（登记，非本骨架裁定）

| # | 项 | 批准粒度 | 状态 |
|---|---|---|---|
| 1 | flags 词条与 taxonomy 归类 | 登记令 | 待批（Closure Plan §5-4） |
| 2 | 6 份 needs_ruling 逐份裁定 | 逐份裁定 | 待批（§5-5） |
| 3 | D5-C/D 排期、D5-E 启动令 | 排期令 | 待批（§5-6） |

---

## 4. v0.2 正文待补槽位（非阻塞，起草时填）

| # | 槽位 | 来源 | 依赖 |
|---|---|---|---|
| N1 | 契约 §2.4 补 figure 资产在位性披露（27,240 悬空现状） | Review §C.4 | 无——可独立起草 |
| N2 | 契约 §3.1 required 清单标注 V3 当前消费范围（printed_number / basis / qc_verdict / disposition / provenance 块 / material_ref 字符串 / answers 表 = V3 无消费路径） | Review §D.3-N2 | 无——如实标注 |
| N3 | 契约 §1.3 lineage：确认记为 future（V3 不需要；authority 不迁移模型下 hash 足够） | Review Q2 / 契约 OQ-1 | 无——可关闭 OQ-1 |
| N4 | 契约 §2.4 / OQ-3 figure：确认延迟（V3 现阶段不提需求；DQE §2 独立佐证 registry 不需要） | Review Q3 / DQE §2 | 无——可关闭 OQ-3 |
| N5 | 契约 §2 与 §3.1 消费载体措辞 | CB-1 | **依赖 CB-1 裁决** |
| N6 | 契约 §1.1/§1.2 对账 hash 输入定义 | CB-2 | **依赖 CB-2 裁决** |
| N7 | 契约 §3.3-6 隔离执行面措辞 + DSH 陈述更正 | CB-3 | **依赖 CB-3 裁决** |

**已满足可直接写入 v0.2 的 PASS 面**（Review §D.1，7 项）：IR↔源 sha 绑定 71/71 零漂移 · R50 基线 356/356 · 行锚机制 V3 已验证消费（96.2% coverage）· material binding 稳定 · Authority 不迁移模型两侧一致 · F1 四项对账 2403/2403 · unresolved 显式通道存在。

---

## 5. 冻结前置清单（v0.2 可冻结的充要条件）

| 前置 | 类 | 状态 |
|---|---|---|
| CB-1 传输层裁定 + 契约 §2/§3.1 措辞修订 | Contract blocker | **NOT DECIDED** |
| CB-2 hash 输入定义裁定 + 契约 §1.1/§1.2 增补 | Contract blocker | **NOT DECIDED** |
| CB-3 隔离执行面裁定 + DSH 陈述更正 + §3.3-6 措辞 | Contract blocker | **NOT DECIDED** |
| N1 figure 资产在位性披露补入 §2.4 | 正文补遗 | 待起草 |
| OD-1 披露/清洁路线（**不阻塞接口冻结**，但影响 §2.1 注记措辞） | Owner decision | 待裁 |
| DH-1/2/3 数据清洗执行 | Data hygiene | **不进冻结前置** |

**判定**：**Contract v0.1 当前不可冻结；v0.2 正文尚不可起草**（CB-1~3 未裁则 §2/§3.1/§1.1/§3.3-6 四处措辞无依据）。

---

## 边界声明

**本骨架做了**：问题三分类（Contract blocker / Data hygiene / Owner decisions）；两份输入的口径调和（§0）；每项事实 + 行级锚 + 裁决槽位；v0.2 正文待补槽位与冻结前置清单。

**本骨架没做（任务禁止项）**：未冻结契约；**未提出任何实现方案**（CB 三项全部标 NOT DECIDED，只列裁决槽位）；未改 preprocessing；未改 V3 adapter；未代 Owner 填任何裁决结论。

**EB-008 状态**：不因本骨架变动。

---

*v0.2 DRAFT SKELETON — 2026-09-16，Claude（AITutors-v3 @ `821c53b`）。输入：Consumer Review v0.2 @ `938535d` · Closure Plan v1 @ preprocessing `4fdbb70` · 契约 v0.1 @ `1fbaf5e`（未改）。未冻结；等待 Owner 逐项裁决。*
