"""FRED/ECOS HF 데이터셋 액세스 — gather macro 기본 경로.

KRX 벌크와 같은 패턴:
    - 운영자 cron 이 API 키로 전체 카탈로그를 HF 에 publish
    - 사용자는 API 키 없이 HF snapshot 을 소비
    - 직접 API 호출은 gather("macro", ..., apiKey="...") 로만 선택
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime

import polars as pl

_log = logging.getLogger(__name__)

_SOURCE_TO_CATEGORY = {
    "fred": "macroFred",
    "ecos": "macroEcos",
    "customs": "macroCustoms",
}

# source → 직접 API 키 env (fetchSeries miss 시 안내 힌트용).
_SOURCE_TO_ENVKEY = {
    "fred": "FRED_API_KEY",
    "ecos": "ECOS_API_KEY",
    "customs": "DATA_GO_KR_KEY",
}


def _toDate(value: str | _date) -> _date:
    """YYYY-MM-DD / YYYYMMDD / date → date."""
    if isinstance(value, _date):
        return value
    s = str(value).replace("-", "").strip()
    if len(s) >= 8:
        return _date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    if len(s) == 4:
        return _date(int(s), 1, 1)
    raise ValueError(f"날짜 포맷 오류: {value!r}")


def _category(source: str) -> str:
    key = source.lower()
    if key not in _SOURCE_TO_CATEGORY:
        raise ValueError("source 는 'fred'·'ecos'·'customs' 중 하나여야 합니다.")
    return _SOURCE_TO_CATEGORY[key]


def loadManifest(source: str) -> pl.DataFrame:
    """HF macro manifest 로드 — 사용 가능한 시리즈 카탈로그.

    Capabilities: HF dataset ``macro/{source}/manifest.parquet`` read → DataFrame.
    AIContext: macro engine 의 시리즈 universe — availableSeries / fetchSeries 의 source-of-truth.
    Guide: source "fred"/"ecos" 두 값만. 다른 값은 ValueError.
    When: macro engine 이 사용자 요청 시리즈를 HF 카탈로그와 매칭 시.
    How: ``loadData("manifest", category=macroFred|macroEcos)`` 직접 forward.

    Parameters
    ----------
    source : str
        "fred" 또는 "ecos".

    Returns
    -------
    pl.DataFrame
        seriesId : str — 시리즈 ID
        label : str — 한글 라벨
        group : str — 카탈로그 그룹
        frequency : str — 원본 주기
        unit : str — 단위
        status : str — ok/stale/error

    Raises
    ------
    ValueError
        source 가 ``"fred"``/``"ecos"`` 가 아닐 때.

    Requires
    --------
    HF dataset ``eddmpython/dartlab-data`` 의 ``macro/{source}`` 카탈로그 publish.

    Example
    -------
    >>> mf = loadManifest("fred")

    See Also
    --------
    availableSeries : 본 함수 결과의 seriesId set 추출.
    fetchSeries : 실제 시계열 fetch (manifest 매칭 후 호출).
    latestUpdatedAt : manifest 의 갱신 시각.
    """
    from dartlab.core.dataLoader import loadData

    return loadData("manifest", category=_category(source))


def loadObservations(source: str) -> pl.DataFrame:
    """HF macro observations 로드 — 전체 시리즈 long DataFrame.

    Capabilities: HF dataset ``macro/{source}/observations.parquet`` read + date 정규화.
    AIContext: macro engine 의 실제 시계열 source — fetchSeries 가 filter 후 wide pivot.
    Guide: 전체 시리즈 long DataFrame (수십 MB). 단일 시리즈만 필요하면 fetchSeries 권장.
    When: macro engine 의 bulk 비교 분석 / fetchSeries 내부 호출 시.
    How: ``loadData("observations", category=...)`` + ``date`` 컬럼 ``pl.Date`` cast.

    Parameters
    ----------
    source : str
        ``"fred"`` 또는 ``"ecos"``.

    Returns
    -------
    pl.DataFrame
        date : date — 관측일
        seriesId : str — 시리즈 ID
        value : float — 관측값

    Raises
    ------
    ValueError
        source 가 ``"fred"``/``"ecos"`` 가 아닐 때.

    Requires
    --------
    HF dataset ``macro/{source}/observations.parquet`` publish.

    Example
    -------
    >>> obs = loadObservations("ecos")

    See Also
    --------
    fetchSeries : 단일 시리즈 filter + wide.
    fetchMulti : 복수 시리즈 wide pivot.
    loadManifest : 시리즈 universe.
    """
    from dartlab.core.dataLoader import loadData

    df = loadData("observations", category=_category(source))
    if "date" in df.columns:
        df = df.with_columns(pl.col("date").cast(pl.Date))
    return df


def availableSeries(source: str) -> set[str]:
    """HF manifest 기준 사용 가능한 시리즈 ID 집합.

    Capabilities: loadManifest → seriesId set 추출.
    AIContext: fetchSeries 의 진입 가드 — HF 카탈로그 미수록 시리즈 차단.
    Guide: O(N) 카탈로그 조회 — manifest 캐시 미사용 (호출 비용 작음).
    When: 사용자 요청 시리즈 ID 가 HF 카탈로그에 있는지 사전 검증 시.
    How: loadManifest(source) → ``seriesId`` 컬럼 → set.

    Parameters
    ----------
    source : str
        ``"fred"`` 또는 ``"ecos"``.

    Returns
    -------
    set[str]
        manifest 에 존재하는 모든 시리즈 ID. manifest 비어 있거나
        ``seriesId`` 컬럼 부재면 빈 set.

    Raises
    ------
    ValueError
        source 가 ``"fred"``/``"ecos"`` 가 아닐 때.

    Requires
    --------
    loadManifest 의 요구사항 (HF manifest publish).

    Example
    -------
    >>> ids = availableSeries("fred")

    See Also
    --------
    loadManifest : 본 함수의 source.
    fetchSeries : 본 함수 결과로 시리즈 ID 검증.
    """
    manifest = loadManifest(source)
    if manifest.is_empty() or "seriesId" not in manifest.columns:
        return set()
    return set(manifest.get_column("seriesId").drop_nulls().to_list())


def fetchSeries(
    source: str,
    seriesId: str,
    *,
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """HF macro 단일 시리즈 조회 → ``(date, value)``.

    Capabilities: availableSeries 검증 + loadObservations filter + date 범위 + tail(limit).
    AIContext: macro engine 의 사용자-facing 단일 시리즈 진입점 (apiKey 없는 path).
    Guide: HF 카탈로그 미수록 시리즈는 ValueError — apiKey 명시 호출로 fallback.
    When: ``gather("macro", seriesId, ...)`` 사용자 호출 시 첫 시도.
    How: availableSeries(source) 검증 → loadObservations filter (seriesId, start, end) → sort + tail.

    Parameters
    ----------
    limit : int | None
        반환 행수 상한 (가장 최근 N). None이면 전체.

    Raises
    ------
    ValueError
        HF 카탈로그에 없는 시리즈일 때. 직접 API가 필요하면 ``apiKey=``를 명시해야 한다.

    Requires
    --------
    HF manifest + observations 가용 + seriesId 가 manifest 에 등록.

    Example
    -------
    >>> df = fetchSeries("fred", "GDP", start="2020-01-01", limit=20)

    See Also
    --------
    fetchMulti : 복수 시리즈 wide pivot.
    availableSeries : 진입 가드.
    macroProvider.fetchSeriesLatest : Protocol 위임 (asOf 적용).
    """
    sourceKey = source.lower()
    supported = availableSeries(sourceKey)
    if seriesId not in supported:
        envKey = _SOURCE_TO_ENVKEY.get(sourceKey, "FRED_API_KEY")
        raise ValueError(
            f"{sourceKey.upper()} HF 카탈로그에 없는 지표입니다: {seriesId}. "
            f"직접 API 조회가 필요하면 gather('macro', '{seriesId}', apiKey=...) "
            f"또는 {envKey} 값을 apiKey 인자로 전달하세요."
        )

    df = loadObservations(sourceKey)
    if df.is_empty():
        return pl.DataFrame(schema={"date": pl.Date, "value": pl.Float64})
    df = df.filter(pl.col("seriesId") == seriesId)
    if start:
        df = df.filter(pl.col("date") >= _toDate(start))
    if end:
        df = df.filter(pl.col("date") <= _toDate(end))
    if df.is_empty():
        return pl.DataFrame(schema={"date": pl.Date, "value": pl.Float64})
    out = df.select("date", "value").sort("date")
    if limit is not None and limit > 0:
        return out.tail(limit)
    return out


def fetchMulti(
    source: str,
    seriesIds: list[str],
    *,
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """HF macro 복수 시리즈 조회 → wide DataFrame.

    Capabilities: 시리즈별 fetchSeries → rename({value→seriesId}) → join + forward_fill.
    AIContext: macro engine 의 cross-series 비교 진입 (예: GDP + UNRATE 동시 시계열).
    Guide: 빈 시리즈도 join (null) — 사용자 측 dropna 책임.
    When: 매크로 종합 분석 (regime/correlation) 시.
    How: fetchSeries fan-out → outer join on date → forward_fill missing.

    Parameters
    ----------
    limit : int | None
        반환 행수 상한 (가장 최근 N). None이면 전체.

    Raises
    ------
    ValueError
        HF 카탈로그에 없는 시리즈가 ``seriesIds`` 에 포함된 경우.

    Requires
    --------
    fetchSeries 의 요구사항 + 모든 ``seriesIds`` 가 manifest 에 등록.

    Example
    -------
    >>> df = fetchMulti("fred", ["GDP", "UNRATE"], start="2020-01-01")

    See Also
    --------
    fetchSeries : 본 함수의 내부 fan-out 대상.
    macroProvider.fetchSeriesLatest : asOf 적용 단건 조회.
    """
    if not seriesIds:
        return pl.DataFrame()

    frames: list[pl.DataFrame] = []
    ambiguous: list[str] = []
    for sid in seriesIds:
        df = fetchSeries(source, sid, start=start, end=end)
        if df.is_empty():
            df = pl.DataFrame(schema={"date": pl.Date, sid: pl.Float64})
        elif df["date"].n_unique() != df.height:
            # 한 날짜에 값이 여럿인 시리즈다. date 로 full join 하면 행이 곱해지고, 그
            # 폭발이 멀쩡한 다른 지표까지 오염시킨다. 실측(2026-08-06): CSI 는 하루에
            # 6 값(80·87·76·88·81·96.5), TRADE 는 4 값(6.08조·17469·2861조·5.91조)이라
            # 13 지표 wide 표에서 2026-08-01 한 날짜가 열두 행 넘게 나왔고 BASE_RATE 와
            # USDKRW 까지 같이 복제됐다. seriesId 하나에 세부 항목이 뭉쳐 있는 것이
            # 근본 원인이며 그 분리는 데이터 정의 작업이다.
            #
            # 여기서 값 하나를 고르지 않는다. CSI 가 80 인지 96.5 인지 알 수 없고,
            # 임의로 고르면 조용히 틀린 값을 준다. 조합에서 빼고 뺐다고 말한다.
            ambiguous.append(sid)
            continue
        else:
            df = df.rename({"value": sid})
        frames.append(df)

    if ambiguous:
        _log.warning(
            "macro wide 조합에서 제외: %s. 한 날짜에 값이 여럿이라 date 기준 결합이 성립하지 않습니다. "
            "개별 조회(target 지정)로는 그대로 볼 수 있습니다.",
            ", ".join(ambiguous),
        )
    if not frames:
        return pl.DataFrame()

    result = frames[0]
    for df in frames[1:]:
        result = result.join(df, on="date", how="full", coalesce=True)

    fillCols = [c for c in result.columns if c != "date"]
    if fillCols:
        result = result.sort("date").with_columns([pl.col(c).forward_fill() for c in fillCols])
    out = result.sort("date")
    if limit is not None and limit > 0:
        return out.tail(limit)
    return out


def latestUpdatedAt(source: str) -> datetime | None:
    """manifest 의 최신 갱신 시각 반환 — HF 신선도 추적용.

    Capabilities: loadManifest 의 ``updatedAtUtc`` 컬럼 max → datetime.
    AIContext: macro engine 의 staleness 진단 / 캐시 freshness UI 진입.
    Guide: ISO 8601 (Z 또는 +00:00) 형식 가정. 파싱 실패 시 None.
    When: 사용자 dashboard 가 데이터 freshness 표시 / 운영자 cron 진단 시.
    How: loadManifest → ``updatedAtUtc`` drop_nulls → max → datetime.fromisoformat.

    Parameters
    ----------
    source : str
        ``"fred"`` 또는 ``"ecos"``.

    Returns
    -------
    datetime | None
        manifest 의 ``updatedAtUtc`` 컬럼 최대값. 컬럼/값 부재 또는 파싱 실패 시 None.

    Raises
    ------
    ValueError
        source 가 ``"fred"``/``"ecos"`` 가 아닐 때.

    Requires
    --------
    loadManifest 결과에 ``updatedAtUtc`` 컬럼 존재 + ISO 형식 값.

    Example
    -------
    >>> ts = latestUpdatedAt("fred")

    See Also
    --------
    loadManifest : 본 함수의 source.
    """
    manifest = loadManifest(source)
    if manifest.is_empty() or "updatedAtUtc" not in manifest.columns:
        return None
    vals = manifest.get_column("updatedAtUtc").drop_nulls().to_list()
    if not vals:
        return None
    try:
        return datetime.fromisoformat(str(max(vals)).replace("Z", "+00:00"))
    except ValueError:
        return None
