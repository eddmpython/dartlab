"""실험 ID: 005
실험명: 기업간 비교 뷰어/API 소비 기획

목적:
- 001-004 결과를 종합하여 비교 뷰어의 데이터 구조 설계
- 실제 두 회사 데이터로 mock payload 생성 + 크기 측정
- 서버 엔드포인트 + UI 컴포넌트 설계안 도출

가설:
1. 비교 payload < 500KB (JSON)
2. 서버 엔드포인트 3-5개로 충분
3. UI 컴포넌트 4-5개로 비교 뷰어 구성 가능

방법:
1. 삼성전자/SK하이닉스로 통합 비교 dict 구성
2. JSON 직렬화 크기 측정
3. 서버/UI 설계안을 코드 내 dict로 기록

결과:
- payload 크기: 5.6 KB (목표 500KB의 1.1% — 극도로 가벼움)
- ratioSummary: 34개 항목 side-by-side (2024Q4 기준)
- topicCoverage: 공통 46 topic, Jaccard 0.979
- topicDetails: 5개 핵심 topic 텍스트/키워드 요약
- 엔드포인트 3개, UI 컴포넌트 4개로 비교 뷰어 구성 가능

결론:
- 가설 1 채택 — payload 5.6KB << 500KB
- 가설 2 채택 — 엔드포인트 3개로 충분 (overview/finance/topic)
- 가설 3 채택 — UI 4개 컴포넌트로 비교 뷰어 구성 가능
- **핵심 발견**: 비교 기능은 기존 Company API 위에 얇은 래퍼만으로 구현 가능
  새로운 데이터 구조나 무거운 연산 불필요. ratio 100% 호환, topic 92%+ 호환.

실험일: 2026-03-19

=== 서버 엔드포인트 설계안 ===

1. GET /api/compare/{codeA}/{codeB}/overview
   → {pairMeta, topicCoverage, ratioSummary}
   목적: 비교 랜딩 — 두 회사 기본 정보 + topic Jaccard + 핵심 ratio 차이

2. GET /api/compare/{codeA}/{codeB}/finance?period=2024Q4
   → {ratios: [{항목, 분류, valA, valB, diff}], bs/is/cf: side-by-side}
   목적: 재무 비교 탭 — ratio 테이블 + BS/IS/CF 핵심 계정

3. GET /api/compare/{codeA}/{codeB}/topic/{topic}
   → {textSummary: {lenA, lenB, keywords}, tableItems: {common, onlyA, onlyB}}
   목적: topic 상세 비교 — 텍스트 키워드 + 테이블 항목 교집합

=== UI 컴포넌트 설계안 ===

CompareViewer.svelte (메인 레이아웃)
├── CompareHeader.svelte — 두 회사 이름/코드/업종 + Jaccard 배지
├── CompareFinance.svelte — ratio 비교표 + 차트 (bar chart side-by-side)
├── CompareTopicGrid.svelte — topic coverage 그리드 (공통/고유 시각화)
└── CompareTopicDetail.svelte — 선택한 topic의 텍스트/테이블 비교

"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab import Company

_WORD_RE = re.compile(r"[가-힣]{2,}")


def buildComparePayload(codeA: str, codeB: str) -> dict:
    """두 회사의 비교 payload 생성."""
    cA = Company(codeA)
    cB = Company(codeB)
    nameA = cA.name if hasattr(cA, "name") else codeA
    nameB = cB.name if hasattr(cB, "name") else codeB

    # 1. pairMeta
    pairMeta = {
        "codeA": codeA,
        "codeB": codeB,
        "nameA": nameA,
        "nameB": nameB,
    }

    # 2. topicCoverage
    topicsA = set(cA.topics["topic"].to_list())
    topicsB = set(cB.topics["topic"].to_list())
    common = sorted(topicsA & topicsB)
    onlyA = sorted(topicsA - topicsB)
    onlyB = sorted(topicsB - topicsA)
    jac = len(topicsA & topicsB) / len(topicsA | topicsB) if (topicsA | topicsB) else 0

    topicCoverage = {
        "jaccard": round(jac, 3),
        "common": common,
        "onlyA": onlyA,
        "onlyB": onlyB,
        "countA": len(topicsA),
        "countB": len(topicsB),
    }

    # 3. ratioSummary — 최신 연간 ratio 나란히
    rA = cA.ratios
    rB = cB.ratios
    ratioRows = []
    if rA is not None and rB is not None:
        periods = sorted(
            set(rA.columns[2:]) & set(rB.columns[2:]),
            reverse=True,
        )
        annuals = [p for p in periods if p.endswith("Q4")]
        period = annuals[0] if annuals else (periods[0] if periods else None)

        if period:
            itemsA = set(rA["항목"].to_list())
            itemsB = set(rB["항목"].to_list())
            for item in sorted(itemsA & itemsB):
                rowA = rA.filter(pl.col("항목") == item)
                rowB = rB.filter(pl.col("항목") == item)
                if rowA.is_empty() or rowB.is_empty():
                    continue
                if period not in rowA.columns:
                    continue
                vA = rowA[period][0]
                vB = rowB[period][0]
                if vA is None or vB is None:
                    continue
                cat = rowA["분류"][0]
                ratioRows.append({
                    "category": cat,
                    "item": item,
                    "valA": round(vA, 2),
                    "valB": round(vB, 2),
                    "diff": round(vB - vA, 2),
                })

    ratioSummary = {
        "period": period if rA is not None else None,
        "rows": ratioRows,
    }

    # 4. topicDetails — 핵심 topic별 텍스트/테이블 요약
    focusTopics = ["companyOverview", "businessOverview", "employee", "dividend", "riskDerivative"]
    topicDetails = []

    for topic in focusTopics:
        if topic not in common:
            continue

        # 텍스트 요약
        sec = cA.sections
        secB_obj = cB.sections
        rawA = sec.raw if hasattr(sec, "raw") else sec
        rawB = secB_obj.raw if hasattr(secB_obj, "raw") else secB_obj

        periodCols = [c for c in rawA.columns if re.match(r"\d{4}(Q[1-4])?$", c)]
        annuals = sorted([p for p in periodCols if p.endswith("Q4")], reverse=True)
        latestP = annuals[0] if annuals else (periodCols[0] if periodCols else None)

        textA = ""
        textB = ""
        if latestP:
            tRowsA = rawA.filter((pl.col("topic") == topic) & (pl.col("blockType") == "text"))
            if not tRowsA.is_empty() and latestP in tRowsA.columns:
                texts = tRowsA[latestP].to_list()
                textA = "\n".join(str(t) for t in texts if t is not None)

            tRowsB = rawB.filter((pl.col("topic") == topic) & (pl.col("blockType") == "text"))
            if not tRowsB.is_empty() and latestP in tRowsB.columns:
                texts = tRowsB[latestP].to_list()
                textB = "\n".join(str(t) for t in texts if t is not None)

        # 키워드
        kwA = Counter(_WORD_RE.findall(textA))
        kwB = Counter(_WORD_RE.findall(textB))
        commonKW = sorted(set(kwA) & set(kwB), key=lambda w: kwA[w] + kwB[w], reverse=True)[:10]

        topicDetails.append({
            "topic": topic,
            "textLenA": len(textA),
            "textLenB": len(textB),
            "commonKeywords": commonKW,
        })

    payload = {
        "pairMeta": pairMeta,
        "topicCoverage": topicCoverage,
        "ratioSummary": ratioSummary,
        "topicDetails": topicDetails,
    }

    return payload


def viewerDesign():
    print("=" * 70)
    print("005 — 기업간 비교 뷰어/API 소비 기획")
    print("=" * 70)

    payload = buildComparePayload("005930", "000660")

    # JSON 크기 측정
    jsonStr = json.dumps(payload, ensure_ascii=False)
    sizeKB = len(jsonStr.encode("utf-8")) / 1024

    print(f"\n--- payload 크기 ---")
    print(f"  JSON: {sizeKB:.1f} KB")
    print(f"  ratioSummary rows: {len(payload['ratioSummary']['rows'])}")
    print(f"  topicDetails: {len(payload['topicDetails'])} topics")
    print(f"  topicCoverage: common={len(payload['topicCoverage']['common'])}")

    # payload 구조 요약
    print(f"\n--- payload 구조 ---")
    for key, val in payload.items():
        if isinstance(val, dict):
            subkeys = list(val.keys())
            print(f"  {key}: {subkeys}")
        elif isinstance(val, list):
            print(f"  {key}: [{len(val)} items]")

    # ratioSummary 샘플
    print(f"\n--- ratioSummary 샘플 (기간: {payload['ratioSummary']['period']}) ---")
    for row in payload["ratioSummary"]["rows"][:10]:
        sign = "+" if row["diff"] >= 0 else ""
        print(f"  {row['category']:<8} {row['item']:<20} A={row['valA']:>12} B={row['valB']:>12} diff={sign}{row['diff']}")

    # topicDetails 샘플
    print(f"\n--- topicDetails 샘플 ---")
    for td in payload["topicDetails"]:
        print(f"  {td['topic']}: textLen A={td['textLenA']:,} B={td['textLenB']:,}, 공통KW={td['commonKeywords'][:5]}")

    # 설계 요약
    print(f"\n{'='*70}")
    print("설계 요약")
    print(f"{'='*70}")
    print(f"""
엔드포인트 3개:
  1. GET /api/compare/{{codeA}}/{{codeB}}/overview
     → pairMeta + topicCoverage + ratioSummary (핵심 ratio 5개)
     용도: 비교 랜딩 페이지

  2. GET /api/compare/{{codeA}}/{{codeB}}/finance?period=YYYYQN
     → 전체 ratio side-by-side + BS/IS/CF 핵심 계정
     용도: 재무 비교 탭

  3. GET /api/compare/{{codeA}}/{{codeB}}/topic/{{topic}}
     → 텍스트 요약(길이, 키워드) + 테이블 항목 교집합
     용도: topic 상세 비교

UI 컴포넌트 4개:
  1. CompareHeader — 두 회사 이름/코드 + Jaccard 배지
  2. CompareFinance — ratio 비교표 + 차이 시각화
  3. CompareTopicGrid — topic coverage (공통=초록, 고유=회색)
  4. CompareTopicDetail — 선택 topic 텍스트/테이블 비교

payload 크기: {sizeKB:.1f} KB (목표 500KB 이하 ✓)
""")


if __name__ == "__main__":
    viewerDesign()
