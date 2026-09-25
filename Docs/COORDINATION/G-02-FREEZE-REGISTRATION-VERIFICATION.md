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

### 6.1 Git identity

```text
Repository       : AITutors-v3（https://github.com/kurt-wong/AITutors-v3.git）
Branch           : od01-r3-convergence
L0 source commit : 71f51f97e5674cf04ab12d4c449e3796a160bb27
  parent         : 9f1763ecb9ced7108e61449ee892fe5fadb1adc3
Re-freeze commit : 本记录所在 commit（机械取值：
                   git log -1 --format=%H -- Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md）
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
| **最终卫生收口 M-01~M-05**（`CR-004 §2` 指引 + `§2.4` · `90 §1` L1 例子列事实同步 · `90 §11 (a)` 计数口径 · `90 §11 (c)` 授权落点澄清与声明登记）= **current** | `git rev-parse <本行登记所在 commit>:Docs/V3_SPEC` | 见下方 CURRENT 行 |

```text
fa1e953e… →(f708370)→ b3eeb3e9… →(71f51f9 / OD-R-01)→ 442172f4…
          →(60fa9ff / OD-R-01 re-freeze)→ 8659e2fa… →(12493ca / WS-A)→ a704cd8f…
          →(fbec14e / WS-B provenance)→ 2edd2010… →(最终卫生收口 M-01~M-05)→ CURRENT
```

**同值说明（非笔误）**：`b3eeb3e9…` **同时**是 f708370 的 incorporation tree 与 OD-R-01 的
previous / pre-OD-R-01 tree —— f708370 是 `Docs/V3_SPEC` 在 OD-R-01 之前的最后一次内容变更
（与本文件 §5「last content commit = f708370」一致）。

**CURRENT Frozen Spec tree** = `63810f55c88cee983004136f288f1b6ff3527a8d`
（= `git rev-parse <本行登记所在 commit>:Docs/V3_SPEC`；由 `git add` 后 `git write-tree` +
`git rev-parse T:Docs/V3_SPEC` 计算，**非手填**。字面值可安全存于本文件——它在 `Docs/V3_SPEC/` 之外，
无自指不动点。覆盖范围：M-01~M-05 最终卫生收口（`CR-004 §2` 指引 + 新增 `§2.4` 任务书坐标对照 ·
`90 §1` L1 例子列事实同步 · `90 §11 (a)` 计数口径 · `90 §11 (c)` 授权落点澄清与声明登记）。
**未触及** L0 `00`–`50`；OD-R-01 与 f708370 两条链的结论一律未变。）

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

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md` |
| Status | VERIFIED |
| Parent record | `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` |
