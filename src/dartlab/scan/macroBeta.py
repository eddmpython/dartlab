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

from dartlab.core.polarsUtil import isEmptyDf
from dartlab.scan.io.parquet import preferConsolidatedPerCompany

log = logging.getLogger(__name__)


def scanMacroBeta(
    *,
    stockCode: str | None = None,
) -> pl.DataFrame:
    """전종목 거시경제 베타 횡단면 계산.

    각 종목의 매출 성장률 vs GDP/금리/환율 변화율 간 OLS 베타를 계산한다.

    Parameters
    ----------
    stockCode : str, optional
        특정 종목만 필터 (None이면 전종목).

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        companyName : str — 회사명
        sector : str — 섹터
        gdpBeta : float — GDP 베타 계수
        rateBeta : float — 금리 베타 계수
        fxBeta : float — 환율 베타 계수
        rSquared : float — 결정계수 R²
        nObs : int — 유효 관측치 수
        confidence : str — 신뢰도 (high/medium/low)

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 또는 macro/ecos series 로드 실패 시 빈 DataFrame 반환.

    Examples
    --------
    >>> import dartlab
    >>> dartlab.Ecos().series("GDP", enrich=True)  # 사전 수집
    >>> df = dartlab.scan("macroBeta")
    >>> df.filter(pl.col("gdpBeta").abs() > 1.5).select(["stockCode", "gdpBeta"])

    Capabilities:
        - 전종목 매출 시계열 (연간) vs 거시 3 지표 (GDP/금리/환율) 변화율 간 OLS 베타 계산.
          R² + 유효 관측치 수 로 신뢰도 등급. 최소 4 개년 연간 데이터 필요.
        - GDP 베타 > 1.5 = 경기 민감주, < 0.5 = 방어주. 금리/환율 베타도 동일 해석.

    AIContext:
        Agent 가 ``dartlab.scan("macroBeta")`` 호출 시 본 함수 dispatch. 경기 민감/방어주 분류,
        매크로 시나리오 분석 source (금리 인상 시 영향 추정 등). 사전 ``Ecos().series("GDP",
        enrich=True)`` 필요 — 거시지표 캐시 없으면 빈 DataFrame.

    Guide:
        - 4 개년 미만 시계열은 베타 계산 skip — 신규 상장주는 결과 없음.
        - R² 낮으면 confidence "low" — 호출자가 신뢰도 명시 사용 권장.
        - stockCode 인자로 단일 종목만 빠르게 계산도 가능.

    When:
        매크로 시나리오 분석 시. 경기 민감/방어주 watchlist 작성 시. 단일 종목이면 ``stockCode``
        인자로.

    How:
        ``_ensureScanData`` → finance.parquet 매출 시계열 로드 → 연간 컬럼 추출 (4 개년+ 필수) →
        Ecos 거시지표 캐시 로드 → 변화율 계산 → 종목별 OLS (매출 변화율 vs 3 macro 변화율) →
        gdpBeta/rateBeta/fxBeta/R² + nObs + confidence 분기.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출)
        - Ecos series cache (``Ecos().series("GDP", enrich=True)`` 사전 호출)

    SeeAlso:
        - :class:`dartlab.macro.Ecos` — 거시지표 source
        - :func:`dartlab.scan.financial.profitability.scanProfitability` — 절대 수익성 (보완)
    """
    from dartlab.scan.io.parquet import _ensureScanData

    # 전종목 매출 시계열 로드 (프리빌드 finance.parquet에서 추출)
    try:
        revDf = _loadRevenueSeries(_ensureScanData())
    except (pl.exceptions.PolarsError, OSError, FileNotFoundError, KeyError) as exc:
        log.warning("매출 시계열 로드 실패: %s", exc)
        return _emptyDf()

    if isEmptyDf(revDf):
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
                "rSquared": round(rSq, 4) if rSq is not None else None,
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

    Parameters
    ----------
    scanDir : Path
        scan 프리빌드 디렉토리.

    Returns
    -------
    pl.DataFrame | None
        stockCode : str — 종목코드
        companyName : str — 회사명
        sector : str — 섹터
        {year}A : float — 연도별 매출 (원). 컬럼명 예: "2024A"
        데이터 없으면 None.
    """
    from dartlab.scan.io.parquet import collectScan, financeScanPath, lazyParquet, parquetColumns, parseNumStr

    scanPath = financeScanPath(scanDir)
    if not scanPath.exists():
        return None

    schema = parquetColumns(scanPath)
    scCol = "stockCode"

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

    target = collectScan(
        lazyParquet(scanPath).filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(list(REVENUE_IDS)) | pl.col("account_nm").is_in(list(REVENUE_NMS)))
        )
    )
    if target.is_empty():
        return None

    # 연결 우선
    # 회사별 연결 우선. 유니버스 전체로 한 번에 좁히면 별도만 내는 회사가
    # 다른 회사 때문에 사라진다.
    target = preferConsolidatedPerCompany(target, scCol)

    # 종목-연도별 매출 pivot
    rows: dict[str, dict] = {}
    for row in target.iter_rows(named=True):
        code = row.get(scCol, "")
        year = row.get("bsns_year", "")
        val = parseNumStr(row.get("thstrm_amount"))
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
    """Parquet 캐시에서 거시지표 로드 + 기간 정렬.

    Parameters
    ----------
    periodCols : list[str]
        기간 컬럼명 목록 (예: ["2024A", "2023A", ...]).

    Returns
    -------
    dict[str, list[float | None]] | None
        {gdp: [...], rate: [...], fx: [...]} — 기간별 값.
        유효 데이터 없으면 None.
    """
    from dartlab.gather.transforms.macro import alignToFinancialPeriods, loadMacroParquet

    indicators = {"gdp": "GDP", "rate": "BASE_RATE", "fx": "USDKRW"}
    result: dict[str, list[float | None]] = {}

    for key, indicatorId in indicators.items():
        df = loadMacroParquet(indicatorId, source="ecos")
        if isEmptyDf(df):
            result[key] = [None] * len(periodCols)
            continue

        aligned = alignToFinancialPeriods(df, periodCols)
        result[key] = aligned.get_column("value").to_list()

    # 회귀는 세 지표를 다 쓴다. 하나라도 통째로 비면 종목마다 관측이 모자라 전 종목이
    # 탈락하고 결과가 빈 표가 된다. 예전에는 `any` 로 검사해서 셋 중 하나만 있어도 통과했고,
    # 그래서 호출부의 "거시지표 캐시 없음" 경고가 안 울린 채 조용히 빈 표만 나왔다.
    # 실측 예: ECOS manifest 의 GDP 가 status ok 인데 관측 0 행이라, 금리와 환율이 멀쩡한데도
    # `scan("macroBeta")` 가 전종목 빈 표를 냈다. 어느 지표가 빈 것인지도 드러나지 않았다.
    missing = [key for key, vals in result.items() if not any(v is not None for v in vals)]
    if missing:
        log.warning("거시지표 결측으로 베타 계산 불가: %s (나머지는 정상)", ", ".join(sorted(missing)))
        return None
    return result


def _calcMacroChanges(macroData: dict[str, list[float | None]]) -> dict[str, list[float | None]]:
    """거시지표 전년대비 변화율.

    Parameters
    ----------
    macroData : dict[str, list[float | None]]
        {gdp/rate/fx: 기간별 값}.

    Returns
    -------
    dict[str, list[float | None]]
        {gdp/rate/fx: YoY 변화율(%)} — 금리(rate)는 차분(pp).
    """
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
    """간이 OLS 회귀 (scan 용, 속도 우선).

    Parameters
    ----------
    y : list[float | None]
        종속변수 (매출 성장률).
    macroChanges : dict[str, list[float | None]]
        독립변수 {gdp/rate/fx: 변화율}.

    Returns
    -------
    tuple[dict[str, float] | None, float | None]
        (betas, rSquared) — betas: {gdp: β, rate: β, fx: β}.
        유효 관측치 3개 미만이면 (None, None).
    """
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
    """4x4 가우스-조르단 역행렬.

    Parameters
    ----------
    m : list[list[float]]
        4x4 정방행렬.

    Returns
    -------
    list[list[float]] | None
        4x4 역행렬. 특이행렬이면 None.
    """
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
    """빈 결과 DataFrame.

    Returns
    -------
    pl.DataFrame
        scanMacroBeta 스키마와 동일한 빈 DataFrame
        (stockCode, companyName, sector, gdpBeta, rateBeta, fxBeta, rSquared, nObs, confidence).
    """
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
