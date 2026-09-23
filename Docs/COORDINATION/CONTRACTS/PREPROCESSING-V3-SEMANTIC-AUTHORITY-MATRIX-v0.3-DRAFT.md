# Semantic Authority Matrix v0.3

> **状态**：`CONTRACT FREEZE CANDIDATE` 配套 / **已同步 Owner Decisions P01–P25**
> **配套**：`PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` §6 / **§17**
> **术语**：`Preprocessing` = `kurt-wong/Aitutors-preprocessing`；`AITutors-v3` = 当前 V3 系统；`Producer` **仅**作抽象架构角色（Contract §0）
> **证据标签**：`OBSERVED` / `DERIVED` / `DECISION`（P01–P25 落版）/ `OPEN`
>
> **本轮同步（Contract §16/§17）**：`option label` / `option text` / `option provenance` / `answer-table mapping` = **Preprocessing-discovered structural & evidence facts**；Generated explanation = **AITutors-v3 Derived Enrichment**（**P04 / P07 / P16**）。

## 1. Authority 类别

| 代号 | 类别 | 定义 | 可改写方 |
|---|---|---|---|
| **SRC** | Source Authority | 原始文档字节事实（行文本、字节 hash） | 无（immutable） |
| **PRD** | Preprocessing Authority | Preprocessing 发现/标注且带证据的主张 | 仅 Preprocessing 新版本 + 新 identity |
| **CAN** | Canonical V3 Authority | 经授权 boundary normalization 后的 canonical 表示 | 仅经 OD 授权映射 |
| **V3D** | V3 Derived Authority | V3 自身推导/生成 | V3 enrichment / generation pipeline |
| **EVD** | Evidence Authority | 经 ValidationEvent 等确认的证据权威 | Gate/Validation 流程 |
| **UNK** | Unknown | 显式未知 | 不得静默升级 |

**铁律（`PROPOSED`）**：

1. `V3D` 不得写回或伪装成 `PRD` / `SRC`。
2. `PRD` 不得覆盖 `SRC` 字节事实。
3. `CAN` 只能是 `PRD` 的确定性映射，不能是新的语义发明。
4. `EVD` 产生权威需走既有 Evidence / ValidationEvent，不得另造平行 authority。
5. `UNK` 只能经显式、可审计流程离开 UNKNOWN。

---

## 2. 字段级 Authority 矩阵

| 事实 / 字段 | SRC | PRD | CAN | V3D | EVD | UNK | 说明 |
|---|---|---|---|---|---|---|---|
| 源文件字节 / 行文本 | ● | | | | | | raw bytes 为唯一身份事实来源 |
| `source_content_sha256` | ● 计算值 | ● 声明 | | | ● M2/M4 验证 | | 声明 vs 计算；验证后 identity VERIFIED |
| `identity_version` / Scope | | ● | ● Scope 判定 | | ● M1 | 缺失=UNK→BLOCK | |
| stem/options/answer/explanation/material 正文 | ● | ● 行区间主张 | ● span 表示 | | ● 行锚定验证 | 缺区间=UNK | 正文权威在 SRC |
| `options_lines`（Whole Options Region） | ● | ● 行区间主张 | ● span 表示 | | ● 行锚定验证 | 可缺 | **preserved**（`DECISION` **P04.2**，不得删除） |
| **`option.label`** | | ● | ● | | ● 可验证 | 缺 → UNK / fail closed | **Preprocessing-discovered structural fact**（`DECISION` **P04.1**）；AITutors-v3 **不得**凭空创造或覆盖 |
| **`option.text`** | ● 源行 / 表格格文本 | ● | ● span 表示 | | ● 可回源验证 | 缺 → UNK / fail closed | **Preprocessing-discovered structural fact**（`DECISION` **P04.1**） |
| **`option.provenance`** | | ● | ● **多态** provenance | | ● **须可被 AITutors-v3 验证** | 不可回溯 → fail closed | **Preprocessing evidence / provenance**（`DECISION` **P04.3**）；允许 `line_range` / `char_span_in_line` / `table_cell` / multiple spans；**禁止**"一 option 一行"硬编码 |
| **answer-table mapping** | ● 表格字节 / 格文本 | ● cell↔question_number 映射主张 | | | ● 可复核 | `answer_table_unresolved` = UNC | **Preprocessing-discovered structural / evidence fact**（`DECISION` **P07**）；**禁止**简化为"答案表错误"；**禁止**人为制造 Question→Answer 映射 |
| `unit_id` | | ● | ● | span_id 可派生 | | | |
| `question_numbers` | 印刷可见性 | ● | ● range | 子题拆分可派生 | ● basis 证据 | `unverified` | |
| `printed_number` | 印刷 | ● | | | ● `printed_provenance` | `unknown` | |
| `unit_type` legacy | | ● | ● 仅 OD-2 两条 | | ● mapping event | 非法值 | 禁 QT→UT |
| `original_question_type` | | ● 主张 | ● 闭集内映射 | canonical QT | | unsupported/missing | QT ⊥ UT |
| difficulty | | | | ● | | 可缺 | V3D |
| knowledge_nodes | | | | ● | | 可缺 | V3D |
| skills / abilities | | | | ● | | 可缺 | V3D |
| Preprocessing `explanation_lines` 内容 | ● | ● | | | | 可缺 | source explanation |
| generated explanation | | | | ● | ● 验证后 | pending/failed / suspended | **`DECISION` P16：AITutors-v3 Derived Enrichment**，**不得**标成 Source / Preprocessing Authority |
| generated 其它 enrichment | | | | ● | ● | pending/failed | |
| `basis` / `basis_evidence` / `printed_provenance` | | ● | | | ● 可验证 L 行 | `unverified`/`unknown` | |
| `flags` / QC / disposition | | ● | | | ● 可复核 | flags 即 UNC | **ADMITTED ≠ V3 APPROVED** |
| `answer` 最终正确性 | | ● 声明 | | ● 可再判 | ● 人工/验证 | unresolved | 禁猜填 |
| Gate decision | | | | | ● | | pending_review/approved/rejected |
| Admission 物化实体 | | | | | ● 事务权威 | | Question/Instance 等 |

图例：● = 该层可拥有/产生此权威

---

## 3. 典型冲突裁决（`PROPOSED`）

| 冲突 | 裁决 |
|---|---|
| path 变化 vs identity | identity 不变（content hash） |
| Preprocessing 说 unit_type=`andalone_question` | 不得 CAN 为 standalone_unit；`UNKNOWN_UNIT_TYPE` |
| Preprocessing explanation vs generated explanation | 分槽存储；默认展示策略 `OPEN` |
| Preprocessing answer vs V3 再判 answer | 保留 Preprocessing；V3 结果标 V3D；冲突进 review |
| `printed_number=unknown` vs `question_numbers` | 题号主张可用，printed 权威保持 UNKNOWN |
| flags 非空 vs 无 flags | 有 flag 必须下游可见；禁止丢弃后当 clean |
| QC_FAIL vs 任何语义“看起来对” | 不得进 ADMITTED 消费面 |

---

## 4. Post-Admission 生成物 Authority（`DECISION` **P15 / P16 / P17 / P18 / P19**）

```text
Question (persisted)
  ├── explanation_preprocessing  [PRD/SRC]  可空  ← Original Question 自带（Preprocessing 传递）
  ├── explanation_generated      [V3D]      可空  ← AITutors-v3 Derived Enrichment
  │     ├── generation_job_id
  │     ├── generation_method = LLM
  │     ├── generator = MIMO
  │     ├── validator = DeepSeek（P17）
  │     ├── model / config hash
  │     ├── validation_state ∈ {generated, validated, accepted, rejected, suspended}
  │     ├── retry_count（max 1；第二次 validation failure → suspended，P19）
  │     └── provenance
  └── explanation_display_policy [OPEN]  ← 展示优先级未裁（OD-V3-22）
```

（字段名按 Contract §0 术语规范化：原 `explanation_producer` → `explanation_preprocessing`。）

**`DECISION` P15**：只允许生成 Original Question 中**缺失**的 detailed explanation；**已有 explanation 不生成、不覆盖**。
**`DECISION` P16**：Generated explanation = **AITutors-v3 Derived Enrichment**——**不是** Source Authority，**不是** Preprocessing Authority。
**`DECISION` P18**：Enrichment failure **不 rollback** AITutors-v3 Admission。

**禁止**：`explanation_generated` 覆盖或伪装 `explanation_preprocessing`。

---

## 5. 与 Evidence / ValidationEvent

`OBSERVED`：V3 已有 Evidence Promotion / ValidationEvent（EB-008 系）。  
`PROPOSED`：generated content 的 `validated/accepted` **优先复用**该体系，不另造平行 authority。

`OPEN`（**implementation / schema question**，非 Owner Decision 欠账；对齐 OD-V3-25）：若 ValidationEvent 模型需扩展字段以覆盖 generation provenance，属 schema / governance 变更，**不在本次落版授权范围**（DB schema 明令禁改）。

*End of Semantic Authority Matrix v0.3 — CONTRACT FREEZE CANDIDATE 配套（Owner Decisions P01–P25 已同步）.*
