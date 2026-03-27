"""
실험 ID: 101-015
실험명: finance/report 전 종목 프리빌드 — 단일 parquet 합산 + 압축 측정

목적:
- scan이 느린 이유: 종목별 parquet을 순차 읽기 (2700+파일)
- finance/report를 1개 parquet로 합산하면 얼마나 줄고, 얼마나 빨라지는지 실증
- 8분기(2년) vs 전체, zstd 압축 효과 측정

가설:
1. finance 전종목 합산 parquet(zstd) 100MB 이하
2. report 전종목 합산 parquet(zstd) 80MB 이하
3. 합산 후 횡단 질의 100ms 이내
4. 8분기 컷 시 추가 50% 이상 절감

방법:
1. data/dart/finance/*.parquet, data/dart/report/*.parquet 전수 합산
2. 전체 / 최근 8분기 / 최근 5년 3가지 버전 비교
3. parquet+zstd 저장, 디스크/메모리/로드 시간 측정
4. 횡단 질의 샘플 실행

결과 (2026-03-27):

| 데이터셋 | 원본 | 합산(zstd) | 행수 | 컬럼 | 빌드 | 횡단질의 |
|----------|------|-----------|------|------|------|---------|
| finance-ALL | 570MB | **388MB** | 22,078,241 | 28 | 18초 | ~300ms |
| finance-5Y | - | **197MB** | 11,664,024 | 28 | 20초 | ~100ms |
| finance-2Y | - | **34MB** | 2,042,276 | 28 | 9초 | ~17ms |
| report-ALL | 345MB | **114MB** | 10,132,517 | 167 | 32초 | 48초 ❌ |
| report-5Y | - | **0.4MB** | 72,911 | 120 | 22초 | ~5ms |

- report-5Y/2Y: year 컬럼에 "제XX기" 텍스트 혼재 → int 변환 실패로 2622/2716종목 탈락
  (report year 정규화 필요 — bsns_year 컬럼 사용하면 해결 가능)
- report-ALL 횡단질의 48초: 167컬럼 폭발 (apiType별 컬럼이 diagonal concat로 합쳐짐)
- finance는 28컬럼 고정 → 합산 효율적. report는 apiType별 분리 필요.

결론:
- 가설 1 기각: finance-ALL **388MB** (100MB 초과). 이미 structured data라 zstd 효과 제한적.
  - 단, finance-2Y(최근 2년) **34MB** → 가설 충족. 5Y도 **197MB**로 실용적.
- 가설 2 부분 확인: report-ALL **114MB** (80MB 초과). 컬럼 167개 폭발이 원인.
  - report는 apiType별 분리 저장이 필요 (wide diagonal concat 비효율)
- 가설 3 부분 확인: finance 17~300ms ✅, report 48초 ❌ (컬럼 폭발)
- 가설 4 확인: finance-ALL 388MB → 2Y 34MB (91% 절감)
- **전략**: docs=changes(47MB), finance=5Y(197MB)또는2Y(34MB), report=apiType별 분리 필요

실험일: 2026-03-27
"""

import sys
import time
import gc
from pathlib import Path

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

import polars as pl


def concatAllParquets(dataDir, label, outputPath, yearFilter=None):
    """디렉토리 내 모든 parquet을 합산."""
    allFiles = sorted(dataDir.glob("*.parquet"))
    print(f"\n{'='*70}")
    print(f"[{label}] 대상: {len(allFiles)}종목")
    print(f"{'='*70}")

    t0 = time.perf_counter()
    batchChunks = []
    batchIdx = 0
    success = 0
    failed = 0
    totalRows = 0
    BATCH_SIZE = 200

    tmpDir = Path(f"experiments/101_companyAtom/_tmp_{label}")
    tmpDir.mkdir(exist_ok=True)

    for i, pf in enumerate(allFiles):
        try:
            df = pl.read_parquet(str(pf))
        except Exception:
            failed += 1
            continue

        code = pf.stem
        # stockCode 추가 (이미 있으면 skip)
        if "stockCode" not in df.columns and "stock_code" not in df.columns:
            df = df.with_columns(pl.lit(code).alias("stockCode"))
        elif "stock_code" in df.columns and "stockCode" not in df.columns:
            df = df.rename({"stock_code": "stockCode"})

        # year 필터
        if yearFilter is not None:
            yearCol = None
            if "bsns_year" in df.columns:
                yearCol = "bsns_year"
            elif "year" in df.columns:
                yearCol = "year"

            if yearCol:
                df = df.filter(
                    pl.col(yearCol).cast(pl.Utf8).str.to_integer(strict=False) >= yearFilter
                )

        if df.height == 0:
            failed += 1
            continue

        batchChunks.append(df)
        totalRows += df.height
        success += 1

        # 배치 저장
        if len(batchChunks) >= BATCH_SIZE or i == len(allFiles) - 1:
            if batchChunks:
                # 컬럼 통일 (report는 종목마다 컬럼 조합이 다를 수 있음)
                try:
                    batch = pl.concat(batchChunks, how="diagonal_relaxed")
                except Exception:
                    # fallback: 공통 컬럼만
                    commonCols = set(batchChunks[0].columns)
                    for c in batchChunks[1:]:
                        commonCols &= set(c.columns)
                    commonCols = sorted(commonCols)
                    batch = pl.concat([c.select(commonCols) for c in batchChunks])

                batch.write_parquet(str(tmpDir / f"batch_{batchIdx:03d}.parquet"), compression="zstd")
                del batch
                batchChunks = []
                batchIdx += 1

        if (i + 1) % 500 == 0:
            elapsed = time.perf_counter() - t0
            print(f"  [{i+1:>5d}/{len(allFiles)}] {success}성공, {failed}실패, {totalRows:,}행, {elapsed:.1f}초")

    buildTime = time.perf_counter() - t0
    print(f"\n  빌드: {success}종목 성공, {failed}실패, {totalRows:,}행, {buildTime:.1f}초")

    # 합산
    print(f"  배치 {batchIdx}개 합산 중...")
    t1 = time.perf_counter()
    batchFiles = sorted(tmpDir.glob("batch_*.parquet"))
    if not batchFiles:
        print("  결과 없음")
        return None

    merged = pl.concat([pl.read_parquet(str(f)) for f in batchFiles], how="diagonal_relaxed")
    merged.write_parquet(str(outputPath), compression="zstd")
    mergeTime = time.perf_counter() - t1

    diskMb = outputPath.stat().st_size / 1024 / 1024
    memMb = merged.estimated_size("mb")

    print(f"  합산: {mergeTime:.1f}초")
    print(f"  행수: {merged.height:,}")
    print(f"  컬럼: {merged.width}")
    print(f"  디스크: {diskMb:.1f}MB (zstd)")
    print(f"  메모리: {memMb:.1f}MB")

    # 배치 파일 정리
    for f in batchFiles:
        f.unlink()
    tmpDir.rmdir()

    return merged


def measureLoad(path, label):
    """로드 시간 측정."""
    t0 = time.perf_counter()
    df = pl.read_parquet(str(path))
    loadTime = time.perf_counter() - t0
    print(f"  [{label}] 로드: {loadTime:.3f}초, {df.height:,}행, {df.estimated_size('mb'):.1f}MB")
    return df


def runQueries(df, label, yearCol="bsns_year"):
    """횡단 질의 샘플."""
    print(f"\n  [{label}] 횡단 질의:")

    scCol = "stockCode" if "stockCode" in df.columns else "stock_code"

    # 1. 종목당 행수 TOP10
    t0 = time.perf_counter()
    top = df.group_by(scCol).agg(pl.len().alias("cnt")).sort("cnt", descending=True).head(10)
    t1 = time.perf_counter()
    print(f"    종목당 행수 TOP10: {(t1-t0)*1000:.0f}ms")
    print(f"      1위: {top[scCol][0]} ({top['cnt'][0]:,}행)")

    # 2. 연도별 행수
    if yearCol in df.columns:
        t0 = time.perf_counter()
        yearly = df.group_by(yearCol).agg(pl.len().alias("cnt")).sort(yearCol)
        t1 = time.perf_counter()
        print(f"    연도별 행수: {(t1-t0)*1000:.0f}ms")
        for row in yearly.iter_rows():
            print(f"      {row[0]}: {row[1]:,}")

    # 3. 종목수
    t0 = time.perf_counter()
    nCompanies = df[scCol].n_unique()
    t1 = time.perf_counter()
    print(f"    종목수: {nCompanies:,} ({(t1-t0)*1000:.0f}ms)")


def run():
    finDir = Path("data/dart/finance")
    repDir = Path("data/dart/report")
    outDir = Path("experiments/101_companyAtom")

    # ── Finance ──
    # 전체
    finAll = concatAllParquets(
        finDir, "finance-ALL", outDir / "_allFinance.parquet"
    )
    if finAll is not None:
        runQueries(finAll, "finance-ALL", "bsns_year")

        # 최근 5년
        del finAll
        gc.collect()

    fin5y = concatAllParquets(
        finDir, "finance-5Y", outDir / "_allFinance5y.parquet", yearFilter=2021
    )
    if fin5y is not None:
        runQueries(fin5y, "finance-5Y", "bsns_year")

        # 최근 8분기 (2024~) — bsns_year 기준으로 최근 2년
        del fin5y
        gc.collect()

    fin2y = concatAllParquets(
        finDir, "finance-2Y", outDir / "_allFinance2y.parquet", yearFilter=2025
    )
    if fin2y is not None:
        runQueries(fin2y, "finance-2Y", "bsns_year")
        del fin2y
        gc.collect()

    # ── Report ──
    repAll = concatAllParquets(
        repDir, "report-ALL", outDir / "_allReport.parquet"
    )
    if repAll is not None:
        runQueries(repAll, "report-ALL", "year")
        del repAll
        gc.collect()

    rep5y = concatAllParquets(
        repDir, "report-5Y", outDir / "_allReport5y.parquet", yearFilter=2021
    )
    if rep5y is not None:
        runQueries(rep5y, "report-5Y", "year")
        del rep5y
        gc.collect()

    rep2y = concatAllParquets(
        repDir, "report-2Y", outDir / "_allReport2y.parquet", yearFilter=2025
    )
    if rep2y is not None:
        runQueries(rep2y, "report-2Y", "year")
        del rep2y
        gc.collect()

    # ── 로드 시간 비교 ──
    print(f"\n{'='*70}")
    print("로드 시간 비교")
    print(f"{'='*70}")

    for name in ["_allFinance.parquet", "_allFinance5y.parquet", "_allFinance2y.parquet",
                  "_allReport.parquet", "_allReport5y.parquet", "_allReport2y.parquet"]:
        path = outDir / name
        if path.exists():
            df = measureLoad(path, name)
            del df
            gc.collect()

    # ── 최종 요약 ──
    print(f"\n{'='*70}")
    print("최종 디스크 크기 요약")
    print(f"{'='*70}")

    for name in ["_allFinance.parquet", "_allFinance5y.parquet", "_allFinance2y.parquet",
                  "_allReport.parquet", "_allReport5y.parquet", "_allReport2y.parquet",
                  "_allChanges5y.parquet"]:
        path = outDir / name
        if path.exists():
            mb = path.stat().st_size / 1024 / 1024
            print(f"  {name:40s} {mb:8.1f}MB")

    # 원본 크기 비교
    finOrig = sum(f.stat().st_size for f in finDir.glob("*.parquet")) / 1024 / 1024
    repOrig = sum(f.stat().st_size for f in repDir.glob("*.parquet")) / 1024 / 1024
    print(f"\n  원본 finance 합계: {finOrig:.1f}MB ({len(list(finDir.glob('*.parquet')))}파일)")
    print(f"  원본 report 합계:  {repOrig:.1f}MB ({len(list(repDir.glob('*.parquet')))}파일)")


if __name__ == "__main__":
    run()
