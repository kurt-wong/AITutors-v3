/** QuestionFetchError（VIS-INSPECT-V1）：题目拉取失败的友好错误态。
 *  404 常见于切换卷库后残留旧题号（题号只属于原卷库）——给出明确解释与返回路径，
 *  不再裸抛 API JSON。 */

import { Link } from "react-router-dom";

export function QuestionFetchError({ error }: { error: string }) {
  const is404 = error.includes("404") || error.includes("question not found");
  return (
    <div className="space-y-3 p-4">
      {is404 ? (
        <>
          <div className="rounded-lg border-2 border-amber-300 bg-amber-50 p-4 text-[14px] text-amber-900">
            <div className="font-semibold">当前卷库中不存在该题目</div>
            <p className="mt-1 text-[13px]">
              题目 ID 只属于导入它的那一个卷库。若你刚刚在右上角切换了卷库，
              旧题号不会出现在新卷库中——这是正常的数据域边界，不是题目丢失。
            </p>
          </div>
          <Link
            to="/admin/questions"
            className="inline-block rounded border border-hairline bg-white px-3 py-1 text-[13px] text-primary hover:bg-canvas-parchment"
          >
            ← 返回当前卷库题目列表
          </Link>
        </>
      ) : (
        <div className="text-sm text-red-600">{error}</div>
      )}
    </div>
  );
}
