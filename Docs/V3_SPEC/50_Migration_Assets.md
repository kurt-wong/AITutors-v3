# AI Tutor V3 — 迁移资产与收尾（Migration Assets / Golden Corpus / 清理与归档）

Version: v1.1（Baseline—Frozen，2026-09-05）
Status: V3 收敛基线（50 分册）— 已落实 v1.0 对抗性审查 P1-1~P1-4 + 3×LOW，冻结
Date: 2026-09-05
Supersedes: `Docs/V3_MIGRATION_MAP.md`（起草输入，将归档至 V3 `docs_archive/`）;上位
约束 `00_Master_Spec.md`（宪法级 1.2-final-candidate；**冻结由单独裁决，本册只呈
服从性证据**）;其余分册 `10/20/30/40`（冻结；本分册只引用其锚点，不新增架构/表/字段/
公式/状态机）;术语 `README.md` §2

> 本分册是**收尾与资产治理**：回答四个问题——**什么从 V2 带过来、Golden Corpus 怎么建、
> 什么绝不迁、历史材料怎么归档**。它**不参与架构设计**：五层执行契约（00→40）已闭合，
> 50 不做任何新的架构裁决，凡涉及模型/表的判断一律回指已冻结分册。

---

## 1. 定位：治理分册，不是架构分册

| 分册 | 状态 | 50 的关系 |
|---|---|---|
| 00 宪法 | 1.2-final-candidate | 服从；**本册交付 00 服从性证据（10/20/30/40 已各自服从 00，复核清单随本册），冻结与否由单独裁决**，不由本册自动触发 |
| 10/20/30/40 | 冻结 | 只引用锚点；不重定义 |
| **50** | 本册 | **资产清单 + Golden 计划 + 清理/归档关系** |

50 的内容边界（超此即违规回写架构）：

- **可复用资产清单**：什么可以带进 V3（00 §1 四类继承），供 40 §2 前置资产清点执行。
- **Golden Corpus 计划**：versioned 评测集怎么建（00 §7），与 40 fixture/corpus 两层的关系。
- **迁移与清理边界**：什么**绝不迁**（00 §1/§6 红线、10 §11）。
- **历史材料归档关系**：7 份起草输入 + v0.3 契约如何归档、Supersedes 如何闭合。

---

## 2. V2 → V3 取舍总表（收敛起草输入，列明 V3 落点与依据）

| V2 项 | V3 处理 | V3 落点 / 依据 |
|---|---|---|
| LLM 直接输出题干 | 删除 | 正文唯一来源 = B 域 line + A 域 role text（10 §6.3/20 §4.3） |
| line_id 当最终事实 | 删除 | line_ref 只在 Resolved Span（20 §5.5），live 锚定 span |
| Anchor Corrector 大量规则 | 重写为 Source Resolver | 20 §5；00 P5 禁特判堆积 |
| Native + PP 双源 | 保留思想 | 多源 provenance（10 §4；30 §16 本地确定性） |
| PP-StructureV3 | 保留 | OCR 核心能力；资产清单 §3 |
| LLM VL 作 L1 fallback | 默认删除 | V2 已确认不可作入库驱动（00 §6 红线） |
| Semantic Metadata Annotator | 保留并升级 | = annotation stage（20 §4） |
| simple_pipeline.py | 不迁移 | 单主链（00 §7 硬门槛 10/40 铁律 2） |
| pipeline fallback | 删除 | 单主链 |
| content_slicer.py | 重写为 Deterministic Compiler | 20 §7；禁字段（README §2） |
| answer_matcher | 重写 | answer 三字段独立（20 §8.3） |
| admission_gate/quality_gate | 保留思想，重写 | Evidence/Semantic Gate + decision_status（20 §8/README §2.4） |
| question_candidates | 保留思想，重做 snapshot | Candidate 完整可重放 payload（10 §5.3） |
| 图像/表格 bbox 定位能力 | 保留思想，重写 | source_figures（page/bbox/placement/source，IS-7）+ role 归属（10 §4.4/§6.6、20 §5.3/§7.2.5） |
| API 内启动 worker | 删除 | 30 §2 Process Boundary |
| recover stale → queued | 删除 | 30 §3/§8；Recovery ≠ Retry |
| BackgroundTask | 保留概念，重做状态机 | 30 §3-§5（claim/lease） |
| answer_retry_worker 隐藏消费者 | 不保留 | retry 归显式 Task/Stage（30 §7） |
| LLMGateway | 保留并强化 | 30 §6（disabled/mock/live 组合放行） |
| Provider 自动 retry/fallback | 重写 | 30 §7 fallback explicit + budget（防乘法放大） |
| llm audit | 新增为基础设施 | 30 §10（不可变审计） |
| JSONB sub_questions | 谨慎 | 稳定关系实体化（10 §7）；composite 归 20 IR/unit_group（10 §6.5） |
| content_hash / 精确去重 | 保留 | dedup_key（10 §6.8/20 §7.3） |
| 自动语义 merge | 延后 | 00 §5 非目标 |
| 知识树 seed | 保留 | knowledge seed（10 §6.7 source=seed；50 资产） |
| embedding | 保留 | 本地 embedding（00 资源约束） |
| AI 生成题 | 延后 | 00 §5 非目标（防掩盖基础数据问题） |

---

## 3. 可复用资产清单（50 规划的清单范围；40 §2 前置清点据此执行）

> 清点对象来自 00 §1 继承与 **V2 仓库现存**，不依赖本分册之外新增采集。分**五类**：

| 类别 | 资产 | 处理 | 去处 |
|---|---|---|---|
| 外部能力 | PP-StructureV3 / PaddleOCR（双源）、本地 embedding 模型（`qwen3-embedding:4b`，dim 2560） | 保留；版本与契约记录 | seal（10 §4）；本地确定性（30 §16） |
| 数据样本 | 真实 PDF（经 V2 多轮验收的文档）、golden 对照样本 | 保留；去 V2 标注污染，重新以 V3 逐层结构标注 | Golden Corpus（§4）/ fixture（40 §2） |
| 知识种子 | 标准知识树 seed（知识/题型种子） | 保留 | knowledge_nodes seed（10 §6.7） |
| 非代码资产 | DISPLAY_CONTRACT / canonical question type / true_false 映射需求（00 §1 第四类已验收业务语言） | 保留为业务语言 | canonical type（10 §6.1）；grammar 前置（20 §8.4） |
| 失败教训 | V2 的 BUG 清单、审计教训、V2 代码库（作失败样本库） | **只读参考，不移植** | 归档引用（§6）；00 §1 第二/三类 |

**清点纪律**：只清点"已验证有效的外部能力与测试样本 + 已验收业务契约 + 失败教训"，**不
清点 V2 的库/列/表/镜像/规则**（§5）。

---

## 4. Golden Corpus 计划（00 §7 versioned 评测集）

### 4.1 与 fixture 的两层关系（承接 40 §2）

```text
段内 fixture golden（40 §2，随 D/E/F/G 建，可增删）
        └── 作种子 + 覆盖缺口
             ↓
versioned Golden Corpus（本册：正式固定评测集）
   ├─ 固定样本集（真实 PDF + 预期）
   ├─ 版本化 + 变更记录（样本增删 / 预期修订必须记录）
   └─ 作 00 §7 分层漏斗的评测真值
```

### 4.2 corpus 结构与逐层预期（让失败可定位到层，防与实现同构）

00 §7 的漏斗每一层都是独立可测环节；corpus 预期**不得压成单一 IR 结构**（否则
annotation 判错与 resolver 定位错纠缠、且 golden 与实现共享结构会同步错）。每条目 =
`{ 源 PDF 引用, seal hash, 逐层预期 }`：

```text
语义层预期   unit 划分 / 依赖声明（annotation 该给的 claim；可对照 20 §6 语义结构）
解析层预期   Semantic Reference → 应落到的源边界（行/片段/答案正文位置）
答案层预期   答案正文 / 标签真值（老师版或人工确认，独立于 IR 结构）
图像层预期   图归属 role/order（IS-7）
IR/派生层    由以上逐层比对后确定性派生，不作唯一标注 schema
```

- 评测按 **00 §7 漏斗分层**回放：Source→Semantic→Resolved→IR→Answer→Image→
  Admission→Replay→Idempotency；某层失败即定位该环节，不追求单点 95%。
- **答案真值单一来源**：corpus 中人工确认的答案正文/标签，与 20 §8.2 人工路径的
  review_trail 确认、20 §8.4 grammar 的答案 golden，**同一真值源、不设两套分叉**；
  运行时人工 approve 可引 corpus 真值作 verified 依据。
- 不引入新表：corpus 是**评测数据资产**（仓库内目录 + 版本清单），非运行库内容。

### 4.3 规模判据（不给数字，给覆盖判据）

- **起步规模判据 = 题型 × 版面形态 × OCR 变体的最小多样性集**（fixture 覆盖 + corpus
  缺口补齐），不是凑数到某个 N；宁可小而版本化。
- 规模决策点属 **40 §2 I 段启动前置评审**（corpus 编排前定稿），50 不拍数字。
- 推进规则：fixture 成熟一批 → 汇入 corpus 一批；corpus 版本递增 + changelog。

---

## 5. 迁移与清理边界（什么绝不迁）

**绝不迁**（违反 = 停）：

```text
V2 任何数据库表/列/索引/镜像（10 §11：V3 全新库）
V2 生产 pipeline 及其分支 / legacy 兼容逻辑（00 §6）
单题号/学校/OCR 变体特判规则（00 P5）
Anchor/Anchor Corrector、content_slicer 语义（README §2 禁词）
API 启动 worker、recover stale→queued 自动链（30 §3/§8）
LLM→文本→特判→Gate→回填 整条模式（00 愿景）
任何"它是 V2 最稳定版本"的整体搬入理由（00 §1）
```

**移植触发条件**（唯一的 V2 代码进入 V3 通道）：满足 00 §1 四问（需求/边界/测试/兼容）
且**按 V3 契约重写 + 通过重设计后的测试**（00 §1/40 铁律 1）。V2 代码库只作失败样本库
读，不作实现来源。

---

## 6. 历史材料归档关系

| 材料（源仓库路径） | 去向（落点带仓库 + 日期 + 目录） | Superseded 闭合 |
|---|---|---|
| V3 `Docs/V3_MASTER_SPEC.md`、`V3_LESSONS.md` | → V3 `docs_archive/2026-09-05_v3_draft/` | 00（已在文件头声明） |
| V3 `Docs/V3_DATA_MODEL.md` | → 同上 | 10 |
| V3 `Docs/V3_DOCUMENT_PIPELINE.md` | → 同上 | 20 |
| V3 `Docs/V3_TASK_LLM_SAFETY.md` | → 同上 | 30 |
| V3 `Docs/V3_DEVELOPMENT_RULES.md` | → 同上 | 40 |
| V3 `Docs/V3_MIGRATION_MAP.md` | → 同上 | 50 |
| v0.3 契约（V2 `docs_archive/2026-09-03/`） | 保持原位；**唯一遗留参考** | README §3.4；不指导新实现 |

归档纪律：归档 = 移入上述**带仓库/日期/目录的显式落点**，**不删除、不覆盖**；归档由
收尾动作执行（分册完成后按本表移动）；归档后分册正文不得再引其节号作实现依据
（40 v1.1 已自含）；V2 本体继续作失败样本库，V3 实现只服从 00/10/20/30/40。

---

## 7. 与 P1-P7 的服从对照（治理侧）

| 00 原则 | 50 的落点 |
|---|---|
| 00 §1 四类继承 | §2 取舍表 / §3 资产五类 |
| P7 Replayability | §4 Golden 版本化 + 逐层预期 + 分层回放；seal hash 入条目 |
| P5 稳定由不变量保证 | §5 绝不迁清单（特判/回填/兼容逻辑禁入） |
| 00 §7 成功标准 | §4 分层漏斗评测（逐层预期、可定位）；不追求单点 95% |
| 00 §6 红线 | §5（API-worker、recover→queued、单主链、特判） |

---

## 8. 反 V2（迁移侧）自查

| V2 反模式 | 50 阻止点 |
|---|---|
| "最稳定版本"整体搬入 | §5 移植触发条件（须重写+重测） |
| 库/列/镜像迁移 | §5 绝不迁 / 10 §11 |
| 规则/特判继承 | §5 / §2 表（重写为 Resolver/Compiler） |
| golden 不版本化 | §4.3 versioned + changelog |
| corpus 用生产随机抽样 | §4.3 固定样本集 |
| golden 与实现同构（单一 IR 标注） | §4.2 逐层预期 |

---

## 9. 变更记录

### 2026-09-05

- 建立 50 分册 v1.0：收敛 `V3_MIGRATION_MAP` + 00 §1/§7 + 40 §2 golden 两层；明确 50
  为治理分册（不新增架构）：V2→V3 取舍总表、可复用资产清单、Golden Corpus 计划
  （versioned + 分层漏斗 + fixture→corpus）、绝不迁清单与移植触发、历史材料归档
  Supersedes 闭合表、P1-P7/反 V2 对照。

### 2026-09-05（v1.1，v1.0 对抗性审查 P1-1~P1-4 + 3×LOW）

- P1-1 corpus 预期改**逐层预期**（语义/解析/答案/图像各层独立，IR/派生层只作派生），
  消除与实现同构、恢复 00 §7 分层可定位（§4.2）。
- P1-2 00 冻结改"**本册只呈服从性证据，冻结由单独裁决**"，删除"随本册自动冻结"越权
  措辞（§1/header）。
- P1-3 资产清单"四类"更正为"五类"（失败教训单列）（§3）。
- P1-4 corpus 起步规模给**覆盖判据**（题型×版面×OCR 变体最小多样性集）而非数字；
  规模决策点归 40 §2 I 段前置评审（§4.3）。
- LOW：§6 归档落点补**仓库/日期/目录**显式路径（V3 `docs_archive/2026-09-05_v3_draft/`）；
  §2 取舍表补 **V2 图像/表格 bbox 定位**一行；§4.2 点明 corpus 答案真值与 20 review_trail
  同一真值源（不设两套）。
