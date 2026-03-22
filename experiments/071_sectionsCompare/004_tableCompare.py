"""실험 ID: 004
실험명: 수평화 테이블 항목 기업간 교집합 비교

목적:
- 같은 topic의 수평화된 table block이 기업간에 항목 교집합이 있는지 검증
- 특히 report source (수평화 완료)와 finance source (완전 표준화)에서의 비교 가능성

가설:
1. report source (dividend, employee 등) 항목 교집합율 70%+
2. finance source (BS/IS/CF) 핵심 계정 교집합율 100%
3. docs source table은 회사마다 항목명 다름 → 교집합 낮음 (< 30%)

방법:
1. 삼성전자/SK하이닉스 2개 Company 로드
2. 공통 topic에서 table block 추출 (show 목차에서 type='table' 필터)
3. report/finance source 블록의 항목(첫 컬럼) 교집합 Jaccard 측정
4. docs source table도 항목 추출 시도

결과:
- source별 평균 Jaccard:
  finance: 0.469 (6개 topic) — BS 0.468, IS 0.562, CF 0.264
  report: 0.298 (5개 topic) — dividend 1.000, employee 0.333, majorHolder 0.103
  docs: 0.059 (39개 topic) — 대부분 0.000, shareCapital 0.889 예외

- finance 핵심 계정: BS 36/77 공통, IS 27/48 공통, CF 29/110 공통
  세부 계정명은 회사마다 다르나, 핵심 집계 계정은 모두 존재
- report dividend: 2/2 항목 완전 일치 (현금배당수익률, 주당현금배당금)
- docs shareCapital: 8/9 항목 교집합 (정형화된 양식)
- docs 대부분: 회사마다 테이블 구조/항목명이 완전히 다름 → Jaccard 0

결론:
- 가설 1 부분 채택 — report dividend 100%, employee/majorHolder는 낮음 (0.10~0.33)
  report는 topic별 편차 큼
- 가설 2 부분 채택 — finance 핵심 집계 계정은 100% 존재하나,
  세부 계정 Jaccard는 0.23~0.56 (회사별 XBRL 계정 차이)
- 가설 3 채택 — docs table Jaccard 평균 0.059, 대부분 0.000
- **핵심 발견**:
  1. 기업간 수치 비교는 finance(ratios) + report(dividend) 중심이 현실적
  2. docs table은 원본 markdown이라 항목명 정규화 없이는 비교 불가
  3. shareCapital은 표준 양식이라 예외적으로 높은 교집합 (0.889)
  4. ratios가 Jaccard 1.000 — 비교 뷰어의 핵심 데이터 소스

실험일: 2026-03-19
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab import Company


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def getTableItems(company: "Company", topic: str, blockIdx: int) -> tuple[str, set]:
    """show(topic, blockIdx)에서 항목 set 추출. (source, items) 반환."""
    toc = company.show(topic)
    if toc is None:
        return ("", set())

    row = toc.filter(pl.col("block") == blockIdx)
    if row.is_empty():
        return ("", set())

    source = row["source"][0]
    data = company.show(topic, blockIdx)
    if data is None:
        return (source, set())

    # 첫 컬럼이 항목명
    if hasattr(data, "columns") and len(data.columns) > 0:
        firstCol = data.columns[0]
        items = set(data[firstCol].drop_nulls().to_list())
        return (source, items)

    return (source, set())


def tableCompare():
    print("=" * 70)
    print("004 — 수평화 테이블 항목 기업간 교집합 비교")
    print("=" * 70)

    cA = Company("005930")
    cB = Company("000660")
    nameA = cA.name if hasattr(cA, "name") else "005930"
    nameB = cB.name if hasattr(cB, "name") else "000660"

    # 공통 topic 찾기
    topicsA = set(cA.topics["topic"].to_list())
    topicsB = set(cB.topics["topic"].to_list())
    commonTopics = sorted(topicsA & topicsB)

    print(f"\n{nameA} vs {nameB}: 공통 topic {len(commonTopics)}개")

    results = []

    # finance topic은 show()가 바로 데이터를 반환하므로 별도 처리
    financeTops = {"BS", "IS", "CIS", "CF", "SCE", "ratios"}

    for topic in commonTopics:
        tocA = cA.show(topic)
        tocB = cB.show(topic)
        if tocA is None or tocB is None:
            continue

        # finance topic: show()가 바로 DataFrame
        if topic in financeTops:
            if "block" not in tocA.columns:
                # 직접 데이터 DataFrame
                firstColA = tocA.columns[0]
                firstColB = tocB.columns[0] if "block" not in tocB.columns else None
                if firstColB is None:
                    continue
                itemsA = set(tocA[firstColA].drop_nulls().to_list())
                itemsB = set(tocB[firstColB].drop_nulls().to_list())
                common = itemsA & itemsB
                jac = jaccard(itemsA, itemsB)
                results.append({
                    "topic": topic,
                    "source": "finance",
                    "itemsA": len(itemsA),
                    "itemsB": len(itemsB),
                    "common": len(common),
                    "jaccard": jac,
                    "commonItems": sorted(common)[:10],
                })
                continue

        # 일반 topic: show() 목차
        if "type" not in tocA.columns:
            continue

        tablesA = tocA.filter(pl.col("type") == "table")
        tablesB = tocB.filter(pl.col("type") == "table")

        if tablesA.is_empty() or tablesB.is_empty():
            continue

        # source별 분류
        for source in ["report", "docs"]:
            srcBlocksA = tablesA.filter(pl.col("source") == source)
            srcBlocksB = tablesB.filter(pl.col("source") == source)

            if srcBlocksA.is_empty() or srcBlocksB.is_empty():
                continue

            # 각 source의 첫 번째 table block 비교
            idxA = srcBlocksA["block"][0]
            idxB = srcBlocksB["block"][0]

            srcA, itemsA = getTableItems(cA, topic, idxA)
            srcB, itemsB = getTableItems(cB, topic, idxB)

            if not itemsA and not itemsB:
                continue

            common = itemsA & itemsB
            jac = jaccard(itemsA, itemsB)

            results.append({
                "topic": topic,
                "source": source,
                "itemsA": len(itemsA),
                "itemsB": len(itemsB),
                "common": len(common),
                "jaccard": jac,
                "commonItems": sorted(common)[:10],
            })

    # 결과 출력
    print(f"\n{'topic':<25} {'source':<8} {'A':>5} {'B':>5} {'공통':>5} {'Jaccard':>8}")
    print("-" * 60)

    for r in results:
        print(
            f"{r['topic']:<25} {r['source']:<8} {r['itemsA']:>5} {r['itemsB']:>5} "
            f"{r['common']:>5} {r['jaccard']:>8.3f}"
        )
        if r["commonItems"]:
            print(f"  → 공통 항목: {r['commonItems']}")

    # source별 요약
    print(f"\n{'='*60}")
    print("source별 평균 Jaccard")
    for src in ["finance", "report", "docs"]:
        srcResults = [r for r in results if r["source"] == src]
        if srcResults:
            avgJac = sum(r["jaccard"] for r in srcResults) / len(srcResults)
            count = len(srcResults)
            print(f"  {src}: 평균 Jaccard={avgJac:.3f} ({count}개 topic)")


if __name__ == "__main__":
    tableCompare()
