"""공시 변화 리스크 탐지 — changes.parquet 기반 선행 위험 시그널.

기존 scan 축(debt, audit)이 "결과"를 보는 반면,
이 축은 공시 "변화 과정"에서 선행 리스크를 탐지한다.

시그널 6개:
- contingentDebt: 우발부채 섹션 증가 (숨겨진 부채)
- chronicYears: 우발부채 3년+ 연속 증가 연수 (만성 리스크)
- riskKeyword: 횡령/배임/과징금/손해배상 신규 등장 (audit 미감지 위험)
- auditStruct: 감사/내부통제 구조 변경 3건 이상
- affiliateChange: 계열/타법인 numeric 변화 (M&A 신호)
- bizPivot: 사업 내용 대규모 변경 (구조 전환)

사용법::

    dartlab.scan("disclosureRisk")              # 전 상장사
    dartlab.scan("disclosureRisk", "005930")    # 삼성전자만
"""

from __future__ import annotations

import polars as pl

from dartlab.scan._helpers import _ensureScanData

# 심각 키워드 (audit 안전 67%가 미감지 — 실험 107-002 검증)
_SEVERE_KEYWORDS = ["횡령", "배임", "과징금", "손해배상"]


def _gradeRisk(activeCount: int, hasSevereKeyword: bool) -> str:
    """활성 시그널 수 + 심각 키워드 → 등급."""
    if hasSevereKeyword or activeCount >= 3:
        return "고위험"
    if activeCount >= 1:
        return "주의"
    return "안정"


def _calcChronicYears(fullDf: pl.DataFrame) -> pl.DataFrame:
    """전 기간 우발부채 연속 증가 연수 계산."""
    contingent_yearly = (
        fullDf.filter(pl.col("sectionTitle").str.contains("우발부채") & (pl.col("sizeDelta") > 0))
        .group_by(["stockCode", "toPeriod"])
        .agg(pl.col("sizeDelta").sum().alias("delta"))
    )

    if contingent_yearly.is_empty():
        return pl.DataFrame(schema={"stockCode": pl.Utf8, "chronicYears": pl.Int64})

    rows: list[dict] = []
    for code in contingent_yearly["stockCode"].unique().to_list():
        years = contingent_yearly.filter(pl.col("stockCode") == code).height
        if years >= 3:
            rows.append({"stockCode": code, "chronicYears": years})

    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={"stockCode": pl.Utf8, "chronicYears": pl.Int64})


def _calcRiskKeyword(latest: pl.DataFrame, prev: pl.DataFrame) -> pl.DataFrame:
    """리스크 키워드 신규 등장 탐지 (전년 대비 차분)."""
    now_stocks: set[str] = set()
    prev_stocks: set[str] = set()

    for kw in _SEVERE_KEYWORDS:
        now_stocks |= set(latest.filter(pl.col("preview").str.contains(kw))["stockCode"].unique().to_list())
        prev_stocks |= set(prev.filter(pl.col("preview").str.contains(kw))["stockCode"].unique().to_list())

    new_stocks = now_stocks - prev_stocks
    if not new_stocks:
        return pl.DataFrame(schema={"stockCode": pl.Utf8, "riskKeyword": pl.Int8})

    return pl.DataFrame({"stockCode": list(new_stocks), "riskKeyword": [1] * len(new_stocks)})


def scanDisclosureRisk(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 공시 변화 리스크 스캔.

    changes.parquet에서 최신 기간의 공시 변화를 분석하여
    6개 선행 리스크 시그널과 종합 등급을 반환한다.

    컬럼: stockCode, contingentDebt, chronicYears, riskKeyword,
          auditStruct, affiliateChange, bizPivot, activeSignals, grade
    """
    scanDir = _ensureScanData()
    changesPath = scanDir / "changes.parquet"

    if not changesPath.exists():
        if verbose:
            print("changes.parquet 없음 — 공시리스크 스캔 불가")
        return _emptyDf()

    if verbose:
        print("공시리스크 스캔: changes.parquet 로드...")

    fullDf = pl.read_parquet(str(changesPath))

    # 최신 기간 자동 탐지
    latestTo = fullDf["toPeriod"].max()
    latestFrom = str(int(latestTo) - 1)
    changes = fullDf.filter((pl.col("fromPeriod") == latestFrom) & (pl.col("toPeriod") == latestTo))

    # 이전 기간 (키워드 차분용)
    prevTo = latestFrom
    prevFrom = str(int(prevTo) - 1)
    prevChanges = fullDf.filter((pl.col("fromPeriod") == prevFrom) & (pl.col("toPeriod") == prevTo))

    if changes.is_empty():
        del fullDf
        return _emptyDf()

    if verbose:
        print(f"  기간: {latestFrom}→{latestTo}, {changes['stockCode'].n_unique()}종목")

    # ── 시그널 계산 ──

    # 1. contingentDebt: 우발부채 섹션 sizeDelta > 0 합
    contingent = (
        changes.filter(pl.col("sectionTitle").str.contains("우발부채") & (pl.col("sizeDelta") > 0))
        .group_by("stockCode")
        .agg(pl.col("sizeDelta").sum().alias("contingentDebt"))
    )

    # 2. chronicYears: 전 기간 우발부채 연속 증가 연수
    chronic = _calcChronicYears(fullDf)

    # 3. riskKeyword: 심각 키워드 신규 등장
    keyword = _calcRiskKeyword(changes, prevChanges)

    del fullDf, prevChanges

    # 4. auditStruct: 감사/내부통제 structural 3건 이상
    auditStruct = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("감사") | pl.col("sectionTitle").str.contains("내부통제"))
            & (pl.col("changeType") == "structural")
        )
        .group_by("stockCode")
        .agg(pl.len().alias("auditStruct"))
        .filter(pl.col("auditStruct") >= 3)
    )

    # 5. affiliateChange: 계열/타법인 numeric 변화
    affiliate = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("계열") | pl.col("sectionTitle").str.contains("타법인출자"))
            & (pl.col("changeType") == "numeric")
        )
        .group_by("stockCode")
        .agg(pl.len().alias("affiliateChange"))
    )

    # 6. bizPivot: 사업의 내용 |sizeDelta| > 5000
    bizPivot = (
        changes.filter(pl.col("sectionTitle").str.contains("사업의") & (pl.col("sizeDelta").abs() > 5000))
        .group_by("stockCode")
        .agg(pl.col("sizeDelta").abs().max().alias("bizPivot"))
    )

    del changes

    # ── 병합 + 등급 ──

    allCodes = pl.DataFrame(
        {
            "stockCode": list(
                set(contingent["stockCode"].to_list())
                | set(chronic["stockCode"].to_list())
                | set(keyword["stockCode"].to_list())
                | set(auditStruct["stockCode"].to_list())
                | set(affiliate["stockCode"].to_list())
                | set(bizPivot["stockCode"].to_list())
            )
        }
    )

    result = allCodes
    for right in [contingent, chronic, keyword, auditStruct, affiliate, bizPivot]:
        result = result.join(right, on="stockCode", how="left")

    result = result.fill_null(0)

    # 활성 시그널 수 (6개)
    result = result.with_columns(
        (
            (pl.col("contingentDebt") > 0).cast(pl.Int8)
            + (pl.col("chronicYears") >= 3).cast(pl.Int8)
            + (pl.col("riskKeyword") > 0).cast(pl.Int8)
            + (pl.col("auditStruct") > 0).cast(pl.Int8)
            + (pl.col("affiliateChange") > 0).cast(pl.Int8)
            + (pl.col("bizPivot") > 0).cast(pl.Int8)
        ).alias("activeSignals")
    )

    # 등급 (심각 키워드는 단독으로도 고위험)
    rows = []
    for row in result.iter_rows(named=True):
        hasSevere = row["riskKeyword"] > 0
        rows.append({**row, "grade": _gradeRisk(row["activeSignals"], hasSevere)})

    result = pl.DataFrame(rows).sort("activeSignals", descending=True)

    if verbose:
        grade_dist = result["grade"].value_counts()
        for r in grade_dist.to_dicts():
            print(f"  {r['grade']}: {r['count']}종목")
        print(f"공시리스크 스캔 완료: {result.height}종목")

    return result


def _emptyDf() -> pl.DataFrame:
    """빈 결과."""
    return pl.DataFrame(
        schema={
            "stockCode": pl.Utf8,
            "contingentDebt": pl.Int64,
            "chronicYears": pl.Int64,
            "riskKeyword": pl.Int8,
            "auditStruct": pl.Int64,
            "affiliateChange": pl.Int64,
            "bizPivot": pl.Int64,
            "activeSignals": pl.Int8,
            "grade": pl.Utf8,
        }
    )


__all__ = ["scanDisclosureRisk"]
