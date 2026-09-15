# PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW v0.2

> **角色**：Claude = AITutors-v3 Consumer Owner（非 preprocessing 重新设计方）。
> **任务**：基于 DQE 报告，回答 Integration Contract v0.1 **是否可以冻结**。
> **性质**：仅消费者事实审查。**未修改 preprocessing / 未修改 V3 adapter / 未提出实现方案 / 未冻结契约。**
> **结论先行**：**Contract 当前不可冻结。** 4 项 PASS 面已就绪，3 项 BLOCK 面阻止冻结。详见 §D。
>
> **证据基线（亲验 2026-09-16）**：
> | 仓 | HEAD | 说明 |
> |---|---|---|
> | preprocessing（canonical ledger，`D:/Project/Papers`） | `4d78513` | DQE 报告基线 |
> | V3（`AITutors-v3`） | `b5ddbe3` | 本地；origin/main=`69a6c0b`，ahead 6 |
>
> 被审契约：`Docs/COORDINATION/INTEGRATION/PREPROCESSING-INTEGRATION-CONTRACT.md` v0.1 DRAFT @ preprocessing 仓 `1fbaf5e`。
> `git diff --stat 1fbaf5e 4d78513 -- Docs/COORDINATION/INTEGRATION/` → **空**，契约自起草起未改，基线有效。
>
> 本文件取代 v0.1（`Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md`）的结论部分；
> v0.1 的 GAP-C1/C2/C3 登记仍然有效，本版按 DQE 新证据**收紧并修正其中一处**（见 §B 勘误）。

---

## A. Source Identity

### A.1 事实：IR 层存在 `source_sha256`

**OBSERVED**（DSH 侧 DQE 报告 §4，preprocessing @ `4d78513`）：

- IR（resolver-ir-0.1）文件级字段 `source_sha256` = 源 OCR markdown **文件字节** SHA-256。
- 实测 **71/71 含 IR 的文件与当前源对账，0 缺失 0 不符**——IR↔源绑定完好，零漂移。
- 契约 §1.1 与 §2.2 均以该 sha 为跨系统唯一对账锚。

### A.2 事实：manifest 层不存在

**OBSERVED**（同上）：

- manifest v2 全语料 **0/166 携带任何 sha 键**（精确键遍历；`"shared"` 子串误命中已排除，DQE §6 F-DQ-2）。
- manifest 只钉 `source_file` 路径 + 行号锚。
- DQE 结论定性为「如实的结构事实，非缺陷」——**从 producer 内部分层看成立**。但该分层与 V3 的实际消费面冲突，见 A.3。

### A.3 事实：V3 当前消费路径 = manifest，不是 IR

**OBSERVED**（V3 @ `b5ddbe3`）：

| 检查项 | 结果 | 证据 |
|---|---|---|
| V3 全仓是否读取 IR | **零消费** | `Grep resolver_ir\|resolver-ir\|\.ir\.json\|source_sha256` @ `backend/` → **0 命中** |
| V3 实际读取器 | manifest JSON | `scripts/preprocessing_consumer/manifest_reader.py:44-75`（`load_manifest`） |
| `Manifest` dataclass 是否含 sha 字段 | **无** | `manifest_reader.py:28-35` — 仅 `source_file / model / prompt_version / validation_issues / warnings / units` |
| 下游适配 | manifest → payload / spans | `annotation_adapter.py:97-115`；`resolved_span_adapter.py:50-92` |
| V3 自算的 hash | 存在，但**对不上** | `runner.py:71-73`：`body_text = "\n".join(...)` → `body_hash` → `file_sha = sha256_hex(body_text)` |

**V3 侧 hash 为何对不上 preprocessing sha**（v0.1 §4.2 实测，机制本轮复核仍成立）：

1. `file_sha` 走 `sha256_hex`（`app/core/hashing.py:60-62`）——先 `canonical_json` 再 hash。字符串会被 JSON 引号包裹，故 `sha256_hex(body_text)` **永远不等于** 原始字节 sha256。
2. `body_hash` 走 `compute_body_hash`（`source_loader.py:43-46`）——`splitlines()` 规范化后 join 再 hash。对含 CRLF 或尾随换行的文件**会漂移**（v0.1 实测 12 份 ADMITTED 样本中 6/12 DIFFER）。

### A.4 三事实合取的后果

契约 §3.1 把 `source_sha256` 列为**必须提供**（文件级 + 单元级 provenance），§2 声明「V3 消费以 IR 为准，manifest 为回源凭据」。

但：

- 该 required-field 清单是**按 IR 层写的**；
- V3 实际读的是 **manifest 层**；
- manifest 层**没有 sha**；
- V3 自算的 hash **定义与 producer 不一致**，无法替代。

**因此契约承诺的 source binding 在 V3 当前消费路径上没有数据可用。** 这不是「对账机制尚未实现」，而是「消费面上连对账所需的输入都不存在」。契约 §4.2「`source_version_id` ↔ `source_sha256` 一一对应」当前是**设计意向，不是可达成的事实**。

### A.5 结论：**BLOCK — Contract 当前不可冻结，需要明确传输层。**

冻结前必须先裁定**跨系统传输层**：V3 的消费载体到底是 IR 还是 manifest。三条互斥路径（**仅陈述，不提案**）：

- 契约把 V3 消费面改以 manifest v2 为准，则 §3.1 的 sha 项须落到 manifest，或该项从 V3 required 面移除；
- V3 排期 IR loader，则 §3.1 现状成立，但 V3 当前无任何 IR 读取代码（A.3 第一行）；
- 维持双载体，则 §2 与 §3.1 的措辞必须显式区分哪一层的哪些字段是 V3 required。

在传输层未定前，§3.1 required 清单与 §4.2 一一对应主张**均无法验证**，冻结即冻结一个当前不可满足的承诺。

---

## B. unit_type

### B.1 事实：preprocessing 存在非标准值

**OBSERVED**（DQE §1，全语料穷举 166 manifest × 4,609 单元 + IR 1,664 单元）：

| 值 | manifest 全语料 | IR（88 审计面） | 判定 |
|---|---|---|---|
| `standalone_question` | 3,935 | 1,385 | canonical |
| `composite_question` | 673 | 278 | canonical |
| **`andalone_question`** | **1** | **1** | 非标准（拼写噪声） |

- 唯一异常定位：`Ocr-markdown\reslice-batch-C\合格考\化学\2020北京高中合格考化学（第一次）（教师版）(1).manifest.json`，unit `Q1`。
- 属 **identity v2 可消费面**（batch-C），不是 legacy 边角。
- IR **忠实携带**（零重塑纪律的反面实证：噪声原样过界）。

### B.2 事实：V3 消费**不能**区分未知 `unit_type`

**OBSERVED**（V3 @ `b5ddbe3`）——`manifest_reader.py:52` 硬取 `u["unit_type"]`，**不校验闭集**，值原样进 `ManifestUnit`。下游三处分流：

| 消费点 | 判断式 | `andalone_question` 落入 | 证据 |
|---|---|---|---|
| annotation payload 构建 | `if unit_type == "composite_question" → else` | **standalone**（`_build_standalone`） | `annotation_adapter.py:101-104` |
| ResolvedSpan 构建 | `if unit_type == "standalone_question" → else` | **composite**（material/questions 路径） | `resolved_span_adapter.py:77-90` |
| Track B span 构建 | `if unit_type == "standalone_question" → else` | **composite** | `runner_b2.py:116-127` |
| candidate `unit_type` 字段 | `=="standalone_question" ? "standalone_unit" : "composite_unit"` | **`composite_unit`** | `runner_b2.py:252` |

**无任何一处产生 unknown/隔离信号。** 该值静默通过全部消费点。

### B.3 勘误（修正 v0.1 GAP-C2）

v0.1 GAP-C2 记为「`unit_type` 非闭集值被静默当 **standalone**」——**只覆盖了 `annotation_adapter` 一处，不完整**。

本轮全量核对后的真实事实：**三处消费点对同一个未知值的解释互相矛盾**——

- `annotation_adapter.py:101-104` 把它当 **standalone**（因它不是 composite）；
- `resolved_span_adapter.py:78` 与 `runner_b2.py:117` 把它当 **composite**（因它不是 standalone）；
- `runner_b2.py:252` 落库的 candidate `unit_type` 为 **`composite_unit`**。

即同一 unit 会在 annotation 层按 standalone 编排、在 span 层按 composite 解析、在 candidate 层记为 `composite_unit`。**这不是「静默吞噪」而是「静默分裂」**——比 v0.1 所记更严重。

### B.4 与契约条款的对照

契约 §3.3-6 要求：`unit_type` 超出 `{standalone_question, composite_question}` → **隔离（PENDING 通道）**，「不得静默当 standalone 吃」。

**当前 V3 消费侧未实现该隔离**，且实现面比契约禁止的还要宽（既吃 standalone 又吃 composite）。

### B.5 与 DQE §1 选项 A 的跨仓矛盾（登记，不裁决）

DSH 的 DQE §1 选项 A 陈述：「非标准值 → 隔离进 PENDING 通道（契约 §3.3-6 既有条款）……**已生效，无需动作**」。

**该陈述与 V3 实际代码矛盾**（B.2 表：四处消费点零隔离）。DSH 侧认为消费侧已有守卫，V3 侧实际没有。这是**跨仓事实错误，不是意见分歧**，需 DSH 更正其陈述或指明守卫所在位置。

**本节不判断修复方式**（任务禁止项）。仅登记：能否区分 = **不能**；契约要求隔离 = **未实现**；DSH 陈述「已生效」= **与代码不符**。

---

## C. Figure

### C.1 当前交付能力（OBSERVED，DQE §2，源树 4,223 份 md 全量）

| 维度 | 事实 |
|---|---|
| 总引用 | **70,838** 处，分布于 3,578 份文件 |
| 形态 | 行内 HTML `<img src>` 本地相对路径 **70,829（99.99%）** + 外链 http 9（latex.codecogs SVG） |
| markdown `![]()` | **0** |
| 绝对路径 / data URI | **0 / 0** |
| 独立 figure 注册表 | **无**（契约 §2.4） |
| 图片 sha / bbox / page_no | **不提供** |

### C.2 引用存在 vs 资产存在（关键区分）

| | 引用存在 | 资产存在 |
|---|---|---|
| 已改写形态（`../../_imgs/...`） | ✅ | ✅ **悬空 = 0** |
| 未恢复原始形态（`imgs/...`） | ✅ | ❌ **悬空 27,240 处 / 1,396 份文件** |
| 合计 | 70,838 处 | 缺口 = 27,240 处（**单一归因 `bare_imgs_no_asset_anywhere`**） |

**即：引用存在 ≠ 资产存在。** 27,240 处引用指向从未从 PDF 恢复的资产（recover_images 积压家族）。增长主因 = daemon 持续产出新 OCR 文件（其原始形态即含 `imgs/` 引用），DQE 判定为已知机制非新缺陷。

### C.3 V3 侧消费现状

| 检查项 | 结果 | 证据 |
|---|---|---|
| `SourceFigure` 表 | 存在，要求 `figure_id/page_no/bbox/placement/source/object_key/figure_hash` | `app/models/source.py:99-120` |
| preprocessing 提供上述任一字段 | **一样都不提供** | 契约 §2.4；DQE §2 |
| consumer 路径 figure 消费 | **零**（`runner.py:43` 仅 import，全文件无使用） | `runner.py:43` |
| IRBuilder figure | 明确延后 | `ir.py:145`（figure_refs 延后 BUG-V3-020）、`ir.py:220-222`（unsupported → fail-loud） |
| material binding | 现状可用且稳定 | `material_lines` → `sp-{unit_id}.material`（`resolved_span_adapter.py:87`）；composite 共享材料经 IR 校验（`ir.py:230`） |

### C.4 结论

**字段级不可对接**：`SourceFigure` 需要的 7 个字段，preprocessing 一个都不产出。现阶段建 registry **无输入**。

DQE §2 独立得出同一结论：「最小 registry **不需要**……缺的是**资产恢复执行**，不是注册结构」，并明确「若未来 V3 要求图片 sha/独立清单，属 OQ-3，由 Claude Consumer Review 提出后再议」。

**V3 现阶段不提出该需求**（任务禁止假设未来需求）。OQ-3 保持开放。**Figure 不阻塞契约冻结**——但 §C.2 的 27,240 处引用-资产缺口是 producer 侧已量化的事实，契约 §2.4 现只描述引用形态、**未声明资产在位性**，建议冻结前在契约中如实补一句资产缺口现状（措辞由 Owner/DSH 裁，本文件不代拟）。

---

## D. Contract Freeze Gate

### D.1 PASS — 已满足

| # | 项 | 证据 |
|---|---|---|
| P1 | **IR↔源 sha 绑定完好**：71/71 零漂移，producer 侧 source binding 自洽 | DQE §4；契约 §1.1 |
| P2 | **R50 冻结基线零漂移**：356/356，`audit_integrity verify` = 0 drift / 0 missing | DQE §4 |
| P3 | **行锚机制可用且 V3 已验证消费**：`[start,end]` 1-based 闭区间 → `P1L{line:03d}`，span 解析 + 越界显式 unresolved（不猜测） | `resolved_span_adapter.py:30-47,63-75`；Phase 0.3-B 527/548 = 96.2% coverage |
| P4 | **material binding 现状稳定**：`material_lines` → material span，composite 共享不复制经 IR 校验 | `resolved_span_adapter.py:87`；`ir.py:230`；契约 §2.3 |
| P5 | **Authority 不迁移模型两侧一致**：新 sha = 新 source_version，旧权威不迁移 | DEC-016 / 92号；契约 §1.3；`source.py:65`（`parent_version_id` 槽位存在但 consumer 路径不写） |
| P6 | **producer 结构承诺有实测锚**：F1 四项对账 88 份 2403/2403 MATCH | 契约 §2.2；DQE §4 |
| P7 | **unresolved 显式通道存在**：span unresolved 落 `unresolved_references`，无静默默认 | `resolved_span_adapter.py:70-75`；契约 §3.2 特别条款对 V3 天然成立（V3 不读 `answers` 表） |

### D.2 BLOCK — 阻止冻结

| # | 项 | 阻断内容 | 依据 |
|---|---|---|---|
| **B1** | **传输层未定（A）** | 契约 §2「消费以 IR 为准」vs V3 实读 manifest；§3.1 required 清单按 IR 写，manifest 层 0/166 有 sha。**required 承诺在当前消费路径上不可验证** | §A.3–A.5 |
| **B2** | **source identity 对账不可达成（A/Q4）** | 契约 §4.2「一一对应」当前无法成立：V3 自算 hash 两路都对不上（canonical_json 引号 / splitlines 规范化），且 manifest 无 sha 可比。**契约级缺口，已登记未发明** | §A.3；v0.1 GAP-C3 |
| **B3** | **unit_type 隔离未实现且跨仓陈述矛盾（B）** | 契约 §3.3-6 要求隔离；V3 四处消费点零隔离，且三处解释**互相矛盾**（standalone / composite / composite_unit）。DQE §1-A 称「已生效，无需动作」与代码不符，**需 DSH 更正陈述** | §B.2–B.5 |

### D.3 非阻塞但冻结前应补

| # | 项 | 内容 | 依据 |
|---|---|---|---|
| N1 | figure 资产在位性未入契约 | §2.4 只写引用形态，未声明 27,240 处引用-资产缺口 | §C.2 |
| N2 | `printed_number` / `basis` / `qc_verdict` / `disposition` / `provenance` 七字段块 / `material_ref` 字符串 / `answers` 表 | V3 **当前无消费路径，不提出需求**（契约 §3.1 清单对 V3 现阶段偏宽——多出的字段是 producer 自证层，V3 重新推导） | v0.1 Q1 表；本版复核 `Grep qc_verdict\|disposition` @ `backend/` = 0 命中 |

### D.4 冻结判定

**Contract v0.1 不可冻结。**

三个 BLOCK 中，**B1 是根因**——传输层不定，则 B2 的对账无处落地（连要比对的字段在哪个载体上都没定），B3 的隔离也失去统一执行面（隔离该在哪一层做取决于消费载体）。

**建议的解封顺序（陈述依赖关系，非实现方案）**：先裁定传输层（B1）→ 据此定 source identity 对账口径（B2）→ 据此定 unit_type 隔离执行面并请 DSH 更正 §1-A 陈述（B3）→ 补 N1 资产在位性措辞 → 再议冻结。

---

## 边界声明

**本文件做了**：消费者事实审查；四问逐项作答；三项 BLOCK 登记；与 DQE 的一处跨仓矛盾登记（§B.5）；v0.1 GAP-C2 的不完整表述勘误（§B.3）。

**本文件没做（任务禁止项）**：未修改 preprocessing 任何文件；未修改 V3 adapter / 生产代码；未提出实现方案（§A.5 三条路径仅陈述互斥可能，§D.4 仅陈述依赖顺序）；**未冻结契约**——冻结裁决归 Owner。

**EB-008 状态**：不因本文件变动。设计冻结保持（DEC-016 / 92号）；P1 待外部验证的状态不变。

---

*v0.2 — 2026-09-16，Claude（AITutors-v3 @ `b5ddbe3`）。被审契约：preprocessing 仓 @ `1fbaf5e`（未改）；DQE 基线：preprocessing @ `4d78513`。不冻结；等待 Owner 最终裁决。*
