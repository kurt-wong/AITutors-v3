# G-02-FREEZE-REGISTRATION-VERIFICATION

```text
STATUS: VERIFIED
AUTHORITY: GOVERNANCE VERIFICATION RECORD
PURPOSE: G-02 re-verification of b743c5d → 7934844
RESULT: VERIFIED
```

> **Binding wording（Owner）：**
>
> ```text
> b743c5d remains the Frozen Semantic Baseline.
> 7934844 is the Freeze Registration / governance-state commit.
> ```
>
> **禁止表述：**「7934844 修改了 Frozen Semantic Baseline」或「7934844 是 Frozen Semantic Baseline」。

---

## 1. Comparison Identity

```text
base           = b743c5daf0806ea00c84afb1b92ca2a3b5dbfc98
head           = 79348441dae0efce6855017b2b5c0491b08d6bb8
ahead_by       = 1
total_commits  = 1
```

| SHA | Role | Commit message |
|-----|------|----------------|
| `b743c5daf0806ea00c84afb1b92ca2a3b5dbfc98` | **Frozen Semantic Baseline**（approved Contract content） | `docs(contracts): clarify question metadata and post-admission enrichment` |
| `79348441dae0efce6855017b2b5c0491b08d6bb8` | **Freeze Registration**（governance state only） | `docs(contracts): freeze contract v0.3 at owner-approved baseline` |

---

## 2. Files Touched（exactly 7）

```text
Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md
Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-INFORMATION-PRESERVATION-MATRIX-v0.3-DRAFT.md
Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-OPEN-DECISIONS-v0.3-DRAFT.md
Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-SEMANTIC-AUTHORITY-MATRIX-v0.3-DRAFT.md
Docs/COORDINATION/CONTRACTS/V3-POST-ADMISSION-ENRICHMENT-CONTRACT-v0.3-DRAFT.md
Docs/COORDINATION/CURRENT.md
Docs/COORDINATION/state.yaml
```

---

## 3. Diff Character（status / ledger only）

实际 diff 显示：

| Change | Present |
|--------|---------|
| Contract 进入 `FROZEN` | YES |
| Owner Approval 登记为 `APPROVED` | YES |
| Frozen Baseline 登记为 **`b743c5d`** | YES |
| Freeze timestamp 登记 | YES |
| P01–P25 / P04/P07/P08/P15–P19 状态同步 | YES |
| CURRENT / state.yaml 同步 Freeze Registration | YES |
| Frozen Spec (`Docs/V3_SPEC/**`) 修改 | **NO** |
| P01–P25 语义重写 | **NO** |
| Production / schema / corpus | **NO** |

Scale（Phase 0 re-check）：`7 files changed, 29 insertions(+), 21 deletions(-)` — 与 status/ledger-only 一致。

---

## 4. Formal Conclusion

```text
b743c5d = Frozen Semantic Baseline
7934844 = Freeze Registration / governance-state commit
7934844 does NOT replace b743c5d as semantic baseline
G-02 = VERIFIED
```

若治理文档中仍存在「7934844 是 / 修改了 Frozen Semantic Baseline」的错误表述，以本记录为准并修正。

---

## 5. Companion Baselines（for audit reproducibility）

```text
Frozen Spec tree (Docs/V3_SPEC) = b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f
  last content commit = f708370065870d89ac4ba025a1d47e38c411314e
  drift f708370..registration-HEAD = none
  【historical —— Phase 0 Companion Baseline 快照（与下两行 "(at Phase 0)" 同一时点）；
    当前 Frozen Spec tree 见 §6；本行历史值不得机械替换】

Preprocessing HEAD (at Phase 0) = 2b92898f05f6541a5fc65c8300cb8a59a06c4928
V3 HEAD (at Phase 0)           = 79348441dae0efce6855017b2b5c0491b08d6bb8

Phase 0 test baselines (measured):
  Preprocessing: 338 passed, 1 xfailed
  V3 backend:    2030 passed, 1 skipped, 1 xfailed
```

---

## 6. Re-freeze Registration（OD-R-01 / CR-003，2026-09-24）

> 本节是 **Frozen Spec re-freeze 的字面值可读副本（非权威）**。
> **权威登记 = `Docs/V3_SPEC/CR-003_CONTRACT_CHANGE_RECORD_OD-R-01.md` §10**（commit 锚定表述）。
> 本文件位于 `Docs/V3_SPEC/` **之外**，故可安全承载该目录的 tree hash 字面值（无自指不动点）。
> 争议时以 `git rev-parse <re-freeze commit>:Docs/V3_SPEC` 为准。
>
> **仓外坐标边界（2026-09-25，H-10）**：本节与 §6.4 中的 `H-*` / `HYG-D*` /「DSH 第 N 轮」
> 一类标识，**源自仓外 DSH 审查产物**（外部对抗性审查报告），**不是**仓内原生权威对象
> ——不是 L0 / L0-META / L1 / L2 条目，不是 CA / CR / OD 编号，**不**承载授权效力；
> 引用**仅**为审计可追溯性。仓内可核验证据 = 仓内路径 + commit（完整 SHA）+ 可复现机械检查命令。
> 完整边界口径见 `90 §11 (c)`「仓外坐标可复核性边界」注；**不**复制外部审查正文入仓，
> **不**建立内部替代 registry / 编号映射表。

### 6.1 Git identity

```text
Repository       : AITutors-v3（https://github.com/kurt-wong/AITutors-v3.git）
Branch           : od01-r3-convergence
L0 source commit : 71f51f97e5674cf04ab12d4c449e3796a160bb27
  parent         : 9f1763ecb9ced7108e61449ee892fe5fadb1adc3
Re-freeze commit : `60fa9ff30f70037e1990db7dd5bc255310073432`（OD-R-01 re-freeze，**实名**；
                   与 §6.2 表「OD-R-01 re-freeze」行一致）
                   机械核验（commit-specific，**不用** `git log -1`）：
                   git show --name-only --format= 60fa9ff30f70037e1990db7dd5bc255310073432
                     → 含 `CR-003_…` / `90_DOCUMENT_GOVERNANCE.md` / `10_Data_Model.md` /
                       `20_Document_Pipeline.md`（= §6.2 所称「含 CR-003 / CA-003 / 10 §12 / 20 §12」）
                   git rev-parse 60fa9ff30f70037e1990db7dd5bc255310073432:Docs/V3_SPEC
                     → 8659e2fab715d1d2164f9bc559a04ceb05fd7fc0

> **superseded（2026-09-25，H-12）**：本行原写「Re-freeze commit : 本记录所在 commit（机械取值：
> `git log -1 --format=%H -- Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md`）」。
> ① 该取值法**已被** `90 §11 (c)` 行锚定注明令禁止——`git log -1` 只返回**最近一次**触及本文件的
> commit，与「Re-freeze commit」字段**无关**，且随每次编辑漂移；② 「本记录所在 commit」与 §6.2
> 表所载 OD-R-01 re-freeze = `60fa9ff` **不符**。原文**逐字保留于本注**以存历史证据（**未删除**），
> **不再作为活指令**；现行有效表述 = 上方 commit 锚定 + commit-specific 机械核验。
```

### 6.1a 工作树 untracked 统计口径（2026-09-25，M-05.1）

> 本工作流 hygiene 报告中若出现 untracked 计数，**必须**写明口径。
> 两口径**不得**混成同一个数字。

| 口径 | 命令 | 当前值（2026-09-25 实测） | 含义 |
|---|---|---|---|
| **目录折叠**（git 默认） | `git status --porcelain` | **10** | 未跟踪**目录**按 1 个条目计（`Docs/GOVERNANCE/` 计 1） |
| **逐文件展开** | `git status --porcelain -uall` | **13** | 目录展开为文件：9 × `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-*.md` + 4 × `Docs/GOVERNANCE/*.md` |

> **要求**：报告 untracked 计数时写「默认 `git status --porcelain` 口径 = N」或「`-uall` 口径 = M」，
> **不得**只写裸数字。历史报告中未标口径的数字按**默认目录折叠口径**理解；
> 按 `90 §4`「存量文档不强制回填（Reconcile, don't rewrite）」**不作机械改写**。

### 6.2 Frozen Spec tree 链（全部由 git 对象计算，无手填 / 无猜测）

**两条独立 change 的合并视图**（`f708370` 与 OD-R-01 各有独立 provenance，见 `CR-004` / `CR-003`）：

| 阶段 | 取值命令 | tree hash |
|---|---|---|
| **pre-f708370** | `git rev-parse f708370^:Docs/V3_SPEC` | `fa1e953e7c4638236b298cf1c137aa2a107d5ea5` |
| **f708370 incorporation**（CR-004） | `git rev-parse f708370:Docs/V3_SPEC` | `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f` |
| **pre-OD-R-01**（= `9f1763e`） | `git rev-parse 9f1763e:Docs/V3_SPEC` | `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f` |
| **OD-R-01 incorporation**（CR-003） | `git rev-parse 71f51f9:Docs/V3_SPEC` | `442172f40942368a4856231a742bf4d273242034` |
| **OD-R-01 re-freeze**（含 CR-003 / CA-003 / 10 §12 / 20 §12） | `git rev-parse 60fa9ff:Docs/V3_SPEC` | `8659e2fab715d1d2164f9bc559a04ceb05fd7fc0` |
| **WS-A 治理一致性修正**（CR-003 R-03/04/05/06） | `git rev-parse 12493ca:Docs/V3_SPEC` | `a704cd8f08ba5360bfb3398b235ab26c8ad6a8d4` |
| **WS-B provenance 登记**（CR-004 / CA-004 / 20 §12 / 90 §11） | `git rev-parse fbec14e:Docs/V3_SPEC` | `2edd20101c4abf3238d5689b3bb3cba0d5fc75fe` |
| **最终卫生收口 M-01~M-05**（`CR-004 §2` 指引 + `§2.4` · `90 §1` L1 例子列事实同步 · `90 §11 (a)` 计数口径 · `90 §11 (c)` 授权落点澄清与声明登记） | `git rev-parse 5a46d33:Docs/V3_SPEC` | `63810f55c88cee983004136f288f1b6ff3527a8d` |
| **H-01 修正**（`CR-003 §0.1`「搜索结论」段时点限定 + 历史口径注记；HYG-D1 / DSH 第 4 轮 H-01） | `git rev-parse 1ee84cd:Docs/V3_SPEC` | `47a59e50126f0f7e98f44d281f8d388236240735` |
| **H-05~H-08 闭合**（`90 §11 (c)` 补登 `1ee84cd` 与整改行 · `CR-003 §0.1` 措辞精确化 H-07 · 本节 §6.2 CURRENT 同步 H-06 + 新增 §6.4 机械复核命令表 H-08） | `git rev-parse 6152899:Docs/V3_SPEC` | `ecd12c0e9682eaed2e3ad7c2416984b9cff92bee` |
| **H-09~H-13 闭合**（`90 §11 (c)` 注册补记 H-09 · 仓外坐标可复核性边界 H-10 · 解析精确性 / exclude 盲区澄清 H-11 · `G-02 §6.1` 陈旧取值指令 superseded H-12 · 环境前提与 tree 推导口径 H-13）= **current** | `git rev-parse <本行登记所在 commit>:Docs/V3_SPEC` | 见下方 CURRENT 行 |

```text
fa1e953e… →(f708370)→ b3eeb3e9… →(71f51f9 / OD-R-01)→ 442172f4…
          →(60fa9ff / OD-R-01 re-freeze)→ 8659e2fa… →(12493ca / WS-A)→ a704cd8f…
          →(fbec14e / WS-B provenance)→ 2edd2010… →(5a46d33 / 最终卫生收口 M-01~M-05)→ 63810f55…
          →(1ee84cd / H-01 修正)→ 47a59e50… →(6152899 / H-05~H-08 闭合)→ ecd12c0e…
          →(H-09~H-13 闭合)→ CURRENT
```

> **实名化说明（2026-09-25，H-11）**：上表「H-05~H-08 闭合」行原为自指表述
> （`git rev-parse <本行登记所在 commit>:Docs/V3_SPEC`），现已**解析为实名** `6152899`
> （按 `90 §11 (c)` 行锚定注「已确定的 commit 一律写**实名**」）——该行的 tree **取值未改**
> （仍为 `ecd12c0e…`），只把自指占位换成已确定的 commit identity，使核验可按**精确 SHA** 执行。
> 「H-09~H-13 闭合」行为**本行所在 commit**（自指），其 SHA 不能写入本文件
> （commit hash 由文件内容决定，写入即自指不动点）；解析规则见 §6.4。

**同值说明（非笔误）**：`b3eeb3e9…` **同时**是 f708370 的 incorporation tree 与 OD-R-01 的
previous / pre-OD-R-01 tree —— f708370 是 `Docs/V3_SPEC` 在 OD-R-01 之前的最后一次内容变更
（与本文件 §5「last content commit = f708370」一致）。

**CURRENT Frozen Spec tree** = `14a7450809d4932036f415d765ab29c53671843c`
（= `git rev-parse <本行登记所在 commit>:Docs/V3_SPEC`，其中「本行登记所在 commit」= **引入本 CURRENT
字面值的 commit**（2026-09-25，H-09~H-13 闭合）。**非手填**。字面值可安全存于本文件——它在
`Docs/V3_SPEC/` 之外，无自指不动点。
**覆盖范围（本 tree delta 实际含什么）**：`Docs/V3_SPEC/` 内仅两文件改动——`90_DOCUMENT_GOVERNANCE.md`
（声明登记表补登本 commit 行 · 注册补记 H-09 · 仓外坐标可复核性边界 H-10 · 行锚定注补解析精确性 H-11）与
`CR-003_CONTRACT_CHANGE_RECORD_OD-R-01.md`（`§0.1` 时点限定注补仓外坐标边界 H-10）。
`G-02` 本文件的改动（§6.1 superseded H-12 · §6.2 链与本行 · §6.4 四则澄清 H-11 / H-13）
位于 `Docs/V3_SPEC/` **之外**，**不进入**本 tree delta。
**未触及** L0 `00`–`50`；OD-R-01 与 f708370 两条链的结论一律未变。
**固定点说明**：本行字面值位于 `Docs/V3_SPEC/` **之外**，写入它不改变被记的 `Docs/V3_SPEC` tree
⇒ 无自指不动点（与 `CR-003 §10` 自指防火墙同一处置；`90 §11 (c)` 声明登记表因此**不写**自身
tree 字面值）。今后凡 `Docs/V3_SPEC` 再次变化，本行与 §6.2 链式图须同步追加更新——这是本节的
**既定义务**，不是新机制。）

**tree 推导口径（2026-09-25，H-13）——「什么被执行、在什么前提下、证明了什么」**

```text
权威推导（唯一）：git rev-parse <被验 commit>:Docs/V3_SPEC
    —— 对【已提交】的 commit 对象取 Docs/V3_SPEC 子树；任何人、任何时刻重放均得同值。
       本行字面值即由该式取 <本行登记所在 commit> 得到，并在提交后以
       git rev-parse HEAD:Docs/V3_SPEC 复核相等。

预演推导（仅用于写入前算值，不是证据）：git add <Docs/V3_SPEC 下改动> → git write-tree → T
    → git rev-parse T:Docs/V3_SPEC
    ⚠ T 是【工作树中间快照的根 tree】，与最终 commit 的根 tree 【不必相等】：
      Docs/V3_SPEC/ 之外的后续编辑只改根 tree、不改 Docs/V3_SPEC 子树。
    ⚠ 因此中间 T 的【根】tree 值【不入本记录、不作核验依据】；只取 T:Docs/V3_SPEC 这一子树值，
      且该子树值仍须在提交后用权威推导式复核相等才算成立。
    本次实测：预演 T:Docs/V3_SPEC = 14a7450809d4932036f415d765ab29c53671843c
              提交后 HEAD:Docs/V3_SPEC = 14a7450809d4932036f415d765ab29c53671843c   （== 预演值 ✓）
    ⚠ 上两行是【本节所在 commit】时点的取值；其后任何触及 Docs/V3_SPEC 的 commit 都会改变
      HEAD:Docs/V3_SPEC，届时须按 §6.2 既定义务追加新阶段行并更新 CURRENT。
      重放时请对【指定 commit】取值，勿把「HEAD」读作随时间漂移的当前态。

已证明：上式在本仓 git 对象模型下给出确定的 Docs/V3_SPEC 子树值，且字面值 == 事实值。
未证明：该值在非 git 对象库（导出目录 / 归档包）中的可复算性——那些载体不含 tree 对象。
```

> **历史值不改写**：上表 `ecd12c0e…`（`6152899:Docs/V3_SPEC`）自本行起为**历史阶段值**，
> **不得**被机械替换；`b3eeb3e9…` / `fa1e953e…` 等历史 baseline 同样**永久保留**
> （`90 §4`：存量文档不强制回填 / Reconcile, don't rewrite）。

**历史 hash 处置**：`b3eeb3e9…` 与 `fa1e953e…` 作为历史 baseline **永久保留**；历史表述不得机械替换
（`90 §4`：存量文档不强制回填 / Reconcile, don't rewrite）。

### 6.3 `b3eeb3e9` 全仓断言逐项判定（historical vs false current-state）

| # | 位置 | 性质 | 判定 | 处置 |
|---|---|---|---|---|
| 1 | `FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md:24` | 裸陈述「（UNCHANGED）」，文档 `Status: PENDING`（现行） | **false current-state assertion** | **已修**：改为历史编写基线 + 当前事实 + `CR-003` 指针 |
| 2 | 本文件 §5 `:87` | Companion Baselines 快照（同块他行标 "(at Phase 0)"），本行缺限定语 | **historical（限定语缺失）** | **已修**：加 historical 限定语 + 新增 §6 |
| 3 | `IMPLEMENTATION-PLAN-v0.3.md:31` | baseline 表（自标 `Frozen at 2026-09-23` / `HEAD at planning time`） | **historical** | **已修**：加 Baseline 时点声明（**值不改**） |
| 4 | 同上 `:452` | Phase 0 Scope 核对项 | **historical**（同表同时点） | 由同一声明覆盖 |
| 5 | 同上 `:828` | `Compiled from …` 溯源行 | **historical**（自述 compiled-from） | 由同一声明覆盖 |
| 6 | `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md:347` | 「本轮硬边界要求…」障碍分析 | **historical（会被误读为长期规则）** | **已修**：加时点范围注（**值不改**） |
| 7 | `Docs/REPORTS/OD-01-PROPOSAL-V4-TARGETED-ADVERSARIAL-REVIEW.md:49/:73/:95` | DSH 审查报告，各自锚定被审对象 / HEAD | **historical（已自 scoped）** | **不改**（`90 §2 R8`） |
| 8 | `Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md:27` | 「最终状态（强制保持）」 | **false current-state assertion** | **已修**：加历史范围声明（**值不改**） |
| 9 | AITutor-X `Docs/60_REPORTS/**`（多处） | DSH 外部审查报告，各锚被审 commit | **historical（已自 scoped）· 异仓** | **不改**（不在本仓 git 范围） |

**判定原则（未做全仓替换）**：只修「当前断言与当前事实**直接冲突**」处；historical 处只补
scope 限定语，**不改历史值**。`LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md:320` 的
`Frozen Spec: UNCHANGED (OD-01 change is PROPOSAL only until re-freeze)` 讲的是 **OD-01 Option
Provenance** 那条 change 的状态（该 Proposal 仍未 re-freeze，此半句仍为真），其 `UNCHANGED`
半句所指事实已由本节 §6.3 第 1 行的同一更正覆盖；该文件属 Limited Implementation Authorization
（另一授权面），本轮**不改**，以免扩大修改范围。

### 6.4 机械复核命令表（2026-09-25，H-08）—— 只记录命令与实测结果，**不建机制**

> **本节目的**：把 `Docs/V3_SPEC` tree hash 变化 → **L0 未变** → **`90 §11 (c)` 声明存在** 这条
> 三段关系做成**可机械复现**的检查。**不新增**治理机制 / 审批层 / registry / 状态字段。
> 下列命令**全部实际执行**，结果为实测值。两条取证纪律：
> ① **交替模式检索一律用 `-E` + 裸 `|`** —— 语义唯一、可移植（三种写法的**实测**对照见下
> 「为何必须 `-E`」段；简述：ERE 下裸 `|` = alternation，GNU BRE 下 `\|` = alternation（非 POSIX
> 扩展、不可移植），BRE 下裸 `|` = **字面量**）。本段原写「BRE 下 `\|` 是字面量」**与实测不符**，
> 2026-09-25（H-13，命令实现前提）据下段实测**更正**；取证纪律本身（`-E` + 裸 `|`）不变；
> ② **提交后核验一律指定 commit** —— `git diff --name-only` 在工作区干净时输入为空
> （空验证），**不能**证明该 commit 改了什么。

**结果时点范围（2026-09-25，H-13）**：下列 A / B / C 结果是**引入本节的 commit**（实名
`615289957ecaa1562aced149a22c04bfcbfe3628`）时点的**实测值**，属**历史记录**；
其后 `Docs/V3_SPEC` 再变（含本节所在的 H-09~H-13 闭合 commit）**不改写**这些结果
（`90 §4`：存量文档不强制回填）。复现时须针对**该 commit 的树**重算，或改用新的被验 commit
重算一套——**不得**把下列行号 / 命中数读作对**当前**状态的断言（同类缺陷见 `G-02 §6.3` 判定原则）。

**环境与命令实现前提（2026-09-25，H-13）——「在什么前提下执行」**

| 项 | 前提 | 说明 |
|---|---|---|
| 版本控制 | Git（实测 `git version 2.54.0.windows.1`） | `git grep` / `git show` / `git rev-parse` / `git write-tree` 全部依赖 Git |
| `:(exclude)` pathspec magic | Git ≥ 1.9 | A 类排除本表自身所用；不支持时改用下方「无 GNU grep / 无 pathspec magic 时的等价替代」，并**记录该替代** |
| 正则引擎 | `git grep -E` = POSIX ERE | 与 GNU grep ERE **一致**：裸管道符在 BRE 下是**字面量**，反斜杠加管道符是 GNU BRE 的 alternation 扩展（非 POSIX、不可移植）。三种写法的**实测**对照见下「为何必须 `-E`」段 |
| 裸 `grep -rnE` / `grep -rn` / `grep -vE` | **GNU grep（或兼容实现）在 PATH** | 仅「为何必须 `-E`」对照段与 B2/B3 用到；实测环境有 GNU grep 3.0，DSH 复核环境**无** GNU grep |
| shell | POSIX sh / Git Bash | 管道、`exit` 码语义（`exit 1` = 无命中） |

**无 GNU grep / 无 pathspec magic 时的等价替代**：`grep -rnE '<pat>' <path>` → `git grep -n -E '<pat>' -- <path>`；
`grep -vE '<pat>'` → `git grep … | git grep -v -E '<pat>'` 或等价管道。DSH 侧即以此在**无 GNU grep**
环境复现，结果一致。无 `:(exclude)` pathspec magic 时，A 类排除本表自身的写法改为在管道末端
以 `git grep -v -E '<本文件路径字面量>'`（或等价的 `grep -v`）滤掉本文件路径的输出行，
**并记录该替代**（结果须与原写法一致）。

**谁执行了什么、证明了什么**：A/B/C 各条由实施代理在 **Windows 11 + Git 2.54.0.windows.1 +
GNU grep 3.0** 环境实际执行并抄录结果；DSH 以 `git grep` 在**无 GNU grep** 环境独立复现 A/B/C
（结果一致）。**已证明** =「在上述前提下，所载命令与结果一一对应、可原样复现」；
**未证明** = 其他 shell / 其他 grep 实现 / 非 git 对象库载体下的行为。

**解析与核验的精确性（2026-09-25，H-11）**：`<被验 commit>` 的**核验一律以精确 commit identity
（完整 SHA）为准**（`git show --name-only --format= <完整 SHA>` / `git rev-parse <完整 SHA>:…`），
**不以** commit subject 文本的模糊比对作判据。下表所载阶段名（如「OD-R-01 H01 follow-up」）
**只是人类可读的定位提示**，与实际 subject（`docs: close OD-R-01 H01 follow-up findings`）
**文本不等**，**不构成判据**；定位到引入 commit 后立即改用其完整 SHA。

**exclude 的适用范围与盲区代价（2026-09-25，H-11）**

```text
:(exclude)…G-02… 【只】适用于 A 类「通用陈旧文本扫描」——因为 A 类检索的是【被检模式的字面量】，
                  而本表把该字面量抄了进来，不排除就会命中本表自身、结果被污染、不构成证据。
                  它【不】适用于 B / C 类【身份核验】：B/C 直接作用于 commit 对象与 tree 对象
                  （git show / git rev-parse），不经过文本模式匹配，【无需排除、也未排除】本文件。

盲区代价（必须记明）：exclude 是【永久】的 ⇒ 今后 G-02 内若再出现「当期」或无限定的
                  「无 Contract Change Record」类陈旧文本，A 类【永远不会报警】。
                  该盲区由【G-02 专用身份核验】覆盖：
                    C1/C4  git rev-parse <被验 commit>:Docs/V3_SPEC == §6.2 CURRENT 字面值
                    B1     git show --name-only --format= <被验 commit>
                  ⇒ G-02 的正确性由【对象身份核验】保证，不由【文本扫描】保证。
                  A 类【不得】被当作 G-02 自身的清洁度证据。
```

**被验 commit = `615289957ecaa1562aced149a22c04bfcbfe3628`**（引入本节的 commit；已解析为**实名**，
按 `90 §11 (c)` 行锚定注「已确定的 commit 一律写**实名**」）。其自身 hash 原不能写进本文件——
commit hash 由文件内容决定，写入即自指不动点；但本节**引入之后**该 SHA 已确定，故按实名回填
（回填不改变 `Docs/V3_SPEC` tree，本文件在其之外）。

**判定为「引入本节的 commit」的机械依据（精确，不靠 subject 文本）**：

```text
P1  git show 615289957ecaa1562aced149a22c04bfcbfe3628:Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md \
        | grep -c '### 6.4'
    → 1   （该 commit 的本文件已含 §6.4）

P2  git show 615289957ecaa1562aced149a22c04bfcbfe3628^:Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md \
        | grep -c '### 6.4'
    → 0   （其 parent 尚无 §6.4）
    ⚠ grep -c 无命中时 exit 1，属预期；只看计数值。

P1 ∧ P2 ⇒ §6.4 首次出现于 6152899…，即【引入本节的 commit】。判据是【内容首次出现】，
   不是 subject 文本匹配。
```

> **不得**用 `git log --format='%H %s' -- …G-02…` 的**单行返回值**当核验依据：该命令返回
> **多行**（每次触及本文件一行，最新在前），且本节所在的 H-09~H-13 闭合 commit 也触及本文件。
> subject 文本仅供人读定位，与本表阶段名**不等**，**不作判据**。

#### A. 交替模式检索（H-08(a)：必须 `-E`，且必须排除本表自身）

**自指污染（必须排除）**：本表把被检模式的**字面量**写进了 `G-02`，任何全仓检索都会命中本表
自身，结果即被污染、不构成证据。下表（**A 类通用陈旧文本扫描**）一律加 `:(exclude)` 排除本表。
> 该排除**只**适用于 A 类，**不**适用于 B / C 类身份核验；盲区代价与 G-02 专用身份核验见上方
> 「exclude 的适用范围与盲区代价（2026-09-25，H-11）」段。

```text
EXC = ':(exclude)Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md'

A1  git grep -n -E '§1:41' -- Docs/ Status.md "$EXC"
    → 4 处，全在 CR-003（:52 / :55 / :56 / :57），均带时点限定

A2  git grep -n -E '无 Contract Change Record|不存在 Contract Change Record|无一份 L1' \
        -- Docs/ Status.md "$EXC"
    → 唯一命中 Docs/DECISIONS/84_CONFLICT_LEDGER.md:176
      （= H-02 / HYG-D2，NON-AUTHORIZED，按授权保留未改）

A3  git grep -n -E '当期|上述文件清单|亦已新增' -- Docs/ Status.md "$EXC"
    → 0 命中（exit 1）—— H-07(a)(b)(c) 三项均已消除

A4  git grep -n -E '现存仅|当前无 Contract|尚未有.*Contract Change' -- Docs/ Status.md "$EXC"
    → 唯一命中 CR-003:50，位于「截至 CR-003 创建时」限定范围内
```

**为何必须 `-E`（三种写法实测对照，均排除本表）**

```text
grep -rnE '无 Contract Change Record|不存在 Contract Change Record|无一份 L1' Docs/ Status.md
    → 命中 84:176，exit 0        ERE：裸 `|` = alternation（语义唯一、可移植）

grep -rn  '无 Contract Change Record\|不存在 Contract Change Record\|无一份 L1' Docs/ Status.md
    → 命中 84:176，exit 0        GNU BRE 扩展：`\|` = alternation（非 POSIX，不可移植）

grep -rn  '无 Contract Change Record|不存在 Contract Change Record|无一份 L1' Docs/ Status.md
    → 0 命中，exit 1            BRE：裸 `|` = 字面量，无 alternation 语义
```

> **结论**：裸 `|` 在 BRE 下是**字面量**，写 `grep 'a|b|c'` 不可能产出 A2/A4 的结果；
> `\|` 在 GNU grep 上虽可用，但属非 POSIX 扩展、语义含混、不可移植。
> 取证一律写 **`-E` + 裸 `|`**。本表所载命令与结果一一对应，均可原样复现。

#### B. 提交后改动核验必须指定 commit（H-08(b)：空验证 → 必须 `git show`）

```text
被验 commit（完整 SHA）= 615289957ecaa1562aced149a22c04bfcbfe3628

B1  git show --name-only --format= 615289957ecaa1562aced149a22c04bfcbfe3628
    → 3 个 .md：
        Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md
        Docs/V3_SPEC/CR-003_CONTRACT_CHANGE_RECORD_OD-R-01.md
        Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md

B2  git show --name-only --format= 615289957ecaa1562aced149a22c04bfcbfe3628 | grep -vE '\.md$'
    → 0 命中（exit 1）⇒ 非 .md 改动 = 0
    （无 GNU grep 时：… | git grep -v -E '\.md$'  或等价管道）

B3  git show --name-only --format= 615289957ecaa1562aced149a22c04bfcbfe3628 | grep -E 'V3_SPEC/(00|10|20|30|40|50)_'
    → 0 命中（exit 1）⇒ L0 00–50 改动 = 0
```

#### C. tree hash 变化 → L0 未变 → `90 §11 (c)` 声明存在（H-08(c)：三段机械链）

```text
被验 commit（完整 SHA）= 615289957ecaa1562aced149a22c04bfcbfe3628

C1  tree 确已变化
    git rev-parse 1ee84cd:Docs/V3_SPEC        → 47a59e50126f0f7e98f44d281f8d388236240735
    git rev-parse 615289957ecaa1562aced149a22c04bfcbfe3628:Docs/V3_SPEC
                                              → ecd12c0e9682eaed2e3ad7c2416984b9cff92bee

C2  L0 未变 —— 同 B3
    → 0 命中 ⇒ 变化面不含 L0 00–50

C3  §11(c) 声明存在
    git grep -n -E 'L0-META / L1 面改动，非 L0 修改' -- Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md
    → 命中 4 行（本节引入时点的实测值）：
        :491  规则原文（90 §11 (c) 必须要求）
        :512  5a46d33 行（最终卫生收口 M-01~M-05）
        :513  1ee84cd 行（H-01 修正）
        :514  6152899… 行（H-05~H-08 闭合）
    ⇒ 每次非 L0 的 Docs/V3_SPEC 变化均有对应声明行
    （⚠ 行号为【历史值】：其后本文件再次改动会平移行号；重放时按内容匹配，勿按行号断言）

C4  登记值 == 事实值
    git rev-parse 615289957ecaa1562aced149a22c04bfcbfe3628:Docs/V3_SPEC
        ==  §6.2 表「H-05~H-08 闭合」行所载 tree hash
    → ecd12c0e9682eaed2e3ad7c2416984b9cff92bee
    （本行原写「== 本节 §6.2 CURRENT 字面值」——在本节引入时点成立；其后 CURRENT 随
      §6.2 既定义务推进到新值，故现改为与【该阶段行】比对，使等式对任何时点都可复算。
      逐时点的 CURRENT 等式另见 §6.2「tree 推导口径」：git rev-parse HEAD:Docs/V3_SPEC
      == §6.2 CURRENT 字面值）
```

> **C1→C2→C3→C4 即 `90 §11 (c)`「tree hash 变化 ⇒ 必须能找到对应 CA 条目；否则补一行声明」的
> 机械可审计形式**。任一环节断链即违规。本表**只**记录命令与结果的对应关系，不引入新检查机制。

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md` |
| Status | VERIFIED |
| Parent record | `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` |
