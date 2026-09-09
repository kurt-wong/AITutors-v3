"""Source Quality Gate（Phase I-2 Revision）：Seal 后、Annotation 前的文本质量检测。

职责：评估 OCRResult 提取文本的可用性，产出 QualityReport。检测维度：
- replacement char ratio（U+FFFD，编码损坏标志）
- non-printable char ratio（控制字符/非法 unicode）
- CJK ratio（中文文档 CID 编码失败时 CJK 极低）
- total chars（扫描 PDF 提取为空 → ocr_required）

失败语义：invalid → task fail (source_quality_failed)；ocr_required → task fail
(ocr_required，未来走 OCR fallback)。quality report 落 source_meta 供 Review Console 展示。
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from app.ai.ocr.result import OCRResult

# 阈值（可调）：超过即判对应问题
_REPLACEMENT_CHAR = "�"  # U+FFFD
_MAX_REPLACEMENT_RATIO = 0.05  # 5% replacement char → invalid
_MAX_NON_PRINTABLE_RATIO = 0.10  # 10% non-printable → invalid
_MIN_CJK_RATIO = 0.01  # <1% CJK 且有大量文本 → 疑似 CID 乱码
_MIN_CHARS_FOR_CJK_CHECK = 100  # 文本太少时不做 CJK 比例判断


@dataclass(frozen=True)
class QualityReport:
    """质量评估结果。status ∈ {valid, degraded, invalid, ocr_required}。"""

    status: str
    total_chars: int
    replacement_char_ratio: float
    non_printable_ratio: float
    cjk_ratio: float
    issues: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "total_chars": self.total_chars,
            "replacement_char_ratio": round(self.replacement_char_ratio, 4),
            "non_printable_ratio": round(self.non_printable_ratio, 4),
            "cjk_ratio": round(self.cjk_ratio, 4),
            "issues": list(self.issues),
        }


def _is_cjk(ch: str) -> bool:
    """CJK Unified Ideographs + Extension A。"""
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF) or (0x3400 <= cp <= 0x4DBF)


def _is_non_printable(ch: str) -> bool:
    """不可打印：控制字符（除 \\n \\r \\t）+ 未分配 unicode。

    注意：Private Use Area (Co, U+F000-U+F8FF) 不算不可打印——数学 PDF 用 PUA 编码
    符号（≥, ≤, →, 向量箭头）。BUG-V3-042。
    """
    if ch in ("\n", "\r", "\t", " "):
        return False
    cat = unicodedata.category(ch)
    # Cc = control, Cn = unassigned, Cf = format (除 zero-width space)
    # Co = private use → 合法（数学符号），不算不可打印
    return cat in ("Cc", "Cn") or (cat == "Cf" and ch != "​")


class SourceQualityGate:
    """评估提取文本质量。纯函数，无 IO。"""

    def evaluate(self, result: OCRResult) -> QualityReport:
        all_text = "\n".join(line.text for line in result.lines)
        return self.evaluate_text(all_text)

    def evaluate_text(self, text: str) -> QualityReport:
        """评估纯文本质量（供 executor 从 sealed body_text 调用）。"""
        total_chars = len(text)

        # 无文本提取 → 扫描 PDF / 图片 PDF → 需要 OCR
        if total_chars == 0:
            return QualityReport(
                status="ocr_required",
                total_chars=0,
                replacement_char_ratio=0.0,
                non_printable_ratio=0.0,
                cjk_ratio=0.0,
                issues=("no text extracted (scanned/image PDF?)",),
            )

        # 统计各维度
        replacement_count = text.count(_REPLACEMENT_CHAR)
        non_printable_count = sum(1 for ch in text if _is_non_printable(ch))
        cjk_count = sum(1 for ch in text if _is_cjk(ch))

        replacement_ratio = replacement_count / total_chars
        non_printable_ratio = non_printable_count / total_chars
        cjk_ratio = cjk_count / total_chars

        # 判定
        issues: list[str] = []

        if replacement_ratio > _MAX_REPLACEMENT_RATIO:
            issues.append(
                f"replacement char ratio {replacement_ratio:.2%} > {_MAX_REPLACEMENT_RATIO:.0%}"
            )

        if non_printable_ratio > _MAX_NON_PRINTABLE_RATIO:
            issues.append(
                f"non-printable ratio {non_printable_ratio:.2%} > {_MAX_NON_PRINTABLE_RATIO:.0%}"
            )

        # CID 编码检测：大量文本但几乎无 CJK → 可能是 CID 乱码
        if total_chars >= _MIN_CHARS_FOR_CJK_CHECK and cjk_ratio < _MIN_CJK_RATIO:
            # 只有当文本看起来应该是中文时才告警（有大量 replacement 或 non-printable）
            if replacement_ratio > 0.01 or non_printable_ratio > 0.05:
                issues.append(
                    f"CJK ratio {cjk_ratio:.2%} < {_MIN_CJK_RATIO:.0%} with "
                    f"high replacement/non-printable (CID encoding?)"
                )

        # 判定 status
        # BUG-V3-042 fix: _is_non_printable now excludes Co (PUA), so math PDFs
        # with PUA symbols won't be marked invalid. Cc/Cn still trigger invalid.
        if replacement_ratio > _MAX_REPLACEMENT_RATIO or non_printable_ratio > _MAX_NON_PRINTABLE_RATIO:
            status = "invalid"
        elif issues:
            status = "degraded"
        else:
            status = "valid"

        return QualityReport(
            status=status,
            total_chars=total_chars,
            replacement_char_ratio=replacement_ratio,
            non_printable_ratio=non_printable_ratio,
            cjk_ratio=cjk_ratio,
            issues=tuple(issues),
        )


class SourceQualityError(Exception):
    """Source quality 检测失败。error_type 供 task fail 分类。"""

    error_type = "source_quality_failed"

    def __init__(self, report: QualityReport) -> None:
        self.report = report
        detail = "; ".join(report.issues) if report.issues else report.status
        super().__init__(f"source quality {report.status}: {detail}")


class OCRRequiredError(Exception):
    """提取文本为空，需要 OCR fallback。"""

    error_type = "ocr_required"

    def __init__(self, report: QualityReport) -> None:
        self.report = report
        super().__init__("OCR required: no extractable text (scanned/image PDF)")
