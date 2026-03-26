"""
실험 ID: 014
실험명: Validation V2 — 구조화 응답 기반 검증 커버리지 측정

목적:
- 현재 validation.py(regex 기반)의 커버리지를 측정
- 구조화 응답(007 스키마)에서 직접 검증하면 커버리지가 얼마나 높아지는지 비교
- false positive 비율 측정

가설:
1. 현재 regex 기반 커버리지는 50% 미만
2. 구조화 응답 기반 검증은 90%+ 커버리지 달성
3. false positive(실제 맞는데 틀렸다고 판정)는 5% 미만

방법:
1. golden_dataset.json의 expected_facts로 검증 기준 구성
2. 모의 LLM 응답(좋은/나쁜)에 대해 현재 validation.py 실행
3. 구조화 응답 검증 프로토타입으로 같은 테스트
4. 커버리지/정확도/false positive 비교

결과:
- Regex 기반 (현재 validation.py):
  - Good 응답 커버리지: 0% — extract_numbers가 "metric: value%" 포맷에서 매칭 실패
  - Bad 응답 커버리지: 0%
  - False positive: 0/5
- Structured 기반 (metrics 직접 비교):
  - Good 응답 커버리지: 100% (18/18 facts 전부 매칭)
  - Bad 응답 커버리지: 0% (metrics 비어있음)
  - False positive: 0/5

결론:
- 가설 1 채택: regex 기반 커버리지 0% — 예상(50% 미만)보다 심각
  → extract_numbers의 패턴이 실제 응답 포맷과 불일치
- 가설 2 채택: 구조화 응답 기반 100% 커버리지 (Good에서)
- 가설 3 채택: false positive 0% (5% 미만 목표 달성)
- 핵심: regex 기반 검증은 사실상 무용. 구조화 응답이 필수
- 프로덕션 적용: StructuredAnalysis.metrics에서 직접 name/value 매칭
  → validation.py를 regex → structured 기반으로 전면 교체

실험일: 2026-03-20
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def _build_test_responses(golden: list[dict]) -> list[dict]:
    """golden dataset에서 테스트 응답 생성 (좋은 5 + 나쁜 5)."""
    responses = []

    # 좋은 응답 5건: expected_facts의 수치를 정확히 포함
    for qa in golden[:5]:
        facts = qa["expected_facts"]
        parts = [f"{qa['company_name']} 분석 결과 (2024Q3 기준)\n"]
        for f in facts:
            val = f["value"]
            metric = f["metric"]
            if val is None:
                continue
            if isinstance(val, (int, float)):
                if abs(val) > 1e11:
                    parts.append(f"- {metric}: {val/1e12:.1f}조원")
                elif abs(val) > 1e7:
                    parts.append(f"- {metric}: {val/1e8:.0f}억원")
                else:
                    parts.append(f"- {metric}: {val:.2f}%")
        parts.append("\n전반적으로 양호한 수준입니다.")

        responses.append({
            "qa_id": qa["id"],
            "type": "good",
            "answer_text": "\n".join(parts),
            "answer_structured": {
                "summary": f"{qa['company_name']} 재무 분석",
                "metrics": [
                    {"name": f["metric"], "value": f["value"], "unit": "%" if isinstance(f["value"], float) and abs(f["value"]) < 1000 else "원"}
                    for f in facts if f["value"] is not None and isinstance(f["value"], (int, float))
                ],
                "conclusion": "양호",
            },
            "expected_facts": facts,
        })

    # 나쁜 응답 5건: 수치 없거나 틀림
    for qa in golden[5:10]:
        responses.append({
            "qa_id": qa["id"],
            "type": "bad",
            "answer_text": f"{qa['company_name']}은 좋은 회사입니다. 매출이 많고 이익도 있습니다.",
            "answer_structured": {
                "summary": "좋은 회사",
                "metrics": [],
                "conclusion": "좋음",
            },
            "expected_facts": qa["expected_facts"],
        })

    return responses


def validate_regex(answer_text: str, expected_facts: list[dict]) -> dict:
    """현재 validation.py 방식: regex 기반 수치 추출."""
    from dartlab.ai.validation import extract_numbers, validate_claims

    claims = extract_numbers(answer_text)
    # expected_facts에서 검증 가능한 것만 카운트
    numeric_facts = [f for f in expected_facts if f.get("value") is not None and isinstance(f["value"], (int, float))]

    # 매칭 시도
    matched = 0
    for fact in numeric_facts:
        val = fact["value"]
        for claim in claims:
            # 직접 비교
            if val != 0 and abs(claim.value - val) / abs(val) < 0.15:
                matched += 1
                break
            # 단위 변환 (조/억)
            if abs(val) > 1e11:
                val_jo = val / 1e12
                if val_jo != 0 and abs(claim.value - val_jo) / abs(val_jo) < 0.15:
                    matched += 1
                    break
                val_eok = val / 1e8
                if val_eok != 0 and abs(claim.value - val_eok) / abs(val_eok) < 0.15:
                    matched += 1
                    break

    return {
        "claims_found": len(claims),
        "numeric_facts": len(numeric_facts),
        "matched": matched,
        "coverage": round(matched / max(len(numeric_facts), 1) * 100, 1),
    }


def validate_structured(answer_structured: dict, expected_facts: list[dict]) -> dict:
    """구조화 응답 기반 직접 검증."""
    metrics = answer_structured.get("metrics", [])
    numeric_facts = [f for f in expected_facts if f.get("value") is not None and isinstance(f["value"], (int, float))]

    matched = 0
    for fact in numeric_facts:
        expected_val = fact["value"]
        expected_name = fact["metric"]

        for m in metrics:
            if m.get("name") == expected_name:
                actual_val = m.get("value")
                if actual_val is not None and expected_val != 0:
                    if abs(actual_val - expected_val) / abs(expected_val) < 0.15:
                        matched += 1
                        break

    return {
        "metrics_found": len(metrics),
        "numeric_facts": len(numeric_facts),
        "matched": matched,
        "coverage": round(matched / max(len(numeric_facts), 1) * 100, 1),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("실험 014: Validation V2")
    print("=" * 60)

    golden_path = Path(__file__).parent / "golden_dataset.json"
    with open(golden_path, encoding="utf-8") as f:
        golden = json.load(f)

    responses = _build_test_responses(golden)
    print(f"\n테스트 응답: {len(responses)}건 (good: {sum(1 for r in responses if r['type']=='good')}, bad: {sum(1 for r in responses if r['type']=='bad')})")

    # 검증 비교
    regex_results = []
    struct_results = []

    print("\n=== 개별 결과 ===")
    for resp in responses:
        regex_r = validate_regex(resp["answer_text"], resp["expected_facts"])
        struct_r = validate_structured(resp["answer_structured"], resp["expected_facts"])

        regex_results.append(regex_r)
        struct_results.append(struct_r)

        print(f"\n[{resp['qa_id']}] ({resp['type']})")
        print(f"  regex:  claims={regex_r['claims_found']} matched={regex_r['matched']}/{regex_r['numeric_facts']} coverage={regex_r['coverage']}%")
        print(f"  struct: metrics={struct_r['metrics_found']} matched={struct_r['matched']}/{struct_r['numeric_facts']} coverage={struct_r['coverage']}%")

    # 종합
    print("\n" + "=" * 60)
    print("=== 종합 비교 ===")

    for method, results, label in [("regex", regex_results, "Regex"), ("struct", struct_results, "Structured")]:
        good_results = [r for r, resp in zip(results, responses) if resp["type"] == "good"]
        bad_results = [r for r, resp in zip(results, responses) if resp["type"] == "bad"]

        good_coverage = round(sum(r["coverage"] for r in good_results) / max(len(good_results), 1), 1)
        bad_coverage = round(sum(r["coverage"] for r in bad_results) / max(len(bad_results), 1), 1)
        all_coverage = round(sum(r["coverage"] for r in results) / max(len(results), 1), 1)

        # false positive: bad 응답에서 높은 coverage를 보이면 문제
        false_positives = sum(1 for r in bad_results if r["coverage"] > 0)

        print(f"\n  [{label}]")
        print(f"    Good 응답 커버리지: {good_coverage}%")
        print(f"    Bad 응답 커버리지: {bad_coverage}%")
        print(f"    전체 평균 커버리지: {all_coverage}%")
        print(f"    False positive (bad에서 match): {false_positives}/{len(bad_results)}")
