# Preprocessing ↔ V3 Integration Contract

**Status**: DRAFT v0.1 — 待 DSH 确认（双方契约，非单方规范）
**Date**: 2026-09-15
**Owner**: Claude (AITutors-v3) 提出需求侧；DSH (Aitutors-preprocessing) 供给侧协商
**协作模型**：DSH = 输入事实生产（OCR / Annotation / Source Version）；V3 = 教学系统构建（Resolver / IR / Authority / Admission）。DSH 不是 V3 的 QA/审查团队。

```
             Integration Contract (本文档)
       DSH                         Claude
AITutors-preprocessing       AITutors-v3
  OCR / Annotation              Resolver / IR
  Source Version facts          Authority / Admission
              └── EB-008 跨边界约束（frozen, DEC-016/92号）──┘
```

---

## 0. Authority 分类（跨边界总则）

| 对象 | Authority Level | 说明 |
|---|---|---|
| SourceVersion（sealed） | V3 formal | 不可变源；Seal 后禁 UPDATE |
| preprocessing manifest units | 事实输入（untrusted producer output） | 不构成 Authority；仅作为待验证证据 |
| Resolved Evidence / span | V3 派生（Resolver） | 由 Source 行 + manifest 声明共同解析 |
| ValidationEvent / Authority | V3 formal（EB-008） | 持久化于 validation_events，append-only |
| Human review proof | V3 formal（EB-008） | candidate 级，防 DB 直篡改，不做 API 认证 |

**EB-008 跨边界约束（frozen，不得因接口协商而改动）**：
- Identity Model：Run=Process / Candidate=Entity / le_hash=语义身份；同 hash 跨 Run 复用 Candidate 合法；run_id 不进 AuthorityIdentity
- AuthorityIdentity = (source_version_id, candidate_id, claim_id)
- IR Boundary = Option B：IR provisional，IR 不是可信知识资产

---

## 1. Source Version 接口需求

### 1.1 必需输入

| 字段 | 类型 | 语义 | 来源 |
|---|---|---|---|
| source_file | str (abs path) | 源文档本体（当前 markdown；DEC-009 raw HTML 为 intended 表示，HTML 通路未开） | preprocessing |
| 文档行序列 | lines[] | 1-based 行序，行文本 = 原样，不清洗 | preprocessing 源文件本身 |
| line_ref 约定 | `P{page}L{line:03d}` | markdown 恒为 page 1（如 `P1L007`）；seq 0-based 全局序 | **契约约定（双方共同遵守）** |
| body_hash | sha256 hex | `sha256("\n".join(line.text))`，行连接符为 `\n` | 消费侧计算，生产侧不得另造算法 |
| line_hash | sha256 hex | 单行 `sha256(text)` | 同上 |

### 1.2 字段语义边界

- 行号是**唯一定位原语**。所有下游声明（stem/options/answer/material lines）都以 1-based 闭区间 `[start, end]` 对引用行号。
- `page_count=1, line_count=N`：markdown 路径下 V3 以此建 DocumentSourceLine。分页源（PDF）出现时需扩展 line_ref 的 page 段——**扩展前必须先修订本文档**，不得单方面改格式。
- V3 Seal 后 SourceVersion 不可变。preprocessing 重新产出同一文档的修正版 = **新 source_version**（新 le_hash / 新 version 行），不是旧 version 的原地改写。

### 1.3 不接受的输入

| 情况 | 处置 |
|---|---|
| 行号越界（end > line_count 或 start < 1） | 拒收该 unit 声明，记 FACT，不猜测修复 |
| 区间倒置（start > end） | 同上 |
| 同一文档内行文本与 manifest 引用行哈希不一致（错版对错号） | 整份 manifest 拒收——版本错配不得静默继续 |
| source_file 缺失/不可读 | 拒收整份 manifest |

### 1.4 Fallback 策略

- **无 fallback 到猜测**。行号解析失败 = 证据缺失 = unit incomplete（fail-loud，见 `ir.py` validate：span 未解析 → incomplete，绝不静默丢弃）。
- 唯一允许的降级：manifest 整体拒收后，V3 侧保留已 Seal 的 SourceVersion，等 preprocessing 重发正确 manifest。

---

## 2. Annotation（manifest units）接口需求

### 2.1 必需输入字段

每 unit（合成示例值见右列）：

| 字段 | 必需性 | 语义 / 示例 |
|---|---|---|
| unit_id | 必需 | unit 内唯一标识，如 `"Q1"`；后续 claim_id 以此为根 |
| unit_type | 必需 | `standalone_question` \| `composite_question` |
| question_numbers | 必需（≥1） | `[3]` 或 `[12,13,14]`（composite 范围） |
| original_question_type | 必需 | 语义类型原样，如 `single_choice` / `填空题`（V3 归一化到 canonical 在 V3 侧完成，不要求 preprocessing 归一） |
| stem_lines | 必需 | `[10, 15]` |
| options_lines | choice 类型必需 | `[16, 23]`——**区域级**（见 2.3 gap） |
| answer_evidence | 必需 | `{type: "answer_table", lines: [200, 201], value: "B"}` |
| explanation_lines | 可选 | `[50, 58]` |
| material_lines / questions_lines | composite 必需 | 材料区 / 子题区 |
| answer_lines | 可选 | 独立答案行区（与 answer_evidence 并存时以 evidence 为准） |
| section / printed_number | 可选 | 试卷结构元数据 |
| extra_lines | 可选 | 未归类附属行 |

manifest 级：`source_file`（必需）、`model`、`prompt_version`（必需，进 provenance）、`validation_issues[]`、`warnings[]`。

### 2.2 字段语义

- **lines 是区域声明，不是内容**。manifest 永不携带行文本；文本只从 SourceVersion 行取（单源原则）。
- **annotation payload 禁止 line_refs**（V3 IRBuilder 约束）。manifest 的行号只用于 span 解析；进入 SemanticAnnotation.payload 的是纯语义角色声明（`{role: "stem", question_label: "1"}` 等）。
- composite 的子题结构：preprocessing 当前**不拆子题**（整块 questions 区域 = 一个 sub）。V3 侧以单 sub 编译，这是已知粗糙面，见 2.3。

### 2.3 已知 Gap（不阻断，但登记在案）

| Gap | 现状 | 契约方向（待 DSH 协商） |
|---|---|---|
| per-label options 粒度 | preprocessing 只给 `options_lines` 区域，不给 A/B/C/D 逐标签行号 | 方向 A：DSH 增加 `options_labels: [{label, lines}]`；方向 B：维持区域级，V3 在区域内检测 Source marker（P3.2 实验路径）。**未决前 V3 不 fabricate per-label 声明**——choice unit 因 options missing 判 incomplete 是诚实结果 |
| composite 子题不拆 | 一个 composite = 一个 sub | 待 `sub_question_units[]` 字段协商 |
| figure 归属 | manifest 无 figure binding 字段 | 见 §3 |

### 2.4 不接受的输入

| 情况 | 处置 |
|---|---|
| unit_id 重复 | 拒收整份 manifest |
| choice 类型缺 options_lines（且无 per-label 替代） | unit 保留，IR 判 incomplete（"options missing for choice type"） |
| composite 缺 material_lines | IR 判 invalid（"composite has no shared component material"） |
| payload 中夹带 line_refs / 行文本 | 拒收（Schema 违规） |
| `validation_issues` 非空的 manifest | 不自动进 Admission——issues 是 producer 自声明缺陷，Gate 会再判 |

### 2.5 Fallback

- unit 级缺陷 → unit incomplete，**不拖垮整份 manifest**（除 1.3/2.4 的整份拒收项）。
- answer_evidence 缺失 → answer role 未解析 → incomplete。
- 无 LLM 现场补全。text 永不来自 LLM（10 §6.3 冻结约束）。

---

## 3. Material / Figure Binding 接口需求

### 3.1 Material（现状可用）

- `material_lines: [start, end]` → V3 解析为 `sp-{unit_id}.material` span → Material 记录（Source-scoped，M1 不跨 SourceVersion 共享）。
- composite 子题对 material 的依赖：V3 以 `relations: material_dependency` + `shared_components.material` 表达；target span 解析失败 → invalid。

### 3.2 Figure（缺口，待协商）

V3 侧已有 `SourceFigure`（UNIQUE(source_version_id, figure_id)，无 role_owner/题号归属）与 `InstanceFigureLink`。preprocessing manifest **当前不产出任何 figure 字段**。

契约需求（提案，未冻结）：

| 字段 | 语义 |
|---|---|
| figures[].figure_id | version 内唯一，如 `"fig-3"` |
| figures[].page_no / bbox | 版面定位 |
| figures[].referenced_by_units | 声明哪些 unit 引用该图（如 `["Q7"]`）——归属是 producer 事实声明，V3 校验后落 InstanceFigureLink |

- 不接受：figure 声明的 bbox 越出版面；referenced_by_units 指向不存在的 unit_id → 该条 figure 声明拒收，其余继续。
- Fallback：figure 缺失时含图 unit 的 image role 判 unsupported/incomplete（BUG-V3-020 延后路径），不静默去掉图。

---

## 4. Evidence Binding 接口需求（EB-008 边界）

### 4.1 证据链

```
SourceVersion (sealed, V3 formal)
  → manifest unit 行区间声明 (producer facts, untrusted)
    → Resolved spans (V3 Resolver 派生)
      → IRNode (provisional, Option B)
        → ValidationEvent ledger (V3 Authority, append-only)
          → Admission (project_authority, fail-closed)
```

### 4.2 跨边界规则

- **preprocessing 产出的一切都是 untrusted producer output**。包括 answer_evidence——它是"待验证的声称"，不是 Authority。
- Authority 只能由 V3 validation_events 投影产生（EB-008 P1 已实现：EvidenceRepository append-only + latest-by-validated_at）。
- claim_id 以 unit_id 为根（`"Q1"`）；AuthorityIdentity 三元组内**永不出现 run_id/attempt_id**。
- reference_ids：ValidationEvent 可引用证据对象 ID 列表（JSONB）；preprocessing 若提供跨文档引用 ID，必须是稳定字符串且在 manifest 内自洽。

### 4.3 不接受

- producer 直接声称"已验证/VALIDATED"——validation_result 只能出自 V3 Gate/人工 review 路径。
- 用 attempt/run 维度要求 V3 区分同 le_hash 的两次产出——设计目标就是复用 Candidate（DEC-016 Rule 1）。

---

## 5. 拒收/降级总表

| 层级 | 触发 | 动作 |
|---|---|---|
| 整份 manifest | source_file 不可读 / 行号普遍越界 / 版本错配 / unit_id 重复 | 拒收 + 记 FACT + 请 DSH 重发 |
| 单 unit | 区间倒置/越界、类型缺必需区、Schema 违规 | unit incomplete 或拒收该声明 |
| 单 evidence 声明 | figure/unit 引用不存在目标 | 丢该声明，其余继续 |
| Admission | Authority 未 VALIDATED（含 incomplete IR） | fail-closed：RepositoryError，candidate 停在 pending_review |
| 人工 review | proof 校验失败 / APP_SECRET 缺失(<32B) | fail-closed，拒事件写入 |

---

## 6. 变更治理

- 本文档任何字段级变更需双方 ack 后升版本号（v0.x → v1.0 = 冻结首版）。
- EB-008 冻结约束（§0）不在本契约协商范围内——只可引用，不可修改。
- 与 Producer Contract（DEC-003 未冻结）的关系：本文档是 V3 侧需求提案；DSH 侧对应产物出现分歧时，以双方 ack 后的修订版为准，冲突记入 84_CONFLICT_LEDGER。

## 7. 待 DSH 确认清单（协商入口）

1. options 粒度走方向 A（producer 给 per-label）还是方向 B（V3 区域内检测）？
2. composite 子题拆分：preprocessing 能否产出 `sub_question_units[]`？
3. figure binding 字段（§3.2 提案）是否可进入 preprocessing 产出？
4. 分页源（PDF）timeline：line_ref page 段扩展的触发条件。
5. `validation_issues` 的语义清单（producer 缺陷分类）是否需要双方对齐枚举？
