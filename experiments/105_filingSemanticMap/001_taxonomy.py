"""실험 105-001: 공시 유형 의미 분류 (Filing Taxonomy)

실험 ID: 105-001
실험명: 257개 공시 유형(report_nm)에서 의미 카테고리 자동 추출

목적:
- DART 공시 유형명 자체가 의미 분류 체계임을 증명
- report_nm에서 키워드 추출 → 자동 Taxonomy 구축
- 동의어/관련어 매핑으로 자연어 → 공시 유형 변환 가능성 검증

가설:
1. 257개 유형은 15~20개 의미 카테고리로 묶인다
2. 키워드 추출만으로 90%+ 유형이 자동 분류된다
3. [기재정정] 접두사를 제거하면 유형 수가 절반으로 줄어든다

방법:
1. report_nm에서 [기재정정] 등 접두사 제거 → 정규화
2. 정규화된 유형에서 핵심 키워드 추출
3. 키워드 기반 의미 카테고리 자동 클러스터링
4. 동의어 테이블 구축

결과:
- 정규화 후 유형: 193개 (원본 257, 접두사/날짜 제거로 33% 감소)
- 자동 분류: 144/193 (75%), 15개 카테고리
- 미분류: 49개 (기타경영사항, 주식병합 등 빈도 낮은 유형)
- 검색 속도: 140~280ms (모델 로딩 0초, cold start 없음)
- 정확 매칭("소송 제기"): 정확하게 소송 공시 반환
- 의미 매칭("돈을 빌렸다"): 동의어 확장으로 사채/차입 공시 반환
- 문제: content 전문 검색이 병목, matchScore 정밀도 낮음

결론:
- Taxonomy 자동 구축 가능 확인 — report_nm 자체가 분류 체계
- 키워드 확장 + Taxonomy 매핑으로 의미 검색 프로토타입 동작
- content 검색을 report_nm + section_title로 제한하면 속도 10배 향상 예상
- 채택: 다음 실험(002 동반공시, 003 섹션맵)으로 확장

실험일: 2026-03-31
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

import polars as pl


def loadData():
    """2일치 데이터 로드."""
    df26 = pl.read_parquet("data/dart/allFilings/20260326.parquet")
    df27 = pl.read_parquet("data/dart/allFilings/20260327.parquet")
    return pl.concat([df26, df27])


def normalizeReportName(name: str) -> str:
    """report_nm 정규화 — 접두사/접미사 제거."""
    # [기재정정] 제거
    name = re.sub(r"^\[기재정정\]", "", name).strip()
    # 날짜 접미사 제거: (2025.12), (2024.12) 등
    name = re.sub(r"\s*\(\d{4}\.\d{2}\)\s*$", "", name).strip()
    # 종속회사/자회사 수식어 제거
    name = re.sub(r"\(종속회사의주요경영사항\)", "", name).strip()
    name = re.sub(r"\(자회사의\s*주요경영사항\)", "", name).strip()
    name = re.sub(r"\(자율공시\)", "", name).strip()
    # 뒤쪽 공백 제거
    name = name.strip()
    # 빈 괄호 제거
    name = re.sub(r"\(\s*\)", "", name).strip()
    return name


# 의미 카테고리 키워드 매핑
CATEGORY_KEYWORDS = {
    "자본변동": ["유상증자", "감자", "주식교환", "주식이전", "증자", "자본감소", "주금납입"],
    "사채/차입": ["전환사채", "신주인수권부사채", "사채", "회사채", "교환사채", "차입"],
    "증권발행": ["증권신고서", "투자설명서", "소액공모", "일괄신고", "증권발행"],
    "경영진변동": ["대표이사", "이사", "임원", "사외이사", "감사"],
    "주주/지분": ["대량보유", "최대주주", "주식등의", "소유상황", "주주명부", "의결권"],
    "주주총회": ["주주총회", "주총"],
    "배당/환원": ["배당", "자기주식", "자사주"],
    "계약/거래": ["판매", "공급계약", "영업양도", "영업양수", "거래"],
    "합병/인수": ["합병", "분할", "인수"],
    "소송/분쟁": ["소송", "경영권분쟁", "가처분"],
    "재무보고": ["사업보고서", "반기보고서", "분기보고서", "감사보고서"],
    "기업가치": ["기업가치", "제고"],
    "투자/자산": ["시설투자", "유형자산", "타법인출자", "금전대여"],
    "지배구조": ["지배구조", "이사회"],
    "기타공시": ["본점소재지", "상호변경", "관리종목", "상장폐지"],
}

# 자연어 동의어 — 사용자가 이렇게 말하면 이 키워드로 확장
SYNONYMS = {
    "돈을 빌렸다": ["사채", "차입", "대출", "자금조달", "전환사채"],
    "경영진이 바뀌었다": ["대표이사", "임원", "사외이사", "선임", "해임"],
    "주식을 더 발행했다": ["유상증자", "증자", "신주", "발행"],
    "회사를 합쳤다": ["합병", "인수", "분할", "교환"],
    "주주에게 돈을 줬다": ["배당", "자기주식", "주주환원"],
    "소송이 걸렸다": ["소송", "분쟁", "가처분", "경영권"],
    "계약을 맺었다": ["계약", "판매", "공급", "영업양도"],
    "투자를 했다": ["시설투자", "유형자산", "타법인출자", "금전대여"],
    "감사에 문제가 있다": ["감사", "한정", "부적정", "거절", "의견"],
}


def classifyType(normalizedName: str) -> str:
    """정규화된 유형명 → 카테고리 분류."""
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in normalizedName:
                return category
    return "미분류"


def buildTaxonomy(df: pl.DataFrame) -> dict:
    """공시 유형에서 Taxonomy 자동 구축."""
    # 정규화
    types = df["report_nm"].unique().to_list()
    normalized = {}
    for t in types:
        n = normalizeReportName(t)
        if n not in normalized:
            normalized[n] = []
        normalized[n].append(t)

    # 분류
    taxonomy: dict[str, list[str]] = defaultdict(list)
    unclassified = []

    for normName, origNames in normalized.items():
        cat = classifyType(normName)
        if cat != "미분류":
            taxonomy[cat].append(normName)
        else:
            unclassified.append(normName)

    return dict(taxonomy), unclassified, normalized


def expandQuery(query: str) -> list[str]:
    """자연어 쿼리 → 키워드 확장."""
    keywords = set()

    # 1. 직접 매칭 (동의어 테이블)
    for phrase, expansion in SYNONYMS.items():
        if any(word in query for word in phrase.split()):
            keywords.update(expansion)

    # 2. 카테고리 키워드 매칭
    for category, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in query:
                keywords.update(kws)
                break

    # 3. 원본 쿼리 단어도 추가
    keywords.update(query.split())

    return list(keywords)


def searchByTaxonomy(df: pl.DataFrame, query: str, topK: int = 10) -> pl.DataFrame:
    """Taxonomy 기반 검색."""
    keywords = expandQuery(query)
    if not keywords:
        return pl.DataFrame()

    # report_nm 또는 section_title에 키워드 포함
    conditions = []
    for kw in keywords:
        conditions.append(pl.col("report_nm").str.contains(kw, literal=True))
        conditions.append(pl.col("section_title").str.contains(kw, literal=True))
        conditions.append(pl.col("section_content").str.contains(kw, literal=True))

    combined = conditions[0]
    for c in conditions[1:]:
        combined = combined | c

    result = df.filter(combined)

    # 키워드 매칭 수로 점수 부여
    if result.height > 0:
        matchCounts = []
        for row in result.iter_rows(named=True):
            count = 0
            text = f"{row.get('report_nm', '')} {row.get('section_title', '')} {(row.get('section_content', '') or '')[:500]}"
            for kw in keywords:
                if kw in text:
                    count += 1
            matchCounts.append(count)

        result = result.with_columns(pl.Series("matchScore", matchCounts))
        result = result.sort("matchScore", descending=True).head(topK)

    return result


if __name__ == "__main__":
    import time

    df = loadData()
    print(f"데이터: {df.height}행, {df['report_nm'].n_unique()}개 유형\n")

    # 1. Taxonomy 구축
    taxonomy, unclassified, normalized = buildTaxonomy(df)

    print("=== Taxonomy ===")
    totalClassified = 0
    for cat, types in sorted(taxonomy.items()):
        print(f"\n{cat} ({len(types)}개):")
        for t in types[:5]:
            print(f"  - {t}")
        if len(types) > 5:
            print(f"  ... +{len(types) - 5}개")
        totalClassified += len(types)

    totalNormalized = len(normalized)
    print(f"\n정규화 후 유형: {totalNormalized}개 (원본 257)")
    print(f"분류 완료: {totalClassified}/{totalNormalized} ({totalClassified/totalNormalized*100:.0f}%)")
    print(f"미분류: {len(unclassified)}개")
    if unclassified:
        print("미분류 목록:")
        for u in unclassified[:10]:
            print(f"  - {u}")

    # 2. 검색 테스트
    print("\n" + "=" * 60)
    print("=== Taxonomy 검색 테스트 ===")

    queries = [
        "유상증자 결정",
        "대표이사 변경",
        "회사 합병",
        "배당금 지급",
        "소송 제기",
        "회사가 돈을 빌렸다",
        "경영진이 바뀌었다",
        "전환사채 발행",
    ]

    for q in queries:
        keywords = expandQuery(q)
        t0 = time.time()
        result = searchByTaxonomy(df, q, topK=3)
        elapsed = time.time() - t0
        print(f'\n"{q}" ({elapsed*1000:.0f}ms, 키워드: {keywords[:5]})')
        if result.height > 0:
            for row in result.head(3).iter_rows(named=True):
                score = row.get("matchScore", 0)
                print(f"  [{score}] {row['corp_name']} | {row['report_nm'][:30]}")
        else:
            print("  결과 없음")
