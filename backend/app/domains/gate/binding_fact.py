"""P0-R16 independent binding fact (unified root-cause fix).

The ONLY trusted source of answer ownership + bound answer text + source
version identity. Produced from real source lines at resolve time
(resolver-internal derive path), registered in a process-local registry
keyed by (source_version_id, span_id). Transport payloads cannot write
here, cannot rebuild facts, and cannot supply raw_lines / ownership /
table_qn to re-derive a "trusted" fact.

Trust chain:
  real source lines + source_version_id + unit_id + question_number
    → classify_answer_ownership → BindingFact
      (fact_id HMAC covers ownership + answer_text_hash + source_hash
       + source_version_id + decode_loc)
      → registry[(source_version_id, span_id)]
      → _materialize / seal / Repository

Invariants (R16):
  - source_version_id is REQUIRED (empty is rejected).
  - fact_id and source_hash are REQUIRED (empty is rejected).
  - ownership is always recomputed from source_lines + question_number;
    declared ownership strings are never trusted.
  - table_qn is NOT used for ownership decision (R16: prevents
    `table_qn == qn` self-fulfilling classification). Structural
    evidence lives in decode_loc + entry_nums.
  - answer_text_hash binds the published text to the fact.
  - unit_id binds the fact to a specific IR unit (question identity).
  - decode_loc records structural position (cell index / range offset)
    and is covered by the HMAC.
  - resolve_trusted_binding_fact reads ONLY the registry, keyed by
    (source_version_id, span_id). No transport fallback.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import threading
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.core.secrets import derive_domain_key
from app.domains.resolver import resolver as _resolver_mod
from app.domains.resolver.resolver import classify_answer_ownership

# Domain-separated key (P1-A). Distinct from publish-seal label.
_FACT_KEY_LABEL = "aitutors/binding-fact/v1"


def _fact_key() -> bytes:
    return derive_domain_key(_FACT_KEY_LABEL)

_ENTRY_RE = re.compile(r"(?:^|[\s(（])(\d{1,3})\s*[.．、)）]")

_OWNERSHIP_ALIASES = {
    "match": "match",
    "foreign": "foreign",
    "foreign_question": "foreign",
    "unknown": "unknown",
}


@dataclass(frozen=True)
class BindingFact:
    """Verifiable, structured answer-ownership fact.

    ownership is ALWAYS derived (via classify_answer_ownership) from
    source_lines + question_number. Callers cannot declare it.
    answer_text / answer_text_hash bind the fact to a specific answer
    body so a foreign/match fact cannot authorize a different text.
    unit_id binds the fact to a specific IR unit (question identity).
    source_version_id binds the fact to a specific document version
    (prevents cross-document span_id pollution).
    decode_loc records structural position (cell/range offset) so the
    fact is bound to the specific source structure, not just a label.
    """

    span_id: str
    source_version_id: str
    unit_id: str
    question_number: str
    ownership: str
    evidence_kind: str
    source_lines: tuple[str, ...]
    entry_nums: tuple[str, ...]
    answer_text: str
    answer_text_hash: str
    decode_loc: str = ""
    table_qn: str = ""  # diagnostic only, NOT used for ownership
    source_hash: str = ""
    # Verifiable-binding input: Manifest answer_evidence.value used for the
    # content-consistency check. Stored so verify_binding_fact can re-derive
    # ownership with the SAME inputs (never a trust shortcut — the value is
    # still verified against source lines at derive AND at verify).
    declared_value: str = ""
    fact_id: str = ""

    def to_payload(self) -> dict:
        """Diagnostic only. NOT a trust input for materialize/repo."""
        return {
            "span_id": self.span_id,
            "source_version_id": self.source_version_id,
            "unit_id": self.unit_id,
            "question_number": self.question_number,
            "ownership": self.ownership,
            "evidence_kind": self.evidence_kind,
            "source_lines": list(self.source_lines),
            "entry_nums": list(self.entry_nums),
            "answer_text": self.answer_text,
            "answer_text_hash": self.answer_text_hash,
            "decode_loc": self.decode_loc,
            "table_qn": self.table_qn,
            "source_hash": self.source_hash,
            "declared_value": self.declared_value,
            "fact_id": self.fact_id,
        }


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _extract_entry_nums(lines: Sequence[str]) -> tuple[str, ...]:
    nums: list[str] = []
    for line in lines or ():
        for m in _ENTRY_RE.finditer(line or ""):
            n = m.group(1)
            if n not in nums:
                nums.append(n)
    return tuple(nums)


def _source_hash(lines: Sequence[str]) -> str:
    return _sha256_text("\n".join(lines or ()))


def _fact_digest(
    span_id: str,
    source_version_id: str,
    unit_id: str,
    question_number: str,
    ownership: str,
    evidence_kind: str,
    source_hash: str,
    entry_nums: Sequence[str],
    decode_loc: str,
    answer_text_hash: str,
    declared_value: str = "",
) -> str:
    msg = "\x1f".join(
        [
            span_id or "",
            source_version_id or "",
            unit_id or "",
            question_number or "",
            ownership or "unknown",
            evidence_kind or "",
            source_hash or "",
            ",".join(entry_nums or ()),
            decode_loc or "",
            answer_text_hash or "",
            declared_value or "",
        ]
    )
    return hmac.new(_fact_key(), msg.encode("utf-8"), hashlib.sha256).hexdigest()


def _normalize_ownership(raw: str) -> str:
    return _OWNERSHIP_ALIASES.get((raw or "unknown").strip().lower(), "unknown")


def _parse_decode_loc(decode_loc: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for piece in (decode_loc or "").split("|"):
        if ":" in piece:
            k, _, v = piece.partition(":")
            key = k.strip()
            val = v.strip()
            if key in parts and parts[key] != val:
                # Conflicting structural claims → poison the parse
                # (caller falls back to entry classification; no match).
                parts["__conflict__"] = "1"
            parts[key] = val
    return parts


_QN_ENTRY_RE_TMPL = r"(?:^|[\s(（]){qn}\s*[.．。、:：)）]"
_RANGE_LO_HI_RE = re.compile(r"(?<![\d])(\d{1,3})\s*[-–—~～]\s*(\d{1,3})")
_COMPACT_LETTERS_RE = re.compile(r"\s*[:：]?\s*([A-Za-z]{2,20})")


def _answer_letter(text: str) -> str:
    """Primary answer letter of a slice (e.g. 'B', '1. B' → 'B')."""
    m = re.search(r"[A-Za-z]", text or "")
    return m.group(0).upper() if m else ""


# Entry prefix: "1." / "（1）" / "1、" / "1．" / "1)" etc.
_ENTRY_PREFIX_RE = re.compile(
    r"^\s*[\s(（\[]?\d{1,3}\s*[.．、:：)）\]]\s*"
)


def _value_supported_by_lines(value: str, lines: Sequence[str]) -> bool:
    """Source-line content consistency for the verifiable-binding path.

    Declared answer_evidence.value must be recoverable from the declared
    answer_evidence.lines content. This is the '源行内容一致性' gate: never
    upgrade ownership just because a value was declared — the source must
    actually carry it.

    Single-letter value (choice answers): an answer token in the lines must
    BE that letter after stripping entry prefixes (`（1）A` → 'A').
    Multi-char value: contiguous occurrence in the joined lines.
    Empty value / empty lines → False (nothing to verify).
    """
    v = (value or "").strip()
    if not v:
        return False
    src = [x for x in (lines or ()) if x is not None]
    joined = "\n".join(src)
    if not joined.strip():
        return False

    if len(v) == 1 and v.isalpha():
        for line in src:
            raw = line or ""
            # Bare line that IS the letter.
            if raw.strip().upper() == v.upper():
                return True
            # Answer token after entry prefix: "1. A" / "（1）A" / "1、A".
            cleaned = _ENTRY_PREFIX_RE.sub("", raw).strip()
            cleaned = cleaned.strip(".．、:：)）（）【】[] \t")
            if len(cleaned) == 1 and cleaned.isalpha() and cleaned.upper() == v.upper():
                return True
            # Standalone letter token in the line (e.g. "答案：A").
            if re.search(
                rf"(?<![A-Za-z]){re.escape(v)}(?![A-Za-z])", raw, re.I
            ):
                return True
        return False

    # Multi-char value: contiguous occurrence (whitespace-normalized).
    _v_norm = re.sub(r"\s+", "", v)
    _j_norm = re.sub(r"\s+", "", joined)
    return _v_norm in _j_norm or _v_norm.upper() in _j_norm.upper()


def _answer_consistent_with_cell(answer_text: str, cell: str) -> bool:
    """answer_text must agree with the declared structural cell.

    Single-letter cell (the common answer-letter case): the answer slice
    must BE that letter (after stripping entry prefixes/punctuation).
    Multi-char answer_text like 'TiCl4' or 'DABCA' is NOT a single-letter
    answer — its first letter must not be treated as the answer token.
    Empty cell → no constraint.
    Non-letter cell (table value): cell must appear in the answer text.
    """
    c = (cell or "").strip()
    if not c:
        return True
    ans = (answer_text or "").strip()
    if len(c) == 1 and c.isalpha():
        if not ans:
            return False
        # Strip common entry prefixes ("1.", "1、", "1）") and punctuation.
        cleaned = re.sub(r"^\s*\d+\s*[.．。、:：)）]\s*", "", ans).strip()
        cleaned = cleaned.strip(".．。、:：()（） \t")
        # Must be EXACTLY one letter — not TiCl4, DABCA, etc.
        return len(cleaned) == 1 and cleaned.isalpha() and cleaned.upper() == c.upper()
    return c in ans or ans in c


def _source_supports_structural_qn(
    lines: Sequence[str], question_number: str, parts: Mapping[str, str]
) -> bool:
    """Re-derive structural support from source lines (never from decode_loc alone).

    True only when the source itself proves that `question_number` maps to
    the claimed cell: an entry token whose post-token letter equals the
    cell, a range covering that qn whose letter list yields the cell, or a
    compact key whose declared qn list maps that qn to the cell. A range
    without letters cannot prove any mapping and must NOT upgrade.
    """
    qn = (question_number or "").strip()
    if not qn:
        return False
    cell = (parts.get("cell") or "").strip()
    src = [x for x in (lines or ()) if x is not None]

    # 1) Entry token for this question (e.g. "19. D" / "19、D").
    # The claimed cell must be the letter that follows the entry token.
    try:
        entry_re = re.compile(_QN_ENTRY_RE_TMPL.format(qn=re.escape(qn)))
    except re.error:
        return False
    for line in src:
        m = entry_re.search(line or "")
        if not m:
            continue
        rest = (line or "")[m.end():]
        letter_m = re.search(r"[A-Za-z]", rest)
        if cell:
            if letter_m and letter_m.group(0).upper() == cell.upper():
                return True
            continue
        # No cell claimed: entry token alone is structural support.
        return True

    # 1b) HTML table cell holding this qn (e.g. `<td>1</td><td>B</td>`).
    # Cell value must appear on the same source line when claimed.
    try:
        td_qn_re = re.compile(
            r"<td[^>]*>\s*" + re.escape(qn) + r"\s*</td>", re.I
        )
    except re.error:
        td_qn_re = None
    if td_qn_re is not None:
        for line in src:
            if td_qn_re.search(line or ""):
                if not cell or cell in (line or ""):
                    return True

    # 2) Range key covering this question (e.g. "19-23 DABCA").
    # Without a letter list there is no verifiable qn→answer mapping.
    try:
        target_n = int(qn)
    except (TypeError, ValueError):
        target_n = None
    if target_n is not None:
        for line in src:
            for m in _RANGE_LO_HI_RE.finditer(line or ""):
                lo, hi = int(m.group(1)), int(m.group(2))
                if hi < lo or not (lo <= target_n <= hi):
                    continue
                rest = (line or "")[m.end():]
                letters_m = _COMPACT_LETTERS_RE.match(rest)
                if not letters_m:
                    # Range without letters: cannot prove the mapping.
                    continue
                letters = letters_m.group(1)
                if len(letters) != hi - lo + 1:
                    continue
                expected = letters[target_n - lo]
                if cell and cell.upper() != expected.upper():
                    continue
                return True

    # 3) Compact key with an explicitly declared qn list (qns:1-5 / 1,2,3).
    qns_raw = (parts.get("qns") or "").strip()
    if qns_raw and target_n is not None:
        ordered: list[int] = []
        for piece in re.split(r"[,，\s]+", qns_raw):
            if not piece:
                continue
            rng = re.match(r"(\d{1,3})\s*[-–—]\s*(\d{1,3})$", piece)
            if rng:
                lo, hi = int(rng.group(1)), int(rng.group(2))
                if hi >= lo:
                    ordered.extend(range(lo, hi + 1))
                continue
            if piece.isdigit():
                ordered.append(int(piece))
        if target_n in ordered and len(ordered) >= 2:
            idx = ordered.index(target_n)
            for line in src:
                compact = re.sub(r"\s+", "", line or "")
                if not re.fullmatch(r"[A-Za-z]+", compact):
                    continue
                if len(compact) != len(ordered):
                    continue
                expected = compact[idx]
                if not cell or cell.upper() == expected.upper():
                    return True
    return False


def _classify(
    lines: Sequence[str],
    question_number: str,
    decode_loc: str = "",
    answer_text: str = "",
    declared_value: str = "",
) -> str:
    """Recompute ownership from evidence. Never trusts a declared ownership.

    R16c-FIX: structural evidence in decode_loc only upgrades to match when
    (a) decode_loc.qn == question_number, (b) the source lines independently
    support that mapping (entry letter / range letter / compact letter), and
    (c) answer_text agrees with the claimed cell. A bare `cell:` substring is
    NOT proof (`qn:999|cell:Z`, `qn:19|cell:Z` + `1. A`, `19-23` without
    letters, `cell:D` + text `A` must all fail).

    Verifiable-binding path (Manifest answer_evidence contract):
        unit_id/question_numbers + answer_evidence.value + answer_evidence.lines
        + source-line content consistency  →  auditable ownership=match.
    Never upgrades from the mere presence of answer_evidence — the source
    lines must actually carry the declared value, and entry numbering must
    not name a different question. Content inconsistency / cross-question
    conflict / missing lines → reject (unknown / foreign).
    No reliable evidence → unknown (fail-closed, withheld_review).
    """
    qn = (question_number or "").strip()
    parts = _parse_decode_loc(decode_loc or "")
    loc_qn = (parts.get("qn") or "").strip()
    cell = (parts.get("cell") or "").strip()
    has_cell = bool(cell)
    no_conflict = "__conflict__" not in parts

    _cell_fail_closed = False
    if has_cell and loc_qn and loc_qn == qn and no_conflict:
        # Declared structural cell: upgrade to match when supported.
        # Cell contradicting the answer body → fail closed (unknown).
        # Cell agreeing but source not proving structural mapping → fall
        # through to the verifiable-binding path ONLY (NOT the entry
        # classifier, which ignores cell and would wrongly upgrade
        # `19. D` + cell:Z to match).
        if _answer_consistent_with_cell(answer_text, cell):
            if _source_supports_structural_qn(lines, qn, parts):
                return "match"
            _cell_fail_closed = True
        else:
            return "unknown"
    elif has_cell and loc_qn and loc_qn == qn and not no_conflict:
        return "unknown"

    # Verifiable binding: declared_value + real source lines + content consistency.
    # Guard: lines must be real source content, not a value-only placeholder
    # (add_value_only_answer passes source_lines=[value]).
    # declared_value is ALWAYS the answer for THIS target at the same semantic
    # scope — for a single composite question (Chinese Q1), it is the FULL
    # multi-part block. Never truncate to per-q here.
    dv = (declared_value or "").strip()
    src = [x for x in (lines or ()) if x is not None]
    joined = "\n".join(src)
    is_value_only_placeholder = (
        len(src) == 1 and (src[0] or "").strip() == dv and dv != ""
    )
    if dv and src and joined.strip() and not is_value_only_placeholder:
        entry_nums = _extract_entry_nums(src)
        qn_in = qn in entry_nums if entry_nums else False
        others = [n for n in entry_nums if n != qn]
        # Cross-question conflict: entry numbering names ONLY other questions.
        if entry_nums and not qn_in and others:
            return "foreign"
        # Content consistency: declared value must be recoverable from source.
        content_ok = _value_supported_by_lines(dv, src)
        if not content_ok:
            # Declared value contradicts source content → do NOT upgrade.
            return "unknown"
        # Entry numbering matches, or no recognizable entry numbering
        # (e.g. `（1）A` style the entry regex may or may not catch) —
        # declared binding + content consistency is auditable proof.
        if qn_in or not entry_nums:
            return "match"
        # Entry nums exist but qn not among them and no others (edge) → unknown.
        return "unknown"

    # Structural cell was present but unproven: do NOT let the entry
    # classifier (which ignores cell) upgrade `19. D` + cell:Z to match.
    if _cell_fail_closed:
        return "unknown"

    own = _resolver_mod.classify_answer_ownership(list(lines or ()), qn)
    return _normalize_ownership(own)


def derive_binding_fact(
    *,
    span_id: str,
    source_version_id: str,
    unit_id: str = "",
    question_number: str,
    source_lines: Sequence[str],
    answer_text: str,
    evidence_kind: str = "",
    decode_loc: str = "",
    declared_value: str = "",
) -> BindingFact:
    """Sole producer of BindingFact. Resolver-internal derive path ONLY.

    Recomputes ownership from source evidence. Never trusts a declared
    ownership string. source_version_id is REQUIRED.
    decode_loc records structural position (cell index / range offset).
    declared_value is the Manifest answer_evidence.value used for the
    verifiable-binding content-consistency check (never a trust shortcut).
    """
    if not source_version_id:
        raise ValueError("source_version_id is required for BindingFact")
    svid = str(source_version_id)
    lines = tuple(x for x in (source_lines or ()) if x is not None)
    qn = (question_number or "").strip()
    entry_nums = _extract_entry_nums(lines)
    sh = _source_hash(lines)
    ans = answer_text or ""
    ans_h = _sha256_text(ans)

    kind = (evidence_kind or "").strip()
    if not kind:
        if decode_loc:
            kind = "structural"
        elif entry_nums:
            kind = "entry_line"
        elif lines:
            kind = "bare_or_value"
        else:
            kind = "empty"

    own = _classify(
        lines, qn, decode_loc, answer_text=ans, declared_value=declared_value
    )

    fid = _fact_digest(
        span_id, svid, unit_id, qn, own, kind, sh,
        entry_nums, decode_loc, ans_h, declared_value,
    )
    return BindingFact(
        span_id=span_id or "",
        source_version_id=svid,
        unit_id=unit_id or "",
        question_number=qn,
        ownership=own,
        evidence_kind=kind,
        source_lines=lines,
        entry_nums=entry_nums,
        answer_text=ans,
        answer_text_hash=ans_h,
        decode_loc=decode_loc or "",
        source_hash=sh,
        declared_value=declared_value or "",
        fact_id=fid,
    )


def _fact_from_mapping(fact: Mapping) -> BindingFact | None:
    try:
        return BindingFact(
            span_id=str(fact.get("span_id") or ""),
            source_version_id=str(fact.get("source_version_id") or ""),
            unit_id=str(fact.get("unit_id") or ""),
            question_number=str(fact.get("question_number") or ""),
            ownership=str(fact.get("ownership") or "unknown"),
            evidence_kind=str(fact.get("evidence_kind") or ""),
            source_lines=tuple(fact.get("source_lines") or ()),
            entry_nums=tuple(fact.get("entry_nums") or ()),
            answer_text=str(fact.get("answer_text") or ""),
            answer_text_hash=str(fact.get("answer_text_hash") or ""),
            decode_loc=str(fact.get("decode_loc") or ""),
            table_qn=str(fact.get("table_qn") or ""),
            source_hash=str(fact.get("source_hash") or ""),
            declared_value=str(fact.get("declared_value") or ""),
            fact_id=str(fact.get("fact_id") or ""),
        )
    except Exception:
        return None


def verify_binding_fact(fact: BindingFact | Mapping | None) -> bool:
    """Re-derive ownership from fact's own structured evidence.

    Hard requirements (R16c-FIX):
      - source_version_id non-empty (empty SV → fail)
      - fact_id non-empty and matches recomputed HMAC
      - source_hash non-empty and matches source_lines
      - answer_text_hash non-empty and matches answer_text
      - ownership equals re-classification (declared value ignored)
      - declared cell must be supported by source_lines AND agree with
        answer_text (signature integrity alone is NOT enough)
    """
    if fact is None:
        return False
    if isinstance(fact, Mapping):
        fact = _fact_from_mapping(fact)
        if fact is None:
            return False

    # R16: empty SV is a hard failure.
    if not fact.source_version_id:
        return False
    if not fact.fact_id:
        return False
    if not fact.source_hash:
        return False
    if not fact.answer_text_hash:
        return False

    lines = tuple(fact.source_lines or ())
    if _source_hash(lines) != fact.source_hash:
        return False
    if _sha256_text(fact.answer_text or "") != fact.answer_text_hash:
        return False

    # Source-evidence verification: a declared cell must agree with the
    # answer body, not conflict across questions, AND be supported by the
    # source lines. Structural proof (_source_supports_structural_qn) is
    # checked by _classify which falls through to the verifiable-binding
    # path. Here we require content support: the cell value must appear
    # in the source (e.g. `故选：A.` supports cell `A`, but `19. D` does
    # NOT support cell `Z`).
    parts = _parse_decode_loc(fact.decode_loc or "")
    cell = (parts.get("cell") or "").strip()
    if cell:
        if "__conflict__" in parts:
            return False
        if not _answer_consistent_with_cell(fact.answer_text or "", cell):
            return False
        loc_qn = (parts.get("qn") or "").strip()
        if loc_qn and loc_qn != (fact.question_number or "").strip():
            return False
        # Content support: cell must be recoverable from source lines.
        # Structural support (range-key / compact / entry) OR plain content
        # consistency (e.g. `故选：A.` carries cell `A`).
        if not _source_supports_structural_qn(
            lines, fact.question_number or "", parts
        ) and not _value_supported_by_lines(cell, lines):
            return False

    own = _classify(
        lines, fact.question_number, fact.decode_loc,
        answer_text=fact.answer_text or "",
        declared_value=fact.declared_value or "",
    )
    if own != (fact.ownership or "unknown"):
        return False

    expected = _fact_digest(
        fact.span_id,
        fact.source_version_id,
        fact.unit_id,
        fact.question_number,
        fact.ownership,
        fact.evidence_kind,
        fact.source_hash,
        fact.entry_nums,
        fact.decode_loc,
        fact.answer_text_hash,
        fact.declared_value or "",
    )
    return hmac.compare_digest(expected, fact.fact_id)


def binding_fact_digest(fact: BindingFact | Mapping | None) -> str:
    if fact is None:
        return ""
    if isinstance(fact, Mapping):
        return str(fact.get("fact_id") or "")
    return fact.fact_id or ""


class BindingFactRegistry:
    """Trusted binding-fact store (process-local).

    Populated ONLY by the resolver/derive path via register_trusted.
    Keyed by (source_version_id, span_id) — R16 composite key prevents
    cross-document span_id pollution. Transport payloads cannot write
    here. _materialize / Repository look up by (SV, span_id).
    """

    def __init__(self) -> None:
        self._facts: dict[tuple[str, str], BindingFact] = {}
        self._lock = threading.Lock()

    def register_trusted(self, fact: BindingFact) -> BindingFact:
        """Resolver derive path ONLY. Rejects unverified / empty-id facts."""
        if fact is None:
            raise ValueError("fact is required")
        if not fact.source_version_id:
            raise ValueError("binding fact missing source_version_id")
        if not fact.fact_id or not fact.source_hash or not fact.answer_text_hash:
            raise ValueError("binding fact missing fact_id/source_hash/answer_text_hash")
        if not verify_binding_fact(fact):
            raise ValueError("binding fact failed verification at register")
        key = (fact.source_version_id, fact.span_id)
        with self._lock:
            self._facts[key] = fact
        return fact

    def get(self, source_version_id: str, span_id: str) -> BindingFact | None:
        if not source_version_id or not span_id:
            return None
        key = (source_version_id, span_id)
        with self._lock:
            fact = self._facts.get(key)
        if fact is not None and not verify_binding_fact(fact):
            return None
        return fact

    def clear(self) -> None:
        with self._lock:
            self._facts.clear()


_default_registry = BindingFactRegistry()


def get_registry() -> BindingFactRegistry:
    return _default_registry


def register_trusted_binding_fact(fact: BindingFact) -> BindingFact:
    return _default_registry.register_trusted(fact)


def lookup_binding_fact(source_version_id: str, span_id: str) -> BindingFact | None:
    return _default_registry.get(str(source_version_id), span_id)


def resolve_trusted_binding_fact(
    *, source_version_id: str, span_id: str
) -> BindingFact | None:
    """Obtain the independent binding fact for an answer span.

    READ-ONLY over the registry. Keyed by (source_version_id, span_id).
    No transport fallback: caller-supplied raw_lines / ownership /
    decode_loc cannot rebuild a fact here.
    Returns None when no trusted fact exists (fail closed → unknown).
    """
    return lookup_binding_fact(str(source_version_id), span_id)


def fact_matches_answer_text(fact: BindingFact | Mapping | None, candidate_text: str) -> bool:
    """True when candidate_text is the text this fact authorizes."""
    if fact is None:
        return False
    if isinstance(fact, Mapping):
        fact = _fact_from_mapping(fact)
        if fact is None:
            return False
    return _sha256_text(candidate_text or "") == (fact.answer_text_hash or "")
