# 架构决策记录

记录项目中的关键技术决策，供后续开发参考。

---

## D001: QuestionType.code 作用域

**日期**：2026-09-01  
**状态**：已决策  
**关联**：P8 Sprint 2、ROADMAP.md §P8

### 背景

`question_types` 表的 `code` 字段有全局唯一约束（`unique=True`）。项目中存在两套命名空间：

- **Seed 数据**（`question_type_seed/data/*.py`）：`MATH-OBJ-CHOICE`、`ENG-READ-DETAIL` 等，3 级层次结构
- **Ingestion 路径**（`ingestion.py:_CANONICAL_QUESTION_TYPE_NAMES`）：`single_choice`、`reading` 等扁平类型

两套命名空间在实践中不冲突（seed 码更细粒度，ingestion 码更通用）。

### 决策

**保持现状，不做迁移。**

- `unique=True` 全局唯一已满足当前需求（9 学科 × ~15 类型无冲突）
- 迁移需要：改 unique 约束为 `(subject_id, code)` 复合唯一 → Alembic migration → 代码适配
- 当前不迁移 = 零风险、零成本

### 触发迁移的条件

如果未来出现以下需求，再执行迁移：
- 同一题型（如 `single_choice`）在不同学科需要不同行为
- 需要按学科隔离题型管理
- Seed 数据和 ingestion 路径需要统一命名空间

---

## D002: SubjectResolver 抽取

**日期**：2026-09-01  
**状态**：已实施  
**关联**：P8 Sprint 2

### 背景

`ingestion.py` 内联了学科解析逻辑（alias dict + canonical set + fallback），与 `knowledge/tree_seed/types.py` 的 `SUBJECT_CODES` 存在重复定义。

### 决策

抽取为独立 `SubjectResolver` 类（`app/domains/subject/resolver.py`）：
- `resolve(session, name) → Subject`：外部输入 → canonical Subject
- `code_for(subject) → str`：Subject → canonical code (MATH/PHYS/...)

`ingestion.py` 和 `admission/service.py` 统一使用 `SubjectResolver`。
