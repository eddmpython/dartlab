"""실험 105-002: 동반 공시 그래프 (Co-filing Graph)

실험 ID: 105-002
실험명: 같은 날 같은 회사가 제출한 공시의 동반 출현 패턴 분석

목적:
- 동반 공시 패턴에서 기업 이벤트의 인과/절차 관계 추출
- PMI(Pointwise Mutual Information)로 우연 vs 의미 연관 구분
- 그래프 탐색으로 연관 공시 자동 발견

가설:
1. 주주총회결과 + 사외이사선임은 PMI > 3 (강한 연관)
2. 유상증자 + 증권신고서는 절차적 연관
3. 동반 그래프로 검색 확장 가능 ("주총" 검색 → 사외이사, 대표이사 변경도 반환)

방법:
1. (corp_code, rcept_dt) 그룹으로 동반 공시 쌍 추출
2. 쌍별 공동 출현 빈도 계산
3. PMI = log2(P(A,B) / (P(A) * P(B))) 로 연관 강도 측정
4. PMI > 2 인 쌍을 그래프 엣지로 등록

결과:
- 1,660 기업-일자 그룹에서 388개 동반 공시 쌍 추출
- PMI 계산: 140쌍 (coCount >= 2)
- 강한 연관 (PMI > 5): 의결권대리행사↔주총소집공고(7.24), 일괄신고↔투자설명서(6.30, 21회)
- 인과 관계: 최대주주변동↔최대주주변경(4.79), 감사보고서↔사업보고서(4.74)
- 절차 관계: 주주명부폐쇄↔주총소집결의(5.77), 일괄신고↔증권발행실적(5.82)
- 부정 연관 (PMI < 0): 사외이사↔대량보유(-1.63), 기업가치↔임원소유(-2.51)
- 그래프: 30노드, 33엣지 (PMI >= 2.0)
- 문제: 정규화가 과도해서 주요사항보고서(유상증자) 같은 괄호 내용이 소실됨

결론:
- PMI 기반 동반 공시 그래프 구축 가능 확인
- 절차/인과/부정 연관을 구분할 수 있음
- 2일치 데이터로도 의미 있는 패턴 발견 (5년치면 더 강력)
- 정규화 전략 개선 필요: 괄호 내 핵심 키워드 보존
- 채택: 그래프 확장을 검색에 활용 (004에서 통합)

실험일: 2026-03-31
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from itertools import combinations

import polars as pl

import re
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def loadData():
    df26 = pl.read_parquet("data/dart/allFilings/20260326.parquet")
    df27 = pl.read_parquet("data/dart/allFilings/20260327.parquet")
    return pl.concat([df26, df27])


def normalizeReportName(name: str) -> str:
    name = re.sub(r"^\[기재정정\]", "", name).strip()
    name = re.sub(r"^\[첨부정정\]", "", name).strip()
    name = re.sub(r"\s*\(\d{4}\.\d{2}\)\s*$", "", name).strip()
    name = re.sub(r"\(종속회사의주요경영사항\)", "", name).strip()
    name = re.sub(r"\(자회사의\s*주요경영사항\)", "", name).strip()
    name = re.sub(r"\(자율공시\)", "", name).strip()
    name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
    return name.strip()


def buildCofilingPairs(df: pl.DataFrame) -> dict:
    """동반 공시 쌍 빈도 계산."""
    # 기업-일자별 공시 유형 목록
    groups = df.group_by(["corp_code", "rcept_dt"]).agg(
        pl.col("report_nm").unique().alias("types")
    )

    # 정규화된 유형으로 쌍 추출
    pairCounts: Counter = Counter()
    typeCounts: Counter = Counter()
    totalGroups = groups.height

    for row in groups.iter_rows(named=True):
        types = [normalizeReportName(t) for t in row["types"]]
        types = list(set(types))  # 중복 제거
        for t in types:
            typeCounts[t] += 1
        for a, b in combinations(sorted(types), 2):
            pairCounts[(a, b)] += 1

    return pairCounts, typeCounts, totalGroups


def calcPMI(pairCounts, typeCounts, totalGroups) -> list[dict]:
    """PMI 계산 — 우연 대비 얼마나 자주 동반 출현하는지."""
    results = []
    for (a, b), coCount in pairCounts.items():
        if coCount < 2:
            continue
        pA = typeCounts[a] / totalGroups
        pB = typeCounts[b] / totalGroups
        pAB = coCount / totalGroups
        if pA > 0 and pB > 0 and pAB > 0:
            pmi = math.log2(pAB / (pA * pB))
            results.append({
                "typeA": a,
                "typeB": b,
                "coCount": coCount,
                "countA": typeCounts[a],
                "countB": typeCounts[b],
                "pmi": round(pmi, 2),
            })

    results.sort(key=lambda x: x["pmi"], reverse=True)
    return results


def buildGraph(pmiResults, threshold=2.0) -> dict[str, list[dict]]:
    """PMI 기반 그래프 구축."""
    graph: dict[str, list[dict]] = defaultdict(list)
    for r in pmiResults:
        if r["pmi"] >= threshold:
            graph[r["typeA"]].append({"target": r["typeB"], "pmi": r["pmi"], "coCount": r["coCount"]})
            graph[r["typeB"]].append({"target": r["typeA"], "pmi": r["pmi"], "coCount": r["coCount"]})
    return dict(graph)


def expandByGraph(graph: dict, filingType: str, maxDepth: int = 2) -> set[str]:
    """그래프 탐색으로 연관 공시 유형 확장."""
    visited = {filingType}
    frontier = {filingType}

    for _ in range(maxDepth):
        nextFrontier = set()
        for node in frontier:
            for edge in graph.get(node, []):
                if edge["target"] not in visited:
                    visited.add(edge["target"])
                    nextFrontier.add(edge["target"])
        frontier = nextFrontier
        if not frontier:
            break

    return visited


if __name__ == "__main__":
    df = loadData()
    print(f"데이터: {df.height}행\n")

    # 1. 동반 공시 쌍 추출
    pairCounts, typeCounts, totalGroups = buildCofilingPairs(df)
    print(f"기업-일자 그룹: {totalGroups}")
    print(f"동반 공시 쌍: {len(pairCounts)}")
    print(f"고유 유형: {len(typeCounts)}")

    # 2. PMI 계산
    pmiResults = calcPMI(pairCounts, typeCounts, totalGroups)
    print(f"\nPMI 계산 완료: {len(pmiResults)}쌍 (coCount >= 2)")

    # 상위 연관 쌍
    print("\n=== PMI 상위 20 (강한 연관) ===")
    for r in pmiResults[:20]:
        print(f"  PMI={r['pmi']:5.2f} | {r['typeA'][:25]:25s} ↔ {r['typeB'][:25]:25s} (공동 {r['coCount']}회)")

    # 하위 (우연적 공존)
    print("\n=== PMI 하위 5 (약한/부정 연관) ===")
    for r in pmiResults[-5:]:
        print(f"  PMI={r['pmi']:5.2f} | {r['typeA'][:25]:25s} ↔ {r['typeB'][:25]:25s} (공동 {r['coCount']}회)")

    # 3. 그래프 구축
    graph = buildGraph(pmiResults, threshold=2.0)
    print(f"\n=== 그래프 (PMI >= 2.0) ===")
    print(f"노드: {len(graph)}")
    totalEdges = sum(len(edges) for edges in graph.values()) // 2
    print(f"엣지: {totalEdges}")

    # 4. 그래프 확장 테스트
    print("\n=== 그래프 확장 (1-hop) ===")
    testTypes = ["정기주주총회결과", "대표이사변경", "주요사항보고서(유상증자결정)", "주식등의대량보유상황보고서(일반)"]
    for t in testTypes:
        expanded = expandByGraph(graph, t, maxDepth=1)
        expanded.discard(t)
        if expanded:
            print(f'  "{t[:20]}" → {list(expanded)[:5]}')
        else:
            print(f'  "{t[:20]}" → 연관 없음')
