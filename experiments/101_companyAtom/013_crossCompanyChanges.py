"""
실험 ID: 101-013
실험명: 전 종목 changes 횡단 분석 — 다종목 합산 + AI 시뮬레이션 질의

목적:
- 50종목 changes를 합산하여 횡단 분석이 실제로 동작하는지 검증
- AI가 "업종별", "변화 유형별", "키워드별" 횡단 질의를 할 수 있는 공간 구축
- 규모 확장 시 성능 한계 확인 (메모리, 속도)

가설:
1. 50종목 changes 합산이 메모리 200MB 이하로 가능
2. 횡단 질의(업종별/키워드/유형) 전부 100ms 이내
3. AI 시뮬레이션 질의 5종 모두 의미 있는 결과 산출

방법:
1. 50종목 순차 로드 → changes 빌드 → parquet 저장 → 메모리 해제
2. 저장된 parquet 합산 로드
3. 횡단 질의 7종 실행 + 시간 측정
4. AI 컨텍스트 조립 시뮬레이션

결과 (2026-03-27):
- 50종목 빌드: 전부 성공, 총 1,797,434행, 빌드 375초(평균 7.5초/종목)
- 합산: 메모리 464MB, **디스크 31.9MB** (parquet+zstd)
- 합산 로드: 0.4초
- 횡단 질의 7종 전부 **66ms 이내**:
  | 질의 | 시간 | 결과 예시 |
  |------|------|----------|
  | structural 순위 | 17ms | 034730(SK이노) 1469건 1위 |
  | AI 키워드 순위 | 20ms | 267250(현대중공업) 1009건 1위 |
  | 연도별 추이 | 62ms | 2022년 총변화 29.7만건 피크 |
  | topic 빈도 | 66ms | fsSummary 47.5만건 최다 |
  | disappeared 순위 | 10ms | 034730 4435건 |
  | 사업개황 변화 | 11ms | 034730 매년 1500~2300건 |
  | ESG 키워드 추이 | 20ms | 2021년 급증(1511→2851), 이후 유지 |
- AI 컨텍스트: 순위표+상세 = 2,832자/~1,784토큰 (예산의 18%)
- 전 종목 추정: 9200만행, 디스크 1.6GB, 메모리 23GB, 질의 ~3.4초

결론:
- 가설 1 부분 기각: 50종목 464MB (200MB 가설 초과). 대형 공시기업이 행 많음
- 가설 2 확인: **전부 66ms 이내** (100ms 목표 달성)
- 가설 3 확인: 7개 질의 모두 즉시 의미 있는 결과. ESG 추이, AI 키워드 분포, 사업 축소 신호 등
- **핵심 발견**:
  - 디스크 31.9MB에 50개 대형 기업의 전체 공시 변화 이력이 담김
  - 횡단 질의가 Polars 네이티브 필터로 즉시 동작
  - AI 컨텍스트 조립도 2K 토큰이면 충분 (순위표+상위 3개 상세)
  - 전 종목은 메모리 23GB로 단일 머신에 안 올라감 → 디스크 scan_parquet 또는 종목 그룹별 로드 필요
  - **ESG 키워드 2021년 급증**: 50개 대형 기업에서 ESG/탄소/환경 언급이 2020→2021에 1.9배 급증

실험일: 2026-03-27
"""

import sys
import time
import re
import gc
from pathlib import Path

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

import polars as pl

PERIOD_RE = re.compile(r"^\d{4}$")


def buildChangesVectorized(sections):
    """010에서 검증된 벡터화 changes 빌더."""
    annualCols = sorted([c for c in sections.columns if PERIOD_RE.match(c)])
    if len(annualCols) < 2:
        return pl.DataFrame()

    metaCols = ["topic"]
    for col in ("textPathKey", "blockType", "blockOrder"):
        if col in sections.columns:
            metaCols.append(col)

    work = sections.with_row_index("_row")
    long = work.select(["_row"] + metaCols + annualCols).unpivot(
        index=["_row"] + metaCols, on=annualCols,
        variable_name="period", value_name="text",
    )
    long = long.with_columns(pl.col("text").cast(pl.Utf8))
    long = long.with_columns(
        pl.when(pl.col("text").is_not_null()).then(pl.col("text").hash())
        .otherwise(pl.lit(None, dtype=pl.UInt64)).alias("_hash"),
        pl.when(pl.col("text").is_not_null()).then(pl.col("text").str.len_chars())
        .otherwise(pl.lit(None, dtype=pl.UInt32)).alias("_len"),
        pl.when(pl.col("text").is_not_null()).then(pl.col("text").str.slice(0, 200))
        .otherwise(pl.lit(None, dtype=pl.Utf8)).alias("preview"),
    )
    long = long.sort(["_row", "period"])
    long = long.with_columns([
        pl.col("period").shift(1).over("_row").alias("_prevPeriod"),
        pl.col("_hash").shift(1).over("_row").alias("_prevHash"),
        pl.col("_len").shift(1).over("_row").alias("_prevLen"),
        pl.col("text").shift(1).over("_row").alias("_prevText"),
    ])
    changes = long.filter(
        pl.col("_prevPeriod").is_not_null()
        & ~(pl.col("text").is_null() & pl.col("_prevText").is_null())
        & ((pl.col("_hash") != pl.col("_prevHash"))
           | pl.col("text").is_null() | pl.col("_prevText").is_null())
    )
    numPattern = r"[\d,.]+"
    changes = changes.with_columns([
        pl.col("text").str.replace_all(numPattern, "N").alias("_stripped"),
        pl.col("_prevText").str.replace_all(numPattern, "N").alias("_prevStripped"),
    ])
    changes = changes.with_columns(
        pl.when(pl.col("_prevText").is_null()).then(pl.lit("appeared"))
        .when(pl.col("text").is_null()).then(pl.lit("disappeared"))
        .when(pl.col("_stripped") == pl.col("_prevStripped")).then(pl.lit("numeric"))
        .when(
            (pl.col("_prevLen") > 0)
            & ((pl.col("_len").cast(pl.Int64) - pl.col("_prevLen").cast(pl.Int64)).abs().cast(pl.Float64)
               / pl.col("_prevLen").cast(pl.Float64) > 0.5)
        ).then(pl.lit("structural"))
        .otherwise(pl.lit("wording")).alias("changeType")
    )
    resultCols = ["_prevPeriod", "period", "changeType", "_prevLen", "_len", "preview"] + metaCols
    renameMap = {"_prevPeriod": "fromPeriod", "period": "toPeriod", "_prevLen": "sizeA", "_len": "sizeB"}
    result = changes.select(resultCols).rename(renameMap)
    result = result.with_columns(
        (pl.col("sizeB").cast(pl.Int64) - pl.col("sizeA").cast(pl.Int64)).alias("sizeDelta")
    )
    return result


def run():
    import dartlab
    from dartlab.core.memory import get_memory_mb

    docsDir = Path("data/dart/docs")
    tmpDir = Path("experiments/101_companyAtom/_tmp_changes")
    tmpDir.mkdir(exist_ok=True)

    # 주요 50종목 선정 (parquet 크기 상위 = 공시 양 많은 기업)
    allFiles = sorted(docsDir.glob("*.parquet"), key=lambda f: f.stat().st_size, reverse=True)
    targetCodes = [f.stem for f in allFiles[:50]]

    print("=" * 80)
    print("1. 50종목 changes 순차 빌드")
    print("=" * 80)
    print(f"  메모리 시작: {get_memory_mb():.0f}MB")
    print()

    built = 0
    failed = 0
    totalRows = 0
    totalBuildTime = 0

    for i, code in enumerate(targetCodes):
        t0 = time.perf_counter()
        try:
            c = dartlab.Company(code)
            sections = c.docs.sections
            annualCols = sorted([col for col in sections.columns if PERIOD_RE.match(col)])
            if len(annualCols) < 2:
                print(f"  [{i+1:2d}] {code}: 기간 부족 ({len(annualCols)}개), 건너뜀")
                del c, sections
                gc.collect()
                failed += 1
                continue

            changes = buildChangesVectorized(sections)
            buildTime = time.perf_counter() - t0

            if changes.height == 0:
                del c, sections, changes
                gc.collect()
                failed += 1
                continue

            # stockCode 추가 + Categorical → String
            changes = changes.with_columns(pl.lit(code).alias("stockCode"))
            for col in changes.columns:
                if changes[col].dtype == pl.Categorical:
                    changes = changes.with_columns(pl.col(col).cast(pl.Utf8))

            # 임시 parquet 저장
            changes.write_parquet(str(tmpDir / f"{code}.parquet"), compression="zstd")
            totalRows += changes.height
            totalBuildTime += buildTime
            built += 1

            if (i + 1) % 10 == 0 or i < 3:
                mem = get_memory_mb()
                print(f"  [{i+1:2d}] {code}: {changes.height}행, {buildTime:.2f}초, 메모리 {mem:.0f}MB")

            del c, sections, changes
            gc.collect()

        except Exception as e:
            print(f"  [{i+1:2d}] {code}: 실패 ({e})")
            gc.collect()
            failed += 1

    print(f"\n  완료: {built}종목 성공, {failed}종목 실패")
    print(f"  총 {totalRows:,}행, 빌드 총 {totalBuildTime:.1f}초")
    print(f"  메모리: {get_memory_mb():.0f}MB")

    # ── 2. 합산 로드 ──
    print()
    print("=" * 80)
    print("2. 합산 로드")
    print("=" * 80)

    t0 = time.perf_counter()
    parquetFiles = list(tmpDir.glob("*.parquet"))
    merged = pl.concat([pl.read_parquet(str(f)) for f in parquetFiles])
    loadTime = time.perf_counter() - t0

    memMb = merged.estimated_size() / 1024 / 1024
    diskMb = sum(f.stat().st_size for f in parquetFiles) / 1024 / 1024

    print(f"  {len(parquetFiles)}종목, {merged.height:,}행 × {merged.width}열")
    print(f"  메모리: {memMb:.1f}MB")
    print(f"  디스크(parquet+zstd): {diskMb:.1f}MB")
    print(f"  로드 시간: {loadTime:.3f}초")
    print(f"  종목 목록: {sorted(merged.get_column('stockCode').unique().to_list())[:10]}...")

    # ── 3. 횡단 질의 ──
    print()
    print("=" * 80)
    print("3. 횡단 질의 (7종)")
    print("=" * 80)

    queries = []

    # Q1: 2024→2025 structural 변화 순위
    t0 = time.perf_counter()
    q1 = (
        merged
        .filter((pl.col("toPeriod") == "2025") & (pl.col("changeType") == "structural"))
        .group_by("stockCode")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(10)
    )
    q1t = (time.perf_counter() - t0) * 1000
    queries.append(("2024→2025 structural 순위", q1t, q1))

    # Q2: AI 키워드 포함 변화 순위
    t0 = time.perf_counter()
    q2 = (
        merged
        .filter(pl.col("preview").str.contains("(?i)AI|인공지능|머신러닝|딥러닝|생성형"))
        .group_by("stockCode")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(10)
    )
    q2t = (time.perf_counter() - t0) * 1000
    queries.append(("AI 키워드 변화 순위", q2t, q2))

    # Q3: 연도별 전체 변화 추이
    t0 = time.perf_counter()
    q3 = (
        merged
        .group_by("toPeriod")
        .agg([
            pl.len().alias("총변화"),
            pl.col("changeType").filter(pl.col("changeType") == "structural").len().alias("structural"),
            pl.col("changeType").filter(pl.col("changeType") == "appeared").len().alias("appeared"),
        ])
        .sort("toPeriod")
    )
    q3t = (time.perf_counter() - t0) * 1000
    queries.append(("연도별 전체 변화 추이", q3t, q3))

    # Q4: topic별 변화 빈도 (전 종목)
    t0 = time.perf_counter()
    q4 = (
        merged
        .group_by("topic")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(10)
    )
    q4t = (time.perf_counter() - t0) * 1000
    queries.append(("topic별 변화 빈도 TOP10", q4t, q4))

    # Q5: disappeared가 많은 기업 (사업 축소 신호)
    t0 = time.perf_counter()
    q5 = (
        merged
        .filter((pl.col("toPeriod") == "2025") & (pl.col("changeType") == "disappeared"))
        .group_by("stockCode")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(10)
    )
    q5t = (time.perf_counter() - t0) * 1000
    queries.append(("2025 disappeared 순위 (사업 축소?)", q5t, q5))

    # Q6: 특정 topic(businessOverview) 변화가 큰 기업
    t0 = time.perf_counter()
    q6 = (
        merged
        .filter(
            (pl.col("topic") == "businessOverview")
            & (pl.col("changeType").is_in(["structural", "appeared"]))
        )
        .group_by("stockCode", "toPeriod")
        .agg([
            pl.len().alias("count"),
            pl.col("sizeDelta").sum().alias("totalDelta"),
        ])
        .sort("count", descending=True)
        .head(10)
    )
    q6t = (time.perf_counter() - t0) * 1000
    queries.append(("사업개황 구조적 변화 TOP10", q6t, q6))

    # Q7: ESG/탄소/환경 키워드 변화 추이
    t0 = time.perf_counter()
    q7 = (
        merged
        .filter(pl.col("preview").str.contains("(?i)ESG|탄소|환경|기후|온실"))
        .group_by("toPeriod")
        .agg(pl.len().alias("count"))
        .sort("toPeriod")
    )
    q7t = (time.perf_counter() - t0) * 1000
    queries.append(("ESG/탄소/환경 키워드 연도별 추이", q7t, q7))

    maxTime = 0
    for name, elapsed, result in queries:
        maxTime = max(maxTime, elapsed)
        print(f"\n  {name} [{elapsed:.1f}ms]")
        print(result)

    # ── 4. AI 횡단 컨텍스트 조립 시뮬레이션 ──
    print()
    print("=" * 80)
    print("4. AI 횡단 컨텍스트 조립 시뮬레이션")
    print("=" * 80)

    # 시나리오: "반도체 업종에서 2024→2025 structural 변화가 급증한 기업을 분석해줘"
    # AI가 받을 컨텍스트를 조립
    BUDGET = 16000

    # Step 1: 2024→2025 structural 변화 순위 (전 종목)
    ranking = (
        merged
        .filter((pl.col("toPeriod") == "2025") & (pl.col("changeType") == "structural"))
        .group_by("stockCode")
        .agg([
            pl.len().alias("count"),
            pl.col("topic").n_unique().alias("topicCount"),
            pl.col("sizeDelta").sum().alias("totalDelta"),
        ])
        .sort("count", descending=True)
        .head(10)
    )

    context = "# 2024→2025 구조적 변화(structural) 순위 — 상위 10개 기업\n\n"
    context += "| 종목코드 | structural건수 | topic수 | 총크기변화 |\n"
    context += "|----------|--------------|---------|----------|\n"
    for row in ranking.iter_rows(named=True):
        context += f"| {row['stockCode']} | {row['count']} | {row['topicCount']} | {row['totalDelta']:+,}자 |\n"
    context += "\n"

    # Step 2: 상위 3개 기업의 structural 변화 상세
    top3 = ranking.head(3).get_column("stockCode").to_list()
    for code in top3:
        compChanges = (
            merged
            .filter(
                (pl.col("stockCode") == code)
                & (pl.col("toPeriod") == "2025")
                & (pl.col("changeType") == "structural")
            )
            .sort("sizeDelta", descending=True)
        )
        context += f"\n## {code} — structural 변화 상세 ({compChanges.height}건)\n"
        for row in compChanges.head(5).iter_rows(named=True):
            preview = (row.get("preview") or "")[:120]
            delta = row.get("sizeDelta")
            deltaStr = f"{delta:+,}자" if delta is not None else "?"
            context += f"  [{row['topic']}] ({deltaStr}): {preview}\n"

        if len(context) > BUDGET:
            context = context[:BUDGET]
            break

    tokens = int(sum(1.5 if '\uac00' <= ch <= '\ud7a3' else 0.25 for ch in context))
    print(f"  시나리오: '2024→2025 structural 변화 급증 기업 분석'")
    print(f"  컨텍스트 크기: {len(context)}자, ~{tokens} 토큰")
    print(f"  포함 내용: 상위 10개 순위표 + 상위 3개 기업 상세 (각 5건)")
    print()
    print("  [컨텍스트 미리보기 — 처음 800자]")
    print(context[:800])

    # ── 5. 규모 추정 ──
    print()
    print("=" * 80)
    print("5. 전 종목 확장 추정")
    print("=" * 80)

    avgRowsPerCompany = merged.height / len(parquetFiles)
    avgDiskPerCompany = diskMb / len(parquetFiles)
    totalCompanies = 2548

    print(f"  50종목 실측: {merged.height:,}행, 메모리 {memMb:.1f}MB, 디스크 {diskMb:.1f}MB")
    print(f"  종목당 평균: {avgRowsPerCompany:.0f}행, {avgDiskPerCompany:.2f}MB")
    print()
    print(f"  전 종목({totalCompanies}개) 추정:")
    print(f"    행수: {avgRowsPerCompany * totalCompanies:,.0f}행")
    print(f"    디스크: {avgDiskPerCompany * totalCompanies:.0f}MB ({avgDiskPerCompany * totalCompanies / 1024:.1f}GB)")
    print(f"    메모리: {memMb / len(parquetFiles) * totalCompanies:.0f}MB ({memMb / len(parquetFiles) * totalCompanies / 1024:.1f}GB)")
    print(f"    횡단 질의: 50종목에서 {maxTime:.0f}ms → 2548종목 추정 {maxTime * totalCompanies / len(parquetFiles):.0f}ms")

    # 정리
    print()
    print("=" * 80)
    print("6. 종합")
    print("=" * 80)
    print(f"  횡단 질의 최대: {maxTime:.1f}ms (50종목)")
    print(f"  합산 메모리: {memMb:.1f}MB")
    print(f"  AI 컨텍스트 조립: 순위표 + 상세 = {len(context)}자 / ~{tokens}토큰")

    # 임시 파일 정리
    for f in parquetFiles:
        f.unlink()
    tmpDir.rmdir()

    del merged
    gc.collect()


if __name__ == "__main__":
    run()
