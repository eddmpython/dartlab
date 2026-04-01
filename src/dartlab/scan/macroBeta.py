"""scan macroBeta — 전종목 거시경제 베타 횡단면.

사전 조건: ECOS 거시지표 Parquet 캐시 (~/.dartlab/cache/macro/ecos/)가 존재해야 함.
``Ecos().series("GDP", enrich=True)`` 등으로 사전 수집.

사용법::

    dartlab.scan("macroBeta")              # 전종목 GDP/금리/환율 베타
    dartlab.scan("macroBeta", "005930")    # 삼성전자만 필터
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

log = logging.getLogger(__name__)


def scan_macroBeta(
    *,
    stockCode: str | None = None,
) -> pl.DataFrame:
    """전종목 거시경제 베타 횡단면 계산.

    각 종목의 매출 성장률 vs GDP/금리/환율 변화율 간 OLS 베타를 계산한다.
    scan 데이터(ratioSeries)에서 매출 시계열을 가져오고,
    Parquet 캐시에서 거시지표를 로드한다.

    Returns:
        DataFrame with columns:
        - stockCode, companyName, sector
        - gdpBeta, rateBeta, fxBeta
        - rSquared, nObs, confidence
    """
    from dartlab.scan._helpers import _ensureScanData

    # 전종목 매출 시계열 로드 (프리빌드 finance.parquet에서 추출)
    try:
        revDf = _loadRevenueSeries(_ensureScanData())
    except Exception as exc:
        log.warning("매출 시계열 로드 실패: %s", exc)
        return _emptyDf()

    if revDf is None or revDf.is_empty():
        return _emptyDf()

    # stockCode 필터
    if stockCode:
        revDf = revDf.filter(pl.col("stockCode") == stockCode)
        if revDf.is_empty():
            return _emptyDf()

    # 기간 컬럼 추출 (연간)
    periodCols = [c for c in revDf.columns if c.endswith("A") and c[:4].isdigit()]
    periodCols.sort(reverse=True)
    if len(periodCols) < 4:
        log.warning("연간 기간 컬럼 부족: %d개", len(periodCols))
        return _emptyDf()

    # 거시지표 로드 (Parquet 캐시)
    macroData = _loadMacroForScan(periodCols)
    if macroData is None:
        log.warning("거시지표 캐시 없음. Ecos().series('GDP', enrich=True) 먼저 실행")
        return _emptyDf()

    # 거시 변화율 계산
    macroChanges = _calcMacroChanges(macroData)

    # 종목별 OLS
    rows: list[dict] = []
    for row in revDf.iter_rows(named=True):
        code = row.get("stockCode", "")
        name = row.get("companyName", "")
        sector = row.get("sector", "")

        # 매출 성장률 계산
        revGrowth = []
        for i in range(len(periodCols) - 1):
            cur = row.get(periodCols[i])
            prev = row.get(periodCols[i + 1])
            if cur is not None and prev is not None and prev != 0:
                revGrowth.append((cur - prev) / abs(prev) * 100)
            else:
                revGrowth.append(None)

        # OLS 회귀
        betas, rSq = _quickOLS(revGrowth, macroChanges)
        if betas is None:
            continue

        nValid = sum(1 for g in revGrowth if g is not None)
        confidence = "high" if nValid >= 8 and (rSq or 0) > 0.3 else ("medium" if nValid >= 5 else "low")

        rows.append(
            {
                "stockCode": code,
                "companyName": name,
                "sector": sector,
                "gdpBeta": round(betas.get("gdp", 0), 3),
                "rateBeta": round(betas.get("rate", 0), 3),
                "fxBeta": round(betas.get("fx", 0), 3),
                "rSquared": round(rSq or 0, 4),
                "nObs": nValid,
                "confidence": confidence,
            }
        )

    if not rows:
        return _emptyDf()

    result = pl.DataFrame(rows).sort("gdpBeta", descending=True)
    return result


def _loadRevenueSeries(scanDir: Path) -> pl.DataFrame | None:
    """프리빌드 finance.parquet에서 종목별 매출 시계열 추출.

    Returns:
        DataFrame with columns: stockCode, companyName, sector, <yearA>, ...
    """
    from dartlab.scan._helpers import parse_num

    scanPath = scanDir / "finance.parquet"
    if not scanPath.exists():
        return None

    schema = pl.scan_parquet(str(scanPath)).collect_schema().names()
    scCol = "stockCode" if "stockCode" in schema else "stock_code"

    REVENUE_IDS = {
        "Revenue",
        "Revenues",
        "revenue",
        "revenues",
        "ifrs-full_Revenue",
        "dart_Revenue",
        "RevenueFromContractsWithCustomers",
    }
    REVENUE_NMS = {"매출액", "수익(매출액)", "영업수익", "매출", "순영업수익"}

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(list(REVENUE_IDS)) | pl.col("account_nm").is_in(list(REVENUE_NMS)))
        )
        .collect()
    )
    if target.is_empty():
        return None

    # 연결 우선
    cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
    if not cfs.is_empty():
        target = cfs

    # 종목-연도별 매출 pivot
    rows: dict[str, dict] = {}
    for row in target.iter_rows(named=True):
        code = row.get(scCol, "")
        year = row.get("bsns_year", "")
        val = parse_num(row.get("thstrm_amount"))
        if not code or not year or val is None:
            continue
        if code not in rows:
            rows[code] = {"stockCode": code, "companyName": "", "sector": ""}
        colName = f"{year}A"
        if colName not in rows[code] or val > 0:
            rows[code][colName] = val

    if not rows:
        return None

    return pl.DataFrame(list(rows.values()))


def _loadMacroForScan(periodCols: list[str]) -> dict[str, list[float | None]] | None:
    """Parquet 캐시에서 거시지표 로드 + 기간 정렬."""
    from dartlab.gather.macro import alignToFinancialPeriods, loadMacroParquet

    indicators = {"gdp": "GDP", "rate": "BASE_RATE", "fx": "USDKRW"}
    result: dict[str, list[float | None]] = {}

    for key, indicatorId in indicators.items():
        df = loadMacroParquet(indicatorId, source="ecos")
        if df is None or df.is_empty():
            result[key] = [None] * len(periodCols)
            continue

        aligned = alignToFinancialPeriods(df, periodCols)
        result[key] = aligned.get_column("value").to_list()

    hasData = any(any(v is not None for v in vals) for vals in result.values())
    return result if hasData else None


def _calcMacroChanges(macroData: dict[str, list[float | None]]) -> dict[str, list[float | None]]:
    """거시지표 전년대비 변화율."""
    changes: dict[str, list[float | None]] = {}
    for key, vals in macroData.items():
        ch = []
        for i in range(len(vals) - 1):
            cur, prev = vals[i], vals[i + 1]
            if cur is not None and prev is not None and prev != 0:
                if key == "rate":
                    ch.append(cur - prev)
                else:
                    ch.append((cur - prev) / abs(prev) * 100)
            else:
                ch.append(None)
        changes[key] = ch
    return changes


def _quickOLS(
    y: list[float | None],
    macroChanges: dict[str, list[float | None]],
) -> tuple[dict[str, float] | None, float | None]:
    """간이 OLS (scan 용, 속도 우선)."""
    n = min(len(y), *(len(v) for v in macroChanges.values()))
    validY: list[float] = []
    validX: list[list[float]] = []

    for i in range(n):
        yVal = y[i]
        xVals = [macroChanges[k][i] for k in ["gdp", "rate", "fx"]]
        if yVal is not None and all(x is not None for x in xVals):
            validY.append(yVal)
            validX.append(xVals)

    if len(validY) < 3:
        return None, None

    nObs = len(validY)
    k = 4
    X = [[1.0] + row for row in validX]

    XtX = [[sum(X[r][i] * X[r][j] for r in range(nObs)) for j in range(k)] for i in range(k)]
    Xty = [sum(X[r][i] * validY[r] for r in range(nObs)) for i in range(k)]

    inv = _invertMatrix4(XtX)
    if inv is None:
        return None, None

    beta = [sum(inv[i][j] * Xty[j] for j in range(k)) for i in range(k)]

    yMean = sum(validY) / nObs
    ssTot = sum((y_ - yMean) ** 2 for y_ in validY)
    yPred = [sum(X[r][j] * beta[j] for j in range(k)) for r in range(nObs)]
    ssRes = sum((validY[r] - yPred[r]) ** 2 for r in range(nObs))
    rSq = 1 - ssRes / ssTot if ssTot > 0 else 0.0

    return {"gdp": beta[1], "rate": beta[2], "fx": beta[3]}, rSq


def _invertMatrix4(m: list[list[float]]) -> list[list[float]] | None:
    """4x4 가우스-조르단 역행렬."""
    n = len(m)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        maxRow = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[maxRow][col]) < 1e-12:
            return None
        aug[col], aug[maxRow] = aug[maxRow], aug[col]
        pivot = aug[col][col]
        aug[col] = [x / pivot for x in aug[col]]
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                aug[row] = [aug[row][j] - factor * aug[col][j] for j in range(2 * n)]
    return [row[n:] for row in aug]


def _emptyDf() -> pl.DataFrame:
    """빈 결과 DataFrame."""
    return pl.DataFrame(
        schema={
            "stockCode": pl.Utf8,
            "companyName": pl.Utf8,
            "sector": pl.Utf8,
            "gdpBeta": pl.Float64,
            "rateBeta": pl.Float64,
            "fxBeta": pl.Float64,
            "rSquared": pl.Float64,
            "nObs": pl.Int64,
            "confidence": pl.Utf8,
        }
    )
