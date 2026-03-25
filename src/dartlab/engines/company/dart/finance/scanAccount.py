"""전종목 단일 계정/비율 연간 시계열 배치 추출.

finance parquet 2,744개를 병렬 읽기하여
특정 snakeId 하나의 전종목 × 연도 시계열 DataFrame을 생성한다.

Q4 사업보고서 thstrm_amount = 연간 누적값이므로 standalone 변환 불필요.

설계: ThreadPool I/O + 파일별 즉시 필터(CFS+account 매칭)
      → concat 대상 ~25K행 → 메모리 +135MB, 속도 ~3초
"""

from __future__ import annotations

import functools
import logging
import operator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.finance.mapper import (
    ACCOUNT_NAME_SYNONYMS,
    ID_SYNONYMS,
    AccountMapper,
)

_log = logging.getLogger(__name__)

_SCAN_COLS = [
    "sj_div",
    "fs_div",
    "fs_nm",
    "account_id",
    "account_nm",
    "bsns_year",
    "thstrm_amount",
    "reprt_nm",
]


def _resolveSjDiv(snakeId: str) -> str:
    """sortOrder.json에서 snakeId → sjDiv 자동 결정."""
    from dartlab.engines.common.finance.ordering import _ensureLoaded

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


class _FileProcessor:
    """파일별 처리: I/O → CFS → account 매칭 → 금액 파싱."""

    __slots__ = ("filterDivs", "fsPref", "fastKeys", "mapper", "snakeId")

    def __init__(
        self,
        filterDivs: list[str],
        fsPref: str,
        fastKeys: set[str],
        mapper: AccountMapper,
        snakeId: str,
    ):
        self.filterDivs = filterDivs
        self.fsPref = fsPref
        self.fastKeys = fastKeys
        self.mapper = mapper
        self.snakeId = snakeId

    def __call__(self, pf: Path) -> pl.DataFrame | None:
        stockCode = pf.stem
        try:
            df = (
                pl.scan_parquet(str(pf))
                .select(_SCAN_COLS)
                .filter(
                    pl.col("sj_div").is_in(self.filterDivs)
                    & (pl.col("reprt_nm") == "4분기")
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            return None

        if df.is_empty():
            return None

        # CFS/OFS: 연결재무제표가 있으면 연결만, 없으면 별도
        cfsLabel = "연결" if self.fsPref == "CFS" else "재무제표"
        cfs = df.filter(pl.col("fs_nm").str.contains(cfsLabel))
        df = cfs if cfs.height > 0 else df

        if df.is_empty():
            return None

        # account 매칭: Python set 교집합 → Polars is_in (소수 키만)
        nmSet = set(df["account_nm"].drop_nulls().unique().to_list())
        idSet = set(df["account_id"].drop_nulls().unique().to_list())
        matchNm = nmSet & self.fastKeys
        matchId = idSet & self.fastKeys

        if matchNm or matchId:
            conds = []
            if matchNm:
                conds.append(pl.col("account_nm").is_in(list(matchNm)))
            if matchId:
                conds.append(pl.col("account_id").is_in(list(matchId)))
            matched = df.filter(functools.reduce(operator.or_, conds))
        else:
            # fallback: mapper.map (공백/괄호 제거 경로)
            matched = None
            for row in df.iter_rows(named=True):
                aid = row["account_id"] or ""
                anm = row["account_nm"] or ""
                if self.mapper.map(aid, anm) == self.snakeId:
                    matched = df.filter(
                        (pl.col("account_id") == aid)
                        & (pl.col("account_nm") == anm)
                    )
                    break

        if matched is None or matched.is_empty():
            return None

        # 금액 파싱
        parsed = matched.with_columns(
            pl.col("thstrm_amount")
            .cast(pl.Utf8)
            .str.replace_all(",", "")
            .str.strip_chars()
            .pipe(
                lambda s: pl.when(s == "")
                .then(None)
                .when(s == "-")
                .then(None)
                .otherwise(s)
            )
            .cast(pl.Float64, strict=False)
            .alias("amount")
        ).filter(pl.col("amount").is_not_null())

        if parsed.is_empty():
            return None

        return parsed.select(
            pl.lit(stockCode).alias("stockCode"),
            pl.col("bsns_year").cast(pl.Utf8).alias("year"),
            pl.col("amount"),
        )


def scanAccount(
    snakeId: str,
    *,
    sjDiv: str | None = None,
    fsPref: str = "CFS",
) -> pl.DataFrame:
    """전종목 단일 계정 연간 시계열 추출.

    Args:
        snakeId: 표준 계정 식별자 ("sales", "operating_profit", "total_assets" 등)
        sjDiv: 재무제표 구분 ("IS", "BS", "CF"). None이면 sortOrder.json에서 자동 결정.
        fsPref: 연결/별도 우선순위 ("CFS"=연결 우선, "OFS"=별도 우선)

    Returns:
        stockCode | 2016 | 2017 | ... | 2024
        값은 원본 원(원) 단위. 데이터 없으면 null.
    """
    from dartlab.core.dataLoader import _dataDir

    if sjDiv is None:
        sjDiv = _resolveSjDiv(snakeId)

    filterDivs = ["IS", "CIS"] if sjDiv in ("IS", "CIS") else [sjDiv]

    financeDir = Path(_dataDir("finance"))
    parquetFiles = sorted(financeDir.glob("*.parquet"))

    if not parquetFiles:
        _log.warning("finance parquet 없음: %s", financeDir)
        return pl.DataFrame({"stockCode": []})

    fastKeys = _buildFastKeys(snakeId)
    mapper = AccountMapper.get()
    processor = _FileProcessor(filterDivs, fsPref, fastKeys, mapper, snakeId)

    _log.info("scanAccount('%s'): %d 파일 스캔 시작", snakeId, len(parquetFiles))

    with ThreadPoolExecutor(max_workers=8) as pool:
        chunks = [r for r in pool.map(processor, parquetFiles) if r is not None]

    if not chunks:
        return pl.DataFrame({"stockCode": []})

    allDf = pl.concat(chunks)

    # 연도당 첫 값 + pivot
    allDf = allDf.group_by(["stockCode", "year"]).agg(pl.col("amount").first())

    result = allDf.pivot(on="year", index="stockCode", values="amount")
    yearCols = sorted(c for c in result.columns if c != "stockCode")
    result = result.select(["stockCode"] + yearCols)

    _log.info(
        "scanAccount('%s'): %d종목 × %d연도",
        snakeId,
        result.height,
        len(yearCols),
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
) -> pl.DataFrame:
    """전종목 단일 재무비율 연간 시계열 추출.

    Args:
        ratioName: 비율 식별자. 지원 목록은 scanRatioList() 참조.
        fsPref: 연결/별도 우선순위 ("CFS"=연결 우선, "OFS"=별도 우선)

    Returns:
        stockCode | 2016 | 2017 | ... | 2024
        값은 퍼센트(%) 또는 배수. 데이터 없으면 null.
    """
    if ratioName not in _RATIO_DEFS:
        available = ", ".join(sorted(_RATIO_DEFS))
        msg = f"지원하지 않는 비율: '{ratioName}'. 사용 가능: {available}"
        raise ValueError(msg)

    defn = _RATIO_DEFS[ratioName]

    if defn.get("yoy"):
        return _calcYoyRatio(defn, fsPref)
    return _calcSimpleRatio(defn, fsPref)


def scanRatioList() -> list[dict[str, str]]:
    """사용 가능한 비율 목록 반환."""
    return [{"name": k, "label": v["label"]} for k, v in _RATIO_DEFS.items()]


def _calcSimpleRatio(defn: dict, fsPref: str) -> pl.DataFrame:
    """분자/분모 비율 계산."""
    numer = scanAccount(defn["numer"], fsPref=fsPref)
    denom = scanAccount(defn["denom"], fsPref=fsPref)

    yearCols = sorted(c for c in numer.columns if c != "stockCode")
    denomYears = sorted(c for c in denom.columns if c != "stockCode")
    commonYears = sorted(set(yearCols) & set(denomYears))

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

    return joined.select(resultExprs)


def _calcYoyRatio(defn: dict, fsPref: str) -> pl.DataFrame:
    """YoY 성장률 계산."""
    base = scanAccount(defn["base"], fsPref=fsPref)
    yearCols = sorted(c for c in base.columns if c != "stockCode")

    if len(yearCols) < 2:
        return pl.DataFrame({"stockCode": []})

    resultExprs = [pl.col("stockCode")]
    for i in range(1, len(yearCols)):
        cur = yearCols[i]
        prev = yearCols[i - 1]
        expr = (
            pl.when(
                (pl.col(prev) != 0)
                & pl.col(prev).is_not_null()
                & pl.col(cur).is_not_null()
                & (pl.col(prev).abs() > 0)
            )
            .then(((pl.col(cur) - pl.col(prev)) / pl.col(prev).abs() * 100).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(cur)
        )
        resultExprs.append(expr)

    return base.select(resultExprs)
