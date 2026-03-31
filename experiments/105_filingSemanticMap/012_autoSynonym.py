"""실험 105-012: 데이터 기반 자동 동의어 추출 + 역방향 매핑

실험 ID: 105-012
실험명: report_nm + section_title에서 동의어 테이블을 자동 구축

목적:
- 하드코딩 동의어를 제거하고 데이터에서 자동 학습
- report_nm 257개 유형에서 키워드 클러스터를 추출 → 역방향 매핑
- 자연어 → 공시 용어 변환을 데이터가 정의

핵심 아이디어:
  report_nm에 나타나는 모든 단어를 추출하면 DART의 공식 어휘가 된다.
  이 어휘의 공동 출현 패턴이 동의어 관계를 정의한다.
  "유상증자결정" → {"유상", "증자", "결정"} → 이 단어 중 하나만 쿼리해도 나머지로 확장.

방법:
1. 전체 report_nm에서 한국어 단어(2글자+) 추출
2. 같은 report_nm에 공동 출현하는 단어 쌍 → 연관 관계
3. 단어 → [연관 단어들] 역방향 매핑 자동 구축
4. 이 매핑으로 쿼리 확장 → 검색 품질 측정
5. 기존 하드코딩 SYNONYMS 대비 비교

결과:
(실험 후 작성)

결론:
(실험 후 작성)

실험일: 2026-03-31
"""

from __future__ import annotations

import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import polars as pl


def loadAllReportNames() -> list[str]:
    """allFilings + docs에서 모든 report_nm/report_type 수집."""
    names = set()

    # allFilings
    afDir = Path("data/dart/allFilings")
    for f in afDir.glob("*.parquet"):
        if "_meta" in f.stem:
            continue
        df = pl.read_parquet(f, columns=["report_nm"])
        names.update(df["report_nm"].unique().to_list())

    # docs (50종목 샘플)
    docsDir = Path("data/dart/docs")
    for f in sorted(docsDir.glob("*.parquet"))[:50]:
        df = pl.read_parquet(f, columns=["report_type"])
        names.update(df["report_type"].unique().to_list())

    return list(names)


def loadAllSectionTitles() -> list[str]:
    """section_title 수집."""
    titles = set()

    afDir = Path("data/dart/allFilings")
    for f in afDir.glob("*.parquet"):
        if "_meta" in f.stem:
            continue
        df = pl.read_parquet(f, columns=["section_title"])
        titles.update(df["section_title"].drop_nulls().unique().to_list())

    docsDir = Path("data/dart/docs")
    for f in sorted(docsDir.glob("*.parquet"))[:50]:
        df = pl.read_parquet(f, columns=["section_title"])
        titles.update(df["section_title"].drop_nulls().unique().to_list())

    return list(titles)


def extractWords(text: str) -> list[str]:
    """텍스트에서 한국어 2글자+ 단어 추출."""
    # 접두사 제거
    text = re.sub(r"^\[기재정정\]", "", text)
    text = re.sub(r"^\[첨부정정\]", "", text)
    text = re.sub(r"\(\d{4}\.\d{2}\)", "", text)
    text = re.sub(r"\(종속회사의주요경영사항\)", "", text)
    text = re.sub(r"\(자율공시\)", "", text)
    text = re.sub(r"\(자회사의\s*주요경영사항\)", "", text)

    # 한국어 단어 추출
    words = re.findall(r"[가-힣]{2,}", text)
    return words


def buildAutoSynonyms(reportNames: list[str], sectionTitles: list[str]) -> dict[str, list[str]]:
    """report_nm + section_title에서 자동 동의어 매핑 구축.

    같은 report_nm/section_title에 공동 출현하는 단어들은 의미적 연관.
    """
    # 단어별 출현 문서 set
    wordDocs: dict[str, set[int]] = defaultdict(set)
    # 단어쌍 공동 출현
    pairCount: Counter = Counter()

    allTexts = reportNames + sectionTitles

    for docId, text in enumerate(allTexts):
        words = list(set(extractWords(text)))  # 중복 제거
        for w in words:
            wordDocs[w].add(docId)
        # 쌍
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                a, b = tuple(sorted([words[i], words[j]]))
                pairCount[(a, b)] += 1

    # 연관 매핑: 같은 문맥에 3회+ 공동 출현한 단어 → 연관
    synonymMap: dict[str, set[str]] = defaultdict(set)
    for (a, b), count in pairCount.items():
        if count >= 2:
            synonymMap[a].add(b)
            synonymMap[b].add(a)

    # dict로 변환
    return {word: sorted(related) for word, related in synonymMap.items() if len(related) >= 1}


def expandQueryAuto(query: str, synonymMap: dict[str, list[str]]) -> str:
    """자동 동의어 매핑으로 쿼리 확장."""
    words = extractWords(query)
    expanded = set(query.split())

    for word in words:
        if word in synonymMap:
            expanded.update(synonymMap[word])
        # 부분 매칭도 시도 (2글자 이상)
        for key in synonymMap:
            if len(word) >= 2 and word in key:
                expanded.update(synonymMap[key])

    return " ".join(expanded)


# ── 검색 (autoSynonym 적용) ──

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

    # 1. 데이터 수집
    print("=== 1. report_nm + section_title 수집 ===")
    reportNames = loadAllReportNames()
    sectionTitles = loadAllSectionTitles()
    print(f"  report_nm: {len(reportNames)}개, section_title: {len(sectionTitles)}개")

    # 2. 자동 동의어 구축
    print("\n=== 2. 자동 동의어 구축 ===")
    synonymMap = buildAutoSynonyms(reportNames, sectionTitles)
    print(f"  매핑된 단어: {len(synonymMap)}개")

    # 샘플 출력
    sampleWords = ["유상증자", "대표이사", "배당", "소송", "합병", "감사", "사채", "주주총회",
                   "상장폐지", "횡령", "워크아웃", "지배구조", "자기주식", "사업보고서"]
    print("\n  주요 단어 연관:")
    for w in sampleWords:
        if w in synonymMap:
            print(f"    {w} → {synonymMap[w][:8]}")
        else:
            print(f"    {w} → (없음)")

    # 3. 쿼리 확장 테스트
    print("\n=== 3. 쿼리 확장 테스트 ===")
    testQueries = [
        "사장이 바뀌었다",
        "회사가 망할 것 같다",
        "돈이 없다",
        "횡령",
        "워크아웃",
        "상장폐지",
        "M&A",
        "IPO",
        "ESG",
        "삼성전자 배당",
        "빚이 많다",
        "주가가 떨어졌다",
    ]
    for q in testQueries:
        expanded = expandQueryAuto(q, synonymMap)
        # 원본 대비 추가된 단어만
        origWords = set(q.split())
        newWords = set(expanded.split()) - origWords
        print(f'  "{q}" → +{list(newWords)[:6]}')

    elapsed = time.time() - t0
    print(f"\n총 소요: {elapsed:.1f}초")

    # 4. 검색 품질 측정 (자동 동의어 vs 하드코딩)
    print("\n=== 4. 자동 동의어로 검색 ===")

    # stemIndex 로드
    import json
    stemIndexDir = Path("data/dart/stemIndex")
    loaded = np.load(stemIndexDir / "stemIndex.npz")
    offsets = loaded["offsets"]
    docIds = loaded["docIds"]
    stemToId = json.loads((stemIndexDir / "stemDict.json").read_text(encoding="utf-8"))
    meta = pl.read_parquet(stemIndexDir / "meta.parquet")
    nDocs = meta.height

    def searchWithAutoSynonym(query, topK=5):
        expanded = expandQueryAuto(query, synonymMap)
        tokens = _tokenize(expanded)
        queryStems = [stemToId[t] for t in tokens if t in stemToId]
        if not queryStems:
            return []

        allMatched = []
        for stemId in queryStems:
            start = offsets[stemId]
            end = offsets[stemId + 1]
            if end > start:
                allMatched.append(docIds[start:end])

        if not allMatched:
            return []

        flat = np.concatenate(allMatched)
        counts = np.bincount(flat, minlength=nDocs)

        nTop = min(topK * 3, nDocs)
        topIndices = np.argpartition(counts, -nTop)[-nTop:]
        topIndices = topIndices[np.argsort(counts[topIndices])[::-1]]

        results = []
        seen = set()
        for docId in topIndices:
            mc = int(counts[docId])
            if mc == 0:
                break
            row = meta.row(int(docId), named=True)
            rcept = row["rcept_no"]
            if rcept in seen:
                continue
            seen.add(rcept)
            results.append((mc / len(queryStems), row))
            if len(results) >= topK:
                break
        return results

    for q in testQueries:
        t1 = time.time()
        results = searchWithAutoSynonym(q, topK=3)
        ms = (time.time() - t1) * 1000
        if results:
            score, row = results[0]
            print(f'  "{q}" ({ms:.0f}ms) [{score:.2f}] {row["corp_name"]} | {row["report_nm"][:30]} | {row.get("section_title","")[:20]}')
        else:
            print(f'  "{q}" ({ms:.0f}ms) 0건')
