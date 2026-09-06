"""集中导入 A/B/C 三域全部模型，供 alembic env.py 读取 Base.metadata。

依赖方向：Base ← models ← __init__ ← env.py（禁反向导入，防 import cycle）。
"""

from app.models.content import (
    InstanceFigureLink,
    InstanceRoleContent,
    KnowledgeNode,
    Material,
    MaterialLink,
    Question,
    QuestionInstance,
    QuestionKnowledgeLink,
    UnitGroup,
    UnitGroupMember,
)
from app.models.runtime import Budget, LlmCallAudit, Task, TaskClaim
from app.models.snapshot import AdmissionCandidate, AdmissionEvent, SemanticAnnotation
from app.models.source import (
    Document,
    DocumentActiveSource,
    DocumentSourceLine,
    DocumentSourceSelectionEvent,
    DocumentSourceVersion,
    SourceFigure,
)

__all__ = [
    "Document",
    "DocumentSourceVersion",
    "DocumentSourceLine",
    "SourceFigure",
    "DocumentActiveSource",
    "DocumentSourceSelectionEvent",
    "SemanticAnnotation",
    "AdmissionCandidate",
    "AdmissionEvent",
    "Question",
    "QuestionInstance",
    "InstanceRoleContent",
    "Material",
    "MaterialLink",
    "UnitGroup",
    "UnitGroupMember",
    "InstanceFigureLink",
    "KnowledgeNode",
    "QuestionKnowledgeLink",
    "LlmCallAudit",
    "Budget",
    "Task",
    "TaskClaim",
]
