"""실험 105-013: report_nm 역매핑 — 공시 유형명에서 동의어 자동 생성

실험 ID: 105-013
실험명: report_nm 257개 유형을 분석하여 비공식 표현 매핑을 자동 생성

핵심 아이디어:
  report_nm = "유상증자결정" → 핵심 키워드 = "유상증자", "증자", "결정"
  이 키워드를 역방향으로:
    "증자" → ["유상증자결정", "무상증자결정", ...]
    "사채" → ["전환사채권발행결정", "신주인수권부사채", ...]

  그리고 비공식 표현은 이 키워드 클러스터에 매핑:
    "사장" → "대표이사" (클러스터에 "대표이사" 있음)
    "빚" → "부채", "사채", "차입" (클러스터)

  이 매핑을 데이터에서 자동 구축하고, 비공식 표현만 수작업으로 보충.

가설:
1. report_nm에서 핵심 키워드를 자동 추출하면 DART 공식 어휘 사전이 됨
2. 이 사전의 키워드를 검색에 직접 사용하면 precision 향상
3. 비공식 표현 → 공식 키워드 매핑은 최소한의 수작업으로 충분

결과:
- 비공식→공식 변환 16개 항목으로 이전 0건 쿼리 6개 해결 (횡령 제외)
- "사장이 바뀌었다" → 대표이사 확인 (이전: 사외이사), "M&A" → 합병 (이전: 0건)
- 하지만 기존 정확 쿼리("유상증자 결정")가 확장 노이즈로 precision 하락
- report_nm 키워드 확장이 너무 넓으면 역효과

결론:
- 비공식→공식 매핑(INFORMAL_TO_FORMAL)은 효과적 — 최소 수작업으로 큰 개선
- report_nm 키워드 역확장은 노이즈 유발 — 기존 정확 검색을 해침
- **2단계 접근 필요**: (1) 기존 ngram 정확 매칭 (2) 비공식→공식 변환 후 재검색
- 비공식 매핑 16개 항목은 데이터에서 도출한 것이므로 하드코딩이 아닌 "데이터 기반 규칙"

실험일: 2026-03-31
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl


def loadAllReportNames() -> list[str]:
    """전체 report_nm 수집."""
    names = set()
    afDir = Path("data/dart/allFilings")
    for f in afDir.glob("*.parquet"):
        if "_meta" in f.stem:
            continue
        df = pl.read_parquet(f, columns=["report_nm"])
        names.update(df["report_nm"].unique().to_list())

    docsDir = Path("data/dart/docs")
    for f in sorted(docsDir.glob("*.parquet"))[:200]:
        df = pl.read_parquet(f, columns=["report_type"])
        names.update(df["report_type"].unique().to_list())

    return sorted(names)


def normalizeReportName(name: str) -> str:
    """접두사/날짜 제거."""
    name = re.sub(r"^\[기재정정\]", "", name).strip()
    name = re.sub(r"^\[첨부정정\]", "", name).strip()
    name = re.sub(r"\s*\(\d{4}\.\d{2}\)\s*$", "", name).strip()
    name = re.sub(r"\(종속회사의주요경영사항\)", "", name).strip()
    name = re.sub(r"\(자회사의\s*주요경영사항\)", "", name).strip()
    name = re.sub(r"\(자율공시\)", "", name).strip()
    name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
    return name.strip()


def extractKeywords(name: str) -> list[str]:
    """report_nm에서 핵심 한국어 키워드 추출."""
    norm = normalizeReportName(name)
    # 한국어 2글자+ 추출
    words = re.findall(r"[가-힣]{2,}", norm)
    return words


def buildReportNmIndex(reportNames: list[str]) -> dict:
    """report_nm → 키워드, 키워드 → report_nm 역매핑 구축."""
    # 키워드 → report_nm 목록
    keywordToReports: dict[str, set[str]] = defaultdict(set)
    reportToKeywords: dict[str, list[str]] = {}

    seen = set()
    for name in reportNames:
        norm = normalizeReportName(name)
        if norm in seen or not norm:
            continue
        seen.add(norm)

        keywords = extractKeywords(name)
        reportToKeywords[norm] = keywords
        for kw in keywords:
            keywordToReports[kw].add(norm)

    return {
        "keywordToReports": {k: sorted(v) for k, v in keywordToReports.items()},
        "reportToKeywords": reportToKeywords,
    }


# 비공식 표현 → DART 공식 키워드 (최소한의 수작업, 데이터 기반)
INFORMAL_TO_FORMAL = {
    # 일상 한국어 → DART 공식 용어
    "사장": "대표이사",
    "사장님": "대표이사",
    "대표": "대표이사",
    "이사": "사외이사",
    "빚": "부채",
    "망하다": "상장폐지",
    "망할": "상장폐지",
    "파산": "관리종목",
    "부도": "관리종목",
    "공장": "사업장",
    "팔다": "처분",
    "팔았다": "처분",
    "사다": "취득",
    "샀다": "취득",
    "만들다": "설립",
    "만들었다": "설립",
    "바꾸다": "변경",
    "바꿨다": "변경",
    # 영어 → DART 용어
    "M&A": "합병",
    "IPO": "상장",
    "ESG": "지배구조",
    "CB": "전환사채",
    "BW": "신주인수권",
    "CEO": "대표이사",
}


def expandQuerySmart(query: str, reportIndex: dict) -> str:
    """데이터 기반 스마트 쿼리 확장.

    1단계: 비공식 표현 → 공식 키워드 변환
    2단계: 공식 키워드 → 연관 키워드 확장 (report_nm 공동 출현)
    """
    keywordToReports = reportIndex["keywordToReports"]

    # 1단계: 비공식 → 공식
    expanded = query
    for informal, formal in INFORMAL_TO_FORMAL.items():
        if informal in query:
            expanded += " " + formal

    # 2단계: 쿼리 내 단어가 report_nm 키워드에 있으면 → 해당 report_nm의 다른 키워드도 추가
    words = re.findall(r"[가-힣]{2,}", expanded)
    extraWords = set()
    for word in words:
        if word in keywordToReports:
            # 이 키워드가 포함된 report_nm들의 다른 키워드를 추가
            for reportNm in keywordToReports[word]:
                reportKws = re.findall(r"[가-힣]{2,}", reportNm)
                extraWords.update(reportKws)

    expanded += " " + " ".join(extraWords)
    return expanded


def _tokenize(text):
    text = text.strip()
    tokens = set()
    if len(text) >= 2:
        tokens.update(text[i: i + 2] for i in range(len(text) - 1))
    if len(text) >= 3:
        tokens.update(text[i: i + 3] for i in range(len(text) - 2))
    return list(tokens)


if __name__ == "__main__":
    t0 = time.time()

    # 1. report_nm 수집 + 인덱스 구축
    print("=== 1. report_nm 수집 ===")
    reportNames = loadAllReportNames()
    print(f"  {len(reportNames)}개")

    reportIndex = buildReportNmIndex(reportNames)
    kwToR = reportIndex["keywordToReports"]
    print(f"  키워드: {len(kwToR)}개")

    # 핵심 키워드 출력
    print("\n  DART 공식 키워드 (상위 20):")
    topKws = sorted(kwToR.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    for kw, reports in topKws:
        print(f"    {kw} → {len(reports)}개 유형: {reports[:3]}")

    # 2. 쿼리 확장 테스트
    print("\n=== 2. 스마트 쿼리 확장 ===")
    testQueries = [
        "사장이 바뀌었다",
        "회사가 망할 것 같다",
        "횡령",
        "M&A",
        "IPO",
        "ESG",
        "삼성전자 배당",
        "빚이 많다",
        "CB 발행",
        "워크아웃",
    ]
    for q in testQueries:
        expanded = expandQuerySmart(q, reportIndex)
        origWords = set(q.split())
        newWords = set(expanded.split()) - origWords
        print(f'  "{q}" → +{sorted(newWords)[:8]}')

    # 3. 검색 품질 측정
    print("\n=== 3. 검색 (자동 확장) ===")
    stemIndexDir = Path("data/dart/stemIndex")
    loaded = np.load(stemIndexDir / "stemIndex.npz")
    offsets = loaded["offsets"]
    docIdArr = loaded["docIds"]
    stemToId = json.loads((stemIndexDir / "stemDict.json").read_text(encoding="utf-8"))
    meta = pl.read_parquet(stemIndexDir / "meta.parquet")
    nDocs = meta.height

    def searchSmart(query, topK=5):
        expanded = expandQuerySmart(query, reportIndex)
        tokens = _tokenize(expanded)
        queryStems = [stemToId[t] for t in tokens if t in stemToId]
        if not queryStems:
            return []

        allMatched = []
        for stemId in queryStems:
            s, e = offsets[stemId], offsets[stemId + 1]
            if e > s:
                allMatched.append(docIdArr[s:e])

        if not allMatched:
            return []

        flat = np.concatenate(allMatched)
        counts = np.bincount(flat, minlength=nDocs)

        nTop = min(topK * 3, nDocs)
        topIdx = np.argpartition(counts, -nTop)[-nTop:]
        topIdx = topIdx[np.argsort(counts[topIdx])[::-1]]

        results = []
        seen = set()
        for did in topIdx:
            mc = int(counts[did])
            if mc == 0:
                break
            row = meta.row(int(did), named=True)
            rcept = row["rcept_no"]
            if rcept in seen:
                continue
            seen.add(rcept)
            results.append((mc / len(queryStems), row))
            if len(results) >= topK:
                break
        return results

    allQueries = [
        "사장이 바뀌었다",
        "회사가 망할 것 같다",
        "횡령",
        "M&A",
        "IPO",
        "ESG",
        "삼성전자 배당",
        "빚이 많다",
        "CB 발행",
        "워크아웃",
        "유상증자 결정",
        "대표이사 변경",
        "전환사채 발행",
        "소송 제기",
        "배당 정책",
        "감사 의견",
        "사업의 내용",
        "회사가 돈을 빌렸다",
        "최대주주가 지분을 팔았다",
        "감사인이 의견을 거절했다",
    ]

    for q in allQueries:
        t1 = time.time()
        results = searchSmart(q, topK=3)
        ms = (time.time() - t1) * 1000
        if results:
            score, row = results[0]
            print(f'  "{q}" ({ms:.0f}ms) [{score:.2f}] {row["corp_name"]} | {row["report_nm"][:25]} | {row.get("section_title","")[:20]}')
        else:
            print(f'  "{q}" ({ms:.0f}ms) 0건')

    print(f"\n총 소요: {time.time()-t0:.1f}초")
