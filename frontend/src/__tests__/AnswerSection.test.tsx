/**
 * P0-R4 render verification: pending answers must NOT look like the
 * standard answer. Uses react-dom/server renderToStaticMarkup so the
 * assertion is against real rendered HTML, not just JSX source.
 */
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import {
  AnswerSection,
  computeIsPendingReview,
} from "../components/AnswerSection";

const verified = {
  id: "a1",
  text: "B",
  answer_status: { verified_correct: true },
};
const unverified = {
  id: "a2",
  text: "【分析】这是解析不是答案",
  answer_status: { verified_correct: null },
};
const stemMisbind = {
  id: "a3",
  text: "下列图像不能在光学显微镜下观察到的是",
  answer_status: { complete: true, source_located: true, verified_correct: null },
} as never;

describe("computeIsPendingReview", () => {
  it("verified answers are not pending", () => {
    expect(computeIsPendingReview([verified])).toBe(false);
  });
  it("null verified_correct is pending", () => {
    expect(computeIsPendingReview([unverified])).toBe(true);
  });
  it("empty list is not pending (no answer section)", () => {
    expect(computeIsPendingReview([])).toBe(false);
  });
  it("mixed: any unverified makes the block pending", () => {
    expect(computeIsPendingReview([verified, unverified])).toBe(true);
  });
});

describe("AnswerSection rendered HTML", () => {
  it("pending title and risk warning are present", () => {
    const html = renderToStaticMarkup(<AnswerSection answers={[unverified]} />);
    expect(html).toContain("待核实答案（非标准答案）");
    expect(html).toContain("请勿作为标准答案使用");
    // must NOT use the bare standard-answer heading
    expect(html).not.toContain('text-ink-muted">答案<');
  });

  it("verified answers show as 答案 without the risk warning", () => {
    const html = renderToStaticMarkup(<AnswerSection answers={[verified]} />);
    expect(html).toContain('text-ink-muted">答案<');
    expect(html).not.toContain("待核实答案");
    expect(html).not.toContain("请勿作为标准答案使用");
  });

  it("stem misbind still shows risk warning (not trusted)", () => {
    const html = renderToStaticMarkup(<AnswerSection answers={[stemMisbind]} />);
    expect(html).toContain("待核实答案（非标准答案）");
    expect(html).toContain("请勿作为标准答案使用");
    expect(html).toContain("下列图像不能在光学显微镜下观察到的是");
  });

  it("explanation-as-answer is labeled untrusted", () => {
    const html = renderToStaticMarkup(<AnswerSection answers={[unverified]} />);
    expect(html).toContain("【分析】这是解析不是答案");
    expect(html).toContain("待核实答案");
    expect(html).toContain("请勿作为标准答案使用");
    expect(html).not.toContain('text-ink-muted">答案<');
  });

  it("empty answers render nothing", () => {
    const html = renderToStaticMarkup(<AnswerSection answers={[]} />);
    expect(html).toBe("");
  });
});
