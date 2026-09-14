# 85 — Preprocessing Consumer Phase 0：消费验证实验

**Date**: 2026-09-14
**Status**: **Phase 0 + 0.2-R2 + 0.3-B CLOSED — 见 §9/§11/§12**
**权威范围**: V3 消费 preprocessing 产出的架构边界与 Phase 0 实验设计。

> **定位**：Phase 0 是 contract validation harness（契约验证器），不是生产集成。
> 它只回答一个问题：「preprocessing 当前产出的事实结构，经过最小转换后，能否被
> V3 的 Gate / Admission 模型正确消费？」
> 不改 V3 生产代码，不写生产数据库，不建正式 import API。

---

## 0. 背景

AITutors-preprocessing（`D:\Project\Papers`）已完成 P2.1-c 答案证据契约：

| 指标 | 值 |
|---|---|
| parse_success | 97.44%（38/39 卷） |
| answer_rate | 100% |
| admission_ready | 100% |
| 产出 | `reslice-p2-b1/` 38 卷（prompt v2.3）+ `reslice-p2-fix1/` 5 卷（v2.5，含 answer_evidence） |

preprocessing 的 Phase P2 Charter 明确目标是「输出 V3 Admission 可消费的 Question IR」。
当前两侧各自正确，但**系统级兼容性未验证**。

---

## 1. 架构结论（用户裁定 2026-09-14）

### 1.1 三层模型

```
文档事实生产层          AITutors-preprocessing
                            |
                Source Evidence / Span Manifest
                            |
                            ↓
V3 Domain Layer       Source → Resolver → Gate → Admission → Question/Instance
                            |
                            ↓
Application Layer
```

- **preprocessing** = Document Fact Extraction System（这份文件的事实边界在哪里）
- **V3** = Knowledge Asset Admission System（这些事实如何成为可信知识资产）
- preprocessing 不是 V3 的 OCR 模块，是**上游事实生产系统**

### 1.2 当前不集成代码的理由

| 模块 | 变化频率 | 集成风险 |
|---|---|---|
| preprocessing OCR/reslice prompt | 高频 | 高 |
| preprocessing QC 规则 | 高频 | 高 |
| manifest schema | 中频 | 中 |
| V3 domain model | 低频 | 极高 |

原则：**核心领域模型稳定，外围生产策略可迭代。** 合并会导致 prompt 调整 → V3 CI 波动。

### 1.3 长期方向（成熟后）

```
AITutors-v3/
  domains/
    └── preprocessing/    # 生产模块（OCR/reslice/QC/manifest）

AITutors-preprocessing/   # 审计工具 + 回归验证（独立仓库）
```

类似 Linux kernel / kernel-test / fuzzing infrastructure 的关系。

---

## 2. 两侧接口现状（实测）

### 2.1 preprocessing 产出格式

manifest units 核心结构：

```json
{
  "unit_id": "Q1",
  "unit_type": "standalone_question",
  "question_numbers": [1],
  "original_question_type": "single_choice",
  "stem_lines": [45, 62],
  "options_lines": [63, 78],
  "answer_lines": [85, 92],
  "explanation_lines": [93, 110]
}
```

**定位哲学：精确行号区间**（`[起, 止]`，1-based，闭区间）。

### 2.2 V3 annotation 格式

```json
{
  "semantic_units": [{
    "unit_id": "Q1",
    "unit_type": "standalone_question",
    "question_number": "1",
    "original_question_type": "single_choice",
    "content": {
      "stem": {"role": "stem"},
      "options": [{"label": "A", "role": "option"}],
      "answer": {"role": "answer", "answer_zone": "answer_table"},
      "explanation": {"role": "explanation", "explanation_zone": "inline_explanation"}
    }
  }]
}
```

**定位哲学：角色声明**，由 SourceResolver 从 sealed source 中模式匹配。
**禁止** payload 中出现 `line_refs`（任何深度）。

### 2.3 V3 Gate 输入要求

`GateService.run(source_version_id, annotation_id)` 从数据库加载：

| 表 | 关键字段 |
|---|---|
| `document_source_versions` | status="sealed", body_text, body_hash, line_count |
| `document_source_lines` | line_ref=`P{page}L{line:03d}`, seq, text, line_hash |
| `source_figures` | figure_id, page_no, bbox, object_key |
| `semantic_annotations` | status="valid", payload (JSONB), source_version_id FK |

### 2.4 核心 Contract Gap

| | preprocessing | V3 |
|---|---|---|
| 定位方式 | 行号区间 `[85, 92]` | 角色声明 + Resolver 搜索 |
| 定位权归属 | manifest（事实） | Resolver（声明→解析） |
| answer 表达 | `answer_lines` | `answer_zone` 枚举 |
| 正文 | 不含（纯引用） | 不含（Resolver 从 source 解析） |

**Philosophy Gap**：preprocessing 说「答案在第 85-92 行」，V3 期望「有答案区，Resolver 自己找」。
这是 Phase 0 最重要的验证目标。

---

## 3. Phase 0 实验设计：双轨验证

### 目录

```
backend/scripts/preprocessing_consumer/
├── manifest_reader.py          # 读取 preprocessing manifest
├── source_loader.py            # 加载 source .md → V3 SourceLine 格式
├── annotation_adapter.py       # Track A: manifest → V3 annotation payload
├── resolved_span_adapter.py    # Track B: manifest → ResolvedSpan
├── runner.py                   # 双轨执行器
└── report.py                   # 结果汇总 → consumer-report.json
```

### Track A：模拟 V3 原生 Annotation 消费

验证 preprocessing manifest 是否只是「另一种 annotation 表达」。

```
manifest → annotation_adapter → SemanticAnnotation → GateService → Resolver → Admission
```

- 把 `stem_lines: [45,62]` 转成 `content.stem: {role: "stem"}`
- 让 V3 Resolver 自己从 source lines 中搜索匹配
- **失败是有价值的信息**——记录为 CONTRACT_GAP

### Track B：事实直通模式

模拟未来正式方向（manifest 的行号优势直接利用）。

```
manifest → ResolvedSpanAdapter → Gate → Admission
```

- 把 `stem_lines: [45,62]` 直接生成 `ResolvedSpan(role="stem", start_line_ref=..., end_line_ref=...)`
- 跳过 Resolver 的搜索阶段
- 验证 Gate/Admission 能否接受预解析的 span

### 对照表

| 维度 | Track A | Track B |
|---|---|---|
| 模拟当前 V3 | ✅ | ❌ |
| 保留 preprocessing 行号优势 | ❌ | ✅ |
| 发现模型冲突 | ✅ | 部分 |
| 未来生产价值 | 低 | 高 |
| 验证架构方向 | 高 | 高 |

---

## 4. 失败分类（三类 Gap）

| 类型 | 含义 | 反馈方向 |
|---|---|---|
| **Schema Gap** | 字段命名/结构不同 | adapter 映射或 schema version |
| **Semantic Gap** | V3 模型缺少 preprocessing 表达的概念 | V3 扩展 domain model |
| **Philosophy Gap** | 定位权归属冲突（行号 vs 角色搜索） | 架构决策（本文档 §2.4） |

---

## 5. 实验边界（硬约束）

1. **不写生产数据库** — 用临时数据库或 SQLite
2. **不改 V3 生产代码** — `backend/app/` 零改动
3. **不建正式 API** — 无 `POST /documents/import-manifest`
4. **只读 preprocessing 产出** — `reslice-p2-b1/` 38 卷
5. **输出是报告** — `consumer-report.json`，不是入库结果

---

## 6. 成功标准

不是 pass/fail，是**contract matrix**：

```json
{
  "dataset": "reslice-p2-b1",
  "version": "v2.3",
  "total_units": 0,
  "track_a": { "gate_pass": 0, "resolver_fail": 0, "schema_fail": 0 },
  "track_b": { "gate_pass": 0, "admission_ready": 0 },
  "contract_gaps": [{ "type": "locator_authority", "count": 0 }]
}
```

决策规则：

| 结果 | 结论 |
|---|---|
| Track B > 95% | 设计正式 ManifestAdmissionImporter |
| Track A 大量失败 + Track B 成功 | V3 需增加 external authoritative span source |
| Track B 也失败 | 两侧 domain model 有结构冲突，需架构决策 |

---

## 7. 回滚条件

Phase 0 失败 ≠ 项目失败。回滚动作：

1. `scripts/preprocessing_consumer/` 整目录删除
2. 本文档 Status 改为 `EXPERIMENT CLOSED — SEE REPORT`
3. consumer-report.json 保留为决策依据
4. V3 生产代码/数据库零影响（从未触碰）

---

## 9. Phase 0 实验结果（2026-09-14，已完成）

### 9.1 Track B — 决定性证据

| 指标 | 结果 |
|---|---|
| Manifest 数量 | 38 |
| Question Unit 数量 | 871 |
| Span 总数 | 2934 |
| Span 构造成功 | **2934（100%）** |
| Span 失败 / Unresolved | **0** |
| Bad Reference | **0** |

**preprocessing 的 Resolved Evidence 模型与 V3 sealed source 完全兼容。**
preprocessing 产生的 span reference 信息熵低于 V3 Resolver（确定位置 vs 搜索猜测），
是更强的定位源。

### 9.2 Track A — Lossy Transformation 实证

| 指标 | 结果 |
|---|---|
| 871 units → candidates | 1（0.11%） |
| skipped（Resolver 未 ready） | ~870 |
| 根因 | **有损转换**：高精度行号 → 低精度角色声明 → Resolver 无法恢复 |

Track A 不是证明 Resolver 不行，而是证明「把高精度 annotation 降级成低精度后，
再让 Resolver 恢复信息」不可行。

### 9.3 修正后的架构结论

**原假设**：preprocessing manifest 与 V3 存在定位 contract gap。
**实测修正**：定位没有冲突。冲突发生在 **Annotation Representation** 层。

| 层 | 兼容性 |
|---|---|
| Source 层 | **完全兼容** |
| Span 层 | **完全兼容** |
| Annotation 层 | 存在哲学差异（强定位 vs 弱定位） |
| Gate 层 | 尚未验证（Phase 0.2） |

### 9.4 V3 Contract 修正方向

不推翻 V3，而是增加第二个合法 ResolvedSpan Producer：

```
LLM Annotation → SourceResolver → ResolvedSpan     （现有 Path A）
Preprocessing Manifest → EvidenceAdapter → ResolvedSpan （新增 Path B）
```

preprocessing manifest 属于 **Source Evidence Layer**（不是 Annotation Layer）：
它提供文档切片、行级定位、图文关系、question/answer boundary——
都是 V3 不应该重新推理的信息。

### 9.5 对 preprocessing 项目的定位升级

~~preprocessing 是 V3 上游 OCR 工具~~
**preprocessing 是 V3 的 Source Intelligence Layer。**

---

## 10. Phase 0.2 结果（2026-09-14，已完成）

> **⚠ Phase 0.2 为含 synthetic option boundaries 的 provisional run。**
> 最终 baseline 以 §11 Phase 0.2-R2 为准。

### 总体

| 指标 | 值 |
|---|---|
| 卷级完成 | 38/38（0 错误） |
| Ready units | **647 / 871（74.3%）** |
| Skipped | 224 |
| Compiled leaves | 647 |
| **Gate auto_approve** | **44** |
| **Gate rejected** | **0** |
| Gate pending_review | 603 |

### 迭代

| 轮次 | Ready | 修复 |
|---|---|---|
| 首次 | 181（20.8%） | 基线 |
| 修正 annotation 格式 | 632（72.6%） | composite shared_components + per-label option spans |
| 修正 answer_evidence | **647（74.3%）** | answer_lines null → fallback evidence.lines |

### 核心结论

**preprocessing 的 Resolved Evidence 模型与 V3 完全兼容。冲突在 Annotation Representation，不在 Source Resolution。**

正确方向：增加 EvidenceAdapter 入口（Path B），让 preprocessing 的 ResolvedSpan 直接进入 IR。

### Skipped 原因（224 个）

composite 格式映射不完整（语文/英语阅读理解）· answer_evidence 与 explanation 行重叠 · options 均分假设 · 题型边缘情况。**均属 adapter 调优范畴，非架构障碍。**

> **⚠ Provisional**: Phase 0.2 的 647 ready 包含实验性 per-label option inference（均分假设）。
> 不应作为最终 adapter compatibility baseline。见 §11 Phase 0.2-R2。

---

## 11. Phase 0.2-R2 — Evidence-Faithful Re-run（2026-09-14，已完成）

### 背景

Phase 0.2 的 647 ready 中，choice-type 单元的 options 依赖均分假设（伪造 per-label A/B/C/D span）。
实验 harness 不能制造它正在验证的证据。移除 synthetic option boundaries 后重跑。

### 变更

| 变更 | 内容 |
|---|---|
| annotation_adapter | 移除 per-label option 声明（不再 fabricate A/B/C/D） |
| runner_b2 | `_try_options` → `_try_options_region`（单个 options region span） |
| 输出 | `consumer-report-b2-r2.json` |

### 结果

| 指标 | Phase 0.2 (synthetic) | **Phase 0.2-R2 (evidence-faithful)** |
|---|---|---|
| Ready | 647 (74.3%) | **289 (33.2%)** |
| Skipped | 224 | **582** |
| auto_approve | 44 | **0** |
| pending_review | 603 | **289** |
| rejected | 0 | **0** |
| Compiled leaves | 647 | **289** |

### 关键结论

1. **-358 ready**：全部来自 choice-type 的 per-label option fabrication。这些单元的 options 是 preprocessing 的 region-level 事实，V3 IRBuilder 要求 per-label 粒度——这是真实的 Evidence Semantics gap。
2. **auto_approve 44 → 0**：证实之前的 auto_approve 是 synthetic evidence 产物，不是真实兼容性。
3. **289 ready = 真实兼容 baseline**：这些单元（fill_in, short_answer, essay 等非 choice-type）的 Resolved Evidence 与 V3 完全兼容，无需合成假设。
4. **0 rejected**：Gate 对真实证据仍然不会 reject——它只是标记不确定性。

### 三个数字的分层含义

| 数字 | 含义 | 回答的问题 |
|---|---|---|
| 100% span 构造 | 事实层 | preprocessing 的定位模型能否被 V3 理解？**能。** |
| 33.2% IR ready | 结构表达层 | preprocessing 的证据粒度能否满足 V3 格式？**非 choice 可以，choice 不行（需要 options 语义解决）。** |
| 0 auto_approve | Gate 策略层 | Gate 是否对真实证据有信心？**保守，正确。语义不确定性走人工。** |

### Phase 0.3 Mandate（Evidence Producer Contract Freeze Candidate）

Phase 0.3 分三步（先设计后编码）：

| 子任务 | 问题 | 输出 |
|---|---|---|
| **0.3-A: Evidence Schema** | preprocessing 到底交付什么？ | Source identity / Evidence span / Role / Boundary / Relation / Grouping / Producer provenance / Manifest version |
| **0.3-B: Evidence Semantics** | 哪些是事实？哪些是推断？ | Evidence vs Claim vs Classification vs Relation 的边界定义 |
| **0.3-C: Admission Boundary** | 什么条件下 preprocessing evidence 可成为 Admission 有效事实？ | EvidenceAdapter → ResolvedRun → IR → Gate → Admission 的完整边界 |

**Phase 0.3 完成后进行 Document Birth 判定**（90/91 治理）：

```
现有 L0 能承载？
  ├─ YES → 修改现有 L0（必要时走 L1）
  └─ NO → 是 V3 normative 架构事实？
             ├─ YES → 新 L0（走 L1 批准）
             └─ NO → L2 Decision / integration contract
```

当前名称：**Evidence Producer Contract Candidate**（不是 Contract——90 规定 authority closure 完成后才能叫 Contract）。

---

## 12. Phase 0.3-B — Source-Grounded Option Label Resolution（2026-09-14，已完成）

### 实验设计

用 548 个真实 skipped choice-type units 验证：`options_region` → Source marker detection → labels → per-label spans。

**规则（冻结）**：
1. 输入仅为 preprocessing 已提供的 `options_region`
2. 不从 question_type 生成 labels
3. labels 必须来自该 region 的实际 Source marker（行首 `A.` / `(A)` 等）
4. 复用现有 `option_tokens` / `_LABEL_RE` 检测逻辑
5. 不允许 equal split / 长度猜测 / LLM
6. 无法确定 → unresolved / ambiguous
7. 不修改 V3 production code

### 结果

| 分类 | 数量 | 占比 |
|---|---|---|
| **resolved** | **527** | **96.2%** |
| no_labels | 16 | 2.9% |
| incomplete | 5 | 0.9% |
| ambiguous | 0 | 0% |
| invalid_order | 0 | 0% |
| out_of_region | 0 | 0% |

resolved 细分：
- 517 units 检测到恰好 4 labels（A/B/C/D），全部定位成功
- 5 units 检测到 3 labels
- 3 units 检测到 1 label
- 2 units 检测到 5 labels

### Correctness Sampling

抽查验证（多行 / 单行 / 公式 / inline）：

- **多行**（357 units）：`A.` `B.` `C.` `D.` 各占一行，行首 marker 精确定位 ✓
- **单行**（160 units）：`A. NaOH B. Mg(OH)₂ C. Al(OH)₃ D. KOH` → A 行首 ok，B/C/D inline with character offsets ✓
- **含公式**（113 units）：`$ H_2 $` 等 LaTeX 不干扰 label detection ✓

### 16 个 no_labels 归因

| 格式类型 | 数量 | 说明 |
|---|---|---|
| HTML table 内嵌 | 7 | label 在 `<td>` 内，不在行首 |
| 单行首 label 缺标点 | 5 | `A 反映了... B. ...` — `A` 无句号 |
| HTML div 包裹 | 3 | `<div>A.</div>` — 行首是 `<div` |
| 行内混排 | 1 | label 在正文后 |

**定性：Current Resolver marker-grammar coverage gap**（不是 preprocessing bug）。

### 5 个 incomplete 归因

inline 检测从化学式等正文误检到 `H` / `G` label marker。正确归类为 incomplete（保守 pending_review）。

### 架构结论

**PASS — 实验验证支持 Source-grounded option resolution 路线。**

> Producer 提供 Evidence Region（`options_region`）；
> Canonical Resolver 负责从 Source Evidence Region 中解析更细粒度的 per-label Evidence。

```
Preprocessing → options_region → EvidenceAdapter
  → Source-grounded label detection → Canonical Resolver
  → per-label Resolved Evidence → V3 IR
```

**Producer Contract 不需要强制 per-option spans。** preprocessing 继续提供 `options_region` 即可。

**16 + 5 = 21 units → pending_review。** 不猜、不均分、不按题型制造 A/B/C/D。

**不改 L0 Frozen Spec。** 本实验证明既有架构可以这样工作，属于 L2 实现/兼容性决策。

---

## 13. 前置依赖

- [x] preprocessing P2.1-c 收口（38 卷，97.44% parse）
- [x] V3 Gate pipeline 稳定（Step 2 三 BUG 已修，810 passed）
- [x] Phase 0 双轨实验完成（§9）
- [x] Phase 0.2 完整链验证完成（§10，含 synthetic evidence，provisional）
- [x] Phase 0.2-R2 evidence-faithful re-run 完成（§11）
- [x] Phase 0.3-B Source-Grounded Option Label Resolution 完成（§12）
