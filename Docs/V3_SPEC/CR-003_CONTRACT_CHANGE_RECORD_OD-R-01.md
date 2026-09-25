# CR-003 — CONTRACT CHANGE RECORD：OD-R-01 多空题 Answer 业务对象边界

```text
Document ID:           CR-003
Title:                 CONTRACT CHANGE RECORD — OD-R-01 Answer Business-Object Boundary
Document Type:         Contract Change Record
Authority Level:       L1
Status:                ACTIVE
Normative:             YES（对 L0 修改的生效授权与 provenance；不定义任何新业务语义）
Purpose:               把 Owner 已批准的 OD-R-01 业务语义正式 incorporated 进 L0 的
                       唯一入口记录（90 §1：L1 = 修改 L0 的唯一入口）；承载 change
                       classification / procedural remediation / re-freeze 生效信息。
                       与最近似文档的不可合并差异见 §0.1。
Derives From:          OD-R-01（Owner Decision，APPROVED 2026-09-24）·
                       90 §1 / §1.1 / §1.2 / §2 R1 / §3 / §4 / §11 · 91 §5 / §5.1（L0-META，只读）
May Change:            本 Change Record 自身的登记元数据
Must Not Change:       L0 业务语义 · L0-META 90/91 治理原则 · Frozen Contract · Schema ·
                       migration · Code · Corpus · Evidence 契约 · Admission runtime ·
                       历史决策语义
Supersedes:            —
Superseded By:         —
Gate State Authority:  NO
```

> 本文件是 **L1 Contract Change Record**。按 `90 §1`，L1 是**修改 L0 的唯一入口**。
> 本记录**不是**新的 Owner Decision，**不产生**新的业务语义：它只把 Owner 已批准的
> **OD-R-01** 正式 incorporated 进 L0，并补齐 provenance / audit / re-freeze 链。

---

## 0. `91 §5.1` 新文档创建门槛四问（缺一不可）

| # | 必须证明 | 本记录的答案 |
|---|---|---|
| 1 | 为什么现有文档承载不了？（与最近似文档的**不可合并差异**） | 见 §0.1 |
| 2 | 出生证明齐备 | 头块 13 项字段齐全（`91 §5`），无缺项 |
| 3 | 权威归属明确 | `Authority Level: L1` ∈ `90 §1` / `91 §5:167` 已定义层级；**未自创层级** |
| 4 | 允许改什么 / 禁止改什么 | `May Change` / `Must Not Change`；`Must Not Change` **含 L0** |

### 0.1 与最近似文档的不可合并差异

| 最近似文档 | 层 / 状态 | 不可合并的理由 |
|---|---|---|
| `90 §11`（含内嵌 `CR-001`） | L0-META / Change Audit Record | `90 §11` 是 **L0 修改审计**（记录「改了什么」）；L1 是**修改 L0 的唯一入口**（授权「可以这样改」）。二者权限不同：把活的 L1 并入审计日志，会让审计载具兼任授权层，违反 `90 §1` 的层分离；且会要求为创建 L1 而直接改写 L0-META `90` 本体。`CR-001` 是事后补建的**历史追认**记录（CHANGE-2，目标 `40 §5`），不是可引用的活 L1。 |
| `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` | **未归层**（`90:47`）/ `NOT RELEASED` | `Docs/COORDINATION/` **不在** `90 §1.2` 目录模型内 ⇒ 「未归层 = 不得引用为权威」（`90:47`）。CR-002 自述 `Registration Level: NOT REGISTERED`，并明令「禁止声称：CR-002 已是正式注册 L1」。 |
| `Docs/DECISIONS/67_ANNOTATION_RESOLVER_BOUNDARY_ADJUSTMENT.md` | L2 目录位置 / `NOT RELEASED` | `67` 是 CHANGE-4/5 候选，**不是**已注册正式 L1（`OWNER-DECISIONS:342`），且目标是另一变更（删 `20:117` FORBIDDEN_FIELDS 的 `line_refs`）。 |
| `Docs/COORDINATION/OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` | L2 Owner Decision Record | `90 §2 R2`：L2 只能解释与裁决，**不能修改 L0**。Owner Decision 是本 Change Record 的**输入**，不是 L0 修改的**入口**。 |

**搜索结论（无可合并同用途文件）**：**截至 CR-003 创建时**（观察范围仅限本记录编制时点的
`Docs/V3_SPEC/` 状态），`Docs/V3_SPEC/` 现存仅 `README.md` + `00/10/20/30/40/50/90/91`，
`Document Type` 均为 Frozen Spec / Governance Meta-Spec，**无** `Contract Change Record`；
`90 §1:41` **当时**自述「L1 … 暂无」。

> **时点限定（历史口径）**（2026-09-25，H-01 修正 / H-07 措辞精确化）：上述**「搜索结论」中的**
> `Docs/V3_SPEC/` 文件清单与 `90 §1:41` 引文**仅**描述 **CR-003 编制时点**的历史状态，
> **不表示**「Contract Change Record 从未存在」。其后 `90 §1:41` 已按事实同步（见 `90:47` 注）。
> **L1 当前状态以 `90 §1:41` 为准（本注记不作重复计数，不自建第二套 registry）**。

**物理落点依据**：`90 §1.2:79` 对 `Docs/V3_SPEC/` 的**允许**列明文含「引用；补 Change Record；**新增 L1**」。
本文件即依该允许列创建；**不创建第二套 governance registry**。

**`91 §5.1`「DG 期间冻结新建治理文档」的适用性**：`90`/`91`/`82`/`84` 已分别承载
「谁说了算 / 词是什么意思 / 现在什么状态 / 哪里有冲突」四问；本记录回答的是**第五问**——
「这次 L0 修改凭什么生效」，该问在上述四份中均无载体。且既有解读（`OWNER-DECISIONS:340`）
已就同一规则写明：「DG 期间冻结新建治理文档（**指 90/91/82/84 类元治理文档**）」——
L1 Contract Change Record 属 `90 §1.2` 明文允许的层级产物，不在该冻结范围内。

---

## 1. Change Record 标识与来源

```text
Change Record ID : CR-003
Owner Decision   : OD-R-01（多空题 Answer 业务对象边界）
Owner            : Owner
Decision Status  : APPROVED（2026-09-24）
Decision Scope   : Business semantics only
Source Commit    : 71f51f97e5674cf04ab12d4c449e3796a160bb27（2026-09-24）
Audit ID         : 90 §11 CA-003
Date             : 2026-09-24
```

**编号说明（避免第二次编号碰撞）**：`CR-002` / `CA-002` 已被
`Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` 占用（`NOT RELEASED` /
`NOT REGISTERED`，位于未归层目录，且 `90 §11` 表内**无** `CA-002`）。本记录**不复用**
该编号，取 **CR-003 / CA-003**。

---

## 2. Target 与 before / after（最小语义描述）

### Target 1 — `Docs/V3_SPEC/10_Data_Model.md §6.3`（instance_role_contents 约束列表）

| 项 | 内容 |
|---|---|
| **Before** | 约束列表仅三条（`(instance_id, role, label, role_index)` 唯一 / `text` 绝不来自 LLM 输出 / `source_span` 是 JSONB 不是 FK）。**未规定** Answer 的业务对象边界。`role_index` note 为「options/多值顺序」，但「多值」指一份 Answer 的多个有序值、还是多份 Answer，**未定义**。 |
| **After** | 新增一条「**Answer 业务对象边界（OD-R-01 冻结）**」：一个 QuestionInstance 的 answer role 对应**一份 Answer**；同一题号下多空题的多个空是**同一份 Answer 的多个有序值**（multi-value），`value[i]` 对应第 i 个空，顺序取**空在题面中的自然出现顺序**（`role_index` 承载该顺序）；三个空**不是**三个 QuestionInstance，也**不是**三份 Answer 对象；本条只约束「一个题号 / 一个 QuestionInstance 下多个作答空位」的正常多空题，**不改变**既有普通答案语义（例如多选题答案 `ABD` 仍是一份 Answer，不拆成 A/B/D 三份），也不推广为「所有答案都是 multi-value / 多步骤计算拆 value / 复杂答案结构化分解」等其他形态。 |
| **字段表 / 约束 / DDL** | **零改动**——未新增列、未改类型、未改唯一约束、未改 schema、未改 migration |

### Target 2 — `Docs/V3_SPEC/20_Document_Pipeline.md §5.3`（Role Resolution 规则·blank 条）

| 项 | 内容 |
|---|---|
| **Before** | 「**blank**：一个 blank 必须映射到一个 sub_question/answer；无闭合 → IR incomplete。」——`sub_question/answer` 可读作「一空 → 一个 sub_question **或一份 Answer**」，即 N 空 = N 份 Answer。 |
| **After** | 「**blank**：一个 blank 必须映射到一个 sub_question，或**同一份 Answer 的一个有序值**（多空题 Answer 业务对象边界见 10 §6.3 OD-R-01）；无闭合 → IR incomplete。」 |
| **变化性质** | 映射目标由二选一的**对象**（sub_question / answer）收窄为「sub_question 或**同一份 Answer 的一个有序值**」⇒ **既有规范行为改变**（N 空 = 1 Answer，而非 N Answer）。 |

---

## 3. Change Classification（`90 §3`，不降级）

| Target | Classification | 判定依据 |
|---|---|---|
| `10 §6.3` | **CHANGE-2 — Normative Addition** | 此前**未规定** Answer 业务对象边界；本次新增「必须 / 不得」强制约束（一份 Answer / 不得拆分 / 不得推广）。语义有新增 ⇒ **不是** CHANGE-1 Clarification。与 `90 §11 CR-001` 先例同型（在未规定处新增强制规则）。 |
| `20 §5.3` | **CHANGE-3 — Normative Modification** | 既有规定「一个 blank → 一个 sub_question/answer」被**收窄**，映射目标集合发生变化 ⇒ **改变既有规定的行为**。既非 CHANGE-1（语义已变），也非 CHANGE-4/5（**没有放宽**、**没有删除**既有约束——是把一个含混约束改为一个更窄的约束）。 |
| **本 Change Record 主导分类** | **CHANGE-3 — Normative Modification** | `90 §3` 判定规则「**拿不准往高里归**」：两 target 取较高者。 |

**流程要求（`90 §3`）**

```text
CHANGE-3 → Change Record + 受影响层回归
四道门（69 §5）仅适用 CHANGE-4 / CHANGE-5  ⇒  本记录【不需要】四道门
```

**受影响层回归**：本任务明令禁止 code / runtime tests，故受影响层回归以**静态一致性回归**
执行（§7）。受影响层 = L0 文本层（`10` / `20`）+ 引用该 baseline 的现行断言层。

**显式不降级声明**：`20 §5.3` 的收窄**不**记为 CHANGE-1 Clarification。CHANGE-1 要求
「规范语义**零**变化」，而本条使「N 空 = N Answer」这一此前可接受的读法变为不可接受，
实现行为随之改变 ⇒ 语义有变化。按 `90 §3`「归低了就是绕过治理」，如实归 **CHANGE-3**。

---

## 4. Rationale

**业务理由**：多空题（一个题号下多个作答空位）是高频正常高中题型。OD-R-01 之前的
Frozen Spec 同时存在两种读法且从未择一——

| 读法 | 支撑文本 |
|---|---|
| 「一份 Answer」 | `20 §6.1` IR 示例 `content.answer` 为**单对象**；`20 §6.3` M1 Role Contract 12 型均为 `answer \| required`（单一 role requirement） |
| 「多份 Answer」 | `20 §5.3`「一个 blank 必须映射到一个 sub_question/**answer**」；`10 §5.3` payload `answer[]`（数组）；`10 §6.3` `role_index`「options/**多值**顺序」 |

两读法给出的记录事实不同（1 份 Answer 带 N 个有序值 vs N 份 Answer），导致正常多空题
**无法确定性完成入库**。OD-R-01 择一裁决，本次将其 incorporated 进 L0 消除该 ambiguity。

**关于 `20 §6.3` 的正确表述（更正 DSH F-07 所指的过度推论）**

> OD-R-01 **本身**明确裁决 Answer business-object boundary。
> `20 §6.3` M1 Role Contract 的 `answer=required` **只规定 answer role requirement**
> （该 role 是否必需），**不能单独作为「只有一个 Answer 对象」的证明**。
> 「一份 Answer」的唯一依据是 OD-R-01 本身，不是该 role requirement 表。

**仓内核查**：`git grep`「已排除『多份 Answer』」类表述在 `AITutors-v3/Docs/` **0 命中**——
该过度推论只存在于对话报告，**仓内无需改写**；正确表述以本节为准。

**procedural gap 定性（对齐 `90 §11 CR-001` 先例）**：`71f51f9` 先改了 L0 正文、后补治理手续。
属 **procedural gap，非内容错误**。Owner 已裁决「保留，不回滚」，补救 = 创建本 Change Record
并补齐 `90 §11` Audit Record / `10`·`20 §12` 变更记录 / re-freeze 登记（§8）。

---

## 5. Scope

```text
IN SCOPE（本 Change Record 唯一解决面）:
  Answer business-object boundary —— 一个 QuestionInstance → 一份 Answer → N 个有序值
  （多空题：value[i] 对应第 i 个空，顺序 = 空在题面中的自然出现顺序）

  并保持已有边界：
    多选题 ABD → 1 QuestionInstance / 1 Answer / 1 value（ABD）
```

**不得泛化为**：所有 Answer 都是 multi-value · 多步骤计算拆成多个 value · 复杂答案自动结构化 ·
多选题 A/B/D 拆成多个 Answer · evidence 按空重新建模 · partial correctness · per-blank evidence state。

---

## 6. Explicit Exclusions

```text
本 Change Record 只解决 Answer business-object boundary。

不裁决：
- payload answer[] element representation
- answer_status attachment point
- evidence granularity
- per-blank evidence state
- partial correctness
- new evidence state
- new evidence business object
- database schema redesign
- migration
```

前两项与「`value[i]` 指称 / N 个有序值对应 1 行还是 N 行」已按项目 GAP / 台账纪律
**只登记，不解决**（`84_CONFLICT_LEDGER.md` **D-07** / **D-08**，沿用 D-06 先例，未新增
类别 / 字段 / 状态值）。**不得**据本 Change Record 推导其答案。
DSH F-06 / F-08 **不因本记录而重开 Owner Decision**。

---

## 7. 受影响层回归 / 静态一致性验证

| 检查 | 结果 |
|---|---|
| A. Git identity（`71f51f9` parent / branch / HEAD / origin） | `parent = 9f1763e` · `od01-r3-convergence` · 字面值见 G-02 §6 |
| B. Frozen Spec tree 前后 | `b3eeb3e9…` → `442172f4…`（incorporation）→ re-freeze tree（§10） |
| C. L1 存在 / 来源 / 分类 / review / effective 显式 | 本文件 §1 / §3 / §9 / §10 |
| D. `90 §11` Change Audit Record | `CA-003` 已登记 |
| E. `10 §12` / `20 §12` 变更记录 | 均已追加 OD-R-01 记录 |
| F. 语义 diff 仍只有 `1 QuestionInstance / 1 Answer / N ordered values` | 两处 L0 语义文字**原样保留**（Owner 裁决「不回滚」） |
| G. Forbidden scope | code / schema·DDL / migration / corpus / evidence semantics / Admission runtime **全部未改** |
| H. 旧 hash `b3eeb3e9` 逐项判定 historical vs false-current | 判定表见 G-02 §6 |

**受影响实现层回归（CHANGE-3 要求）—— 如实记录为未验证**

```text
状态：NOT VERIFIED —— 尚未进入对应实施阶段
范围：backend / Resolver / Compiler / IR / Gate / Admission 实现层回归
本轮做了什么：只做 L0 文本层与现行断言层的静态一致性回归（上表 A–H）
本轮没做什么：未改 backend、未增/改测试、未改 IR / Gate / Admission、
              未重跑 Phase 1、未重开 X2.6 M.3
为什么不跑：P1 Segment A 实施仍处 STOP；OD-R-01 的两处修改是 L0 业务语义落点，
            其对应实现尚未进入该实施阶段
```

> **不得误读**：上表 G 项只证明「本轮没有触碰实现面」，**不等于**「实现层回归已通过」。
> 本记录**不伪造** regression evidence。待对应实施阶段启动时，须补做受影响层回归并回填本节。

---

## 8. Procedural Remediation / Ratification

```text
procedural gap（已确认）：先改 L0（71f51f9），后补治理手续。
性质：procedural gap —— 非内容错误（对齐 90 §11 CR-001 的同型定性）。

Owner Decision（2026-09-24）：
  两处 L0 最小业务语义修改   保留，不回滚
  OD-R-01 业务语义          APPROVED
  补救                     建立 L1（本文件）+ 90 §11 CA-003 + 10/20 §12 变更记录
                           + Frozen Spec re-freeze 登记 + 受影响现行断言最小一致性修复
```

**current ratification ≠ historical authorization**：本记录**不重构**、**不主张**任何历史
Owner Order 或既往授权记录；也**不主张** `71f51f9` 在其发生时点已具备完整 L0 生效效力。

**生效区分（对齐 CR-001）**：CR-003 Accepted 之前，「L0 文本已存在 ≠ 该 CHANGE 已完成生效」。
自本记录 Review **ACCEPTED / EFFECTIVE** 起，两处修改具有完整 L0 效力。

---

## 9. Review / Owner Approval

| 项 | 裁决 |
|---|---|
| OD-R-01 业务语义 | **APPROVED** |
| 两处 L0 修改 | **保留，不回滚** |
| Change classification | `10 §6.3` = **CHANGE-2**；`20 §5.3` = **CHANGE-3**；主导 = **CHANGE-3** |
| 四道门 | **不需要**（仅适用 CHANGE-4 / CHANGE-5） |
| 修改 `90`/`91` 治理原则 | **不需要，且不允许**（`OWNER-DECISIONS:351`） |
| 回滚 `71f51f9` | **不回滚** |
| Schema / migration / code | **不需要，且不允许** |
| Review | **ACCEPTED / EFFECTIVE** |

---

## 10. Effective / Re-freeze

**生效时点**：自本记录 Review **ACCEPTED / EFFECTIVE**（2026-09-24）起，两处 L0 修改
具有完整 L0 效力；此前为「文本已存在但 CHANGE 未完成生效」。

**Frozen Spec re-freeze 链**

```text
Previous Frozen Spec tree（pre-OD-R-01，= 9f1763e:Docs/V3_SPEC）
  = b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f     【历史 baseline —— 保留，不得修改】
        ↓
OD-R-01 authorized change（source commit 71f51f9）
        ↓
Incorporation tree（= 71f51f9:Docs/V3_SPEC）
  = 442172f40942368a4856231a742bf4d273242034     【两处业务语义修改后的 L0】
        ↓
Governance closure（CR-003 / 90 §11 CA-003 / 10 §12 / 20 §12 / 本文件）
        ↓
Re-freeze Frozen Spec tree
  = git rev-parse <本记录生效 commit>:Docs/V3_SPEC
```

**Re-freeze identity 的权威表述**：`Docs/V3_SPEC` 的 **git tree object，锚定于本记录生效
commit**（即引入本记录的 commit；沿用仓内既有措辞「本记录所在 commit」）。
机械复核：`git rev-parse <生效 commit>:Docs/V3_SPEC`。

**为何字面值不自记于本文件**：本文件位于 `Docs/V3_SPEC/` 内；若把该目录的 tree hash 字面值
写进本文件，hash 就成了自身的输入 ⇒ 自指不动点，无解。故：

- **权威登记落点 = 本节**（commit 锚定表述，可机械复核）；
- **字面值可读副本** = `Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md` §6
  （该文件在 `Docs/V3_SPEC/` 之外，无自指问题）。副本为**非权威**，仅便于阅读；争议时以
  `git rev-parse` 为准。

**历史 hash 处置**：`b3eeb3e9…` 作为 pre-OD-R-01 baseline **永久保留**，任何文档中的历史
表述**不得**被机械替换（`90 §4`：「**存量文档不强制回填**（Reconcile, don't rewrite）」；
废止传播另见 `90 §2 R8`，两条规则不同，不得互相代引）。

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/V3_SPEC/CR-003_CONTRACT_CHANGE_RECORD_OD-R-01.md` |
| Authority Level | L1 |
| Status | ACTIVE |
| Change Record ID | CR-003 |
| Audit ID | 90 §11 CA-003 |
| Registration Level | REGISTERED AS L1（首条正式 L1） |
