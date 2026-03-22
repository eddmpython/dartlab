"""실험 ID: 006
실험명: sections 파이프라인 단계별 프로파일링

목적:
- sections() 2.4-2.8초 병목의 내부 분포 파악
- 어떤 단계가 가장 비싼지 정량 측정
- 최적화 우선순위 결정

가설:
1. parquet I/O < 전체의 5%
2. _reportRowsToTopicRows (section 매핑 + 청킹) > 50%
3. _expandStructuredRows (텍스트 구조 분석) > 30%
4. DataFrame 조립 < 10%

방법:
1. 삼성전자(005930)로 sections() 파이프라인 단계별 시간 측정
2. iterPeriodSubsets 내부: loadData, selectReport, 필터링
3. 메인 루프 내부: _reportRowsToTopicRows, _expandStructuredRows, dict 누적
4. 후반부: cadenceMeta 계산, 정렬, DataFrame 조립

결과:
- sections() 전체: 2.292s (삼성전자, 40개 기간, 8,109행 × 70열)
- 단계별 비중:
  loadData:               0.162s (7.1%)  — parquet I/O
  selectReport:           0.043s (1.9%)  — 기간별 보고서 선택
  filter/sort:            0.029s (1.3%)  — Polars 필터링
  _reportRowsToTopicRows: 0.474s (20.7%) — section 매핑 + 청킹 + text/table 분리
  applyProjections:       0.017s (0.7%)  — teacher topic 투영
  _expandStructuredRows:  0.767s (33.5%) — 텍스트 구조 분석 (heading/path/level)
  dict+DataFrame 조립:    0.799s (34.9%) — cadenceMeta 계산 + 정렬 + Polars DataFrame 조립
- 기간당: _reportRowsToTopicRows ~12ms, _expandStructuredRows ~12ms
- 40개 기간 × 2단계 = ~50ms/기간 × 40 = ~2s 가 핵심
- 41,234 topicRows → 78,231 expandedRows (1.9배 확장)

결론:
- 가설 1 기각 — parquet I/O는 7.1% (5% 초과하나 여전히 작음)
- 가설 2 기각 — _reportRowsToTopicRows는 20.7% (50% 미만)
- 가설 3 채택 — _expandStructuredRows 33.5% (30% 이상)
- 가설 외 발견 — dict+DataFrame 조립이 34.9%로 가장 큼
- **핵심 발견**:
  1. 3대 병목: dict+DF 조립(35%) ≈ _expandStructuredRows(34%) > _reportRowsToTopicRows(21%)
  2. 단일 지배적 병목 없음 — 3개 단계가 고르게 분산 (20-35%)
  3. 40개 기간 반복이 근본 원인 — 기간당 ~50ms × 40 = ~2s
  4. 최적화 전략: (a) 필요 기간만 로드 (lazy), (b) DataFrame 조립 최적화, (c) 캐싱
  5. finance-only 비교(0.5s)가 즉시 응답에 적합, sections는 비동기 로딩이 현실적

실험일: 2026-03-19
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.sections._common import (
    REPORT_KINDS,
    detectContentCol,
    sortPeriods,
)
from dartlab.engines.company.dart.docs.sections.pipeline import (
    _expandStructuredRows,
    _reportRowsToTopicRows,
    _rowCadenceMeta,
    sections,
)
from dartlab.engines.company.dart.docs.sections.runtime import (
    applyProjections,
    chapterTeacherTopics,
    detailTopicForTopic,
    projectionSuppressedTopics,
)


def profilePipeline(stockCode: str = "005930"):
    print("=" * 70)
    print(f"006 — sections 파이프라인 단계별 프로파일링 ({stockCode})")
    print("=" * 70)

    # ── 1. loadData ──
    t0 = time.perf_counter()
    df = loadData(stockCode)
    t_load = time.perf_counter() - t0
    ccol = detectContentCol(df)
    print(f"\n1) loadData: {t_load:.3f}s  (shape={df.shape})")

    # ── 2. iterPeriodSubsets 분해 ──
    years = sorted(df["year"].unique().to_list(), reverse=True)
    sinceYear = 2016

    t_select_total = 0.0
    t_filter_total = 0.0
    t_topicRows_total = 0.0
    t_expand_total = 0.0
    t_projection_total = 0.0
    periodCount = 0
    totalTopicRows = 0
    totalExpandedRows = 0

    periodRows = {}
    validPeriods = []
    latestAnnualRows = None

    t2 = time.perf_counter()
    for year in years:
        if isinstance(year, str) and year.isdigit() and int(year) < sinceYear:
            continue
        if isinstance(year, (int, float)) and int(year) < sinceYear:
            continue
        for reportKind, suffix in REPORT_KINDS:
            periodKey = f"{year}{suffix}"

            ts = time.perf_counter()
            report = selectReport(df, year, reportKind=reportKind)
            t_select_total += time.perf_counter() - ts

            if report is None or ccol not in report.columns:
                continue

            ts = time.perf_counter()
            subset = (
                report.select(["section_order", "section_title", ccol])
                .filter(pl.col(ccol).is_not_null() & (pl.col(ccol).str.len_chars() > 0))
                .sort("section_order")
            )
            t_filter_total += time.perf_counter() - ts

            if subset.height == 0:
                continue

            ts = time.perf_counter()
            topicRows = _reportRowsToTopicRows(subset, ccol)
            t_topicRows_total += time.perf_counter() - ts

            periodRows[periodKey] = topicRows
            validPeriods.append(periodKey)
            totalTopicRows += len(topicRows)
            periodCount += 1

            if reportKind == "annual" and latestAnnualRows is None:
                latestAnnualRows = topicRows

    t_iter = time.perf_counter() - t2

    print(f"\n2) 기간 순회 총: {t_iter:.3f}s  ({periodCount}개 기간)")
    print(f"   selectReport 총: {t_select_total:.3f}s")
    print(f"   filter/sort 총: {t_filter_total:.3f}s")
    print(f"   _reportRowsToTopicRows 총: {t_topicRows_total:.3f}s  (총 {totalTopicRows:,} rows)")

    # ── 3. applyProjections + _expandStructuredRows ──
    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    validPeriods = sortPeriods(validPeriods)

    t3 = time.perf_counter()
    for periodKey in validPeriods:
        ts = time.perf_counter()
        projected = applyProjections(periodRows.get(periodKey, []), teacherTopics)
        t_projection_total += time.perf_counter() - ts

        ts = time.perf_counter()
        expanded = _expandStructuredRows(projected)
        t_expand_total += time.perf_counter() - ts
        totalExpandedRows += len(expanded)
    t_process = time.perf_counter() - t3

    print(f"\n3) projection + expand 총: {t_process:.3f}s")
    print(f"   applyProjections 총: {t_projection_total:.3f}s")
    print(f"   _expandStructuredRows 총: {t_expand_total:.3f}s  (총 {totalExpandedRows:,} rows)")

    # ── 4. 메인 루프 (dict 누적) + DataFrame 조립 ──
    t4 = time.perf_counter()
    result = sections(stockCode)
    t_full = time.perf_counter() - t4

    print(f"\n4) sections() 전체: {t_full:.3f}s", end="")
    if result is not None:
        print(f"  (shape={result.shape})")
    else:
        print("  (None)")

    # ── 기간별 상세 ──
    print(f"\n--- 기간별 _reportRowsToTopicRows 시간 ---")
    for year in sorted(df["year"].unique().to_list(), reverse=True)[:3]:
        for reportKind, suffix in REPORT_KINDS:
            periodKey = f"{year}{suffix}"
            report = selectReport(df, year, reportKind=reportKind)
            if report is None or ccol not in report.columns:
                continue
            subset = (
                report.select(["section_order", "section_title", ccol])
                .filter(pl.col(ccol).is_not_null() & (pl.col(ccol).str.len_chars() > 0))
                .sort("section_order")
            )
            if subset.height == 0:
                continue
            ts = time.perf_counter()
            rows = _reportRowsToTopicRows(subset, ccol)
            dt = time.perf_counter() - ts
            print(f"  {periodKey}: {dt:.3f}s  ({len(rows)} rows, subset={subset.height})")

    # ── _expandStructuredRows 기간별 상세 ──
    print(f"\n--- 기간별 _expandStructuredRows 시간 ---")
    for periodKey in validPeriods[-6:]:
        projected = applyProjections(periodRows.get(periodKey, []), teacherTopics)
        ts = time.perf_counter()
        expanded = _expandStructuredRows(projected)
        dt = time.perf_counter() - ts
        print(f"  {periodKey}: {dt:.3f}s  ({len(projected)} → {len(expanded)} rows)")

    # ── 요약 ──
    overhead = t_full - t_load - t_iter - t_process
    print(f"\n{'='*70}")
    print("요약 (비중 = sections() 전체 대비)")
    print(f"{'='*70}")
    print(f"  loadData:              {t_load:.3f}s  ({t_load/t_full*100:.1f}%)")
    print(f"  selectReport:          {t_select_total:.3f}s  ({t_select_total/t_full*100:.1f}%)")
    print(f"  filter/sort:           {t_filter_total:.3f}s  ({t_filter_total/t_full*100:.1f}%)")
    print(f"  _reportRowsToTopicRows:{t_topicRows_total:.3f}s  ({t_topicRows_total/t_full*100:.1f}%)")
    print(f"  applyProjections:      {t_projection_total:.3f}s  ({t_projection_total/t_full*100:.1f}%)")
    print(f"  _expandStructuredRows: {t_expand_total:.3f}s  ({t_expand_total/t_full*100:.1f}%)")
    print(f"  dict+DataFrame 조립:   {overhead:.3f}s  ({overhead/t_full*100:.1f}%)")
    print(f"  ──────────────────")
    print(f"  sections() 전체:       {t_full:.3f}s  (100%)")


if __name__ == "__main__":
    profilePipeline("005930")
