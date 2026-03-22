"""실험 ID: 001
실험명: sections topic coverage 기업간 비교

목적:
- 두 회사의 topic 집합이 얼마나 겹치는지 정량화
- 업종/규모/관계별로 topic 교집합율 차이 확인
- 기업간 비교의 기초 데이터 확보

가설:
1. 동종 대기업(삼성전자 vs SK하이닉스) topic Jaccard 유사도 80%+
2. 이업종(삼성전자 vs 현대차) topic Jaccard 유사도 60%+
3. 대기업이 중소기업보다 topic 수 30%+ 더 많음

방법:
1. 4쌍 Company 로드
2. c.topics DataFrame에서 topic 리스트 추출
3. Jaccard 유사도 = |A ∩ B| / |A ∪ B|
4. 공통/고유 topic 분류
5. chapter별 coverage 비교

결과:
- 4쌍 Jaccard 유사도:
  동종대기업(삼성전자/SK하이닉스): 0.979 (47/46 topics, 공통 46)
  대/중소(삼성전자/동화약품):      0.936 (47/44 topics, 공통 44)
  관계회사(삼성전자/삼성SDI):      0.979 (47/46 topics, 공통 46)
  이업종(삼성전자/현대차):         0.920 (47/49 topics, 공통 46)
- finance/report topic은 모든 쌍에서 Jaccard 1.000 (완전 일치)
- docs topic만 0.909~0.976 (회사 특화 topic 1~3개 차이)
- 고유 topic: rndDetail(삼성전자), disclosureChanges(삼성전자),
  businessStatus/financialSoundnessOtherReference/operatingFacilities(현대차)
- 서울반도체(046890)는 docs 데이터 미보유 → 동화약품(000020)으로 교체

결론:
- 가설 1 채택 (동종 0.979 >> 80%)
- 가설 2 채택 (이업종 0.920 >> 60%)
- 가설 3 기각 — 대/중소 topic 수 차이 6.4%뿐 (47 vs 44), 30% 미만
- **핵심 발견**: sections의 topic 매핑이 잘 되어 있어 업종/규모 불문하고
  Jaccard 0.92+ — 기업간 비교의 topic alignment는 사실상 해결된 문제
- finance/report는 모든 회사에서 동일 topic → 비교 인프라 완비
- 차이는 docs 영역의 회사 특화 topic 1~3개뿐

실험일: 2026-03-19
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company

PAIRS = [
    ("005930", "000660", "동종대기업(삼성전자/SK하이닉스)"),
    ("005930", "000020", "대/중소(삼성전자/동화약품)"),
    ("005930", "006400", "관계회사(삼성전자/삼성SDI)"),
    ("005930", "005380", "이업종(삼성전자/현대차)"),
]


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def topicCoverage():
    print("=" * 70)
    print("001 — topic coverage 기업간 비교")
    print("=" * 70)

    results = []
    for codeA, codeB, label in PAIRS:
        cA = Company(codeA)
        cB = Company(codeB)
        nameA = cA.name if hasattr(cA, "name") else codeA
        nameB = cB.name if hasattr(cB, "name") else codeB

        topicsA = set(cA.topics["topic"].to_list())
        topicsB = set(cB.topics["topic"].to_list())

        common = topicsA & topicsB
        onlyA = topicsA - topicsB
        onlyB = topicsB - topicsA
        jac = jaccard(topicsA, topicsB)

        results.append({
            "label": label,
            "nameA": nameA,
            "nameB": nameB,
            "topicsA": len(topicsA),
            "topicsB": len(topicsB),
            "common": len(common),
            "onlyA": len(onlyA),
            "onlyB": len(onlyB),
            "jaccard": jac,
            "commonTopics": sorted(common),
            "onlyATopics": sorted(onlyA),
            "onlyBTopics": sorted(onlyB),
        })

        print(f"\n--- {label} ---")
        print(f"  {nameA}: {len(topicsA)} topics")
        print(f"  {nameB}: {len(topicsB)} topics")
        print(f"  공통: {len(common)}, A만: {len(onlyA)}, B만: {len(onlyB)}")
        print(f"  Jaccard: {jac:.3f}")
        if onlyA:
            print(f"  {nameA}만: {sorted(onlyA)}")
        if onlyB:
            print(f"  {nameB}만: {sorted(onlyB)}")

    # 요약 테이블
    print("\n" + "=" * 70)
    print("요약")
    print("=" * 70)
    print(f"{'쌍':<35} {'A':>4} {'B':>4} {'공통':>4} {'A만':>4} {'B만':>4} {'Jaccard':>8}")
    for r in results:
        print(
            f"{r['label']:<35} {r['topicsA']:>4} {r['topicsB']:>4} "
            f"{r['common']:>4} {r['onlyA']:>4} {r['onlyB']:>4} {r['jaccard']:>8.3f}"
        )

    # source별 분석 (docs/finance/report)
    print("\n" + "=" * 70)
    print("source별 topic 분포 비교")
    print("=" * 70)
    for codeA, codeB, label in PAIRS:
        cA = Company(codeA)
        cB = Company(codeB)
        nameA = cA.name if hasattr(cA, "name") else codeA
        nameB = cB.name if hasattr(cB, "name") else codeB
        tA = cA.topics
        tB = cB.topics

        if tA.is_empty() or tB.is_empty():
            print(f"\n--- {label} --- (skip: topics 없음)")
            continue

        print(f"\n--- {label} ---")
        for src in ["docs", "finance", "report"]:
            sA = set(
                tA.filter(tA["source"].cast(str).str.contains(src))["topic"].to_list()
            )
            sB = set(
                tB.filter(tB["source"].cast(str).str.contains(src))["topic"].to_list()
            )
            if sA or sB:
                jac = jaccard(sA, sB)
                print(f"  {src}: {nameA}={len(sA)}, {nameB}={len(sB)}, 공통={len(sA&sB)}, Jaccard={jac:.3f}")

    return results


if __name__ == "__main__":
    topicCoverage()
