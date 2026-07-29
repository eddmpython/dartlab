"""dart/openapi dart 헬퍼 . dart.py 분할 (규칙 3 LoC).

_dataPath / _buildPeriods / _periodLabel / _maybeValidateFinance / _fetchSeries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import polars as pl

import dartlab.config as _dartlabConfig
from dartlab.core.dartConstants import (
    CODE_TO_LABEL as _CODE_TO_LABEL,
)
from dartlab.core.dartConstants import (
    QUARTER_TO_CODE as _QUARTER_TO_CODE,
)
from dartlab.core.dataConfig import DATA_RELEASES


class _DartFrameClient(Protocol):
    """연속 DART 조회에 필요한 최소 클라이언트 계약."""

    def getDf(self, endpoint: str, params: dict[str, str]) -> pl.DataFrame:
        """DART endpoint를 DataFrame으로 조회한다.

        Args:
            endpoint: `.json`을 포함한 OpenDART endpoint.
            params: endpoint query parameter.
        Returns:
            정규화 전 OpenDART 응답 frame.
        Requires:
            등록된 DART fetch provider의 실제 client.
        Raises:
            Exception: 실제 client의 네트워크·API 오류를 그대로 전달한다.
        Example:
            >>> client.getDf("fnlttSinglAcntAll.json", {"corp_code": "00126380"})
        """
        ...


def _dataPath(category: str, stockCode: str) -> Path:
    """dartlab 데이터 디렉토리 내 저장 경로.

    {dataDir}/dart/{category}/{stockCode}.parquet
    """
    subDir = DATA_RELEASES.get(category, {}).get("dir", f"dart/{category}")
    dest = Path(_dartlabConfig.dataDir) / subDir / f"{stockCode}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


# ── 내부 유틸 ──────────────────────────────────────────────


def _buildPeriods(
    start: int,
    end: int | None,
    quarterly: bool,
    quarter: str,
) -> list[tuple[str, str]]:
    """(bsnsYear, reprtCode) 리스트 생성."""
    endYear = end if end is not None else start
    if endYear < start:
        raise ValueError(f"start({start}) > end({endYear}): 시작 연도가 종료 연도보다 큽니다")
    if start < 2015:
        raise ValueError(f"start={start}: OpenDART는 2015년 이후 데이터만 제공합니다")

    years = range(start, endYear + 1)
    quarters = ["Q1", "Q2", "Q3", "Q4"] if quarterly else [quarter]

    periods = []
    for y in years:
        for q in quarters:
            code = _QUARTER_TO_CODE.get(q, "11011")
            periods.append((str(y), code))
    return periods


def _periodLabel(bsnsYear: str, reprtCode: str) -> str:
    label = _CODE_TO_LABEL.get(reprtCode, reprtCode)
    return f"{bsnsYear} {label}"


def _maybeValidateFinance(df: pl.DataFrame) -> None:
    """opt-in finance schema 검증. DARTLAB_VALIDATE_SCHEMA=1 일 때만 동작.

    Capabilities:
        production path 의 데이터 drift 차단. DART API 응답 schema 가 바뀌면
        검증 예외를 호출자에게 그대로 전달한다. 환경변수 OFF (기본) 면 0 비용.
    Args:
        df: Dart.finance 결과 frame.
    Returns:
        None.
    Example:
        >>> _maybeValidateFinance(df)  # env OFF → no-op
        >>> import os; os.environ['DARTLAB_VALIDATE_SCHEMA'] = '1'
        >>> _maybeValidateFinance(df)  # schema 위반 시 SchemaErrors
    Guide:
        CI / dev 에서 ON (catch drift), production wheel 사용자는 default OFF.
    SeeAlso:
        dartlab.gather.dart.schemas.FinanceSchema.
    Requires:
        dev 환경에서 pandera[polars] 설치. production wheel 은 default OFF 라 무영향.
    Raises:
        ModuleNotFoundError: 검증을 켰지만 pandera가 설치되지 않은 경우.
        pandera.errors.SchemaErrors: finance schema가 어긋난 경우.
    """
    import os

    if not os.environ.get("DARTLAB_VALIDATE_SCHEMA"):
        return
    if df is None or df.is_empty():
        return
    from dartlab.gather.dart.schemas import FinanceSchema

    FinanceSchema.validate(df, lazy=True)


def _fetchSeries(
    client: _DartFrameClient,
    endpoint: str,
    corpCode: str,
    corpName: str,
    periods: list[tuple[str, str]],
    title: str,
    extraParams: dict | None = None,
) -> pl.DataFrame:
    """여러 기간 연속 조회 → concat + rich.progress."""
    from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

    from dartlab.core.logger import getConsole

    frames: list[pl.DataFrame] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=getConsole(),
    )
    _task = progress.add_task(f"{title} | {corpName}", total=len(periods))
    with progress:
        for bsnsYear, reprtCode in periods:
            progress.update(_task, description=f"{title} | {corpName} | {_periodLabel(bsnsYear, reprtCode)}")

            params: dict[str, str] = {
                "corp_code": corpCode,
                "bsns_year": bsnsYear,
                "reprt_code": reprtCode,
            }
            if extraParams:
                params.update(extraParams)

            df = client.getDf(f"{endpoint}.json", params)
            if df.height > 0:
                frames.append(df)
            progress.advance(_task)

    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="diagonal_relaxed")
