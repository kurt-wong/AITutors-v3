"""Source Quality Gate 测试（Phase I-2 Revision）。"""

from __future__ import annotations

from app.ai.ocr.result import OCRLine, OCRResult
from app.domains.source.quality import (
    OCRRequiredError,
    QualityReport,
    SourceQualityError,
    SourceQualityGate,
)


def _make_result(text: str) -> OCRResult:
    return OCRResult(
        provider="test",
        model="test",
        pages=1,
        lines=(OCRLine(text=text, page_no=1),),
    )


class TestSourceQualityGate:
    def setup_method(self):
        self.gate = SourceQualityGate()

    def test_valid_english_text(self):
        result = _make_result("What is the capital of France? Paris is the capital.")
        report = self.gate.evaluate(result)
        assert report.status == "valid"
        assert report.total_chars > 0
        assert report.replacement_char_ratio == 0.0

    def test_valid_chinese_text(self):
        result = _make_result("下列关于集合的说法正确的是（　　）")
        report = self.gate.evaluate(result)
        assert report.status == "valid"
        assert report.cjk_ratio > 0.5

    def test_empty_text_ocr_required(self):
        result = _make_result("")
        report = self.gate.evaluate(result)
        assert report.status == "ocr_required"
        assert report.total_chars == 0

    def test_high_replacement_chars_invalid(self):
        # 10% replacement chars → invalid
        text = "正常文本" + "�" * 20 + "更多正常文本内容在这里"
        result = _make_result(text)
        report = self.gate.evaluate(result)
        assert report.status == "invalid"
        assert report.replacement_char_ratio > 0.05
        assert any("replacement" in i for i in report.issues)

    def test_cid_encoding_detected(self):
        # 模拟 CID 乱码：大量 replacement + 几乎无 CJK
        text = "��1ҳ/��11ҳ" * 50
        result = _make_result(text)
        report = self.gate.evaluate(result)
        assert report.status == "invalid"
        assert report.replacement_char_ratio > 0.05

    def test_non_printable_chars_detected(self):
        # 大量控制字符 → invalid (Cc category, not PUA)
        ctrl = "".join(chr(i) for i in range(4))  # \x00\x01\x02\x03
        text = "正常" + ctrl * 30 + "文本"
        result = _make_result(text)
        report = self.gate.evaluate(result)
        assert report.status == "invalid"
        assert report.non_printable_ratio > 0.10

    def test_evaluate_text_direct(self):
        report = self.gate.evaluate_text("这是一段正常的中文文本")
        assert report.status == "valid"
        assert report.cjk_ratio > 0.8

    def test_evaluate_text_empty(self):
        report = self.gate.evaluate_text("")
        assert report.status == "ocr_required"

    def test_quality_report_to_dict(self):
        report = self.gate.evaluate_text("测试文本")
        d = report.to_dict()
        assert "status" in d
        assert "total_chars" in d
        assert "replacement_char_ratio" in d
        assert "issues" in d
        assert isinstance(d["issues"], list)

    def test_source_quality_error(self):
        report = QualityReport(
            status="invalid",
            total_chars=100,
            replacement_char_ratio=0.1,
            non_printable_ratio=0.0,
            cjk_ratio=0.5,
            issues=("test issue",),
        )
        err = SourceQualityError(report)
        assert err.error_type == "source_quality_failed"
        assert "test issue" in str(err)

    def test_ocr_required_error(self):
        report = QualityReport(
            status="ocr_required",
            total_chars=0,
            replacement_char_ratio=0.0,
            non_printable_ratio=0.0,
            cjk_ratio=0.0,
            issues=("no text",),
        )
        err = OCRRequiredError(report)
        assert err.error_type == "ocr_required"

    def test_pua_only_not_invalid(self):
        """BUG-V3-042: PUA alone (math symbols) should NOT trigger invalid."""
        # 20% PUA chars (math symbols) + no replacement chars → valid
        # PUA (Co category) is excluded from non_printable count
        pua = "".join(chr(0xF000 + i) for i in range(4))  # 4 PUA chars
        text = "正常数学文本" + pua * 20 + "继续正常内容"
        report = self.gate.evaluate_text(text)
        assert report.non_printable_ratio == 0.0  # PUA excluded from count
        assert report.replacement_char_ratio == 0.0
        assert report.status == "valid"

    def test_pua_with_replacement_invalid(self):
        """BUG-V3-042: PUA + replacement chars → invalid (actual corruption)."""
        # 15% PUA + 2% replacement chars → invalid (due to replacement, not PUA)
        pua = "".join(chr(0xF000 + i) for i in range(3))  # 3 PUA chars
        text = "正常数学文本" + pua * 15 + "�" * 3 + "继续"
        report = self.gate.evaluate_text(text)
        assert report.non_printable_ratio == 0.0  # PUA excluded
        assert report.replacement_char_ratio > 0.01
        assert report.status == "invalid"

    def test_replacement_alone_still_invalid(self):
        """replacement_ratio > 5% alone → invalid (independent check preserved)."""
        # 10% replacement chars, no PUA → invalid
        text = "正常文本" + "�" * 20 + "更多正常文本内容在这里"
        report = self.gate.evaluate_text(text)
        assert report.replacement_char_ratio > 0.05
        assert report.status == "invalid"

    def test_math_pdf_scenario_valid(self):
        """Realistic math PDF: moderate PUA (7%) + no replacement → valid."""
        # Simulate math PDF with 7% PUA symbols
        pua_chars = "".join(chr(0xF000 + i) for i in range(7))  # 7 PUA chars
        text = "已知函数" + pua_chars + "的定义域为实数集R，则实数a的取值范围是"
        report = self.gate.evaluate_text(text)
        assert report.non_printable_ratio == 0.0  # PUA excluded from count
        assert report.replacement_char_ratio == 0.0
        assert report.status == "valid"
