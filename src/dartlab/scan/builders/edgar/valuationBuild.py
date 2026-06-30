"""EDGAR scan valuation 빌더 — edgar/finance facts + 주가 스냅샷 → edgar/scan/valuation.parquet.

KR ``builders/kr/valuationBuild`` 대칭. 다만 KR 은 네이버 API 가 per/pbr/marketCap 을 *직접* 주는 반면
EDGAR 는 XBRL primitive 에서 **계산**한다 (별도 수집 0 — 이미 굽힌 edgar/finance facts + edgar/prices
스냅샷 직독):

    marketCap = currentPrice × sharesOutstanding(dei:EntityCommonStockSharesOutstanding 최신)
    per       = currentPrice / EPS_diluted(us-gaap:EarningsPerShareDiluted 최신 연간)
                (EPS 결측 시 marketCap / netIncome 폴백)
    pbr       = marketCap / equity(us-gaap:StockholdersEquity 최신)

출력 스키마는 KR valuation.parquet 동형 (stockCode·per·pbr·marketCap·current·dividendYield·snapshotAt)
이라 런타임 reportSource 가 market 분기 한 줄로 동일 소비한다. 부수효과 — 본 빌드의 marketCap 은
prices-snapshot-us.json 의 marketCap=null 도 채울 수 있다 (snapshot 게이트 보강).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# XBRL 태그 — 밸류에이션 primitive. equity 는 지배+비지배 포함본을 폴백으로 둔다(은행/지주 커버).
_SHARES_TAG = "EntityCommonStockSharesOutstanding"  # namespace=dei, unit=shares
_NETINCOME_TAG = "NetIncomeLoss"  # namespace=us-gaap, unit=USD
_EQUITY_TAGS = ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest")
_EPS_TAG = "EarningsPerShareDiluted"  # namespace=us-gaap, unit≈USD/shares


def _latestVal(df: pl.DataFrame, *, namespace: str, tags: tuple[str, ...], annualOnly: bool = False) -> float | None:
    """facts DataFrame 에서 tag(들)의 최신 값을 'end'(없으면 'filed') 기준으로 뽑는다.

    Args:
        df: edgar/finance/{cik}.parquet (cik·namespace·tag·val·fp·form·filed·end 컬럼).
        namespace: 'dei' 또는 'us-gaap'.
        tags: 후보 태그(앞 우선). 첫 매칭 태그의 최신 행 채택.
        annualOnly: True 면 연간(fp='FY' 또는 form='10-K'/'20-F')만 — flow(EPS·netIncome)용.

    Returns:
        float | None — 최신 값. 매칭 없으면 None.
    """
    for tag in tags:
        sub = df.filter((pl.col("namespace") == namespace) & (pl.col("tag") == tag))
        if annualOnly:
            sub = sub.filter((pl.col("fp") == "FY") | pl.col("form").is_in(["10-K", "20-F", "40-F"]))
        sub = sub.filter(pl.col("val").is_not_null())
        if sub.is_empty():
            continue
        sortCol = "end" if "end" in sub.columns and sub["end"].null_count() < sub.height else "filed"
        row = sub.sort(sortCol, descending=True, nulls_last=True).head(1)
        v = row["val"][0]
        return float(v) if v is not None else None
    return None


def computeValuationRow(facts: pl.DataFrame, ticker: str, price: float | None, *, asOf: str) -> dict | None:
    """단일 회사 facts + 현재가 → 밸류에이션 행 (KR valuation.parquet 동형).

    Args:
        facts: 회사 edgar/finance parquet (XBRL facts).
        ticker: user-facing ticker(=stockCode).
        price: 현재가(USD). None 이면 marketCap/per 계산 불가(pbr 만 시도).
        asOf: 스냅샷 시각 ISO 문자열.

    Returns:
        dict | None — stockCode·marketCap·per·pbr·current·dividendYield·snapshotAt. 전 지표 결측이면 None.
    """
    shares = _latestVal(facts, namespace="dei", tags=(_SHARES_TAG,))
    equity = _latestVal(facts, namespace="us-gaap", tags=_EQUITY_TAGS)
    eps = _latestVal(facts, namespace="us-gaap", tags=(_EPS_TAG,), annualOnly=True)
    netIncome = _latestVal(facts, namespace="us-gaap", tags=(_NETINCOME_TAG,), annualOnly=True)

    marketCap = price * shares if price is not None and shares else None
    per: float | None = None
    if price is not None and eps is not None and eps > 0:
        per = round(price / eps, 2)
    elif marketCap is not None and netIncome is not None and netIncome > 0:
        per = round(marketCap / netIncome, 2)
    pbr = round(marketCap / equity, 2) if marketCap is not None and equity is not None and equity > 0 else None

    if marketCap is None and per is None and pbr is None:
        return None
    return {
        "stockCode": ticker,
        "marketCap": float(marketCap) if marketCap is not None else None,
        "per": per,
        "pbr": pbr,
        "current": float(price) if price is not None else None,
        "dividendYield": None,  # TODO: dividends_paid / marketCap 후속 (report 빌드와 공유)
        "snapshotAt": asOf,
    }


def _loadPriceSnapshot() -> dict[str, float]:
    """prices-snapshot-us.json(HF) → {ticker: currentPrice}. 부재 시 빈 dict(가격 없는 밸류는 pbr 만)."""
    try:
        from huggingface_hub import hf_hub_download

        from dartlab.core.hfRetry import retryHfCall

        p = retryHfCall(
            hf_hub_download,
            "eddmpython/dartlab-data",
            "landing/map/prices-snapshot-us.json",
            repo_type="dataset",
        )
        data = json.loads(Path(p).read_text(encoding="utf-8")).get("data") or {}
        out: dict[str, float] = {}
        for tk, row in data.items():
            cur = row.get("currentPrice") if isinstance(row, dict) else None
            if cur is not None:
                out[str(tk).upper()] = float(cur)
        return out
    except Exception as exc:  # noqa: BLE001 — 스냅샷 부재/네트워크 → 가격 없이(pbr 만) 진행
        _log.warning(f"[edgarValuation] price snapshot 로드 실패(가격 없이 진행): {exc}")
        return {}


def buildEdgarValuation(*, priceSnapshot: dict[str, float] | None = None, verbose: bool = False) -> Path:
    """전종목 EDGAR facts + 현재가 → edgar/scan/valuation.parquet (KR valuation 대칭, 순수 계산).

    edgar/finance/{cik}.parquet(이미 굽힌 companyfacts)와 prices-snapshot-us.json 만 읽어 계산한다 —
    별도 수집 0. CI(edgarSync) 의 US 집계 단계에서 finance 빌드 직후 호출하면 finance parquet 이 로컬에
    있어 재다운로드도 없다.

    Parameters
    ----------
    priceSnapshot : dict[str, float] | None
        {ticker: currentPrice}. None 이면 HF prices-snapshot-us.json 직독.
    verbose : bool
        진행 로그.

    Returns
    -------
    Path
        edgar/scan/valuation.parquet 경로.

    Raises
    ------
    FileNotFoundError
        edgar/finance 디렉토리/parquet 부재.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.valuationBuild import buildEdgarValuation
    >>> p = buildEdgarValuation(verbose=True)  # doctest: +SKIP
    >>> p.name
    'valuation.parquet'

    Capabilities:
        - XBRL primitive(shares·EPS·equity·netIncome) + 현재가에서 marketCap/per/pbr 계산 → KR
          valuation.parquet 동형 행. 런타임 reportSource 가 market 분기 한 줄로 동일 소비.
        - 부수효과 — marketCap 은 prices-snapshot-us.json marketCap=null 보강에 재사용 가능.

    AIContext:
        ``scan("valuation")`` US 분기의 source. KR 과 같은 schema 라 cross-market union 밸류 비교 가능.

    Guide:
        - cron/edgarSync 에서 finance 빌드 직후 호출(로컬 finance parquet 재사용).
        - per 은 reported diluted EPS 우선, 결측 시 marketCap/netIncome 폴백.

    Requires:
        - edgar/finance/{cik}.parquet (companyfacts 빌드 산출)
        - loadEdgarListedUniverse() (cik→ticker)
        - prices-snapshot-us.json (현재가)

    SeeAlso:
        - :func:`dartlab.scan.builders.kr.valuationBuild.buildValuation` — KR 대칭
        - :func:`dartlab.scan.builders.edgar.builder.buildEdgarFinance` — finance 빌드(같은 facts 소스)
    """
    from dartlab import config as _cfg

    edgarDir = Path(_cfg.dataDir) / "edgar" / "finance"
    outDir = Path(_cfg.dataDir) / "edgar" / "scan"
    outDir.mkdir(parents=True, exist_ok=True)
    if not edgarDir.exists():
        raise FileNotFoundError(f"EDGAR finance 디렉토리 없음: {edgarDir}")
    parquets = sorted(edgarDir.glob("*.parquet"))
    if not parquets:
        raise FileNotFoundError("EDGAR finance parquet 없음")

    try:
        from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

        cikToTicker = edgarCikToTicker()  # 대표 보통주 티커 우선(finance 와 동일 키)
    except (OSError, ValueError, KeyError):
        cikToTicker = {}

    prices = priceSnapshot if priceSnapshot is not None else _loadPriceSnapshot()
    asOf = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if verbose:
        _log.info(f"[edgarValuation] {len(parquets)} CIK → valuation (현재가 {len(prices)}종목)")

    rows: list[dict] = []
    for fp in parquets:
        cik = fp.stem.zfill(10)
        ticker = cikToTicker.get(cik)
        if not ticker:
            continue
        try:
            facts = pl.read_parquet(fp, columns=["namespace", "tag", "val", "fp", "form", "filed", "end"])
        except (OSError, pl.exceptions.PolarsError):
            continue
        if facts.is_empty():
            continue
        row = computeValuationRow(facts, str(ticker).upper(), prices.get(str(ticker).upper()), asOf=asOf)
        if row is not None:
            rows.append(row)

    schema = {
        "stockCode": pl.Utf8,
        "marketCap": pl.Float64,
        "per": pl.Float64,
        "pbr": pl.Float64,
        "current": pl.Float64,
        "dividendYield": pl.Float64,
        "snapshotAt": pl.Utf8,
    }
    out = pl.DataFrame(rows, schema=schema) if rows else pl.DataFrame(schema=schema)
    outPath = outDir / "valuation.parquet"
    out.write_parquet(str(outPath), compression="zstd")
    if verbose:
        _log.info(f"[edgarValuation] 완료: {out.height}종목 → {outPath}")
    return outPath
