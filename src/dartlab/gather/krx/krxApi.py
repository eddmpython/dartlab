"""KRX OpenAPI - 사용자 직접 호출 + HF 자동 fallback (3 모드 통합).

`engines.gather §9` 의 3 경로 분기:
    Mode A (운영자 cron) — `.github/scripts/sync/buildKrxData.py` 가 환경변수 ``KRX_API_KEY``
                          read 후 ``fetchKrxBydd(..., apiKey=key)`` 명시 전달.
                          이 모듈은 환경변수 자동 read 없음 (운영자 빌드 스크립트만).
    Mode B (사용자 + apiKey 명시) — ``dartlab.gather("krx", ..., apiKey="...")``.
                                   KRX OpenAPI 직접 호출, 결과 DataFrame 반환만.
    Mode C (사용자 + apiKey 미명시, 기본) — ``dartlab.gather("krx", ...)``.
                                          HF 데이터셋 (`_hfBulk.loadFiltered`) 자동.
                                          키 불필요, 모든 사용자 동일 SSOT.

엔진 내부 (quant/scan/analysis) 는 이 모듈 호출하지 않는다 — `_hfBulk.loadFiltered` 직접.

────────────────────────────────────────────────────────────
KRX OpenAPI 키 발급 (Mode B 사용 시):
    1. https://openapi.krx.co.kr 접속 → 회원가입 (무료)
    2. 로그인 → "API 인증키 신청" → 즉시 발급
    3. 발급키를 아래 3 가지 중 하나로 전달:
       (a) 직접 인자:     gather("krx", date="2024-04-15", apiKey="발급키")
       (b) .env 파일:    KRX_API_KEY=발급키 저장 후 코드에서 ::

              import os
              gather("krx", date="2024-04-15", apiKey=os.environ["KRX_API_KEY"])

       (c) 셸 환경변수:  export KRX_API_KEY=발급키 → 위 (b) 와 동일

키 없이 쓰려면 (Mode C, 권장 — 모든 사용자 사용 가능):
    https://huggingface.co/datasets/eddmpython/krx-prices 데이터셋이 자동으로 받아짐
    (운영자 cron 이 매번 어제~오늘을 재조회해 응답이 있는 일자를 갱신)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date as _date
from datetime import datetime, timedelta, timezone
from typing import Literal

import httpx
import polars as pl

log = logging.getLogger(__name__)

_BASE_URL = "https://data-dbg.krx.co.kr/svc/apis/sto"
_ENDPOINT = {"STK": "stk_bydd_trd", "KSQ": "ksq_bydd_trd"}
_KST = timezone(timedelta(hours=9))

# KRX 응답 schema cast — SSOT (운영자 cron · 사용자 직접 호출 모두 이 캐스트 통과)
_INT_COLS = (
    "TDD_CLSPRC",
    "CMPPREVDD_PRC",
    "TDD_OPNPRC",
    "TDD_HGPRC",
    "TDD_LWPRC",
    "ACC_TRDVOL",
    "ACC_TRDVAL",
    "MKTCAP",
    "LIST_SHRS",
)
_FLOAT_COLS = ("FLUC_RT",)

# Wide pivot target — quant 표준 컨벤션 (소문자, gather/price 일관) → KRX 응답 컬럼.
# target="raw" → long DataFrame 그대로 (KRX 원본 컬럼 보존, escape hatch).
# target=indicator (rsi14, ma20, ...) → _indicatorDispatch 가 처리.
_FIELD_MAP = {
    # quant/gather price 표준 (소문자)
    "close": "TDD_CLSPRC",
    "open": "TDD_OPNPRC",
    "high": "TDD_HGPRC",
    "low": "TDD_LWPRC",
    "volume": "ACC_TRDVOL",
    "amount": "ACC_TRDVAL",
    "marketCap": "MKTCAP",
    "listShares": "LIST_SHRS",
    "fluctuationRate": "FLUC_RT",
    "priceChange": "CMPPREVDD_PRC",
    # 짧은 alias (사용자 친화)
    "mktcap": "MKTCAP",
    "shares": "LIST_SHRS",
    "fluc": "FLUC_RT",
    "change": "CMPPREVDD_PRC",
}

# KRX raw 컬럼 → quant 표준 컬럼 rename 매핑 (wide 모드 normalize 용).
_KRX_TO_STD = {
    "BAS_DD": "date",
    "ISU_CD": "stockCode",
    "ISU_NM": "corpName",
    "MKT_NM": "market",
    "SECT_TP_NM": "sector",
    "TDD_OPNPRC": "open",
    "TDD_HGPRC": "high",
    "TDD_LWPRC": "low",
    "TDD_CLSPRC": "close",
    "CMPPREVDD_PRC": "priceChange",
    "FLUC_RT": "fluctuationRate",
    "ACC_TRDVOL": "volume",
    "ACC_TRDVAL": "amount",
    "MKTCAP": "marketCap",
    "LIST_SHRS": "listShares",
}


def _normalizeDate(d: str | _date) -> str:
    """``YYYY-MM-DD`` / ``YYYYMMDD`` / ``date`` → ``YYYYMMDD``."""
    if isinstance(d, _date):
        return d.strftime("%Y%m%d")
    s = str(d).replace("-", "").strip()
    if len(s) != 8 or not s.isdigit():
        raise ValueError(f"날짜 포맷 오류: {d!r} (YYYYMMDD or YYYY-MM-DD)")
    return s


def _isFinalized(basDd: str, *, now: datetime | None = None) -> bool:
    """미래 날짜 가드 — 어제와 오늘은 실제 KRX API 응답으로 판단한다."""
    target = datetime.strptime(basDd, "%Y%m%d").date()
    current = now.astimezone(_KST) if now is not None else datetime.now(_KST)
    today = current.date()
    return target <= today


async def fetchKrxBydd(
    basDd: str,
    *,
    market: Literal["STK", "KSQ"] = "STK",
    apiKey: str,
    client: httpx.AsyncClient | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """KRX OpenAPI - 하루치 전종목 OHLCV (raw, async).

    Capabilities: 하루치 STK/KSQ 전종목 OHLCV + 시총 + 발행주식수 raw fetch.
    AIContext: 운영자 cron 의 KRX bulk 빌드 source — HF dataset 원본.
    Guide: apiKey 환경변수 자동 read 안 함. 명시 필수 (운영자 cron 만).
    When: 일별 KRX bulk 누적 build / 미래 _isFinalized 분기.
    How: KRX OpenAPI _BASE_URL/_ENDPOINT post → JSON → schema cast → DataFrame.

    apiKey 는 명시 필수 — 환경변수 자동 read 없음. 운영자 cron 은
    `.github/scripts/sync/buildKrxData.py` 가 ``KRX_API_KEY`` 환경변수 read 후 명시 전달.

    Parameters
    ----------
    basDd : str
        조회일자 (YYYY-MM-DD 또는 YYYYMMDD).
    market : str
        ``"STK"`` (KOSPI) 또는 ``"KSQ"`` (KOSDAQ).
    apiKey : str
        KRX OpenAPI 인증키 (필수, 명시).
    client : httpx.AsyncClient | None
        비동기 HTTP 클라이언트. None 이면 자동 생성/종료.
    limit : int | None
        반환 행수 상한 (전종목 중 상위 N). None이면 전체.

    Returns
    -------
    pl.DataFrame
        그 날 시장 전종목 OHLCV + 시총 + 발행주식수. 컬럼은 KRX 응답 그대로.
        미래 일자 또는 거래일 아니면 빈 DataFrame.

    Raises
    ------
    ValueError
        apiKey 미지정 또는 market 이 ``"STK"``/``"KSQ"`` 가 아닌 경우.
    httpx.HTTPStatusError
        KRX OpenAPI 응답이 4xx/5xx (인증/권한/네트워크 오류).

    Example
    -------
    >>> df = await fetchKrxBydd("2024-04-15", market="STK", apiKey="...")

    Requires
    --------
    네트워크 (KRX OpenAPI `data-dbg.krx.co.kr`) + 인증키 (`apiKey` 명시) + 확정일자
    (휴장일 / 미래일자는 빈 DataFrame 반환). 환경변수 `KRX_API_KEY` 자동 read 없음.

    See Also
    --------
    fetchKrxRange : 기간 [start, end] 역방향 일별 루프 호출자.
    gatherKrx : 사용자 진입점 — apiKey 미명시 시 HF dataset fallback.
    """
    if not apiKey:
        raise ValueError("apiKey 필수 — KRX OpenAPI 호출에는 키가 필요합니다")
    basDd = _normalizeDate(basDd)
    if not _isFinalized(basDd):
        log.warning(
            "KRX %s: future date for sto by-day API — use today or a prior date",
            basDd,
        )
        return pl.DataFrame()

    if market not in _ENDPOINT:
        raise ValueError(f"market 은 'STK' 또는 'KSQ' 만 허용: {market!r}")

    url = f"{_BASE_URL}/{_ENDPOINT[market]}"
    headers = {
        "AUTH_KEY": apiKey,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"basDd": basDd}

    own = client is None
    if own:
        client = httpx.AsyncClient(timeout=30.0)
    try:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    finally:
        if own:
            await client.aclose()

    df = _parseKrxResponse(data, market=market, basDd=basDd)
    if limit is not None and limit > 0 and not df.is_empty():
        return df.head(limit)
    return df


def _parseKrxResponse(data: dict, *, market: str, basDd: str) -> pl.DataFrame:
    """KRX OpenAPI JSON 응답 → Polars DataFrame (schema cast SSOT).

    KRX 표준 응답 ``{"OutBlock_1": [...rows...]}`` (휴장일이면 빈 배열).
    응답이 전부 string 이므로 정수·실수 컬럼을 명시 cast — 운영자 cron 과
    사용자 직접 호출 모두 이 함수를 통과해야 schema 일관 (SSOT).
    """
    rows = data.get("OutBlock_1") or []
    if not rows:
        detailKeys = sorted(str(k) for k in data.keys())
        statusHints = {
            k: data.get(k)
            for k in ("status_code", "status", "code", "message", "msg", "error", "error_code", "error_message")
            if k in data
        }
        if statusHints:
            log.info("KRX %s %s: 빈 응답 keys=%s hints=%s", market, basDd, detailKeys, statusHints)
        else:
            log.info("KRX %s %s: 빈 응답 (휴장일 또는 자료 없음) keys=%s", market, basDd, detailKeys)
        return pl.DataFrame()

    df = pl.DataFrame(rows)
    casts = []
    for col in _INT_COLS:
        if col in df.columns:
            casts.append(pl.col(col).cast(pl.Int64, strict=False))
    for col in _FLOAT_COLS:
        if col in df.columns:
            casts.append(pl.col(col).cast(pl.Float64, strict=False))
    if casts:
        df = df.with_columns(casts)
    return df


async def fetchKrxRange(
    start: str,
    end: str,
    *,
    market: Literal["STK", "KSQ", "ALL"] = "ALL",
    apiKey: str,
    sleepSec: float = 0.3,
    limit: int | None = None,
) -> pl.DataFrame:
    """KRX OpenAPI - 기간 루프 (역방향 일별, async).

    Capabilities: 기간 [start, end] 역방향 일별 호출 + sleepSec 간격 + concat.
    AIContext: 운영자 cron / .github/scripts/sync/buildKrxData 가 기간 bulk 빌드 진입.
    Guide: ALL 이면 STK + KSQ 각각 호출 (2 배 비용). apiKey 미지정 시 raise.
    When: HF dataset 빌드 / 누락 기간 backfill 시.
    How: 역방향 (end → start) 일별 fetchKrxBydd 호출 + diagonal_relaxed concat.

    최근일자 → 과거일자 순서. 휴장일/미확정일은 직접 호출 후 빈 응답으로 제외.
    한 일자당 시장당 1 호출. ALL 이면 STK + KSQ 각각.

    Parameters
    ----------
    limit : int | None
        반환 행수 상한 (concat 후 head). None이면 전체.

    Raises
    ------
    ValueError
        apiKey 미지정.
    httpx.HTTPError
        KRX OpenAPI 응답 오류 (날짜 단위 호출 중 실패 시 즉시 raise).

    Example
    -------
    >>> df = await fetchKrxRange("2024-04-01", "2024-04-15", market="ALL", apiKey="...")

    Requires
    --------
    네트워크 (KRX OpenAPI) + 인증키 + 기간 내 거래일 ≥ 1. ALL 시장 시 STK + KSQ 두 번 호출.

    See Also
    --------
    fetchKrxBydd : 일별 단일 호출 (본 함수가 루프 안에서 사용).
    gatherKrx : 사용자 진입점 — 기간 wide pivot 까지 포함.
    """
    if not apiKey:
        raise ValueError("apiKey 필수 — KRX OpenAPI 호출에는 키가 필요합니다")
    startD = datetime.strptime(_normalizeDate(start), "%Y%m%d").date()
    endD = datetime.strptime(_normalizeDate(end), "%Y%m%d").date()
    if startD > endD:
        startD, endD = endD, startD

    markets = ["STK", "KSQ"] if market == "ALL" else [market]
    frames: list[pl.DataFrame] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        cur = endD
        while cur >= startD:
            basDd = cur.strftime("%Y%m%d")
            for mkt in markets:
                try:
                    df = await fetchKrxBydd(basDd, market=mkt, client=client, apiKey=apiKey)
                    if not df.is_empty():
                        frames.append(df)
                except (httpx.HTTPError, ValueError) as exc:
                    log.warning("KRX %s %s 실패: %s", mkt, basDd, exc)
                    raise
                if sleepSec > 0:
                    await asyncio.sleep(sleepSec)
            cur -= timedelta(days=1)

    if not frames:
        return pl.DataFrame()
    out = pl.concat(frames, how="diagonal_relaxed")
    if limit is not None and limit > 0:
        return out.head(limit)
    return out


def gatherKrx(
    target: str = "close",
    *,
    start: str | None = None,
    end: str | None = None,
    market: str = "ALL",
    stockCodes: list[str] | None = None,
    apiKey: str | None = None,
) -> pl.DataFrame:
    """KRX 일별 전종목 — **회사별 wide 시계열** (행 = 회사, 열 = 일자) 또는 long raw.

    Capabilities: target 하나로 raw OHLCV / 시총 / 발행주식수 / 28+ 보조지표 진입.
    AIContext: dartlab.gather("krx", target, ...) 의 본체 — 사용자/AI 모두 진입.
    Guide: apiKey None 이면 HF dataset 자동 fallback. wide pivot 이 기본.
    When: KRX 단일 axis 호출 + 시계열 wide 분석 / 횡단면 ranking 시.
    How: apiKey 분기 (직접 OpenAPI vs HF) → long raw → _indicatorDispatch (옵션) → wide pivot.

    target 하나로 raw OHLCV / 시총 / 발행주식수 / 28+ 보조지표 모두 동일 진입점.
    저장 (HF parquet) 은 long SSOT, 사용자 view 는 wide pivot — scan 의 횡단면 표준과 일관.

    Capabilities:
        - **target = raw OHLCV 컬럼** → 그 컬럼 wide (close/open/high/low/volume/marketCap/...)
        - **target = 보조지표** → `gather/indicators.py` SSOT 의 28+ 지표를 종목별 group 동시 계산 후 wide
            (rsi14, ma20, ema60, macd, bbUpper20, atr14, obv, mfi14, adx14, ...)
        - **target = "raw"** → long DataFrame escape hatch (KRX 원본 컬럼 그대로, events join 자유)
        - apiKey 명시: KRX OpenAPI POST 직접 호출 (본인 키, 확정 일자)
        - apiKey 없음 (기본): HF dataset 자동 — 모든 사용자 동일 SSOT, 재현성 보장
        - 단일일자 또는 기간 (역방향 일별 루프, 휴장일은 빈 응답으로 제외)
        - 시장 필터 (KOSPI / KOSDAQ / ALL), 종목 필터 (stockCodes)
        - 미래 날짜 가드 (오늘 자료는 실제 KRX 응답으로 판단)
        - **환경변수 KRX_API_KEY 보지 않음** — 운영자 cron 빌드 스크립트만 read

    AIContext:
        - 키 없는 사용자도 100% 사용 가능 (HF 자동)
        - 한 호출로 전종목 보조지표까지 — dartlab 의 quant indicators 계산을 gather 가 처리
          (`gather/indicators.py` SSOT, L1 위치, quant L2 가 정방향 import)
        - 출력 wide 매트릭스라 correlation/ranking/screening 즉시 (`df.sort("20250630", descending=True).head(10)`)
        - 결과 DataFrame 반환만 — dartlab 캐시에 머지 X (SSOT 보호)

    Guide:
        - "그날 종가 ranking" → gather("krx", "close", date="...") → sort
        - "기간 회사간 비교" → gather("krx", "close", start=, end=)
        - "거래량/시총" → gather("krx", "volume" 또는 "marketCap", ...)
        - "전종목 RSI" → gather("krx", "rsi14", start=, end=)
        - "전종목 20일 이평" → gather("krx", "ma20", start=, end=)
        - "MACD line" → gather("krx", "macd", start=, end=)
        - "특정 종목만" → gather("krx", ..., stockCodes=["005930", "000660"])
        - "코스닥만" → gather("krx", ..., market="KOSDAQ")
        - "long raw" → gather("krx", "raw", date=)
        - "본인 키로 확정 일자 직접 조회" → gather("krx", ..., apiKey="...")

    SeeAlso:
        - gather/indicators.py — 45개 보조지표 SSOT (vsma/vrsi/vmacd/...)
        - gather/_indicatorDispatch.py — target 문자열 → 함수 디스패치
        - gather/_hfBulk.py — 엔진 내부 long SSOT (loadFiltered)
        - .github/scripts/sync/buildKrxData.py — 운영자 cron 빌드 (환경변수 사용)
        - engines.gather §9 — KRX 수집 경로 SSOT (3 모드)

    Args:
        target: pivot 대상 (positional). 기본 ``"close"``.

            **raw OHLCV 컬럼** (KRX 원본을 quant 표준으로 rename):
                ``close`` (TDD_CLSPRC, 원, Int64) ·
                ``open`` (TDD_OPNPRC) · ``high`` (TDD_HGPRC) · ``low`` (TDD_LWPRC) ·
                ``volume`` (ACC_TRDVOL, 주) · ``amount`` (ACC_TRDVAL, 원) ·
                ``marketCap`` (MKTCAP, 원, alias: ``mktcap``) ·
                ``listShares`` (LIST_SHRS, 주, alias: ``shares``) ·
                ``fluctuationRate`` (FLUC_RT, %, Float64, alias: ``fluc``) ·
                ``priceChange`` (CMPPREVDD_PRC, 원, alias: ``change``)

            **보조지표** (gather/indicators.py SSOT, 종목별 group 동시 계산):
                추세: ``ma{N}`` ``sma{N}`` ``ema{N}`` ``wma{N}`` ``dema{N}`` ``tema{N}`` ``hma{N}`` (예: ma20, ema60)
                모멘텀: ``rsi{N}`` ``roc{N}`` ``momentum{N}`` ``cmo{N}`` (예: rsi14, roc12)
                변동성: ``atr{N}`` ``ulcer{N}`` (예: atr14)
                추세필터: ``adx{N}`` ``cci{N}`` ``williamsR{N}`` (예: adx14, cci20)
                거래량: ``obv`` ``adl`` ``vwap`` ``mfi{N}`` ``forceIndex{N}`` ``nvi`` ``pvi`` ``pvt``
                특수: ``trix{N}`` ``dpo{N}``

            **escape**: ``"raw"`` → long DataFrame (KRX 원본 컬럼 그대로 BAS_DD/ISU_CD/TDD_*).

        date: 단일일자 (YYYY-MM-DD 또는 YYYYMMDD). start/end 와 동시 사용 불가.
        start: 기간 시작일.
        end: 기간 종료일.
        market: ``"KOSPI"`` | ``"KOSDAQ"`` | ``"ALL"`` (별칭 ``"STK"`` / ``"KSQ"``). 기본 ``"ALL"``.
        stockCodes: 필터링할 종목코드 리스트 (None 이면 전종목).
        apiKey: KRX OpenAPI 키 (선택). None (기본) 이면 HF 데이터셋 자동.

    Returns:
        pl.DataFrame:
            **target != "raw"** (기본 — wide pivot, 행 = 회사, 열 = 일자):
                stockCode : str — 종목코드 (6자리)
                corpName : str — 회사명 (scan 일관 컬럼)
                {YYYYMMDD} : Int64 / Float64 — 일자별 target 값 (asc 정렬)

            **target == "raw"** (long, KRX 원본 컬럼 그대로):
                BAS_DD, ISU_CD, ISU_NM, MKT_NM, SECT_TP_NM,
                TDD_OPNPRC / TDD_HGPRC / TDD_LWPRC / TDD_CLSPRC (원, Int64),
                CMPPREVDD_PRC (원), FLUC_RT (%, Float64),
                ACC_TRDVOL (주), ACC_TRDVAL (원), MKTCAP (원), LIST_SHRS (주).

    Requires:
        - **apiKey 미명시 (기본, 권장)**: 키 불필요. 인터넷 연결만 필요.
            HF dataset: https://huggingface.co/datasets/eddmpython/dartlab-data
            카테고리: ``krx/prices/raw-{YYYY}.parquet``
            (운영자 cron 이 매번 어제~오늘을 재조회해 응답이 있는 일자를 갱신)
        - **apiKey 명시**: KRX OpenAPI 인증키.
            발급: https://openapi.krx.co.kr → 회원가입 → "API 인증키 신청" (무료, 즉시)
            전달 방법 3 가지:
                1) 직접 인자: ``gather("krx", "close", ..., apiKey="발급키")``
                2) .env 파일에 ``KRX_API_KEY=발급키`` 저장 → ``import os`` 로 read 후 명시 전달
                3) 셸 환경변수 ``export KRX_API_KEY=...`` → 위 (2) 와 동일

    Example::

        import dartlab

        # 1. 종가 회사간 비교 (기본 — wide, 행=회사, 열=일자)
        prices = dartlab.gather("krx", "close", start="2025-06-01", end="2025-06-30")
        # → stockCode, corpName, 20250602, 20250603, ..., 20250630
        # 그날 종가 상위 10
        top10 = prices.sort("20250630", descending=True).head(10)

        # 2. 거래량 매트릭스
        vols = dartlab.gather("krx", "volume", start="2025-06-01", end="2025-06-30")

        # 3. 특정 종목 시총 시계열
        mcaps = dartlab.gather(
            "krx", "marketCap",
            start="2025-06-01", end="2025-06-30",
            stockCodes=["005930", "000660", "035720"],
        )

        # 4. 보조지표 — 전종목 RSI(14) 동시 계산
        rsi = dartlab.gather("krx", "rsi14", start="2025-01-01", end="2025-06-30")
        # 과매도 종목 (RSI < 30) 스크리닝
        oversold = rsi.filter(pl.col("20250630") < 30).select(["stockCode", "corpName", "20250630"])

        # 5. 보조지표 — 20일 이평 / MACD line / Bollinger
        ma20 = dartlab.gather("krx", "ma20", start="2025-01-01", end="2025-06-30")
        macd = dartlab.gather("krx", "macd", start="2025-01-01", end="2025-06-30")

        # 6. long raw (events join 등 자유 가공)
        raw = dartlab.gather("krx", "raw", date="2025-06-30")

        # 7. 본인 키로 직접 (확정 일자 조회)
        df = dartlab.gather("krx", "close", date="2025-06-30", apiKey="MY_KEY")

        # 8. .env 의 키 사용
        import os
        df = dartlab.gather("krx", "close", date="2025-06-30", apiKey=os.environ["KRX_API_KEY"])

    Notes:
        - **저장 long, view wide** — 같은 데이터 두 표현 (SSOT 위반 아님). 저장 한 곳, view 는 사용 시점.
        - **컬럼명 정합** — wide 모드는 quant 표준 (소문자 close/open/.../stockCode/corpName),
          raw 모드만 KRX 원본 그대로 (BAS_DD/ISU_CD/TDD_*/ACC_*).
        - **scan 일관** — wide 결과의 ``stockCode`` + ``corpName`` 은 scan rank/watch/edgarBuilder 표준과 동일,
          scan 결과와 join 가능.
        - **보조지표 == 종목별 동시** — Polars group_by(stockCode) 에 NumPy 벡터 함수 적용,
          전종목 1년치 (~700K rows × 28 지표) ≈ 5~10초 (CPU). GPU 옵션 (Polars `engine="gpu"`) 후속.
        - **환경변수 KRX_API_KEY 자동 read X** — 명시 전달만. 이유: 키 없는 사용자도 100% 사용 +
          모든 사용자 같은 HF SSOT 로 재현성 보장. 환경변수 read 는 운영자 cron 만.
        - 엔진 (quant/scan/analysis) 은 long 형태가 group_by 친화라 ``_hfBulk.loadFiltered``
          직접 호출 — 이 함수 거치지 않음.

    Raises:
        ValueError: date/start-end 동시 지정 또는 둘 다 None / target 알 수 없음 /
            market 알 수 없음 / apiKey 명시했는데 빈 문자열.
    """
    # SSOT 단순화 (2026-04-24): 모든 인자 옵션, 사용자 친화 디폴트.
    # 디폴트:
    #   - start 없음, end 없음 → 최근 1년 (today - 365일 ~ today)
    #   - start 만 → start ~ today
    #   - end 만 → today - 365일 ~ end
    #   - start + end → 명시 기간
    # 단일일자 = start=end 명시. start/end 형식은 "YYYY-MM-DD" / "YYYYMMDD" / date 모두 OK
    # (`_normalizeDate` 가 자동 정규화).
    from datetime import date as _today_d
    from datetime import timedelta as _td

    today_d = _today_d.today()
    if end is None:
        end = today_d.strftime("%Y-%m-%d")
    if start is None:
        start = (today_d - _td(days=365)).strftime("%Y-%m-%d")
    date = None  # legacy 변수 제거

    mktMap = {
        "KOSPI": "STK",
        "KOSDAQ": "KSQ",
        "ALL": "ALL",
        "STK": "STK",
        "KSQ": "KSQ",
    }
    marketKey = market.upper()
    if marketKey not in mktMap:
        allowed = ", ".join(mktMap)
        raise ValueError(f"알 수 없는 market={market!r}. 허용값: {allowed}")
    mkt = mktMap[marketKey]

    # 1. long DataFrame 확보 (HF or KRX OpenAPI). start/end 단일 경로 (date 폐기).
    # target="raw" 면 KRX 원본 그대로 (adjustment 적용 X), 그 외엔 split-adj 적용.
    adjMode = "raw" if target == "raw" else "split"
    if not apiKey:
        from dartlab.gather.bulkData.hfBulk import loadFiltered

        longDf = loadFiltered(start=start, end=end, adjustment=adjMode)
    else:
        from .infra.http import runAsync

        longDf = runAsync(fetchKrxRange(start, end, market=mkt, apiKey=apiKey))

    if longDf.is_empty():
        return longDf

    # 2. market / stockCodes 필터 (raw KRX 컬럼 기준)
    if mkt == "STK" and "MKT_NM" in longDf.columns:
        longDf = longDf.filter(pl.col("MKT_NM") == "KOSPI")
    elif mkt == "KSQ" and "MKT_NM" in longDf.columns:
        longDf = longDf.filter(pl.col("MKT_NM") == "KOSDAQ")
    if stockCodes:
        longDf = longDf.filter(pl.col("ISU_CD").is_in(stockCodes))

    # 3. raw 모드 — KRX 원본 컬럼 그대로 (escape hatch)
    if target == "raw":
        return longDf

    # 4. quant 표준 컬럼명으로 normalize (BAS_DD → date, ISU_CD → stockCode, TDD_CLSPRC → close, ...)
    renameMap = {k: v for k, v in _KRX_TO_STD.items() if k in longDf.columns}
    stdDf = longDf.rename(renameMap)

    # 5. target 디스패치 — raw 컬럼 vs 보조지표
    if target in _FIELD_MAP:
        # raw 컬럼 (또는 alias) — 표준 컬럼 이름 결정
        krxCol = _FIELD_MAP[target]
        valueCol = _KRX_TO_STD.get(krxCol, krxCol)
    else:
        # 보조지표 — gather/indicators 함수 호출 (종목별 group 동시 계산)
        from dartlab.gather.transforms.indicatorDispatch import computeIndicator

        stdDf = stdDf.sort(["stockCode", "date"])
        indSeries = computeIndicator(stdDf, target)
        stdDf = stdDf.with_columns(indSeries.alias(target))
        valueCol = target

    # 6. corpName 매핑 (종목당 마지막 회사명 사용 — 이름 변경 시 가장 최신)
    nameMap = stdDf.unique(subset=["stockCode"], keep="last").select(["stockCode", "corpName"])

    # 7. wide pivot — 행 = stockCode + corpName, 열 = 일자 (descending — 최신 왼쪽).
    # 사람 view 친화 (네이버/Bloomberg 컨벤션). 시계열 분석 시 사용자가 명시 sort.
    wide = stdDf.pivot(index="stockCode", on="date", values=valueCol)  # polars-streaming-unsupported: pivot
    dateCols = sorted((c for c in wide.columns if c != "stockCode"), reverse=True)
    return wide.join(nameMap, on="stockCode", how="left").select(["stockCode", "corpName"] + dateCols).sort("stockCode")
