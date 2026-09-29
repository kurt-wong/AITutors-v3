# PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW v0.1

> **角色**：Claude = AITutors-v3 Consumer Owner（非 preprocessing 重新设计方）。
> **任务**：回答 DSH handoff 014 四问——确认 V3 是否能基于当前 preprocessing 输出稳定运行。
> **被审对象**：`Docs/COORDINATION/INTEGRATION/PREPROCESSING-INTEGRATION-CONTRACT.md` v0.1 DRAFT（preprocessing 仓 @ `1fbaf5e`）。
> **状态**：本文件 = Consumer Review 应答，**不冻结 Contract**；冻结裁决归 Owner。
>
> **证据基线（双仓亲验 2026-09-15）**：
> - V3 仓 `AITutors-v3` HEAD = `b5ddbe3`（本地；origin/main=`69a6c0b`）。
> - preprocessing 仓 `D:/Project/Papers`（kurt-wong/Aitutors-preprocessing）HEAD = `1fbaf5e`。
>
> **事实基线确认（handoff 014 §事实核验，Owner Decision Point 3）**：
> 四件产物（Review-1 报告 / `attacks/test_eb008_impl_attack.py` / commit `eea4a4e` / DEC-017/018）**均在 preprocessing 仓，已亲验**：
> `git -C D:/Project/Papers show --stat eea4a4e` → 6 files, 888 insertions（含 `Docs/COORDINATION/EVIDENCE/EB008-IMPLEMENTATION-REVIEW-1.md`、`attacks/` 套件、state.yaml `impl_review_1`）。
> 此前 V3 侧记录 "External verification evidence unavailable in current repository state." 对 **V3 仓** 为真、对**事实全貌**不完整——检索方向正确、目标仓错误。**确认此事实基线**，两 Agent 记忆以此对齐。按 Owner 裁定，该 Review-1 不作为推进 EB-008 状态的依据，本文件不改 EB-008 台账。

---

## Question 1 — §3.1 required fields：V3 消费面分类

分类定义：**A** = V3 必须依赖；**B** = V3 可以降级；**C** = V3 当前不需要（无消费路径，**不提出需求**）。

### 前置事实：V3 读 manifest，不读 IR

契约 §2 声明 "V3 消费以 IR 为准，manifest 为回源凭据"。**V3 现状不是**：backend 全库无 `resolver_ir` / `ir_version` / IR loader 代码（`Grep resolver_ir|ir_version|load_ir|read_ir` @ `backend/` → 0 命中）。V3 消费入口是 manifest JSON：

- 读取器：`backend/scripts/preprocessing_consumer/manifest_reader.py:44-75`（`load_manifest`，V3 @ `b5ddbe3`）。
- 适配：`annotation_adapter.py:97-115`（manifest → annotation payload）、`resolved_span_adapter.py:50-92`（manifest → ResolvedSpan）。
- 实验入口：`runner.py` / `runner_b2.py` / `runner_b3.py`（`runner.py:1-14` 边界声明：不改生产代码、只读 preprocessing 产出）。

**这是登记项 GAP-C1（映射缺口，非就地发明）**：Contract 冻结前须裁定消费载体——要么契约改以 manifest v2 为 V3 消费面（IR 为 producer 内部产物），要么 V3 排期 IR loader。现状下 IR 独有字段对 V3 全部是 C。

### 逐字段分类（契约 §3.1 清单 + V3 实际读取面）

| 字段（契约 §3.1） | 类 | V3 代码位置 | 使用场景 | 缺失后的行为 |
|---|---|---|---|---|
| `question_numbers` | **A** | `manifest_reader.py:53`；`annotation_adapter.py:17-18`（`_qn` → `question_label`） | 每 unit 的 question_label；IR/Gate 的题号锚 | 缺 → `question_numbers=[]` → label=""，Gate 单元身份退化；runner 不拒收（`.get` 默认空），**契约层应拒收该 unit** |
| `unit_id` | **A**（仅 SV 内） | `resolved_span_adapter.py:35`（`span_id="sp-{unit_id}.{role}"`）；`annotation_adapter.py:41`；`admission.py:531-538`（claim_id = IR root unit_id） | span 命名、annotation unit 键、EB-008 claim_id | 缺 → `u["unit_id"]` KeyError（`manifest_reader.py:51`）→ 整份 manifest load 失败。**注意**：契约 §2.1 实测 unit_id 汇编卷内可重复（78 例）——V3 用它做 claim_id 安全，因为 AuthorityIdentity=(source_version_id, candidate_id, claim_id) 三元绑定（`evidence.py:28-29`），**禁止**跨文档裸用（与契约 §4.1 一致） |
| `unit_type` | **A** | `annotation_adapter.py:101-104`（composite 分支）；`runner_b3.py:41`（choice 类型集） | standalone/composite 分流 | 缺 → KeyError 整份拒收。**偏差 GAP-C2**：else 分支把任何非 composite 值（含实测噪声 `"andalone_question"`）**静默当 standalone**，违反契约 §3.3-6 隔离要求——待修（实现偏差修复，在 Owner 允许的修复范围内，本轮只登记） |
| `stem_lines` / `options_lines` / `answer_lines` / `explanation_lines` / `material_lines` / `questions_lines` | **A** | `manifest_reader.py:57-62`；`resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` | 行区间 → ResolvedSpan（`line_ref=P1L{n:03d}`，`source_loader.py:32`） | 缺 → 该 role 无 span（`_try` 静默 skip，`resolved_span_adapter.py:63-65`）；composite 缺 material → IR invalid（`ir.py:230`）。行号越界 → unresolved 显式记录（`resolved_span_adapter.py:69-75`），**不猜测**——与契约 §3.3-4 一致 |
| `answer_evidence`（type/lines/value） | **B** | `manifest_reader.py:64-66`；`runner_b2.py:112-114`（answer_lines 优先，fallback 到 answer_evidence_lines） | 答案 span 的降级来源（v2.4+） | 缺 → 无 answer span → 该 unit answer unresolved；不影响其余 role |
| `original_question_type` | **B** | `annotation_adapter.py:44,89`；`runner_b3.py:41,196`（choice 过滤） | choice-type 判定（options 标记检测的前置过滤） | 缺 → 默认 `""`（`manifest_reader.py:54`）→ 非 choice，跳过 options 实验路径 |
| `printed_number` | **C** | 无消费路径（V3 代码无读取） | — | 契约 §3.2 允许 null（27.1%）；V3 不依赖、不补全 |
| `section_ref` / `section_title` / `section` | **C** | `manifest_reader.py:55` 读 `section` 但下游零使用 | — | 无影响；跨系统 claim 身份（契约 §2.2 三元组）中 section_ref 成分 V3 现阶段不消费——对账靠 source_version_id（见 Q4） |
| `basis` / `basis_evidence` / `printed_provenance` | **C** | 无消费路径 | — | 契约 §3.3-7（basis 值域→PENDING）现阶段 V3 无消费面即无该检测点；OQ-4 producer 落地后重评 |
| `qc_verdict` / `disposition` | **C** | 无消费路径（`Grep qc_verdict|disposition` @ `backend/` → 0 命中；Gate 用自己的 `gate_decision`，`runner.py:157-164`） | — | V3 Gate/Admission 独立判定，不读 producer QC 结论。契约 §3.3-1/2 的阻断语义由 V3 侧 Gate rejected + Admission fail-closed 等价承担（`admission.py:213-223`） |
| `provenance` 七字段块 | **C**（作为数据） | 无直接读取；其事实由 V3 **重新推导**：`source_loader.py:24-46`（行/hash）、`runner.py:71-73`（body_hash） | — | 不依赖 producer 自检结论——符合契约 §2.2 "V3 可在自己侧重实现同一对账" |
| `material_ref`（ref 字符串，如 `"L536-567"`） | **C** | V3 用 `material_lines` 行对（`resolved_span_adapter.py:87`），不用 ref 字符串查 materials 表 | — | ref 悬空检测（契约 §3.3-5）在 V3 侧等价为 material_lines 缺失/越界 → unresolved |
| `answers` 表对象 / `answer_text` / `flags` | **C** | 无消费路径 | — | 契约 §3.2 特别条款（unresolved 禁 `answers.get(q,"")` 静默默认）对 V3 **天然成立**——V3 根本不读 answers 表，answer 槽位以 span unresolved 显式呈现 |
| `source_sha256`（文件级+provenance 内） | **B→A 意向** | 现无消费：`Manifest` dataclass 无此字段（`manifest_reader.py:28-35`）；V3 自算 `file_sha`（`runner.py:73`） | 跨系统对账锚（契约 §1.1/§4.2） | 现状缺失不阻断（V3 用自己的 hash），但**对账断裂**——见 Q4 GAP-C3 |

**Q1 结论**：V3 对 §3.1 清单的 A 类依赖 = `question_numbers`、`unit_id`、`unit_type`、六个行区间字段。其余字段 V3 当前**无消费路径，不提出需求**（回答契约 §3.1 完备性：清单对 V3 现阶段偏宽，多出的字段是 producer 自证层，V3 重新推导）。真正要契约补的是两个缺口：**GAP-C1（IR vs manifest 载体）**、**GAP-C3（sha 对账，Q4）**，外加实现偏差 **GAP-C2（unit_type 静默吞噪）**。

---

## Question 2 — Source Version lineage：V3 是否需要

**结论：不需要。明确记录为 future。**

- **使用位置（审查）**：V3 已有 lineage 机制的**模型槽位**——`DocumentSourceVersion.parent_version_id`（`source.py:65`）、`DocumentActiveSource`（`source.py:155-170`，复合 PK(document_id, role)）、`DocumentSourceSelectionEvent`（`source.py:173-190`，append-only，记录 old→new source_version_id）。但 preprocessing consumer 路径**从不写这些**：`runner.py:63-118` 每文件建一个 Document + 一个 sealed version，无 supersede 动作。
- **为什么 hash 足够、lineage 不需要（当前阶段）**：
  1. Identity Model 冻结（DEC-016 / 92号）：新 sha = 新 source_version；Authority 绑定 (source_version_id, candidate_id, claim_id)，**authority 不迁移**——这与契约 §1.3 "旧版本权威不得迁移到新版本"完全一致。既然权威不迁移，跨系统就**没有需要迁移指针才能表达的语义**。
  2. 重 OCR/修正 → 新 sha → V3 侧 = 新 Document（`original_sha256` UNIQUE，`source.py:33`）→ 新 evidence 链从零建立。旧版 authority 留在旧 SV 上，语义自洽。
  3. 跨版本"这是同一份卷的新版"的关联需求，是**运营/UI 层**需求，且 V3 内部用 `parent_version_id` + active-source 选择事件即可自持，**不需要 preprocessing 产出指针**。
- **数据模型需求**：无新增。若未来要，方向是 producer 在 IR/manifest 声明 `supersedes_sha256`，V3 写入既有的 `parent_version_id`——**future，不进 v0.1 冻结面**。

---

## Question 3 — Figure 交付形态

**结论：C — 延迟设计。** 基于当前 `<img relative path>` 形态（契约 §2.4），V3 现阶段**不需要 figure registry，保持 material binding 现状**。

- **V3 现状证据**：
  1. `SourceFigure` 表存在（`source.py:99-120`）但要求 `figure_id / page_no / bbox / placement / source / object_key / figure_hash`——preprocessing **一样都不提供**（行内相对路径、无注册表、无 sha、无 bbox，契约 §2.4 OBSERVED）。字段级不可对接 = 现阶段建 registry 无输入。
  2. IRBuilder 明确延后 figure：`ir.py:145`（figure_refs 延后 BUG-V3-020）、`ir.py:222`（image/blank → unsupported=True）。
  3. consumer 路径零 figure 消费：`runner.py:43` import 了 `SourceFigure` 但全文件无使用（仅 import）；三个 runner 均不建 figure 行。
  4. material binding 现状可用且稳定：`material_lines` → `sp-{unit_id}.material`（`resolved_span_adapter.py:87`），composite 共享材料经 IR 校验（`ir.py:230`）。
- **不假设未来需求**：当 BUG-V3-020（figure_refs 编译表示）排期时，再按契约 OQ-3 提出资产清单+sha 需求。此前 OQ-3 保持开放即可，**v0.1 冻结不被 figure 阻塞**。

---

## Question 4 — source_version_id ↔ sha256 对账

**结论：设计意向 = 一一对应，但对账机制当前不存在，且实测存在 hash 漂移。契约级缺口，登记不发明。**

### 4.1 现状机制（V3 @ `b5ddbe3`）

- V3 `source_version_id` = 生成时 UUID（`UUIDPrimaryKeyMixin`）；跨系统锚是 `documents.original_sha256`（UNIQUE，`source.py:33`）与 `document_source_versions.body_hash`（`source.py:67`）。
- consumer 写入值（`runner.py:71-73,77,92-93`）：
  - `body_text = "\n".join(splitlines())`；
  - `body_hash = sha256(body_text)`（`source_loader.py:43-46`）；
  - `file_sha = sha256_hex(body_text)` — 注意 `sha256_hex` 是 **canonical_json 包裹后**再 hash（`hashing.py:67-69`：字符串会带 JSON 引号），存入 `original_sha256`。

### 4.2 实测对账（2026-09-15，resolver_ir.json ADMITTED 样本）

preprocessing 声明 `source_sha256` 语义 = 源 md **原始文件字节** SHA-256（契约 §1.1）。12 份 ADMITTED 样本实测：

| 对比项 | 结果 |
|---|---|
| preprocessing 声明 sha vs 原始字节 sha256 | **全部 match**（producer 语义成立） |
| V3 `sha256_hex(body_text)`（runner 的 original_sha256） | **永远 DIFFER**（canonical_json 引号包裹所致） |
| V3 `body_hash`（splitlines+join 再 sha256） | **6/12 match，6/12 DIFFER**——差异文件全部含 CRLF 或尾随换行（splitlines 规范化改变了字节） |

**即：当前 V3 产出的任何 hash 都不能可靠对上 preprocessing 的 `source_sha256`。一一对应是设计目标，不是现状。**

### 4.3 登记为 GAP-C3（不就地发明，按 handoff 014 Q4 指令）

对账成立的最小方向（**提案，待 Owner 裁决，非本文件定案**）：V3 消费入口（a）在 manifest reader 增加 `source_sha256` 字段读取；（b）用**原始文件字节** sha256 重算比对（契约 §1.2 赋予 V3 的独立重算权）；（c）不一致 → 按契约 §3.3-3 阻断。**不需要转换表**——sha 本身即跨系统键；`source_version_id` 是 V3 内部句柄，`documents.original_sha256` UNIQUE 约束保证 sha→Document 单射，Seal 层 `UNIQUE(logical_execution_stage, logical_execution_hash)`（`source.py:52-56`）保证同 Seal 身份至多一个 version。漂移风险的根源不是映射缺失而是**hash 输入定义不一致**（字节 vs 规范化文本 vs canonical_json），修在定义对齐，不修在映射表。

### 4.4 附带发现（Q1 相关）

契约 §4.1 跨系统 claim 身份 = `(source_sha256, section_ref, question_numbers)`；V3 内部 claim_id = unit_id（`admission.py:531-538`）。两者**不冲突**：V3 claim 身份被 AuthorityIdentity 三元组的 source_version_id 绑住（`evidence.py:28-29`），跨文档撞号被结构性排除；但 V3 若要与 producer 侧按契约三元组对账 claim，同样依赖 GAP-C3 的 sha 对账先行。

---

## 汇总（登记项，全部待 Owner 裁决，本文件不定案、不冻结）

| # | 类型 | 内容 | 依据 |
|---|---|---|---|
| GAP-C1 | 契约映射缺口 | 消费载体：契约说 IR，V3 实读 manifest v2 | `Grep resolver_ir` @ backend = 0；`manifest_reader.py:44-75` |
| GAP-C2 | V3 实现偏差 | `unit_type` 非闭集值被静默当 standalone，应按契约 §3.3-6 隔离 | `annotation_adapter.py:101-104` |
| GAP-C3 | 契约级缺口（Q4 指令登记） | source_sha256 ↔ source_version_id 对账不存在；hash 输入定义不一致导致漂移实证 6/12 | `runner.py:73`；`hashing.py:67-69`；12 样本实测 |
| OQ-2 确认 | 消费侧策略 | V3 同意 unit_type 噪声不得静默消化；修 GAP-C2 即消费侧隔离落地 | 契约 §3.3-6 |
| OQ-1 回答 | future | lineage 不需要；authority 不迁移模型下 hash 足够 | `source.py:65,155-190`；DEC-016 |
| OQ-3 回答 | 延迟 | figure registry 现阶段无输入无消费；BUG-V3-020 排期时再提 | `source.py:99-120`；`ir.py:145,222` |

**对 §3.3 阻断清单的边界确认（handoff 014 Explicitly Do Not Do 第 2 条）**：V3 不重判 producer 已证结构事实。V3 侧的 "阻断" 实现面 = Gate rejected / Admission fail-closed（`admission.py:213-223`）/ span unresolved 显式化，全部是**消费面校验与自身状态机**，不复制 F1 四项对账等 producer 自检。

**EB-008 状态**：不因本文件变动。设计冻结保持（DEC-016 / 92号）；GAP-C2 属实现偏差修复范畴（Owner 已允许 bugfix/测试补充/实现偏差修复），待指令执行。

---

*v0.1 — 2026-09-15，Claude（AITutors-v3，@ `b5ddbe3`）。被审契约：preprocessing 仓 @ `1fbaf5e`。不冻结；等待 Owner 最终裁决。*
