"""B3-4/B3-4R 父题答案证据 → 子题映射契约（Owner 2026-10-29；DSH 两轮校准后）。

事实基础（已对 181 份真实 Producer 产物 / 5027 单元复算确认；Owner 口径 543/56）：
- Producer 真正声明的只有 ``answer_evidence = {type, lines, value, shared}``
  （56 单元缺 ``shared``，全部单题号）；**不存在** unit 级 ``answer_completeness``（0/5027）。
- e2e 侧 r2x_producer/r2x2_packages 里出现的 ``answer_completeness`` 是
  ``Papers/scripts/reslice_pipeline.py::_assign_answer_completeness`` 从证据
  **推导**后写入的（推导值≠声明），不能当上游权威。
- ``shared`` 的真实语义是 **答案证据区域被共享**（同一物理答案行/表服务多个
  单元），不是"答案值被共享"。实测：同一 lines=[423,423] 上 Q1 value='A'、
  Q2 value='C' —— 共享的是行，各自 value 已由 Producer 归一化到本题。
- 主导证据类型是 ``answer_table``（shared=True 339/543，DSH 同口径 339/511）；
  其 value 已被归一化为单字母或标准 token 串（``26.C 27.B …``），两条解析分支
  （压缩表 / 逐题 token）都能覆盖，无需表格块专用解析。

shared 两种语义（DSH 2026-10-29 校准；合并成一条规则会误伤 438 个单题号单元）：
1. **证据区域共享**（单题号为主，438/543）：该行/表同时服务多个单元。要求
   是"不得因区域共享而把别人的答案借过来" + 区域归属可核。没有"逐子题映射"
   这回事——单题号单元的 value 已经是它自己的答案。
2. **答案块共享**（多题号 composite，105/543）：父级声明块 → 逐子题显式映射。
   映射不全/歧义/冲突 → ``shared_block_not_mapped``，撤销完整性结论，并阻止
   未映射子题借用共享答案发布。
两者 fail-closed 方向不同：前者防串答案，后者防借答案发布。

契约规则（fail-closed，发布面 ⊆ 既有展开期证明面）：
1. 权威值 = Producer ``answer_evidence.value``：按题号显式映射到各子题
   （压缩表 ``11-15 CDBDB`` 或逐题 token ``11.C 12.B``；单题号复合体先做
   区域归属核验再取自己那一段）。
2. completeness 是 **V3 派生语义**（不是 Producer 声明）：``full`` 仅当展开期证明
   （derive：条目唯一 + 候选==条目原文 + label 形）仍在，且与声明段一致。
   声明缺失 → 撤销 ``full``；语义冲突 → 撤销 ``full``。derive 是证明引擎，
   不是第二权威；不得独自补上游缺失的映射。
3. 比对语义分层（不得简单放宽字符串比较）：
   - ``_norm``（空白/大小写）一致 → 一致；
   - ``_repr_norm``（再加 NFKC 全半角折叠）一致而 ``_norm`` 不一致 →
     **表示差异** ``mismatch_representation``（等价表示，不撤销）；
   - 其余 → **语义冲突** ``conflict_semantic``（撤销）。
   标点若改变答案含义（``1,2`` 集合 vs ``12``），NFKC 不会折叠，仍按语义冲突。
4. 值携带 ≠ 官方答案：声明段进 ``expected_value``（一致性守卫通道）并附
   ``answer_evidence`` 溯源（父 unit/声明原文/行范围/shared/type/映射方式/
   completeness_source）。
5. shared=True 块共享且未映射/歧义/冲突：除撤销完整性外，**清空** ``expected_value``
   （禁止借共享块答案发布）；shared=False 未映射只撤销完整性、保留自身 derive
   证据（普通规则）。不触碰 ownership/publish/BindingFact/golden。
"""

from __future__ import annotations

import re
import unicodedata

# P-2 依赖闭合（TASK-B3-4R-P2，2026-10-30）：声明段解析所需的 token 词族自此
# 本模块自带，不再 import subq_expand——其定义位于 R2X-08-P1/R2-C 的未提交
# 改动中，会让提交树 import 断链。以下实现与 subq_expand 工作区版本逐字节
# 同源（仅剥离流派注释）；subq_expand 未改动，两流行为零变化。已知代价：
# 词族双份定义，待 R2X-08/R2-C 落地后做专门去重（不在本轮范围）。
# Compressed answer-table forms: `11-15 CDBDB` / `11~15 CDBDB` /
# `11☐15 CDBDB` (OCR box for hyphen) / `11.C 12.D` (already expanded).
_RANGE_ANS_RE = re.compile(
    r"(\d{1,2})\s*[-–—~☐□■-]\s*(\d{1,2})\s*([A-Za-z]{2,})"
)


def _expand_range_answers(window: str) -> dict[int, str]:
    """Parse compressed `N-M letters` answer tables into {qn: letter}."""
    out: dict[int, str] = {}
    for m in _RANGE_ANS_RE.finditer(window):
        lo, hi, letters = int(m.group(1)), int(m.group(2)), m.group(3)
        if hi - lo + 1 != len(letters):
            continue
        for i, ch in enumerate(letters):
            out[lo + i] = ch
    return out


# Answer-table entry token: `11.` / `12、` / `13：` … not followed by a digit
# (decimal-safe).
_ENTRY_TOKEN_RE = re.compile(r"(\d{1,3})\s*[\.、．：:]\s*(?!\d)")


def _norm(seg: str | None) -> str:
    return re.sub(r"\s+", "", seg or "").upper()


def _repr_norm(seg: str | None) -> str:
    """表示等价层：NFKC（全半角折叠）+ 去空白 + 大小写折叠。

    只折叠"同一答案的不同表示"；不删标点、不合并数字，改变答案含义的
    差异不会在这里消失。
    """
    s = unicodedata.normalize("NFKC", seg or "")
    return re.sub(r"\s+", "", s).upper()


def normalize_decl_surface(value: str | None) -> str:
    """声明值表示层折叠（显式语义规则，非放宽比较）。

    真实 Producer 产物中的等价表示（已在 543/56 人口复算确认）：
    - markdown 转义标点 ``21\\. B`` ≡ ``21. B``；
    - 区间连接号 ``—``/``–``/``～`` ≡ ``-``；
    - 压缩表分隔 ``56-59:CBBA`` ≡ ``56-59 CBBA``（冒号=空格）。
    只折叠这些表示面；不改字母/数字内容（语义冲突仍按 conflict 判）。
    """
    s = re.sub(r"\\([\.、．：:，,；;])", r"\1", value or "")
    s = re.sub(r"[—–―~～]", "-", s)
    return s


# 纯压缩表：整串就是 `N-M letters`（可带冒号/全角冒号分隔）。
_PURE_RANGE_RE = re.compile(
    r"^\s*(\d{1,3})\s*[-]\s*(\d{1,3})\s*[:：]?\s*([A-Za-z]+)\s*$"
)


def _parse_pure_range_table(v: str) -> dict[int, str] | None:
    m = _PURE_RANGE_RE.match(v)
    if not m:
        return None
    lo, hi, letters = int(m.group(1)), int(m.group(2)), m.group(3)
    if hi - lo + 1 != len(letters):
        return None
    return {lo + i: ch for i, ch in enumerate(letters)}


def classify_value_diff(derived: str | None, declared: str | None) -> str:
    """'agree' | 'mismatch_representation' | 'conflict_semantic'"""
    if _norm(derived) == _norm(declared):
        return "agree"
    if _repr_norm(derived) == _repr_norm(declared):
        return "mismatch_representation"
    return "conflict_semantic"


# B3-4R P-1：原始声明值/声明范围的证据串序列化（进入 fact_* 标签）。
# 完整原文始终保留在 payload answer_evidence.declared_value/declared_lines，
# 这里只做有界序列化；回查锚点是同一 provenance 里的 fact_parent_unit。
PROV_DECLARED_VALUE_LIMIT = 120

# completeness_source 值域（P-2，2026-10-30）：producer_declared | v3_derived | none。
# 真实 Producer 从不声明 completeness（0/5067），producer_declared 仅预留；
# 当前唯一写入口恒写 v3_derived（映射只输出 V3 派生结论）。禁止标成 Producer 声明。
COMPLETENESS_SOURCE_PRODUCER = "producer_declared"
COMPLETENESS_SOURCE_V3 = "v3_derived"
COMPLETENESS_SOURCE_NONE = "none"


def clip_declared_value(value: str | None) -> str | None:
    """父声明原文 → 有界证据串；超限截断并保留原长标记（可经 parent_unit 回查）。"""
    if value is None:
        return None
    s = str(value)
    if len(s) <= PROV_DECLARED_VALUE_LIMIT:
        return s
    return f"{s[:PROV_DECLARED_VALUE_LIMIT]}...[truncated orig_len={len(s)}]"


def serialize_declared_lines(lines: list | tuple | None) -> str | None:
    """声明范围 → 紧凑无歧义串：二元 [start, end] → 'start-end'，其余逗号连接。"""
    if not lines:
        return None
    if len(lines) == 2:
        return f"{lines[0]}-{lines[1]}"
    return ",".join(str(x) for x in lines)


def _region_own_segment(value: str | None, qn: int) -> tuple[str | None, str]:
    """区域共享语义下的归属核验：从声明值中取 *本题* 自己的那一段。

    防串答案：声明值若是整条共享答案行（含其他题号 token/压缩表），不得把
    整块借给单题号单元，只取本题段；取不到本题段 → fail-closed (None)。

    返回 (本题段或 None, 归属标记)。
    """
    v = normalize_decl_surface(value).strip()
    if not v:
        return None, "region_empty_declaration"

    # 纯压缩表：按字母表取本题
    pure = _parse_pure_range_table(v)
    if pure:
        if qn in pure:
            return pure[qn], "region_own_letter_extracted"
        return None, "region_shared:foreign_block_not_owned"

    # 逐题 token：N.段 …
    hits = list(_ENTRY_TOKEN_RE.finditer(v))
    if hits:
        segs: dict[int, str] = {}
        for i, m in enumerate(hits):
            tk = int(m.group(1))
            end = hits[i + 1].start() if i + 1 < len(hits) else len(v)
            seg = v[m.end() : end].strip()
            if seg:
                segs[tk] = seg
        if qn in segs:
            note = (
                "region_own_segment_extracted"
                if len(segs) > 1
                else "region_own_segment_single_token"
            )
            return segs[qn], note
        return None, "region_shared:foreign_block_not_owned"

    # 压缩表（非纯形态，混在其他文本里）
    ranged = _expand_range_answers(re.sub(r"\s+", " ", v))
    if ranged:
        if qn in ranged:
            return ranged[qn], "region_own_letter_extracted"
        return None, "region_shared:foreign_block_not_owned"

    # 无 token/表形态：整段即本题声明（Producer 已归一化的单值，如 'A'）。
    return v, "region_whole_value_owned"


def parse_declared_answer_segments(
    value: str | None,
    question_numbers: list[int] | None = None,
) -> tuple[dict[int, str], dict[int, tuple[str, str]], dict[int, tuple[str, str]]]:
    """Producer 合并声明 → ({qn: 段}, {qn: (段A,段B) 语义冲突}, {qn: (A,B) 表示差异})。

    - 单题号复合体：整段 value 即该题声明（区域归属由 _region_own_segment 处理）。
    - 多题号：压缩范围表 + 逐题 token；同题号两解按分层比对归入冲突或表示差异。
    - 表示面折叠见 normalize_decl_surface（em-dash 区间 / 转义标点 / 冒号分隔）。
    """
    out: dict[int, str] = {}
    semantic: dict[int, tuple[str, str]] = {}
    repr_diff: dict[int, tuple[str, str]] = {}
    v = normalize_decl_surface(value).strip()
    if not v:
        return out, semantic, repr_diff

    qns = [int(x) for x in (question_numbers or []) if x is not None]
    if len(qns) == 1:
        out[qns[0]] = v
        return out, semantic, repr_diff

    # 纯压缩表：整串即一张表 → 只走表解析。
    # （否则 token 步会把 `59:CBBA` 误读成 59→'CBBA'，串答案。）
    pure = _parse_pure_range_table(v)
    if pure is not None:
        for qn, ch in pure.items():
            out[qn] = ch
        return out, semantic, repr_diff

    # 压缩范围表（结构性证明：lo-hi 与 letters 长度一致）
    for qn, ch in _expand_range_answers(re.sub(r"\s+", " ", v)).items():
        out[qn] = ch

    # 逐题 token：N.段 直到下一个 N.
    hits = list(_ENTRY_TOKEN_RE.finditer(v))
    for i, m in enumerate(hits):
        qn = int(m.group(1))
        end = hits[i + 1].start() if i + 1 < len(hits) else len(v)
        seg = v[m.end() : end].strip()
        if not seg:
            continue
        prev = out.get(qn)
        if prev is not None:
            kind = classify_value_diff(prev, seg)
            if kind == "agree":
                continue
            if kind == "mismatch_representation":
                repr_diff[qn] = (prev, seg)
                continue
            semantic[qn] = (prev, seg)
            out.pop(qn, None)
            continue
        out[qn] = seg
    return out, semantic, repr_diff


def map_parent_answer_evidence_to_subs(
    subs: list[dict],
    *,
    parent_value: str | None,
    parent_unit_id: str,
    parent_lines: list[int] | None,
    question_numbers: list[int] | None = None,
    parent_shared: bool | None = None,
    parent_type: str | None = None,
) -> dict:
    """把父级声明映射进展开子题的 answer 条目（就地增强）。

    仅处理确定性展开子条目（specs_to_payload_subs 产物）。n_q==1 无展开的
    旁路 sub 直接复用父 content（无信息损失），不经过本函数。

    返回审计摘要：
    {"mapped","revoked","carried","conflict_semantic","mismatch_representation",
     "shared_not_mapped","region_rejected","shared_semantics","declared_shared"}。
    """
    qns = [int(x) for x in (question_numbers or []) if x is not None]
    shared_semantics = "region" if len(qns) <= 1 else "block"
    segments, semantic, repr_diff = parse_declared_answer_segments(
        parent_value, question_numbers
    )
    audit: dict = {
        "mapped": [],
        "revoked": [],
        "carried": [],
        "conflict_semantic": [],
        "mismatch_representation": [],
        "shared_not_mapped": [],
        "region_rejected": [],
        "shared_semantics": shared_semantics,
        "declared_shared": parent_shared,
    }

    for sub in subs:
        content = sub.get("content")
        if not isinstance(content, dict):
            continue
        ans = content.get("answer")
        if not isinstance(ans, dict):
            continue
        try:
            qn = int(sub.get("question_number"))
        except (TypeError, ValueError):
            continue

        prov = {
            "parent_unit_id": parent_unit_id,
            "declared_value": parent_value,
            "declared_lines": list(parent_lines) if parent_lines else None,
            "sub_question_number": qn,
            "declared_shared": parent_shared,
            "declared_type": parent_type,
            "shared_semantics": shared_semantics,
            "completeness_source": COMPLETENESS_SOURCE_V3,
        }
        derived_completeness = ans.get("answer_completeness")
        derived_value = ans.get("expected_value")

        def _revoke_full(reason: str, drop_value: bool) -> None:
            if derived_completeness == "full":
                ans.pop("answer_completeness", None)
            if drop_value:
                # 防借答案发布：清空一致性守卫通道，禁止共享块/他题答案兜底。
                ans.pop("expected_value", None)
            prov["mapping"] = reason

        # ---- 同题号语义冲突（两解不一致）→ fail-closed ----
        if qn in semantic:
            a, b = semantic[qn]
            drop = parent_shared is True
            _revoke_full(f"conflict_semantic:segments_disagree({a!r}|{b!r})", drop)
            audit["conflict_semantic"].append(qn)
            ans["answer_evidence"] = prov
            continue

        decl: str | None = None
        region_note = None
        if shared_semantics == "region":
            # 防串答案：子题题号必须落在父声明范围内（部分展开/装配异常
            # 不得把父单元整值借给范围外题号）。
            if qns and qn not in qns:
                _revoke_full(
                    "region_out_of_declared_scope:derived_full_revoked"
                    if derived_completeness == "full"
                    else "region_out_of_declared_scope",
                    drop_value=True,
                )
                audit["region_rejected"].append(qn)
                ans["answer_evidence"] = prov
                continue
            if not qns and len(subs) > 1:
                _revoke_full(
                    "region_unscoped_multi_subs:derived_full_revoked"
                    if derived_completeness == "full"
                    else "region_unscoped_multi_subs",
                    drop_value=True,
                )
                audit["region_rejected"].append(qn)
                ans["answer_evidence"] = prov
                continue
            decl, region_note = _region_own_segment(parent_value, qn)
            if decl is None:
                # 防串答案：整块是别人的答案行/表，不得借给本单元。
                _revoke_full(
                    f"{region_note}:derived_full_revoked"
                    if derived_completeness == "full"
                    else str(region_note),
                    drop_value=True,
                )
                audit["region_rejected"].append(qn)
                ans["answer_evidence"] = prov
                continue
        else:
            decl = segments.get(qn)

        if decl is not None:
            # 权威值进入 P1-CLOSE 一致性守卫通道（compiler 只用它做物化比对）。
            # 注意：这里写入的是 *本题自己的* 声明段，不是共享块整段，
            # 因此保留 expected_value 不构成"借共享答案发布"。
            ans["expected_value"] = decl
            if derived_completeness == "full":
                if not (derived_value or "").strip():
                    # derive 声称 full 却无值可比 → 证明不成立，fail-closed。
                    ans.pop("answer_completeness", None)
                    prov["mapping"] = (
                        f"{region_note or 'declared_token'}+conflict_semantic:"
                        "derived_full_without_value"
                    )
                    audit["conflict_semantic"].append(qn)
                else:
                    kind = classify_value_diff(derived_value, decl)
                    if kind == "agree":
                        ans["answer_completeness"] = "full"
                        prefix = region_note or "declared_token"
                        prov["mapping"] = f"{prefix}+derived_agrees"
                        audit["mapped"].append(qn)
                    elif kind == "mismatch_representation":
                        # 等价表示（全半角/空白/大小写）：不撤销，单独计数。
                        ans["answer_completeness"] = "full"
                        audit["mapped"].append(qn)
                        audit["mismatch_representation"].append(qn)
                        prov["mapping"] = (
                            f"{region_note or 'declared_token'}+mismatch_representation"
                            f"(derived={derived_value!r},declared={decl!r})"
                        )
                    else:
                        # 语义冲突 → 撤销 full。本题段仍在 expected_value
                        # （非借答案）；完整性双证不成立。
                        ans.pop("answer_completeness", None)
                        prov["mapping"] = (
                            f"{region_note or 'declared_token'}+conflict_semantic:"
                            f"derived_disagrees(derived={derived_value!r},"
                            f"declared={decl!r})"
                        )
                        audit["conflict_semantic"].append(qn)
            else:
                # 无 derive 完整性证明：只携带本题声明段，不给 completeness。
                prov["mapping"] = f"{region_note or 'declared_token'}_only"
                audit["carried"].append(qn)
            ans["answer_evidence"] = prov
            continue

        # ---- 声明缺失（本题无显式段）----
        if parent_shared is True and shared_semantics == "block":
            # 块共享且映射不全：撤销完整性 + 禁止借共享答案发布。
            _revoke_full(
                "declared_missing:shared_block_not_mapped:derived_full_revoked"
                if derived_completeness == "full"
                else "declared_missing:shared_block_not_mapped",
                drop_value=True,
            )
            audit["shared_not_mapped"].append(qn)
        else:
            # 普通规则：只撤销不成立的 derive full，保留自身证据。
            if derived_completeness == "full":
                ans.pop("answer_completeness", None)
                prov["mapping"] = "declared_missing:derived_full_revoked"
                audit["revoked"].append(qn)
            else:
                prov["mapping"] = (
                    "declared_missing:shared_field_absent"
                    if parent_shared is None
                    else "declared_missing"
                )
        ans["answer_evidence"] = prov

    return audit
