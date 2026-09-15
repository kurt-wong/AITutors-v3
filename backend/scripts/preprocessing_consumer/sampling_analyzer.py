"""Phase 0.3-B correctness sampling analysis.

Analyzes the 527 resolved units for correctness issues:
- False positive detections (content text mistaken for option markers)
- Incomplete detections (real options missed)
- Position accuracy
- HTML structure issues

Output: structured findings for each sample.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def analyze_sample(sample: dict) -> dict:
    """Analyze a single resolved sample for correctness issues."""
    issues = []
    detected = sample['detected_labels']
    located = sample['located']
    region_text = sample['region_text']

    # Extract raw text from region (strip line numbers)
    raw_lines = []
    for line in region_text:
        match = re.match(r'L\d+:\s*(.*)', line)
        if match:
            raw_lines.append(match.group(1))
        else:
            raw_lines.append(line)

    full_text = '\n'.join(raw_lines)

    # Check 1: False positive - element symbols in parentheses
    for lab in detected:
        entry = located[lab]
        if entry.get('start_offset') is not None:
            line_no = entry.get('line_no', 0)
            if 0 < line_no <= len(raw_lines):
                line_text = raw_lines[line_no - 1]
                offset = entry['start_offset']
                context = line_text[max(0, offset - 2):offset + len(lab) + 2]
                if re.search(rf'\({re.escape(lab)}\)', context):
                    issues.append({
                        'type': 'false_positive_element_symbol',
                        'label': lab,
                        'evidence': f'Label {lab} appears in parentheses: {context}',
                        'severity': 'HIGH'
                    })
                if '$' in line_text and lab in line_text:
                    dollar_count = line_text[:offset].count('$')
                    if dollar_count % 2 == 1:
                        issues.append({
                            'type': 'false_positive_math_formula',
                            'label': lab,
                            'evidence': f'Label {lab} inside math formula',
                            'severity': 'HIGH'
                        })

    # Check 2: Incomplete detection - look for missed option markers
    all_markers = set()
    for line_text in raw_lines:
        for m in re.finditer(r'(?:^|\s)([A-H])[.．、:：]', line_text):
            all_markers.add(m.group(1).upper())
        for m in re.finditer(r'<(?:div|td|span)[^>]*>\s*([A-H])\.\s*</', line_text):
            all_markers.add(m.group(1).upper())

    missed = all_markers - set(detected)
    if missed:
        issues.append({
            'type': 'incomplete_detection',
            'missed_labels': sorted(missed),
            'evidence': f'Found markers {sorted(all_markers)} but only detected {detected}',
            'severity': 'HIGH'
        })

    # Check 3: HTML structure complexity
    html_count = full_text.count('<div') + full_text.count('<td') + full_text.count('<table')
    if html_count > 0 and len(detected) < 4:
        issues.append({
            'type': 'html_structure_issue',
            'html_elements': html_count,
            'detected_count': len(detected),
            'evidence': f'HTML structure present ({html_count} elements) but only {len(detected)} labels detected',
            'severity': 'MEDIUM'
        })

    # Check 4: Suspicious single-line inline detection
    if sample['options_region'][0] == sample['options_region'][1]:
        line_text = raw_lines[0] if raw_lines else ''
        actual_markers = len(re.findall(r'(?:^|\s)([A-H])[.．、:：]', line_text))
        if len(detected) > actual_markers + 1:
            issues.append({
                'type': 'suspicious_inline_detection',
                'detected': len(detected),
                'actual_markers': actual_markers,
                'evidence': f'Detected {len(detected)} labels but only {actual_markers} clear markers',
                'severity': 'MEDIUM'
            })

    # Check 5: Label order validation
    positions = []
    for lab in detected:
        entry = located[lab]
        line_no = entry.get('line_no', 0)
        offset = entry.get('start_offset') or 0
        positions.append(line_no * 10000 + offset)

    if positions != sorted(positions):
        issues.append({
            'type': 'invalid_label_order',
            'detected': detected,
            'positions': positions,
            'evidence': f'Labels not in source order: {detected}',
            'severity': 'MEDIUM'
        })

    return {
        'paper': sample['paper'],
        'unit_id': sample['unit_id'],
        'stratum': sample.get('_stratum', 'unknown'),
        'detected_labels': detected,
        'issues': issues,
        'correct': len(issues) == 0,
        'issue_count': len(issues),
        'severity': 'HIGH' if any(i['severity'] == 'HIGH' for i in issues)
                   else ('MEDIUM' if issues else 'NONE')
    }


def main():
    review_file = Path(__file__).parent / 'sampling-review-set.json'
    with open(review_file, encoding='utf-8') as f:
        data = json.load(f)

    samples = data['samples']
    print(f"Analyzing {len(samples)} samples...")

    results = [analyze_sample(s) for s in samples]

    total = len(results)
    correct = sum(1 for r in results if r['correct'])
    has_issues = total - correct
    high_severity = sum(1 for r in results if r['severity'] == 'HIGH')
    medium_severity = sum(1 for r in results if r['severity'] == 'MEDIUM')

    print(f"\n{'=' * 60}")
    print(f"Correctness Sampling Results")
    print(f"{'=' * 60}")
    print(f"Total samples: {total}")
    print(f"Correct (no issues): {correct} ({correct / total * 100:.1f}%)")
    print(f"With issues: {has_issues} ({has_issues / total * 100:.1f}%)")
    print(f"  HIGH severity: {high_severity}")
    print(f"  MEDIUM severity: {medium_severity}")

    print(f"\nBy stratum:")
    by_stratum = defaultdict(lambda: {'total': 0, 'correct': 0, 'high': 0, 'medium': 0})
    for r in results:
        s = r['stratum']
        by_stratum[s]['total'] += 1
        if r['correct']:
            by_stratum[s]['correct'] += 1
        if r['severity'] == 'HIGH':
            by_stratum[s]['high'] += 1
        elif r['severity'] == 'MEDIUM':
            by_stratum[s]['medium'] += 1

    for s, stats in sorted(by_stratum.items(), key=lambda x: -x[1]['total']):
        acc = stats['correct'] / stats['total'] * 100 if stats['total'] else 0
        print(f"  {s:25s}: {stats['correct']:3d}/{stats['total']:3d} "
              f"correct ({acc:5.1f}%) | HIGH={stats['high']} MED={stats['medium']}")

    print(f"\nIssue types:")
    issue_types = Counter()
    for r in results:
        for issue in r['issues']:
            issue_types[issue['type']] += 1
    for itype, count in issue_types.most_common():
        print(f"  {itype:35s}: {count}")

    print(f"\n{'=' * 60}")
    print(f"HIGH Severity Issues (detailed)")
    print(f"{'=' * 60}")
    for r in results:
        if r['severity'] == 'HIGH':
            print(f"\n{r['paper'][:50]} {r['unit_id']} [{r['stratum']}]")
            print(f"  Detected: {r['detected_labels']}")
            for issue in r['issues']:
                if issue['severity'] == 'HIGH':
                    print(f"  X {issue['type']}: {issue.get('evidence', '')}")

    output_file = Path(__file__).parent / 'sampling-review-results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_samples': total,
                'correct': correct,
                'with_issues': has_issues,
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'accuracy': correct / total * 100 if total else 0
            },
            'by_stratum': {s: dict(stats) for s, stats in by_stratum.items()},
            'issue_types': dict(issue_types),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
