"""고정 5사 panel 기준선 빌드 오케스트레이션."""

from __future__ import annotations

import logging

import polars as pl

from .builder import buildPanel
from .refScan import scanRefBaseline

_log = logging.getLogger(__name__)
_BASELINE_CODES = ("005930", "005380", "035720", "207940", "000660")


def buildPanelBaseline(
    codes: list[str] | None = None,
    *,
    refDf: pl.DataFrame | None = None,
    verbose: bool = True,
) -> dict[str, dict[str, int]]:
    """고정 5사 또는 지정 회사의 panel을 순차 빌드한다.

    Args:
        codes: 종목코드 목록. None이면 고정 기준선 5사.
        refDf: 제목 매칭 기준표. None이면 기준선 zip에서 생성.
        verbose: 회사별 시작과 완료 로그 출력 여부.

    Returns:
        회사별 기간과 변경 행 수.

    Raises:
        FileNotFoundError: 기준선 zip이 없을 때.
        PanelBuildError: 단일 회사 변환 또는 발행이 실패할 때.

    Example:
        >>> buildPanelBaseline(["005930"])  # doctest: +SKIP
    """

    selectedCodes = list(_BASELINE_CODES) if codes is None else codes
    reference = scanRefBaseline(minCorpCount=1) if refDf is None else refDf
    output: dict[str, dict[str, int]] = {}
    for code in selectedCodes:
        if verbose:
            _log.info("== %s 빌드 시작 ==", code)
        output[code] = buildPanel(code, refDf=reference, verbose=verbose)
        if verbose:
            _log.info(
                "== %s 완료: %d period, %d total row ==",
                code,
                len(output[code]),
                sum(output[code].values()),
            )
    return output


__all__ = ["buildPanelBaseline"]
