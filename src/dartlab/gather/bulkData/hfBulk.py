"""KR 가격 HF 데이터셋 부분 액세스 — 엔진 내부용 (Mode 2).

엔진 (quant/scan/analysis) 이 KR OHLCV/시총/발행주식수가 필요할 때 호출하는 단일 진입점.
**사용자 KRX_API_KEY 환경변수 보지 않음.** HuggingFace 데이터셋이 SSOT.
HF 벌크는 공공데이터포털(data.go.kr) gov 축이 publish (date 샤딩, KRX raw schema 동질).

사용자 직접 호출 (Mode 1) 은 `gather/krxApi.py` 참조 — `engines.gather §9`.

데이터 흐름 (dartlab 표준 — `core/dataLoader.loadData`, category=govPrices):
    1. 로컬 `data/gov/prices/date/{YYYY}.parquet` 확인
    2. 없으면 HF (`eddmpython/dartlab-data` / `gov/prices/date/{YYYY}.parquet`) 다운로드
    3. 있으면 ETag + Content-Length 검증 → stale 시 재다운로드 (3-Layer Freshness, engines.dataHub)
    4. LRU 캐시 (16개) — 같은 세션 재호출 시 메모리 hit

기타 dartlab 카테고리 (finance · report · scan · edgar · ...) 와 완전 동일 패턴.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime
from typing import Literal

import polars as pl

log = logging.getLogger(__name__)

# dartlab 표준 카테고리 (DATA_RELEASES["govPrices"] SSOT — gov/prices/date 샤딩).
# core.dataLoader.loadData 가 dir/repo/freshness 를 자동 처리 — 직접 path 안 박음.
_CATEGORY = "govPrices"

# KRX OpenAPI 응답 컬럼명 — krxApi._parseKrxResponse 통과 후 형식 (검증 2026-04-24)
_COL_DATE = "BAS_DD"  # 기준일 (YYYYMMDD string)
_COL_CODE = "ISU_CD"  # 단축코드 6 자리 (예: "005930")

# Sprint 4 PR3 — Bitemporal SSOT. parquet schema 마이그레이션 후 활성.
# 현재 HF parquet 에는 미존재 — loadFiltered 가 자동 fallback (BAS_DD = business_time).
_COL_BUSINESS_TIME = "business_time"  # 실제 발생일 (event)
_COL_KNOWLEDGE_TIME = "knowledge_time"  # 우리가 알게 된 일 (수집 시각)


def _toDate(d: str | _date) -> _date:
    """YYYY-MM-DD / YYYYMMDD / date → date."""
    if isinstance(d, _date):
        return d
    s = str(d).replace("-", "").strip()
    if len(s) >= 8:
        return _date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    if len(s) == 4:
        return _date(int(s), 1, 1)
    raise ValueError(f"날짜 포맷 오류: {d!r}")


def _resolveYears(
    year: int | None,
    start: str | _date | None,
    end: str | _date | None,
) -> list[int]:
    """필요한 연도 리스트 결정."""
    if year is not None:
        return [int(year)]
    if start is None and end is None:
        return list(range(1995, datetime.now().year + 1))
    s = _toDate(start) if start else _date(1995, 1, 1)
    e = _toDate(end) if end else _date.today()
    if s > e:
        s, e = e, s
    return list(range(s.year, e.year + 1))


def _loadYear(year: int) -> pl.DataFrame | None:
    """``loadData`` 단일 진입점 — 로컬 hit / HF 다운 / ETag freshness 자동.

    dartlab 의 다른 카테고리 (finance · report · scan · edgar · ...) 와 완전 동일 흐름:
        1. ``data/krx/prices/raw-{year}.parquet`` 로컬 확인
        2. 없으면 ``hfBaseUrl("krxPrices")/raw-{year}.parquet`` HF 다운로드
        3. 있으면 ETag + Content-Length 비교 → stale 시 재다운로드
        4. LRU 캐시 (16개) — 동일 세션 재호출 메모리 hit

    Returns
    -------
    pl.DataFrame | None
        해당 연도 raw OHLCV. HF 에 미빌드면 None + 안내 로그.
    """
    from dartlab.core.dataLoader import loadData

    stockCode = f"{year}"  # date 는 dir(gov/prices/date)에 포함 → 파일명 = {year}.parquet
    try:
        return loadData(stockCode, category=_CATEGORY)
    except Exception as exc:
        # HF 미빌드 또는 해당 연도 미수집 — 모든 download/network 에러를 silent skip.
        # 정상 케이스 (HF 에 그 연도 파일 없음) 가 빈번해서 광범위 catch + debug 레벨.
        log.debug(
            "govPrices/%s.parquet 미가용 (HF 미빌드 또는 해당 연도 미수집): %s",
            stockCode,
            type(exc).__name__,
        )
        return None


def _loadEvents(stockCode: str | None) -> pl.DataFrame | None:
    """HF `krx/events/` parquet 로드 (dividends + splits + capital 통합) — Stage 2.

    Stage 1/2 디스패치는 호출자 (`loadFiltered`) 측 — 여기선 Stage 2 (HF events) 만 시도.
    `gather/dividend.py` + `gather/capitalEvent.py` 트랙 도착 시 활성화.
    현재 events HF 미구축 → None.
    """
    # TODO: HF krx/events/{dividends,splits,capital}.parquet 통합 후 활성화
    return None


def loadFiltered(
    *,
    stockCode: str | None = None,
    year: int | None = None,
    start: str | _date | None = None,
    end: str | _date | None = None,
    adjustment: Literal["raw", "split", "tr"] = "split",
    asof: str | _date | None = None,
) -> pl.DataFrame:
    """엔진 내부 — HF 데이터셋에서 raw 받아 수정주가까지 통합 반환.

    Capabilities:
        - 연도별 raw-{year}.parquet 다운로드 (캐시 hit 시 skip, ETag 비교 자동)
        - Polars lazy scan + filter (stockCode, date 범위) → row group pruning
        - 단일 종목 단일 연도 호출 시 ~1MB 만 fetch
        - 데이터셋 미빌드 연도는 자동 skip + 로그만
        - **수정주가 통합 진입점** — adjustment 파라미터로 raw/split/tr 선택
          (events 데이터 미구축 단계엔 자동으로 raw + warning, 호출자 시그니처 불변)

    AIContext:
        - quant/_helpers.py::fetchOhlcv 가 이 함수를 호출 (사용자 키 안 봄)
        - 결과 재현성 보장 — 모든 사용자가 동일 HF snapshot 으로 동일 결과
        - 데이터셋 publish 전이면 빈 DataFrame + 로그 (ValueError 던지지 않음)
        - 수정주가 = `gather/transforms/adjustPrice.applyAdjustment` 단일 SSOT 호출

    Guide:
        - "삼성전자 2024년 수정주가" → loadFiltered(stockCode="005930", year=2024)
        - "전종목 2024 raw" → loadFiltered(year=2024, adjustment="raw")
        - "2020~2024 Total Return" → loadFiltered(start="2020-01-01", end="2024-12-31", adjustment="tr")

    SeeAlso:
        - gather/krxApi.py — 사용자 직접 호출 (Mode 1, 자기 KRX_API_KEY)
        - gather/_adjustPrice.py — 수정주가 알고리즘 (CRSP backward chaining)
        - engines.gather §9 — KRX 수집 경로 SSOT
        - operation.apiContract §12 — EDGAR 와 동일한 벌크/API 분리 패턴

    Args:
        stockCode: 단일 종목 필터 (None 이면 전종목).
        year: 단일 연도 (start/end 와 동시 사용 불가).
        start: 기간 시작 (YYYY-MM-DD). year 없을 때 사용.
        end: 기간 종료. year 없을 때 사용.
        adjustment: ``"raw"`` (원본) | ``"split"`` (한국 수정주가) | ``"tr"`` (Total Return). 기본 ``"split"``.

    Returns:
        pl.DataFrame — KRX 응답 컬럼 + (adjustment != "raw" 시) ``splitFactor`` / ``divFactor``.

    Requires:
        - 인터넷 연결 (HuggingFace Hub 접근).
        - ``huggingface-hub`` 패키지 (이미 dartlab 의존성).

    Example::

        from dartlab.gather.bulkData.hfBulk import loadFiltered
        df = loadFiltered(stockCode="005930", year=2024)              # split (기본)
        df = loadFiltered(stockCode="005930", year=2024, adjustment="tr")  # Total Return

    Raises:
        ValueError: year 와 start/end 동시 지정.

    When:
        엔진 내부 (quant/scan/analysis/gather.krxApi.gatherKrx) 가 KR 시계열 필요 시
        첫 시도 — apiKey 없는 사용자 path / 재현성 보장 path.

    How:
        _resolveYears(year, start, end) → 연도별 _loadYear (HF parquet) → concat →
        stockCode/date filter → adjustPrice.applyAdjustment(adjustment 모드) → DataFrame.
    """
    if year is not None and (start is not None or end is not None):
        raise ValueError("year 와 start/end 는 동시 사용 불가")

    years = _resolveYears(year, start, end)
    frames: list[pl.DataFrame] = []
    for y in years:
        df = _loadYear(y)
        if df is None or df.is_empty():
            continue
        # loadData 는 eager 반환 — 필터는 lazy 보다 단순 (yearly 파일 ~50MB 한도라 메모리 부담 X)
        if stockCode is not None:
            df = df.filter(pl.col(_COL_CODE) == stockCode)
        if start is not None:
            sd = _toDate(start).strftime("%Y%m%d")
            df = df.filter(pl.col(_COL_DATE) >= sd)
        if end is not None:
            ed = _toDate(end).strftime("%Y%m%d")
            df = df.filter(pl.col(_COL_DATE) <= ed)
        if not df.is_empty():
            frames.append(df)

    if not frames:
        return pl.DataFrame()
    raw = pl.concat(frames, how="diagonal_relaxed")

    if adjustment == "raw":
        result = raw
    else:
        from dartlab.gather.transforms.adjustPrice import applyAdjustment, detectEventsFromPrices

        # Stage 2 우선 — HF `krx/events/` parquet 있으면 정확 이벤트 사용
        events = _loadEvents(stockCode)
        if events is None:
            # Stage 1 fallback — 가격 시계열에서 자동 감지 (marcap 방식 + FLUC_RT 정밀화)
            # DART 공시 파싱 트랙 도착 전엔 이게 split-adjusted 의 정답.
            # TR 모드는 dividend events 가 있어야 하므로 자동 감지로는 raw 그대로 (warning).
            events = detectEventsFromPrices(raw)
        result = applyAdjustment(raw, events, mode=adjustment)

    # Sprint 4 PR3 — PIT 컷오프. asof=None 이면 no-op (기존 동작 100% 보존).
    if asof is not None:
        from dartlab.gather.transforms.pit import applyAsOf

        # bitemporal 컬럼 미존재 시 fallback — BAS_DD (string YYYYMMDD) 를 business_time 으로 간주.
        # applyAsOf 의 fallbackCol 인자 사용 + str cast 매개.
        cutoff_yyyymmdd = _toDate(asof).strftime("%Y%m%d")
        if _COL_BUSINESS_TIME in result.columns and _COL_KNOWLEDGE_TIME in result.columns:
            result = applyAsOf(result, asof)
        elif _COL_DATE in result.columns:
            result = result.filter(pl.col(_COL_DATE) <= cutoff_yyyymmdd)
    return result
