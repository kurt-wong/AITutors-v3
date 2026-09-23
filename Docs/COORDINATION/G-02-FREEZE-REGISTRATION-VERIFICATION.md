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

Preprocessing HEAD (at Phase 0) = 2b92898f05f6541a5fc65c8300cb8a59a06c4928
V3 HEAD (at Phase 0)           = 79348441dae0efce6855017b2b5c0491b08d6bb8

Phase 0 test baselines (measured):
  Preprocessing: 338 passed, 1 xfailed
  V3 backend:    2030 passed, 1 skipped, 1 xfailed
```

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md` |
| Status | VERIFIED |
| Parent record | `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` |
