"""밸류에이션 횡단 스캔 -- PER/PBR/PSR + 등급.

기본 경로는 일일 prebuild snapshot (HuggingFace 배포, ``dart/scan/valuation.parquet``)
을 즉시 로드한다. 장중 급변 상황이나 snapshot 이 없어 fallback 이 필요한 경우
``refresh=True`` 로 네이버 API 를 직접 호출한다.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import polars as pl

from dartlab.scan.io.parquet import (
    REVENUE_IDS as _REVENUE_IDS,
)
from dartlab.scan.io.parquet import (
    REVENUE_NMS as _REVENUE_NMS,
)
from dartlab.scan.io.parquet import (
    loadValuationSnapshot,
    scanFinanceParquets,
)

_CONCURRENCY = 50  # 동시 요청 제한


class ValuationFetchError(RuntimeError):
    """전종목 시세 수집이 유효한 snapshot을 만들지 못한 경우."""


def _gradeValuation(pbr: float | None) -> str:
    """PBR 기준 밸류에이션 등급 분류.

    Parameters
    ----------
    pbr : float | None
        주가순자산비율 (배). None 또는 음수면 ``"해당없음"``.

    Returns
    -------
    grade : str
        밸류에이션 등급. 다음 중 하나:
        - ``"저평가"``   : 0 <= pbr < 0.5 (배)
        - ``"적정"``     : 0.5 <= pbr <= 1.5 (배)
        - ``"고평가"``   : 1.5 < pbr <= 3.0 (배)
        - ``"과열"``     : pbr > 3.0 (배)
        - ``"해당없음"`` : pbr 이 None 이거나 음수
    """
    if pbr is None:
        return "해당없음"
    if pbr < 0:
        return "해당없음"
    if pbr < 0.5:
        return "저평가"
    if pbr <= 1.5:
        return "적정"
    if pbr <= 3.0:
        return "고평가"
    return "과열"


async def _fetchAll(
    codes: list[str],
    verbose: bool,
) -> tuple[dict[str, dict], dict[str, str]]:
    """네이버 API 에서 종목별 시세·밸류에이션 지표를 비동기 배치 수집.

    Parameters
    ----------
    codes : list[str]
        수집 대상 종목코드 목록.
    verbose : bool
        True 이면 배치별 진행 상황을 stdout 에 출력.

    Returns
    -------
    tuple[dict[str, dict], dict[str, str]]
        종목코드별 snapshot과 종목코드별 수집 오류 dict.
        snapshot의 각 값은 다음 키를 가진 dict:

        - marketCap : int — 시가총액 (원)
        - per : float | None — 주가수익비율 (배)
        - pbr : float | None — 주가순자산비율 (배)
        - dividendYield : float | None — 배당수익률 (%)
        - current : int — 현재가 (원)
    """
    import httpx

    from dartlab.gather.domains.naver import fetchPrice

    result: dict[str, dict] = {}
    failures: dict[str, str] = {}
    sem = asyncio.Semaphore(_CONCURRENCY)

    async def _fetch(code: str, client: httpx.AsyncClient) -> None:
        async with sem:
            try:
                snap = await fetchPrice(code, client)
                if snap and snap.marketCap and snap.marketCap > 0:
                    result[code] = {
                        "marketCap": snap.marketCap,
                        "per": snap.per if snap.per is not None else None,
                        "pbr": snap.pbr if snap.pbr is not None else None,
                        "dividendYield": (snap.dividend_yield if snap.dividend_yield is not None else None),
                        "current": snap.current,
                    }
            except (httpx.HTTPError, ValueError, AttributeError) as exc:
                failures[code] = f"{type(exc).__name__}: {exc}"

    async with httpx.AsyncClient(timeout=10) as client:
        total = len(codes)
        batch = 200
        for i in range(0, total, batch):
            chunk = codes[i : i + batch]
            tasks = [_fetch(c, client) for c in chunk]
            await asyncio.gather(*tasks)
            if verbose:
                _log.info(f"  {min(i + batch, total)}/{total} 수집...")

    return result, failures


_RAW_SCHEMA = {
    "stockCode": pl.Utf8,
    "marketCap": pl.Float64,
    "per": pl.Float64,
    "pbr": pl.Float64,
    "dividendYield": pl.Float64,
    "current": pl.Int64,
    "snapshotAt": pl.Datetime("ms"),
}

_FINAL_SCHEMA = {
    "stockCode": pl.Utf8,
    "marketCap": pl.Float64,
    "per": pl.Float64,
    "pbr": pl.Float64,
    "psr": pl.Float64,
    "dividendYield": pl.Float64,
    "grade": pl.Utf8,
    "snapshotAt": pl.Datetime("ms"),
}


def fetchValuationRaw(codes: list[str], *, verbose: bool = True) -> pl.DataFrame:
    """네이버 API 로 전종목 밸류에이션 raw 데이터 수집 → DataFrame.

    ``buildValuation`` (prebuild 생성) 과 ``scanValuation(refresh=True)`` 경로가 공유.

    Parameters
    ----------
    codes : list[str]
        대상 종목코드 목록.
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        `_RAW_SCHEMA` 스키마. 수집 실패 종목은 제외.

    Raises
    ------
    ValuationFetchError
        네이버 rate-limit, 네트워크 실패 또는 유효 snapshot 부재로 전 종목 수집이 실패한 경우.

    Examples
    --------
    >>> from dartlab.scan.financial.valuation import fetchValuationRaw
    >>> df = fetchValuationRaw(["005930", "000660"], verbose=False)
    >>> df.select(["stockCode", "per", "pbr"]).to_dicts()

    Capabilities:
        - 네이버 finance API 병렬 호출 (asyncio) → marketCap/per/pbr/dividendYield/current/
          snapshotAt 6 컬럼 raw DataFrame. 일부 실패는 경고하고 전부 실패하면 예외.

    AIContext:
        ``buildValuation`` cron + ``scanValuation(refresh=True)`` 둘 다 본 함수로 raw 수집.
        AI agent 가 실시간 가치평가 요청 시 본 함수가 1 차 source.

    Guide:
        - rate-limit 의식 — 1 호출당 ~50 초 (KR ~2700 종목). 짧은 시간 반복 호출 금지.
        - 전부 실패하면 ``ValuationFetchError``. 일부 실패는 종목 수와 원인 sample을 warning.

    When:
        ``buildValuation`` cron (KST 04:00) 또는 ``scanValuation(refresh=True)`` 경로.

    How:
        asyncio.run(_fetchAll(codes)) → priceMap 누적 → snapshotAt timestamp 추가 → 6 컬럼 row
        적재 → DataFrame.

    Requires:
        - 네이버 finance API 접근 (네트워크)
        - codes list (KRX listing)

    SeeAlso:
        - :func:`dartlab.scan.builders.kr.core.buildValuation` — prebuild 빌더 (본 함수 호출자)
        - :func:`scanValuation` — refresh=True 경로 호출자
    """
    if not codes:
        return pl.DataFrame(schema=_RAW_SCHEMA)

    priceMap, failures = asyncio.run(_fetchAll(codes, verbose))
    if failures:
        sample = ", ".join(f"{code}={reason}" for code, reason in list(failures.items())[:3])
        _log.warning(
            "밸류에이션 수집 일부 실패: %d/%d종목, sample=%s",
            len(failures),
            len(codes),
            sample,
        )
    if verbose:
        _log.info(f"  수집 완료: {len(priceMap)}종목")
    if not priceMap:
        detail = ", ".join(f"{code}={reason}" for code, reason in list(failures.items())[:3])
        raise ValuationFetchError(
            f"밸류에이션 수집 결과가 없습니다: requested={len(codes)}, "
            f"failed={len(failures)}, sample={detail or 'no usable snapshot'}"
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = [
        {
            "stockCode": code,
            "marketCap": float(data["marketCap"]) if data.get("marketCap") else 0.0,
            "per": data.get("per"),
            "pbr": data.get("pbr"),
            "dividendYield": data.get("dividendYield"),
            "current": int(data["current"]) if data.get("current") else 0,
            "snapshotAt": now,
        }
        for code, data in priceMap.items()
    ]
    return pl.DataFrame(rows, schema=_RAW_SCHEMA)


def _enrichValuation(raw: pl.DataFrame, *, verbose: bool) -> pl.DataFrame:
    """raw (marketCap/per/pbr/dividendYield/current/snapshotAt) → 최종 frame (PSR/grade 추가)."""
    if raw.is_empty():
        return pl.DataFrame(schema=_FINAL_SCHEMA)

    revMap = scanFinanceParquets("IS", _REVENUE_IDS, _REVENUE_NMS)

    rows: list[dict] = []
    for rec in raw.iter_rows(named=True):
        code = rec["stockCode"]
        mc = rec.get("marketCap")
        pbr = rec.get("pbr")
        rev = revMap.get(code)
        psr = round(mc / rev, 2) if rev and rev > 0 and mc and mc > 0 else None
        rows.append(
            {
                "stockCode": code,
                "marketCap": mc,
                "per": rec.get("per"),
                "pbr": pbr,
                "psr": psr,
                "dividendYield": rec.get("dividendYield"),
                "grade": _gradeValuation(pbr),
                "snapshotAt": rec.get("snapshotAt"),
            }
        )

    if verbose:
        _log.info(f"밸류에이션 스캔 완료: {len(rows)}종목")

    return pl.DataFrame(rows, schema=_FINAL_SCHEMA)


def _snapshotAgeHours(snapshotAt: datetime | None) -> int | None:
    if snapshotAt is None:
        return None
    ts = snapshotAt if snapshotAt.tzinfo else snapshotAt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - ts
    return max(0, int(delta.total_seconds() // 3600))


def scanValuation(*, refresh: bool = False, verbose: bool = True) -> pl.DataFrame:
    """전종목 밸류에이션 스캔 — PER/PBR/PSR + 등급 (**KR 전용**).

    기본 경로는 HuggingFace 에 매일 배포되는 prebuild snapshot
    (``dart/scan/valuation.parquet``, GH Actions cron KST 04:00) 을 즉시 로드하므로
    **1 초 이내** 반환한다. 매출 데이터 (PSR 계산) 만 runtime 결합.

    장중 급변 상황이나 snapshot 이 없을 때만 ``refresh=True`` 로 네이버 API
    실시간 수집 (KR 2700 종목 기준 ~50 초) 을 강제한다.

    Parameters
    ----------
    refresh : bool, default False
        True 면 prebuild 를 건너뛰고 네이버 API 재수집. AI 가 "지금 기준" 시세가
        꼭 필요한 질문에서만 사용.
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력 (UI 로 tool_progress 이벤트로 스트림).

    Returns
    -------
    pl.DataFrame
        stockCode/marketCap/per/pbr/psr/dividendYield/grade/snapshotAt 컬럼.

        - marketCap : 원
        - per / pbr / psr : 배 (null 가능)
        - dividendYield : % (null 가능)
        - grade : 저평가/적정/고평가/과열/해당없음
        - snapshotAt : 수집 시각 (UTC)

    AI 사용 가이드:
        - **KR 종목 컨텍스트에서만 호출**하라. US/글로벌 종목 분석 중에는 금지.
        - US 종목의 가치평가는 ``Company.analysis("가치평가")`` 또는
          ``quant("valuation", stockCode)`` 사용.
        - scan 은 "전종목 횡단분석" — 단일 종목이면 ``quant("value", stockCode)``.
        - ``snapshotAt`` 이 몇 시간 전인지 사용자에게 명시하면 신뢰도 상승.

    Raises
    ------
    polars.PolarsError
        prebuild snapshot 손상 또는 PSR 계산용 finance.parquet 누락 시.
    RuntimeError
        ``refresh=True`` + 네이버 API rate-limit 으로 0 종목 수집 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("valuation")
    >>> df.sort("PBR").select(["종목코드", "PER", "PBR", "PSR", "등급"]).head()
    >>> df = dartlab.scan("valuation", refresh=True)  # 네이버 실시간

    Capabilities:
        - prebuild snapshot 우선 로드 (≤ 1초) → 매출 결합 후 PSR / 등급 runtime 계산. refresh=True
          시 네이버 실시간 ~50 초 강제 수집.
        - 등급: 저평가/적정/고평가/과열/해당없음. snapshotAt 으로 데이터 freshness 명시.

    AIContext:
        Agent 가 ``dartlab.scan("valuation")`` 호출 시 본 함수 dispatch. AI 가 "지금 기준" 가치평가
        질문에는 refresh=True 명시 — 일반 cross-company 비교는 default snapshot.

    When:
        대시보드 valuation 카드 빌드 시. cross-company 가치 스크리닝 (저PBR/저PER) 시.

    How:
        ``loadValuationSnapshot`` 으로 prebuild parquet 시도 → 성공 시 ``_enrichValuation`` (매출
        결합 + PSR + grade) → 반환. 실패 / refresh=True 시 네이버 API fetchValuationRaw + 동일
        enrich pipeline.

    Requires:
        - 로컬 ``data/dart/scan/valuation.parquet`` (``buildValuation`` cron 산출) — fallback 으로
          네이버 API 시도.
        - 매출 데이터 (``data/dart/scan/finance.parquet``) — PSR 결합.

    SeeAlso:
        - :func:`fetchValuationRaw` — 네이버 raw 수집 (refresh 경로)
        - :func:`dartlab.scan.io.parquet.loadValuationSnapshot` — prebuild 로더
        - :func:`dartlab.scan.builders.kr.core.buildValuation` — prebuild 빌더
    """
    if not refresh:
        frame, snapshotAt = loadValuationSnapshot()
        if frame is not None:
            if verbose:
                age = _snapshotAgeHours(snapshotAt)
                ageMsg = f"{age}시간 전" if age is not None else "기준시각 미상"
                _log.info(f"밸류에이션 prebuild 로드: {frame.height}종목 ({ageMsg})")
            return _enrichValuation(frame, verbose=verbose)
        if verbose:
            _log.info("밸류에이션 prebuild 없음 — 네이버 API 로 fallback")

    # fallback (prebuild 없음) 또는 refresh=True → 네이버 실시간 수집
    if verbose:
        _log.info("밸류에이션 스캔: 상장사 목록 수집...")

    import dartlab as _dl

    listing = getattr(_dl, "listing")()
    codes = listing["종목코드"].to_list() if "종목코드" in listing.columns else []
    if not codes:
        raise ValuationFetchError("상장사 목록에서 밸류에이션 수집 대상 종목을 찾지 못했습니다")

    if verbose:
        _log.info(f"  {len(codes)}종목 → 네이버 API 수집 시작")

    raw = fetchValuationRaw(codes, verbose=verbose)
    return _enrichValuation(raw, verbose=verbose)


__all__ = ["fetchValuationRaw", "scanValuation"]
