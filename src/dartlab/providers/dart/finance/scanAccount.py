"""전종목 단일 계정/비율 연간 시계열 배치 추출.

finance parquet 2,744개를 병렬 읽기하여
특정 snakeId 하나의 전종목 × 연도 시계열 DataFrame을 생성한다.

Q4 사업보고서 thstrm_amount = 연간 누적값이므로 standalone 변환 불필요.

설계: ThreadPool I/O + 파일별 즉시 필터(CFS+account 매칭)
      → concat 대상 ~25K행 → 메모리 +135MB, 속도 ~3초
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

from dartlab.providers.dart.finance.mapper import (
    ACCOUNT_NAME_SYNONYMS,
    ID_SYNONYMS,
    AccountMapper,
)

_log = logging.getLogger(__name__)


def _joinCorpName(df: pl.DataFrame) -> pl.DataFrame:
    """stockCode에 회사명(corpName) 컬럼 추가."""
    try:
        from dartlab.gather.listing import getKindList

        kindDf = getKindList().select(
            pl.col("종목코드").alias("stockCode"),
            pl.col("회사명").alias("corpName"),
        )
        yearCols = [c for c in df.columns if c != "stockCode"]
        return df.join(kindDf, on="stockCode", how="left").select(["stockCode", "corpName"] + yearCols)
    except (ImportError, OSError, pl.exceptions.PolarsError):
        _log.debug("kindList 매핑 실패 — corpName 없이 반환")
        return df


_SCAN_COLS = [
    "sj_div",
    "fs_div",
    "fs_nm",
    "account_id",
    "account_nm",
    "bsns_year",
    "thstrm_amount",
    "thstrm_add_amount",
    "reprt_nm",
]

_REPRT_TO_Q = {"1분기": "Q1", "2분기": "Q2", "3분기": "Q3", "4분기": "Q4"}


def _resolveSjDiv(snakeId: str) -> str:
    """sortOrder.json에서 snakeId → sjDiv 자동 결정."""
    from dartlab.core.finance.ordering import _ensureLoaded

    data = _ensureLoaded()
    for sjDiv in ("IS", "BS", "CF"):
        if snakeId in data.get(sjDiv, {}):
            return sjDiv
    msg = f"snakeId '{snakeId}'를 sortOrder.json에서 찾을 수 없습니다"
    raise ValueError(msg)


def _parseAmount(val: str | None) -> float | None:
    """문자열 금액 → float. 쉼표 제거, 빈값 → None."""
    if val is None:
        return None
    cleaned = str(val).replace(",", "").strip()
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _buildFastKeys(snakeId: str) -> set[str]:
    """snakeId에 매핑되는 모든 원본 키를 사전 수집 (O(1) set lookup)."""
    mapper = AccountMapper.get()
    mappings = mapper._mappings or {}

    directKeys: set[str] = set()
    for key, sid in mappings.items():
        if sid == snakeId:
            directKeys.add(key)

    allKeys = set(directKeys)
    for synonym, canonical in ACCOUNT_NAME_SYNONYMS.items():
        if canonical in directKeys:
            allKeys.add(synonym)

    for synonym, canonical in ID_SYNONYMS.items():
        if canonical in directKeys:
            allKeys.add(synonym)
            for prefix in ("ifrs-full_", "ifrs_", "dart_", "ifrs-smes_"):
                allKeys.add(prefix + synonym)

    for key in list(directKeys):
        for prefix in ("ifrs-full_", "ifrs_", "dart_", "ifrs-smes_"):
            allKeys.add(prefix + key)

    return allKeys


def _parseAmountCol(col: str) -> pl.Expr:
    """금액 문자열 컬럼 → Float64."""
    return (
        pl.col(col)
        .cast(pl.Utf8)
        .str.replace_all(",", "")
        .str.strip_chars()
        .pipe(lambda s: pl.when(s == "").then(None).when(s == "-").then(None).otherwise(s))
        .cast(pl.Float64, strict=False)
    )


class _FileProcessor:
    """파일별 처리: I/O → CFS → account 매칭 → 금액 파싱."""

    __slots__ = ("filterDivs", "fsPref", "fastKeysNm", "fastKeysId", "quarterly", "sjDiv")

    def __init__(
        self,
        filterDivs: list[str],
        fsPref: str,
        fastKeys: set[str],
        *,
        quarterly: bool = False,
        sjDiv: str = "IS",
    ):
        self.filterDivs = filterDivs
        self.fsPref = fsPref
        # fastKeys를 nm/id 리스트로 분리 (scan_parquet is_in용)
        self.fastKeysNm = list(fastKeys)
        self.fastKeysId = list(fastKeys)
        self.quarterly = quarterly
        self.sjDiv = sjDiv

    def __call__(self, pf: Path) -> pl.DataFrame | None:
        stockCode = pf.stem
        try:
            cols = _SCAN_COLS if self.quarterly else [c for c in _SCAN_COLS if c != "thstrm_add_amount"]
            # account 필터를 scan 단계에서 밀어넣어 I/O 최소화
            lz = (
                pl.scan_parquet(str(pf))
                .select(cols)
                .filter(
                    pl.col("sj_div").is_in(self.filterDivs)
                    & (pl.lit(True) if self.quarterly else pl.col("reprt_nm") == "4분기")
                    & (pl.col("account_nm").is_in(self.fastKeysNm) | pl.col("account_id").is_in(self.fastKeysId))
                )
            )
            df = lz.collect()
        except (pl.exceptions.PolarsError, OSError):
            return None

        if df.is_empty():
            return None

        # CFS/OFS: 연결재무제표가 있으면 연결만, 없으면 별도
        cfsLabel = "연결" if self.fsPref == "CFS" else "재무제표"
        cfs = df.filter(pl.col("fs_nm").str.contains(cfsLabel))
        if cfs.height > 0:
            df = cfs

        if df.is_empty():
            return None

        if self.quarterly:
            return self._parseQuarterly(df, stockCode)
        return self._parseAnnual(df, stockCode)

    def _parseAnnual(self, matched: pl.DataFrame, stockCode: str) -> pl.DataFrame | None:
        """연간: thstrm_amount (4분기 사업보고서)."""
        parsed = matched.with_columns(_parseAmountCol("thstrm_amount").alias("amount")).filter(
            pl.col("amount").is_not_null()
        )

        if parsed.is_empty():
            return None

        return parsed.select(
            pl.lit(stockCode).alias("stockCode"),
            pl.col("bsns_year").cast(pl.Utf8).alias("period"),
            pl.col("amount"),
        )

    def _parseQuarterly(self, matched: pl.DataFrame, stockCode: str) -> pl.DataFrame | None:
        """분기: standalone 금액 산출.

        IS/CIS 1~3분기: thstrm_amount = 당분기 standalone
        IS/CIS 4분기: standalone = thstrm_amount - 3분기 thstrm_add_amount
        BS: 시점 잔액 → thstrm_amount 그대로
        CF: thstrm_amount = 당분기 standalone (IS와 동일 패턴)
        """
        parsed = matched.with_columns(
            _parseAmountCol("thstrm_amount").alias("_thstrm"),
            _parseAmountCol("thstrm_add_amount").alias("_addAmount"),
        )

        isBs = self.sjDiv == "BS"
        rows: list[dict] = []

        for year in parsed["bsns_year"].unique().sort().to_list():
            yearDf = parsed.filter(pl.col("bsns_year") == year)

            for reprt in ["1분기", "2분기", "3분기", "4분기"]:
                qDf = yearDf.filter(pl.col("reprt_nm") == reprt)
                if qDf.is_empty():
                    continue

                thstrm = qDf["_thstrm"][0]
                addAmount = qDf["_addAmount"][0] if "_addAmount" in qDf.columns else None

                if thstrm is None:
                    continue

                qLabel = _REPRT_TO_Q[reprt]
                period = f"{year}{qLabel}"

                if isBs or reprt != "4분기":
                    # BS: 잔액 그대로, IS/CF 1~3분기: thstrm = standalone
                    rows.append({"stockCode": stockCode, "period": period, "amount": thstrm})
                else:
                    # IS/CF 4분기: 연간 - 3분기 누적 = Q4 standalone
                    q3 = yearDf.filter(pl.col("reprt_nm") == "3분기")
                    if q3.is_empty() or q3["_addAmount"][0] is None:
                        rows.append({"stockCode": stockCode, "period": period, "amount": thstrm})
                    else:
                        q4Standalone = thstrm - q3["_addAmount"][0]
                        rows.append({"stockCode": stockCode, "period": period, "amount": q4Standalone})

        if not rows:
            return None
        return pl.DataFrame(rows)


def _resolveSnakeId(nameOrId: str) -> str:
    """한글 계정명/영문 snakeId → 정규 snakeId 변환."""
    # 이미 snakeId면 그대로
    if nameOrId.isascii() and "_" in nameOrId:
        return nameOrId

    # mapper로 한글 → snakeId 변환
    mapper = AccountMapper.get()
    # 한글명 우선
    normalizedNm = ACCOUNT_NAME_SYNONYMS.get(nameOrId, nameOrId)
    if normalizedNm in (mapper._mappings or {}):
        return mapper._mappings[normalizedNm]
    # 공백 제거 후 재시도
    noSpace = normalizedNm.replace(" ", "")
    if noSpace in (mapper._mappings or {}):
        return mapper._mappings[noSpace]
    # 영문 ID로도 시도
    stripped = nameOrId.lower().replace("-", "").replace(" ", "")
    normalizedId = ID_SYNONYMS.get(stripped, stripped)
    if normalizedId in (mapper._mappings or {}):
        return mapper._mappings[normalizedId]

    # 변환 실패 시 원본 반환 (이후 _resolveSjDiv에서 에러)
    return nameOrId


def _scanAccountFromMerged(
    scanPath: Path,
    snakeId: str,
    sjDiv: str,
    filterDivs: list[str],
    fsPref: str,
    fastKeys: set[str],
    *,
    annual: bool = False,
) -> pl.DataFrame | None:
    """scan/finance.parquet에서 단일 계정 시계열 추출 (가속 경로).

    기존 _FileProcessor 로직을 단일 DataFrame에서 재현한다.
    실패 시 None을 반환하여 fallback으로 넘긴다.
    """
    try:
        schema = pl.scan_parquet(str(scanPath)).collect_schema()
        scCol = "stockCode" if "stockCode" in schema.names() else "stock_code"

        lz = pl.scan_parquet(str(scanPath)).filter(
            pl.col("sj_div").is_in(filterDivs)
            & (pl.col("account_nm").is_in(list(fastKeys)) | pl.col("account_id").is_in(list(fastKeys)))
        )

        if annual:
            lz = lz.filter(pl.col("reprt_nm") == "4분기")

        df = lz.collect()
    except (pl.exceptions.PolarsError, OSError, FileNotFoundError):
        return None

    if df.is_empty():
        return None

    # CFS/OFS 우선: 종목별로 연결재무제표가 있으면 연결만
    cfsLabel = "연결" if fsPref == "CFS" else "재무제표"
    hasCfs = df.filter(pl.col("fs_nm").str.contains(cfsLabel)).select(scCol).unique().to_series().to_list()
    hasCfsSet = set(hasCfs)

    # 연결 있는 종목은 연결만, 없는 종목은 전체
    if hasCfsSet:
        cfsPart = df.filter(pl.col(scCol).is_in(list(hasCfsSet)) & pl.col("fs_nm").str.contains(cfsLabel))
        ofsPart = df.filter(~pl.col(scCol).is_in(list(hasCfsSet)))
        df = pl.concat([cfsPart, ofsPart]) if not ofsPart.is_empty() else cfsPart

    if df.is_empty():
        return None

    # 금액 파싱
    df = df.with_columns(_parseAmountCol("thstrm_amount").alias("amount"))

    if annual:
        # 연간: thstrm_amount (4분기 사업보고서) 그대로
        parsed = df.filter(pl.col("amount").is_not_null())
        if parsed.is_empty():
            return None
        result = (
            parsed.select(
                pl.col(scCol).alias("stockCode"),
                pl.col("bsns_year").cast(pl.Utf8).alias("period"),
                pl.col("amount"),
            )
            .group_by(["stockCode", "period"])
            .agg(pl.col("amount").first())
        )
    else:
        # 분기별 standalone 계산 — Polars 벡터 연산
        df = df.with_columns(_parseAmountCol("thstrm_add_amount").alias("_addAmount"))
        df = df.filter(pl.col("amount").is_not_null())
        if df.is_empty():
            return None

        isBs = sjDiv == "BS"

        # period 컬럼 생성
        qMap = pl.DataFrame({"reprt_nm": list(_REPRT_TO_Q.keys()), "_qLabel": list(_REPRT_TO_Q.values())})
        df = df.join(qMap, on="reprt_nm", how="inner")
        df = df.with_columns((pl.col("bsns_year").cast(pl.Utf8) + pl.col("_qLabel")).alias("period"))

        if isBs:
            # BS: 잔액 그대로
            result = df.select(
                pl.col(scCol).alias("stockCode"),
                pl.col("period"),
                pl.col("amount"),
            )
        else:
            # IS/CF: 1~3분기 thstrm = standalone, 4분기 = thstrm - Q3 addAmount
            notQ4 = df.filter(pl.col("reprt_nm") != "4분기").select(
                pl.col(scCol).alias("stockCode"),
                pl.col("period"),
                pl.col("amount"),
            )

            q4 = df.filter(pl.col("reprt_nm") == "4분기")
            q3Add = df.filter(pl.col("reprt_nm") == "3분기").select(
                pl.col(scCol).alias("_sc"),
                pl.col("bsns_year").alias("_by"),
                pl.col("_addAmount").alias("_q3add"),
            )
            q4j = q4.join(q3Add, left_on=[scCol, "bsns_year"], right_on=["_sc", "_by"], how="left")
            q4j = q4j.with_columns(
                pl.when(pl.col("_q3add").is_not_null())
                .then(pl.col("amount") - pl.col("_q3add"))
                .otherwise(pl.col("amount"))
                .alias("amount")
            ).select(
                pl.col(scCol).alias("stockCode"),
                pl.col("period"),
                pl.col("amount"),
            )
            result = pl.concat([notQ4, q4j])

    return result


def scanAccount(
    snakeId: str,
    *,
    sjDiv: str | None = None,
    fsPref: str = "CFS",
    annual: bool = False,
) -> pl.DataFrame:
    """전종목 단일 계정 시계열 추출.

    Args:
        snakeId: 계정 식별자. 영문("sales") 또는 한글("매출액") 모두 가능.
        sjDiv: 재무제표 구분 ("IS", "BS", "CF"). None이면 자동 결정.
        fsPref: 연결/별도 우선순위 ("CFS"=연결 우선, "OFS"=별도 우선)
        annual: True면 연간 (기본 False=분기별 standalone).

    Returns:
        stockCode | corpName | 2025Q4 | 2025Q3 | ... (분기, 기본)
        stockCode | corpName | 2025 | 2024 | ... (연간)
    """
    from dartlab.core.dataLoader import _dataDir

    snakeId = _resolveSnakeId(snakeId)

    if sjDiv is None:
        sjDiv = _resolveSjDiv(snakeId)

    filterDivs = ["IS", "CIS"] if sjDiv in ("IS", "CIS") else [sjDiv]
    fastKeys = _buildFastKeys(snakeId)

    # ── scan/finance.parquet 가속 경로 ──
    from dartlab.market._helpers import _ensureScanData

    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"
    allDf = None

    if scanPath.exists():
        allDf = _scanAccountFromMerged(
            scanPath,
            snakeId,
            sjDiv,
            filterDivs,
            fsPref,
            fastKeys,
            annual=annual,
        )
        if allDf is not None:
            _log.info("scanAccount('%s'): scan/finance.parquet 가속 경로 사용", snakeId)

    # ── fallback: 종목별 파일 순회 ──
    if allDf is None:
        financeDir = Path(_dataDir("finance"))
        parquetFiles = sorted(financeDir.glob("*.parquet"))

        if not parquetFiles:
            from dartlab.core.guidance import emit

            emit("hint:market_data_needed", category="finance", fn="scanAccount")
            return pl.DataFrame({"stockCode": []})

        processor = _FileProcessor(
            filterDivs,
            fsPref,
            fastKeys,
            quarterly=not annual,
            sjDiv=sjDiv,
        )

        _log.info("scanAccount('%s', annual=%s): %d 파일 스캔 시작 (fallback)", snakeId, annual, len(parquetFiles))

        with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as pool:
            chunks = [r for r in pool.map(processor, parquetFiles) if r is not None]

        if not chunks:
            return pl.DataFrame({"stockCode": []})

        allDf = pl.concat(chunks)

    # 기간당 첫 값 + pivot
    allDf = allDf.group_by(["stockCode", "period"]).agg(pl.col("amount").first())

    result = allDf.pivot(on="period", index="stockCode", values="amount")
    periodCols = sorted(c for c in result.columns if c != "stockCode")

    # 분기: 첫 연도에 Q4만 존재하면 제거 (불완전 분기)
    if not annual and periodCols:
        firstYear = periodCols[0][:4]
        firstYearQs = [c for c in periodCols if c.startswith(firstYear)]
        if len(firstYearQs) == 1 and firstYearQs[0].endswith("Q4"):
            periodCols = periodCols[1:]

    # 최신 먼저 역순 정렬
    periodCols = list(reversed(periodCols))
    result = result.select(["stockCode"] + periodCols)

    # 회사명 매핑 (kindList)
    result = _joinCorpName(result)

    _log.info(
        "scanAccount('%s'): %d종목 × %d기간",
        snakeId,
        result.height,
        len(periodCols),
    )

    return result


# ── scanRatio ──────────────────────────────────────────────────


_RATIO_DEFS: dict[str, dict] = {
    # 수익성
    "roe": {"numer": "net_income", "denom": "total_stockholders_equity", "pct": True, "label": "ROE"},
    "roa": {"numer": "net_income", "denom": "total_assets", "pct": True, "label": "ROA"},
    "operatingMargin": {
        "numer": "operating_profit",
        "denom": "sales",
        "pct": True,
        "label": "영업이익률",
    },
    "netMargin": {"numer": "net_income", "denom": "sales", "pct": True, "label": "순이익률"},
    "grossMargin": {"numer": "gross_profit", "denom": "sales", "pct": True, "label": "매출총이익률"},
    # 안정성
    "debtRatio": {
        "numer": "total_liabilities",
        "denom": "total_stockholders_equity",
        "pct": True,
        "label": "부채비율",
    },
    "currentRatio": {
        "numer": "current_assets",
        "denom": "current_liabilities",
        "pct": True,
        "label": "유동비율",
    },
    "equityRatio": {
        "numer": "total_stockholders_equity",
        "denom": "total_assets",
        "pct": True,
        "label": "자기자본비율",
    },
    # 성장성 (YoY)
    "revenueGrowth": {"base": "sales", "yoy": True, "pct": True, "label": "매출성장률"},
    "operatingProfitGrowth": {
        "base": "operating_profit",
        "yoy": True,
        "pct": True,
        "label": "영업이익성장률",
    },
    "netProfitGrowth": {
        "base": "net_income",
        "yoy": True,
        "pct": True,
        "label": "순이익성장률",
    },
    # 효율성
    "totalAssetTurnover": {
        "numer": "sales",
        "denom": "total_assets",
        "pct": False,
        "label": "총자산회전율",
    },
    # 현금흐름
    "operatingCfMargin": {
        "numer": "operating_cashflow",
        "denom": "sales",
        "pct": True,
        "label": "영업CF마진",
    },
}


def scanRatio(
    ratioName: str,
    *,
    fsPref: str = "CFS",
    annual: bool = False,
) -> pl.DataFrame:
    """전종목 단일 재무비율 시계열 추출.

    Args:
        ratioName: 비율 식별자. 지원 목록은 scanRatioList() 참조.
        fsPref: 연결/별도 우선순위 ("CFS"=연결 우선, "OFS"=별도 우선)
        annual: True면 연간 (기본 False=분기별).

    Returns:
        stockCode | corpName | 기간컬럼들...
    """
    if ratioName not in _RATIO_DEFS:
        available = ", ".join(sorted(_RATIO_DEFS))
        msg = f"지원하지 않는 비율: '{ratioName}'. 사용 가능: {available}"
        raise ValueError(msg)

    defn = _RATIO_DEFS[ratioName]

    if defn.get("yoy"):
        return _calcYoyRatio(defn, fsPref, annual=annual)
    return _calcSimpleRatio(defn, fsPref, annual=annual)


def scanRatioList() -> list[dict[str, str]]:
    """사용 가능한 비율 목록 반환."""
    return [{"name": k, "label": v["label"]} for k, v in _RATIO_DEFS.items()]


def _calcSimpleRatio(defn: dict, fsPref: str, *, annual: bool = False) -> pl.DataFrame:
    """분자/분모 비율 계산."""
    numer = scanAccount(defn["numer"], fsPref=fsPref, annual=annual)
    denom = scanAccount(defn["denom"], fsPref=fsPref, annual=annual)

    # corpName 제외하고 연도 컬럼만 추출
    numerYears = [c for c in numer.columns if c not in ("stockCode", "corpName")]
    denomYears = [c for c in denom.columns if c not in ("stockCode", "corpName")]
    commonYears = sorted(set(numerYears) & set(denomYears), reverse=True)

    if not commonYears:
        return pl.DataFrame({"stockCode": []})

    joined = numer.select(["stockCode"] + commonYears).join(
        denom.select(["stockCode"] + commonYears),
        on="stockCode",
        suffix="_d",
    )

    isPct = defn.get("pct", False)
    multiplier = 100.0 if isPct else 1.0

    resultExprs = [pl.col("stockCode")]
    for y in commonYears:
        expr = (
            pl.when((pl.col(f"{y}_d") != 0) & pl.col(f"{y}_d").is_not_null() & pl.col(y).is_not_null())
            .then((pl.col(y) / pl.col(f"{y}_d") * multiplier).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(y)
        )
        resultExprs.append(expr)

    result = joined.select(resultExprs)
    return _joinCorpName(result)


def _calcYoyRatio(defn: dict, fsPref: str, *, annual: bool = False) -> pl.DataFrame:
    """YoY 성장률 계산."""
    base = scanAccount(defn["base"], fsPref=fsPref, annual=annual)
    # base는 이미 최신 먼저 — YoY 계산은 오름차순 필요
    yearCols = sorted(c for c in base.columns if c not in ("stockCode", "corpName"))

    if len(yearCols) < 2:
        return pl.DataFrame({"stockCode": []})

    resultExprs = [pl.col("stockCode")]
    for i in range(1, len(yearCols)):
        cur = yearCols[i]
        prev = yearCols[i - 1]
        expr = (
            pl.when(
                (pl.col(prev) != 0) & pl.col(prev).is_not_null() & pl.col(cur).is_not_null() & (pl.col(prev).abs() > 0)
            )
            .then(((pl.col(cur) - pl.col(prev)) / pl.col(prev).abs() * 100).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(cur)
        )
        resultExprs.append(expr)

    # 최신 먼저 역순으로 컬럼 재배치
    yoyCols = [yearCols[i] for i in range(1, len(yearCols))]
    result = base.select(resultExprs).select(["stockCode"] + list(reversed(yoyCols)))
    return _joinCorpName(result)
