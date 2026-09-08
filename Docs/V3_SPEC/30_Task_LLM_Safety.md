# AI Tutor V3 — 任务安全与 LLM 执行宪法（Task / Worker / Lease / Recovery / Retry / Gateway / Audit / Budget）

Version: v1.1（Baseline—Frozen，2026-09-05）
Status: V3 收敛基线（30 分册）— 已落实 v1.0 对抗性审查 P0-1 + 10×P1 + 3×LOW 与冻结前 1 条预算实现禁令，冻结
Date: 2026-09-05
Supersedes: `Docs/V3_TASK_LLM_SAFETY.md`（起草输入）;上位约束 `00_Master_Spec.md`
（不可修改，P6 含 `task_type`）;执行身份/落库 `10_Data_Model.md`（v1.2.1，
`logical_execution_stage/hash` 双列冻结、§9 canonical 序列化下放）;内容管线
`20_Document_Pipeline.md`（v1.2 冻结，decision_status 唯一入口）;术语裁决
`README.md` §2.3/§2.4

> 本分册是**执行层宪法**：回答"谁能调 LLM、Task/Logical Execution/Attempt 如何区分、
> 一次真实调用如何被审计与限额、崩溃后如何安全恢复"。**不定义内容语义**（那是 20）、
> **不定义内容域表**（那是 10 的 A/B/C）。本分册拥有的持久化对象只有运行域表：
> tasks / task_claims / llm_call_audit / budget（见 §17）——它们是执行基础设施，
> 不在内容 A/B/C 域内，也不得在 10 的三域外另立"内容快照"。

---

## 1. 定位：与 00/10/20 的消费边界

```text
00 宪法（P1-P7）   —— 本分册服从对象
10 数据模型        —— logical_execution_stage/hash 双列、attempt_id、input_identity
                      已在 10 §3/§5/§9 冻结；本分册只消费，绝不重定义
20 内容管线        —— decision_status 状态机、approve() 唯一入口、annotation supersede
                      已冻结；本分册只负责"驱动它们的执行与恢复安全"
README §2.3/2.4   —— Task/Worker/Claim/Logical Execution Key/LLM Call Audit/Budget/
                      Live Mode 术语裁决
```

三条铁律：

1. **`logical_execution_key` 不在本分册被重新定义**。它已由 10 §3 冻结为
   stage-scoped 双列：`logical_execution_stage`（枚举：seal/ann/compile/…）+
   `logical_execution_hash CHAR(64)`（SHA256），`UNIQUE(stage, hash)`。00 P6 的 key
   = `task_type + stage + input_hash + contract_version + model_config_hash`；本分册
   §16 给出**精确计算与序列化规则**，**不得新增第三个"全局 run_id"或单列
   prefix+hash 变体**。
2. **Attempt ≠ Logical Execution**。一次 Logical Execution（同 stage 同 hash）可以有
   多次 attempt（attempt_id 区分）。重试是否产生**新 LE** 取决于输入/契约是否变化，
   不是取决于"它失败了几次"（§7）。
3. **Worker 崩溃不自动重跑**（00 §5 非目标 / 红线）。Recovery ≠ Retry（§8）。
   内容物化的防重复**不依赖 "Worker 记得自己做过"**，而依赖 LE 幂等 + 事务 + 唯一
   约束 + 条件状态迁移（§12）。

---

## 2. Process Boundary

- **API 进程**只负责 HTTP/auth/upload/query/create-task/read-task。**绝不消费队列、
  启动 Worker、因 startup 自动调 LLM**（00 §7 硬门槛 1/2）。
- **Worker 是独立进程，必须显式启动**：

```bash
python -m app.worker run               # 默认 safe mode：mock/disabled，无真实外部调用
python -m app.worker run --allow-live  # 显式放行 live（还需 live mode + task + budget）
```

- 启动 API / reload / DB 恢复 / 测试收集均不得触发副作用（00 P4：副作用分列、
  external/persistence/lifecycle 各自显式入口）。Worker 显式启动 ≠ 自动恢复 ≠ 自动重试。

---

## 3. Task 状态机

```text
created
  ↓
queued
  ↓
running
  ├── succeeded
  ├── failed            （停靠态：无自动出口，经人工决策 → queued / 封存）
  └── interrupted       （lease 过期/崩溃；唯一出口 = 人工 recovery → queued 或人工决策）
```

红线（00 §5/§6）：**禁止 `running → timeout → queued → 自动重跑`**；禁止 `stale →
queued` 无审计重进；recovery 只把失效租约置 `interrupted`，**不等价于重跑**。
**`failed` / `interrupted` 均无自动出口**：回到 `queued` 只经人工 retry（开新 claim
轮次，§5）或人工封存——任何状态到 `queued` 的迁移都必须是显式人工动作。

---

## 4. Logical Execution vs Attempt（00 P6 落地）

### 4.1 定义与命名分层

```text
Task                    高层异步工作驱动对象（如"解析文档 D"）；每次被人工放行消费 =
                         一次 task claim 轮次（claim_round，task 级，§5）
  └── Logical Execution   由 (stage, hash) 标识；落在产生它的内容行上
        （annotation 行 / candidate 行，10 §3/§5.1/§5.2）
        └── Attempt       attempt_id 标识一次实际执行尝试（LE 级，README §2.3 冻结）
              └── 内部可含 1..n 次 LLM Request（各进 llm_call_audit）
```

**两个"执行尝试"必须区分**：task 级的是 **claim_round**（租约轮次，§5）；LE 级的是
**attempt_id**（README 冻结，落于产物行 / audit）。一次 task claim 可在内部驱动多个
stage 的 LE；每个 LE 的产物行独立带自己的 attempt_id。**二者不同名、不同粒度、
不得互换**（防 Agent 把 task 重试当成 LE 重试、或反之）。

- **Logical Execution 不是 Task 的别名，也不是跨派生实体传播的 run_id。** 一个 Task
  驱动多个阶段；每个阶段各有一个 stage-scoped LE，落位各自的 A/B/C 行。
- 持久化结果（annotation/candidate 行）必须归属其 LE，并带 `attempt_id` 作为审计线索。

### 4.2 与 20 的接线

- **annotation stage** LE → `semantic_annotations.logical_execution_*`（10 §5.1）；
- **compile stage**（resolver→ir→compiler→gate 整段）LE → `admission_candidates.
  logical_execution_*`（10 §5.2）；
- 重试沿 §7 的二分落入：同 LE 重试共享同一 key（靠 `UNIQUE(stage, hash)` + 幂等写入
  返回既有行）；新 LE 才有新 key、新行。**任何一行的 key 都不含 `task_id`**（含的是
  `task_type`，见 §16）。

---

## 5. Claim / Lease

Task 携带：`worker_id / lease_token / started_at / heartbeat_at / lease_expires_at /
claim_round`（task 级租约轮次计数，非 LE attempt）。

- **Claim 必须原子**：`UPDATE tasks SET status='running', worker_id=…, lease_token=…,
  claim_round=claim_round+1 WHERE status='queued' AND … RETURNING …`（或
  `FOR UPDATE SKIP LOCKED` 等价）。禁止 `SELECT queued → Python 判断 → UPDATE running`。
- **Heartbeat / completion 必须验证**：`task_id + worker_id + lease_token + status=running`
  四元组；验证失败即拒绝。
- **旧 Worker 诈尸不得改写已被 recovery/重试接管的新状态**：所有状态写都必须带上
  lease_token 条件，token 不匹配 → no-op / 审计告警（防 V2 zombie 双写）。
- 每次人工 retry / recovery 后放行 = **新 claim_round**；内部各 stage 的 LE 按 §7
  幂等，产物行 attempt_id 与该 LE 的实际尝试一致，不随 claim_round 递增而伪造。

---

## 6. 执行入口：Live 放行链（谁能真正调 LLM）

唯一调用链（00 §3 强制）：

```text
Domain/Application → LLMGateway → Provider → HTTP
```

业务代码禁止直接构造真实 Provider。Gateway 三态：

| mode | 行为 |
|---|---|
| disabled | 不创建 HTTP 请求；任何调用即抛错（默认） |
| mock | 允许测试流程运行，无真实外部副作用（常规 pytest 默认） |
| live | 必须**同时**满足：live mode + `--allow-live` + task 上下文 + budget 可用（§11） |

`live` 是显式组合放行，不是全局开关；缺任一前置即拒绝并记录原因。本分册的 external
副作用口径**含 cloud OCR / cloud embedding**（00 P4 列为 external service call）——
任何 external 调用（LLM 或云 OCR）都必须过 Gateway + 审计 + budget 同类闸（§16 seal
裁决）。

---

## 7. Retry 语义二分（防"重试偷改业务语义"）

**核心问题：重试会不会悄悄变成一次新的业务执行？** 30 的裁决——**以输入/契约是否变化
为准，不以失败次数为准**：

| 场景 | 输入/契约 | 结果 | 依据 |
|---|---|---|---|
| LLM timeout / 网络瞬时错误 / 进程在 LLM 请求中崩溃（同输入、同 prompt 契约、同模型配置） | 不变 | **同 LE，新 attempt**；预算累计（§11） | 00 P6：同一逻辑执行重复执行不得产生不同持久化结果 |
| Annotation 判 `incomplete` → 聚焦重试（换聚焦指令/提示契约） | **变化**（prompt_version / contract 变） | **新 LE**（新 hash），旧 annotation 置 superseded | 20 §4.7 / §5.2；输入或契约变化 = 新逻辑执行 |
| Resolver/Compiler/Gate 确定性失败（数据异常、bug） | 不变 | **不是重试目标**：修 build_versions 后走 **Rebuild**（新 compile LE、新 candidate），不覆盖旧行 | 10 §9 Rebuild；00 P7 |
| Provider fallback（同语义、不同 provider/model） | 变化（model_config_hash 变） | **新 LE** 或显式配置的降级路径——**必须计入审计与预算，默认不自动无限 fallback** | 00 §5 非目标；防 fallback×retry 成本失控 |
| task 级人工 retry（recovery 后放行） | 见 §7 各行 | 新 claim_round；内部 LE 幂等复用，除非上行判定新 LE | §5 / §13 |

分界红线：**凡需重新生成语义结果的重试一律是新 LE；凡只是把同一次逻辑执行再跑一遍的
重试一律是 attempt。** 本表即 V3 与 V2"每次 retry 都像新调用"成本失控的分界。

每层独立 bounded：

| 层 | 规则 |
|---|---|
| Task Retry | 人工触发（`app.worker retry <task_id>`）；每次放行开新 claim_round |
| Pipeline Retry | bounded（明确次数上限，不嵌套自动链） |
| LLM Request Retry | bounded（同 LE 内 attempt 上限） |
| HTTP Retry | bounded（传输层，不影响业务语义） |
| Provider Fallback | explicit（默认关闭；开启须过审计/预算） |
| 熔断器 | `MAX_LLM_CALLS_PER_TASK`（最终上限，非正常业务逻辑） |

---

## 8. 恢复（Recovery）

Recovery **只做一件事**：`expired lease → interrupted`。

```bash
python -m app.worker recover --dry-run   # 预览将受影响的任务
python -m app.worker recover --confirm   # 执行：置 interrupted + 审计
```

- Recovery 不调 LLM、不重新排队、不改变业务语义。
- `interrupted` 后的唯一前路是人工决策（retry / reject / 诊断），人工重试进入 queued
  时**开新 claim_round**（同 Task 的下一轮驱动），其内部各阶段按 §7 幂等。

---

## 9. Oversized Output

超大 reasoning/output 既是成本问题也是 pipeline 异常信号。超过阈值必须：audit 标记
`oversized_output`；允许 Gate/Task 决定 failed 或 review；**不得自动无限 retry**。
oversize 的 usage 照常计入预算并 settle（§11），不因超限而豁免。

---

## 10. LLM Call Audit（基础设施，不可变）

每次**真实 LLM 请求**（live 且真正发出 HTTP）必须写一条不可变审计（append-only）。

至少字段：`request_id / idempotency_key / logical_execution_stage / logical_execution_hash
/ attempt_id / task_id / document_id / stage / provider / model / process_id / process_name
/ hostname / start / end / status / prompt_chars / input_tokens / output_tokens /
reasoning_tokens / total_tokens / estimated_cost / error_type / oversized_output`。

- 状态 ∈ `{started, completed, failed, unknown}`。**`started` ≠ 已发 HTTP**；进程在未知
  时刻死亡 → 置 `unknown`，**不得假装 failed 或 succeeded**。
- **`idempotency_key`**：同一 LE+attempt 内对**同一逻辑 LLM 请求**的稳定键，由
  Gateway 在请求前生成、重试沿用——作用是防同一次 HTTP 重试双写 audit / 双扣预算
  （provider 层幂等交给 provider 自身的键，二者不同）。
- Audit 使任何真实调用可追溯到 `task/document/(stage,hash)/attempt`（00 §7 硬门槛 4）；
  annotation 行与 candidate 行的 `attempt_id`（10 §3）与之对齐。

---

## 11. 预算（Budget）

预算 = **五个正交账户**，不是嵌套层级：每一笔 request **同时**计入其所属的五个账户，
任一账户超限即拒绝（防 V2 `retry×fallback×vision×huge completion`）。document 不是
le 的子层——同一 document 常被多个 task/LE 处理，是独立 scope 标签。

**实现约束（冻结）**：五个预算账户均为**独立 scope**；一次 request 的 reserve/settle
必须**同时作用于五个 scope**；任一账户的额度 / 已用量 / 预留量均**不得从其他账户派生、
扣减或继承**；**禁止实现为 `daily → document → task → LE → request` 的父子预算树**。

```text
一条 request 同时归属于 5 个账户：
  request       本次调用自身（reserve→settle）
  task          所在任务（task 内全部 request）
  logical exec  所在 LE（同 (stage,hash) 的全部 attempt 累计）   ← 跨 attempt 累计
  document      所在文档（同 document 的全部 LE/attempt）
  daily         全局（当日全部 request）
```

- **reserve → settle**：请求前 reservation 扣额度；完成后按实际 usage 结算、补/退。
  attempt 失败也要 settle 其真实 usage。
- **LE 级累计**：同 LE 的第 2/3 次 attempt 不是重新领满配额，而是共享该 LE 的累计额度
  ——这是"每次 retry 都像新调用"的直接反制。
- **并发安全**：每个账户扣减用条件 UPDATE（`UPDATE … SET used=used+X WHERE used+X<=limit
  RETURNING …`）或等价行锁；**禁止 `read → compare → write`**（两个并发请求同时过检）。
- **reservation 超时回收**：reserve 记录带时间戳（`reserved_at`）；长期未 settle 的
  reservation 由本地对账（确定性、不调 LLM、可并入 recovery 流程）回收——防进程崩溃
  多次后 document/daily 额度被挂起饿死（§17 budget）。
- 五账户任一超限 → Gateway 拒绝新 request，记录原因；不自动降级重试。

---

## 12. approve() / Admission 与 Worker 崩溃（防双物化）

**20 §8.2 已冻结唯一入口**：`decision_status` 只能经 Admission Service 的
`approve()`/`reject()` 迁移；Repository/ORM/Review/Worker 不得直接 UPDATE；Gate 只产
判定不物化。Worker 只是执行环境：compile stage 里由 Task Executor **经 Application /
Admission Service** 调同一 `approve()`（00 §3 单向链），不自行实现物化、不直写
decision_status。本分册补**崩溃语义**（Worker 不需要"记得自己做过"）：

```text
Worker 在 compile stage 驱动 approve()
  ├─ 崩溃于事务 COMMIT 之前 → ROLLBACK，candidate 保持 pending_review；
  │    重试重跑 compile → 仍 pending，可再次 approve（无害）
  ├─ 崩溃于 COMMIT 之后、task 标记 succeeded 之前
  │    → candidate 已 approved（A 域已物化 + admission_event 已写 + 状态已置）；
  │    重试重跑 compile → 幂等：以 (stage, hash) 命中既有 candidate，decision_status
  │    = approved → 视为该 stage 已完成（no-op），继续推进任务，不二次物化
  └─ 重复 approve 同一已 approved candidate → 状态机拦截 no-op，返回既有结果（10 §5.4）
```

防重复物化的三个机制**共同**成立，缺一不可：
1. LE 幂等（`UNIQUE(stage, hash)`，10 §3）→ 同一 compile 不产生两个 candidate；
2. Admission 事务原子性（物化+event+approved 同事务，10 §5.4/20 §8.2）→ 无
   "approved 但未物化"；
3. approve 唯一入口 + 条件状态迁移（`WHERE decision_status='pending_review'`，20 §8.2）
   → 状态机拦截重复。

**不依赖**：Worker 记忆、跨进程缓存、任务"已做标记"的顺带信任。

**每 stage 持久化产物单事务落库（崩溃窗口只在事务边界）**：annotation 行 = LLM 响应 →
validate → INSERT annotation 行 → COMMIT 单条事务；compile 产物同理。崩溃在事务前 →
无行、重试可写；在事务后 → 行在、重试复用（§13）。配合 §10 `unknown` 审计归因，杜绝
"audit 有 started、产物半截"的中间态。

---

## 13. Task 级幂等（驱动层）

任务本身可安全重跑：manual retry / recovery 后重跑时，每一 stage 都以自身
(stage, hash) 幂等写——annotation/candidate 已存在的行被复用（不重调 LLM 重造语义，
除非 §7 判定新 LE）。Task 状态推进只关心"该 stage 的产物是否已就绪"，不关心
"是不是我这次跑出来的"。

显式边界：**想强制重新生成语义（而非复用）不是 retry 旧任务，而是建"新任务 / 新 LE"**
（改输入/契约后经 §7 判定），或人工走 20 的 annotation 聚焦重试——retry 通道默认幂等
复用，绝不静默改变结果。

---

## 14. 测试红线与灾难测试

常规 pytest：不访问真实 LLM / 真实 OCR / 真实网络 / 不消费生产任务。Live 测试必须
同时满足：explicit test + `--allow-live` + safe fixture + bounded budget。

灾难测试（必测，验证"无自动重跑"）：

```text
claim → running → LLM call → kill worker → restart
  → recover --dry-run → recover --confirm → interrupted
  → manual retry → queued → 重跑（claim_round+1，内部 stage 幂等复用）
```

断言点：崩溃不自动回 queued；无第二套 Question/Instance/Material；同 LE 不会产生
两个 candidate；approved 不会二次物化；reserve 未 settle 的预算被对账回收。

---

## 15. 与 P1-P7 的服从对照

| 00 原则 | 本分册落点 |
|---|---|
| P1 最小闭环 M1 | 单一显式 Worker + 单链 Gateway；无第二消费路径/legacy worker |
| P2 LLM 无 Admission Authority | approve() 唯一入口 + Worker 不直写 decision_status（§12） |
| P3 Source 唯一事实源 | 本分册不产生内容；重试不生成新语义，除非 §7 判新 LE（输入变化） |
| P4 副作用显式 | Process Boundary（§2）；live 放行链含 external OCR 口径（§6/§16）；Recovery 只置 interrupted（§8） |
| P5 稳定由不变量保证 | LE/attempt 二分（§4/§7）；熔断器非业务逻辑（§7） |
| P6 Idempotency | stage-scoped 双列 + `task_type` 消费（§4/§16）；approve 防双物化（§12）；Task 级幂等（§13） |
| P7 Replayability | 确定性失败走 Rebuild 新 LE（§7）；产物复用不改旧行（§13） |

---

## 16. Canonical 序列化与 hashing utility（10 §9 下放，本分册权威）

提供**公共确定性序列化**，供 `logical_execution_hash`、`input_identity` 各 hash、
（与 20 §7.3 内容规范化组合后）dedup/occurrence 键使用：

```text
hash_value = SHA256( canonical_json( obj ) )
canonical_json(obj)：
  递归序列化；对象键按字典序排序；数组保序；
  键/值间无多余空白（紧凑分隔）；字符串 UTF-8；
  数字用稳定表示（整数原样；浮点按定长十进制格式化，避免科学计数/尾数漂移）；
  不引入时间戳/随机数/进程态；同一对象同键序必得同串
```

- **结构性 canonical**（键序/空白稳定）由本 utility 负责；
- **内容级规范化**（全半角/空白折叠/LaTeX/NFKC/前后缀剥离）只对 20 §7.3 明确指定的
  键在 **compiler** 内先行执行，随后才进本序列化 → hash；text_hash/source_span 保持
  raw（10 §8 2c）。
- utility 自身版本化，随 build_versions 记录；升级即影响 identity，必须走 Rebuild。

**`logical_execution_hash` 组合公式（00 P6 精确化；各 stage 声明 input_domain 与
contract_domain = 相关 build_versions 子集）**：

```text
input_domain(stage)   = 该 stage 真实消费、决定语义结果的输入
contract_domain(stage)= 该 stage 相关的 build_versions 子集（10 §9）
  seal    ：input = 原始文件内容 hash + 引用；contract = seal/解析契约（解析器版本、
            如含 OCR 则 OCR 契约；本地确定性）
  ann     ：input = source_version_id + 文档内容引用；
            contract = annotation_schema_version + prompt_version + model_config_hash
  compile ：input = annotation_id + annotation payload hash；
            contract = resolver_version + ir_schema_version + compiler_version
            + gate_policy_version（compile 为确定性阶段，无 model_config 依赖，不含）

hash = SHA256(canonical_json(
  { task_type, stage, contract_domain(stage), input_domain(stage) }
))
```

**含 `task_type`（执行目的类型：document_ingest / re-annotate / …），不含 `task_id`
（任务实例）**——两个不同业务流对同一 source/stage/契约/模型**不共享幂等桶**（否则
B 流会被 A 流的既有行 UNIQUE 挡回、被迫借用 A 产物 = 串台）；同一任务实例的重试共享
同一 key。也**不含 attempt、worker、时间**——否则同一逻辑执行在两次 attempt 下 key
漂移（10 §3 冻结）。幂等写入时若 `UNIQUE(stage, hash)` 冲突 → 返回既有行。

**seal 与 external OCR 的归属裁决（P1-3）**：
- 本地确定性 seal（本地 OCR / 本地解析）按 00 P4 属 deterministic computation，
  **不强审计**——记录 seal/解析器版本 + 输入/输出 hash + 结果即可；其幂等由
  source_version 的 LE 身份 `UNIQUE(logical_execution_stage, logical_execution_hash)` 保证
  （同一 `original_sha256` 允许多 sealed version 跨 role/provider；非原始文件 hash 全局唯一；
  `documents` 层 `UNIQUE(original_sha256)` 只保证一个原始文件一个主档），不需要本分册 budget。seal 也按上式
  有 LE 身份（`task_type + seal + …`），供 Replay 根对齐。
- 若 seal 走 **cloud OCR**（external service call，00 P4）→ 必须过 Gateway + 审计 +
  budget 同类闸（§6/§10/§11），缺任一不放行。cloud OCR 是否在 M1 纳入属跨册裁决
  （00 §1 继承 OCR 双源、40 定序）；**本分册只钉"external 副作用必须过闸"这条线，
  不单方决定 M1 是否启用**。

---

## 17. 运行域表契约（本分册权威；不属于内容 A/B/C）

| 表 | 关键列 | 不变量 |
|---|---|---|
| `tasks` | id、task_type、status（created/queued/running/succeeded/failed/interrupted）、`task_params JSONB`（轻量目标/参数引用 id，**不内嵌内容**）、claim_round、current_stage、created_by、created_at、decided_at | 状态迁移只能经 Task Service 显式接口；无自动 stale→queued |
| `task_claims`（append-only） | id、task_id、claim_round、start/end、outcome、error_type、lease 快照 | **task 级租约记录，非 LE attempt**；人工 retry/recovery 放行开新 claim_round |
| `llm_call_audit`（append-only） | 见 §10；`logical_execution_stage/hash`、`attempt_id` | 不可变；进程未知死亡 → `unknown` |
| `budget` | account_dim（request/task/le/document/daily）、`stage VARCHAR NULL`（le 账户用）、scope_id、limit、used、reserved_at、updated_at | 扣减条件 UPDATE（并发安全）；LE 账户按 `(stage, hash)` scope；LE 跨 attempt 累计；reserve 带时间，超时对账回收 |

运行域表不得持有"内容快照/题目/材料"字段；需要复用的内容状态一律指向 A/B/C 行 id，
不复制内容。`tasks.task_params` 只存目标引用（documents.id 等），**不存内容正文**。
**A/B/C 表**上的 `logical_execution_stage/hash + attempt_id` 由 10 管辖，本分册只给出
公式与 utility（§16）。

---

## 18. 反 V2 模式逐条自查

| V2 反模式 | 30 的阻止点 |
|---|---|
| API startup → worker / 自动消费 | §2 Process Boundary |
| worker startup → automatic recovery | §2 / §8 Recovery 仅 dry-run/confirm |
| running 超时 → queued 自动重跑 | §3 状态机红线（含 failed/interrupted 无自动出口） |
| stale → queued 无审计重进 | §3 / §8 人工出口 |
| recovery 当 retry 用 | §8（只置 interrupted） |
| 每次 retry = 新一次业务执行 / 新 run_id | §4/§7 LE-二分；key 含 task_type 不含 task_id |
| 预算画成嵌套层级 / 每 retry 重新领满 | §11 五账户正交 + LE 累计 |
| retry×fallback×vision 成本失控 | §11 LE 累计 + 熔断器 + §7 fallback explicit |
| 双 worker 同时消费同一 task | §5 原子 claim + lease_token 校验 |
| worker "记得自己做没做" 防重复 | §12 幂等 + 事务 + 唯一约束 + 条件迁移 |
| worker 直接 UPDATE decision_status / approve | §12 唯一入口（20 §8.2） |
| task claim 当 LE attempt / 反之 | §4.1 命名分层 + §5 claim_round |
| 崩溃挂起预算额度 | §11 reservation 超时回收 |
| 测试默认打真实外部 API | §14 |

---

## 19. 词汇红线（README §2.3/§2.4 强制）

- **Logical Execution = (task_type, stage, hash) 行级身份**；不用旧
  `task_id+stage+operation+attempt` 做幂等键。
- **Attempt = 一次 LE 实际执行**（attempt_id）；**Claim_round = 一次 task 租约轮次**；
  二者不混写。
- 用 **Claim/Lease**（原子领取+租约），不用模糊的 "recover stale / 自动恢复"。
- 用 **Recovery（置 interrupted）≠ Retry（人工/幂等重放）**，两个动作不混写。
- 用 **Live Mode**（disabled/mock/live + 显式 allow-live），不用单一 `LLM_GATEWAY_MODE`
  布尔化理解。
- 用 **Budget 五账户正交 + LE 累计**；不用单一 token 预算表 / 嵌套树。

---

## 20. 变更记录

### 2026-09-05

- 建立 30 分册 v1.0：收敛起草 `V3_TASK_LLM_SAFETY` + 00 P4/P6 + 10 §3/§9 + 20 §8.2；
  固化 Process Boundary、Task 状态机、Claim/Lease、LE vs Attempt 二分、Retry 语义表
  （业务重试=新 LE / 瞬时故障=新 attempt）、Live 放行链、不可变 LLM Call Audit、
  四维+LE 累计预算、approve 防双物化崩溃语义、Task 级幂等、canonical 序列化 utility
  （10 §9 下放收口）、运行域表契约、灾难测试与测试红线。

### 2026-09-05（v1.1，v1.0 对抗性审查 P0-1 + 10×P1 + 3×LOW）

- P0-1 `task_type` 回归 hash 组合域：`hash = SHA256(canonical_json({task_type, stage,
  contract_domain, input_domain}))`——含类型不含实例，防跨业务流共享幂等桶/串台
  （§16；00 P6 精确化，10 §3 委派收口）。
- P1-1 预算改**五账户正交**（request/task/le/document/daily 多标签记账），废除嵌套树
  （§11）。
- P1-2 "Attempt" 双粒度命名分层：task 级 = `claim_round`（§5/§17 task_claims），LE 级
  = `attempt_id`（README 冻结）；删自造的 `task_attempts` 表名。
- P1-3 seal stage 纳入 LE（§16 input/contract domain）+ cloud OCR external 过闸裁决
  （本地确定性不强审计；cloud OCR 须 Gateway+audit+budget，M1 是否启用跨册裁决）。
- P1-4 `failed` 措辞修正为停靠态，无自动出口；回 queued 只经人工（§3）。
- P1-5 budget 增 `stage` 列，LE 账户按 `(stage, hash)` scope（§17）。
- P1-6 Worker 只是执行环境：compile stage 经 Application/Admission Service 调同一
  approve()，不自行实现物化（§12）。
- P1-7 每 stage 持久化产物**单事务落库**，崩溃窗口只在事务边界（§12）。
- P1-8 hash 的 `contract_domain(stage)` 显式 = 该 stage 相关 build_versions 子集
  （ann=annotation_schema+prompt+model_config；compile=resolver+ir+compiler+gate）
  （§16）。
- P1-9 reservation 带 `reserved_at`，超时由本地对账回收（§11/§17）。
- P1-10 `tasks.payload_ref` → `task_params JSONB`（只存目标引用，不内嵌内容）（§17）。
- LOW：audit `idempotency_key` 作用域定义（§10）；oversize usage 照常 settle（§9）；
  canonical_json 浮点定长十进制表述（§16）。

### 2026-09-05（冻结，1 条文字补强）

- 冻结前补强：预算实现禁令（§11）——五账户均为独立 scope，一次 request 的
  reserve/settle 同时作用于五个 scope，额度/已用/预留互不派生继承，禁止实现为
  `daily→document→task→LE→request` 父子预算树。无表/无公式/无状态机改动。
