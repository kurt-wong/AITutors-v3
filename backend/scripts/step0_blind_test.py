"""Step 0.5 Blind Structural Claim Test.

临时实验脚本，不属于 V3 生产代码。
不修改任何 V3 模块。仅调用 MIMO API 做盲测。
"""
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

# Load from .env
def load_env():
    env = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

_env = load_env()
API_KEY = _env.get("MIMO_API_KEY", "")
BASE_URL = _env.get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
MODEL = _env.get("MIMO_MODEL", "mimo-v2.6-pro")  # FORMAL-E2E-ENABLEMENT-02: no legacy default

PROMPT_TEMPLATE = """You are a structural annotation system for Chinese exam papers.

Given a source document with line references in the format [P{{page}}L{{line}}],
identify every question unit and provide structural annotations.

For EACH question unit, output:
- unit_id: sequential identifier (Q1, Q2, ...)
- question_number: the question number as printed in the document
- unit_type: "standalone_question" or "composite_question"
- stem_lines: [start_line_ref, end_line_ref] — the question stem text
- options_lines: [start_line_ref, end_line_ref] — ALL option lines (null if no options, e.g. fill-in-the-blank)
- answer_lines: [start_line_ref, end_line_ref] — the answer line(s)
- explanation_lines: [start_line_ref, end_line_ref] — the explanation/solution text (null if none)

Rules:
- Use the EXACT line references from the source (e.g. "P1L007")
- For questions sharing the same material (composite), use unit_type="composite_question" and include material_lines
- For shared answer tables, point each question's answer_lines to the table line(s)
- Do NOT include section headers or page headers as question content
- Output ONLY valid JSON, no other text

Source document:
{source}

Output format:
{{"units": [{{"unit_id": "Q1", "question_number": 1, "unit_type": "standalone_question", "stem_lines": ["P1L007", "P1L007"], "options_lines": ["P1L009", "P1L009"], "answer_lines": ["P1L155", "P1L155"], "explanation_lines": ["P1L157", "P1L165"]}}]}}"""


def prepare_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    result = []
    for i, line in enumerate(lines):
        ref = f"P1L{i+1:03d}"
        result.append(f"[{ref}] {line.rstrip()}")
    return "\n".join(result)


def call_llm(prompt: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 32768,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    content = data["choices"][0]["message"]["content"]
    if not content:
        print(f"WARNING: Empty content. Full response: {raw[:2000]}")
    return content


def parse_llm_output(text: str) -> dict:
    match = re.search(r'\{[\s\S]*"units"[\s\S]*\}', text)
    if not match:
        match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError(f"No JSON found in LLM output:\n{text[:500]}")
    json_str = match.group(0)
    return json.loads(json_str)


def parse_line_ref(ref: str) -> int:
    m = re.search(r"L(\d+)", ref)
    if m:
        return int(m.group(1))
    raise ValueError(f"Cannot parse line ref: {ref}")


def compare_with_ground_truth(llm_units: list, manifest_path: str) -> None:
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    gt_units = {u["unit_id"]: u for u in manifest["units"]}
    llm_by_id = {u["unit_id"]: u for u in llm_units}

    fields = ["stem_lines", "options_lines", "answer_lines", "explanation_lines"]

    total = 0
    exact_match = 0
    partial_match = 0
    mismatch = 0
    missing = 0
    false_positive = 0

    errors = []

    for uid, gt in gt_units.items():
        llm = llm_by_id.get(uid)
        if llm is None:
            gt_qn = gt.get("question_numbers", [None])[0]
            for luid, lu in llm_by_id.items():
                if lu.get("question_number") == gt_qn:
                    llm = lu
                    break
        if llm is None:
            missing += 1
            errors.append(f"{uid}: MISSING in LLM output")
            continue

        for field in fields:
            gt_val = gt.get(field)
            llm_val = llm.get(field)
            total += 1

            if gt_val is None and llm_val is None:
                exact_match += 1
                continue
            if gt_val is None and llm_val is not None:
                false_positive += 1
                errors.append(f"{uid}.{field}: LLM produced {llm_val} but GT is None")
                continue
            if gt_val is not None and llm_val is None:
                mismatch += 1
                errors.append(f"{uid}.{field}: LLM is None but GT is {gt_val}")
                continue

            gt_start, gt_end = gt_val[0], gt_val[1]
            llm_start = parse_line_ref(llm_val[0])
            llm_end = parse_line_ref(llm_val[1])

            if gt_start == llm_start and gt_end == llm_end:
                exact_match += 1
            elif llm_start <= gt_end and gt_start <= llm_end:
                partial_match += 1
                errors.append(
                    f"{uid}.{field}: PARTIAL mine=[{llm_start},{llm_end}] gt=[{gt_start},{gt_end}]"
                )
            else:
                mismatch += 1
                errors.append(
                    f"{uid}.{field}: MISMATCH mine=[{llm_start},{llm_end}] gt=[{gt_start},{gt_end}]"
                )

    gt_qns = set()
    for u in manifest["units"]:
        for qn in u.get("question_numbers", []):
            gt_qns.add(qn)
    for luid, lu in llm_by_id.items():
        qn = lu.get("question_number")
        if qn is not None and qn not in gt_qns:
            false_positive += 1
            errors.append(f"{luid}: FALSE POSITIVE (qn={qn} not in GT)")

    print()
    print("=" * 60)
    print("BLIND TEST RESULTS")
    print("=" * 60)
    print(f"Ground truth units: {len(gt_units)}")
    print(f"LLM output units:   {len(llm_by_id)}")
    print()
    if total:
        print(f"Total fields compared: {total}")
        print(f"Exact match:           {exact_match} ({exact_match/total*100:.1f}%)")
        print(f"Partial match (IoU):   {partial_match} ({partial_match/total*100:.1f}%)")
        print(f"Mismatch:              {mismatch} ({mismatch/total*100:.1f}%)")
    print(f"Missing units:         {missing}")
    print(f"False positives:       {false_positive}")
    print()

    print("Per-field breakdown:")
    for field in fields:
        f_total = 0
        f_exact = 0
        for uid, gt in gt_units.items():
            gt_val = gt.get(field)
            llm = llm_by_id.get(uid)
            if llm is None:
                for luid, lu in llm_by_id.items():
                    if lu.get("question_number") == gt.get("question_numbers", [None])[0]:
                        llm = lu
                        break
            if llm is None:
                continue
            llm_val = llm.get(field)
            if gt_val is None and llm_val is None:
                f_total += 1
                f_exact += 1
            elif gt_val is not None and llm_val is not None:
                f_total += 1
                try:
                    llm_s = parse_line_ref(llm_val[0])
                    llm_e = parse_line_ref(llm_val[1])
                    if gt_val[0] == llm_s and gt_val[1] == llm_e:
                        f_exact += 1
                except (ValueError, IndexError, KeyError):
                    pass
        if f_total:
            print(f"  {field:25s}: {f_exact}/{f_total} exact ({f_exact/f_total*100:.1f}%)")

    print()
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors[:30]:
            print(f"  {e}")
        if len(errors) > 30:
            print(f"  ... and {len(errors)-30} more")
    else:
        print("NO ERRORS")


def run_test(name: str, source_path: str, manifest_path: str) -> None:
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")

    source = prepare_source(source_path)
    prompt = PROMPT_TEMPLATE.format(source=source)

    print(f"Source: {source_path}")
    print(f"Source length: {len(source)} chars")
    print(f"Model: {MODEL} @ {BASE_URL}")
    print("Calling LLM...")

    raw_output = call_llm(prompt)

    print(f"LLM output length: {len(raw_output)} chars")

    try:
        parsed = parse_llm_output(raw_output)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"PARSE ERROR: {e}")
        print(f"Raw output (first 1000 chars):\n{raw_output[:1000]}")
        return

    llm_units = parsed.get("units", [])
    print(f"Parsed {len(llm_units)} units from LLM output")

    compare_with_ground_truth(llm_units, manifest_path)


if __name__ == "__main__":
    test_name = sys.argv[1] if len(sys.argv) > 1 else "math"
    source_path = sys.argv[2]
    manifest_path = sys.argv[3]
    run_test(test_name, source_path, manifest_path)
