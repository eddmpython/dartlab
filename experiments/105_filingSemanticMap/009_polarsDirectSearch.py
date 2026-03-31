"""실험 105-009: Polars 직접 검색 — 역인덱스 없이 parquet + str.contains

실험 ID: 105-009
실험명: 역인덱스 없이 Polars str.contains + 동의어 확장으로 검색

목적:
- 별도 인덱스 파일 없이 parquet 원본에서 직접 검색
- docs(사업보고서) + allFilings(수시공시) 통합 검색
- 규모별 성능 확인 (9K → 수만 → 수십만 행)

가설:
1. 9K 행: < 5ms
2. 수만 행 (docs 일부): < 50ms
3. 수십만 행 (docs 전체): < 200ms
4. precision@5 ≥ 90% (동의어 확장 + str.contains)

방법:
1. allFilings parquet에서 Polars str.contains 검색
2. docs parquet 추가하여 통합 검색
3. 규모별 속도 벤치마크

결과:
| 데이터 | 행 수 | precision@5 | 평균 속도 |
|--------|------:|:---:|--------:|
| allFilings (9K) | 9,033 | 79% | 78ms |
| docs 50종목 | 89,979 | 71% | 1,118ms |
| 통합 (9K+90K) | 99,012 | 76% | 1,092ms |
| docs 200종목 | 353,295 | - | 1,998ms |
| docs 전체 추정 | ~4.5M | - | **~25초** |

- allFilings 9K: 78ms — 실용적
- docs 50종목(90K): 1.1초 — 느리지만 허용 범위
- docs 200종목(350K): 2초 — 느림
- docs 전체 추정(4.5M): 25초 — **실용 불가**

결론:
- **Polars 직접 검색은 수만 행까지만 실용적**, 수십만 행부터 1초+
- docs 전체(450만 행) str.contains는 25초 — ngram 역인덱스가 필수
- allFilings(수시공시)는 데이터량이 적어 직접 검색 가능하지만, docs(사업보고서)는 인덱스 없이는 안 됨
- **ngram 역인덱스 방식이 올바른 선택** — docs까지 확장 시 인덱스 빌드 필요
- 기각: Polars 직접 검색으로 대체하는 것은 대규모에서 불가

실험일: 2026-03-31
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl

DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="

SYNONYMS = {
    "돈을 빌렸다": ["사채", "차입", "대출", "자금조달", "전환사채", "회사채"],
    "빌렸다": ["사채", "차입", "대출"],
    "경영진이 바뀌었다": ["대표이사", "임원", "선임", "해임", "변경"],
    "바뀌었다": ["변경", "교체", "선임", "해임"],
    "돈을 줬다": ["배당", "배당금", "현금배당"],
    "나빠졌다": ["부채", "미지급", "손실", "감자"],
    "높이겠다": ["제고", "기업가치", "개선"],
    "맺었다": ["계약", "체결", "공급"],
    "매수했다": ["대량보유", "취득", "매수"],
    "합병": ["합병", "인수", "분할", "교환"],
    "소송": ["소송", "분쟁", "가처분", "경영권"],
    "감사": ["감사", "감사의견", "한정", "부적정"],
    "재무": ["재무", "재무제표", "재무상태"],
    "배당": ["배당", "현금배당", "배당금"],
}


def expandQuery(query: str) -> list[str]:
    """동의어 확장 → 검색 키워드 목록."""
    keywords = set()
    for phrase, syns in SYNONYMS.items():
        if phrase in query:
            keywords.update(syns)
    for word in query.split():
        if len(word) >= 2:
            keywords.add(word)
    return list(keywords)


def searchDirect(
    df: pl.LazyFrame,
    query: str,
    topK: int = 5,
) -> pl.DataFrame:
    """Polars 직접 검색 — str.contains + 동의어 확장."""
    keywords = expandQuery(query)
    if not keywords:
        return pl.DataFrame()

    # report_nm 정확 매칭 (가중치 5)
    # section_title 매칭 (가중치 2)
    scoreExprs = []
    filterExprs = []

    for kw in keywords:
        rnMatch = pl.col("report_nm").str.contains(kw, literal=True)
        stMatch = (
            pl.col("section_title").is_not_null()
            & pl.col("section_title").str.contains(kw, literal=True)
        )
        scoreExprs.append(rnMatch.cast(pl.Int32) * 5)
        scoreExprs.append(stMatch.cast(pl.Int32) * 2)
        filterExprs.append(rnMatch | stMatch)

    # 하나라도 매칭되는 행만
    combined = filterExprs[0]
    for f in filterExprs[1:]:
        combined = combined | f

    # 점수 합산
    totalScore = scoreExprs[0]
    for s in scoreExprs[1:]:
        totalScore = totalScore + s

    result = (
        df.filter(combined)
        .with_columns(totalScore.alias("score"))
        .sort("score", descending=True)
        .collect()
    )

    if result.height == 0:
        return pl.DataFrame()

    # rcept_no 중복 제거 (최고 점수만)
    result = result.unique(subset=["rcept_no"], keep="first").head(topK)

    # dartUrl 추가
    if "rcept_no" in result.columns:
        result = result.with_columns(
            (pl.lit(DART_VIEWER) + pl.col("rcept_no")).alias("dartUrl")
        )

    return result


QUERIES = [
    ("유상증자 결정", ["유상증자"]),
    ("대표이사 변경", ["대표이사"]),
    ("정기주주총회 결과", ["주주총회", "정기주주총회"]),
    ("사외이사 선임", ["사외이사"]),
    ("대량보유 변동", ["대량보유", "보유주식"]),
    ("주식매수선택권 부여", ["주식매수선택권", "스톡옵션"]),
    ("자기주식 취득", ["자기주식", "자사주"]),
    ("소송 제기", ["소송"]),
    ("회사가 돈을 빌렸다", ["사채", "차입", "대여", "발행"]),
    ("경영진이 바뀌었다", ["대표이사", "임원", "이사"]),
    ("주주에게 배당을 줬다", ["배당", "주주총회"]),
    ("회사 주식을 대량 매수했다", ["대량보유", "취득"]),
    ("기업 가치를 높이겠다", ["기업가치", "제고"]),
    ("새로운 계약을 맺었다", ["계약", "공급", "판매"]),
    ("감사보고서에 문제가 있다", ["감사", "의견", "거절"]),
    ("재무 상태가 나빠졌다", ["재무", "부채", "미지급", "손실"]),
    ("회사 합병", ["합병", "인수"]),
    ("회사채 발행", ["사채", "회사채", "발행"]),
    ("임원 보수", ["보수", "임원", "급여"]),
    ("증권 발행", ["증권", "발행", "유상"]),
]


def evalPrecision(df: pl.LazyFrame, label: str):
    """precision@5 + 속도 측정."""
    totalHit = totalCheck = 0
    latencies = []

    for query, expectedKws in QUERIES:
        t0 = time.time()
        result = searchDirect(df, query, topK=5)
        elapsed = time.time() - t0
        latencies.append(elapsed)

        hits = 0
        resultCount = min(5, result.height)
        for row in result.head(5).iter_rows(named=True):
            combined = f"{row.get('report_nm', '')} {row.get('section_title', '')}".lower()
            if any(kw in combined for kw in expectedKws):
                hits += 1

        totalHit += hits
        totalCheck += resultCount

    p5 = totalHit / totalCheck if totalCheck > 0 else 0
    import numpy as np
    avgMs = np.mean(latencies) * 1000
    p95Ms = sorted(latencies)[int(len(latencies) * 0.95)] * 1000

    print(f"  {label}: p@5={p5:.0%} ({totalHit}/{totalCheck}), avg={avgMs:.0f}ms, p95={p95Ms:.0f}ms")
    return p5, avgMs


if __name__ == "__main__":
    # ═══════════════════════════════════════
    # 1. allFilings만 (9K 행)
    # ═══════════════════════════════════════
    print("=== 1. allFilings (9K 행) ===")
    af26 = pl.scan_parquet("data/dart/allFilings/20260326.parquet")
    af27 = pl.scan_parquet("data/dart/allFilings/20260327.parquet")
    allFilings = pl.concat([af26, af27]).filter(pl.col("section_content").is_not_null())
    rowCount = allFilings.select(pl.len()).collect().item()
    print(f"  행 수: {rowCount}")
    evalPrecision(allFilings, "allFilings")

    # ═══════════════════════════════════════
    # 2. docs (사업보고서) — 규모 확인
    # ═══════════════════════════════════════
    print("\n=== 2. docs (사업보고서) ===")
    docsDir = Path("data/dart/docs")
    docsFiles = sorted(docsDir.glob("*.parquet"))[:50]  # 50종목만
    print(f"  docs 파일: {len(docsFiles)}개 (50종목 샘플)")

    if docsFiles:
        docs = pl.scan_parquet(docsFiles)
        docsCount = docs.select(pl.len()).collect().item()
        print(f"  행 수: {docsCount}")

        # docs 스키마 확인
        sample = pl.read_parquet(docsFiles[0], n_rows=1)
        print(f"  컬럼: {sample.columns}")

        # docs에도 report_nm이 있는지 → report_type으로 대체 가능
        hasReportNm = "report_nm" in sample.columns
        hasReportType = "report_type" in sample.columns
        hasSectionTitle = "section_title" in sample.columns
        print(f"  report_nm: {hasReportNm}, report_type: {hasReportType}, section_title: {hasSectionTitle}")

        # docs에서 검색 (컬럼명 맞춰서)
        if hasReportType and hasSectionTitle:
            # report_type을 report_nm으로 rename
            docsRenamed = docs.rename({"report_type": "report_nm"}) if not hasReportNm else docs
            evalPrecision(docsRenamed, "docs(50종목)")

    # ═══════════════════════════════════════
    # 3. allFilings + docs 통합
    # ═══════════════════════════════════════
    print("\n=== 3. 통합 (allFilings + docs 50종목) ===")
    if docsFiles:
        docsForMerge = docs
        if not hasReportNm and hasReportType:
            docsForMerge = docs.rename({"report_type": "report_nm"})

        # 공통 컬럼만 추출
        commonCols = ["rcept_no", "corp_name", "report_nm", "section_title", "section_content"]
        if "stock_code" in sample.columns:
            commonCols.append("stock_code")
        if "rcept_date" in sample.columns:
            commonCols.append("rcept_date")

        afCols = [c for c in commonCols if c in allFilings.collect_schema().names()]
        dCols = [c for c in commonCols if c in docsForMerge.collect_schema().names()]
        sharedCols = [c for c in afCols if c in dCols]

        combined = pl.concat([
            allFilings.select(sharedCols),
            docsForMerge.select(sharedCols),
        ])
        combinedCount = combined.select(pl.len()).collect().item()
        print(f"  통합 행 수: {combinedCount}")
        evalPrecision(combined, "통합")

    # ═══════════════════════════════════════
    # 4. docs 200종목 규모 테스트 (OOM 방지 — 전체 로드 금지)
    # ═══════════════════════════════════════
    print("\n=== 4. docs 200종목 규모 테스트 ===")
    allDocsFiles = sorted(docsDir.glob("*.parquet"))
    print(f"  docs 전체 파일: {len(allDocsFiles)}개")

    # 200종목만 샘플 (메모리 안전)
    sampleFiles = allDocsFiles[:200]
    if len(sampleFiles) > 50:
        docs200 = pl.scan_parquet(sampleFiles)
        count200 = docs200.select(pl.len()).collect().item()
        print(f"  200종목 행 수: {count200}")

        if not hasReportNm and hasReportType:
            docs200 = docs200.rename({"report_type": "report_nm"})

        for q in ["유상증자", "배당", "대표이사"]:
            t0 = time.time()
            r = searchDirect(docs200, q, topK=5)
            elapsed = time.time() - t0
            print(f"  \"{q}\" ({elapsed*1000:.0f}ms) {r.height}건")

        # 행 수 기반 전체 추정
        totalFiles = len(allDocsFiles)
        estimatedRows = int(count200 / 200 * totalFiles)
        estimatedMs = int(elapsed * 1000 / 200 * totalFiles)
        print(f"  전체 추정: ~{estimatedRows:,}행, ~{estimatedMs}ms/쿼리")
    else:
        print("  docs 파일 부족 — 건너뜀")

    # 최종 비교
    print(f"\n{'='*60}")
    print("인덱스 없이 Polars 직접 검색이 실용적인가?")
