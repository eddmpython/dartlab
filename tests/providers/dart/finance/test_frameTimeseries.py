"""DART finance frame 시계열 변환의 provider 경계를 검증한다."""

from __future__ import annotations

import polars as pl

from dartlab.providers.dart.finance.frameTimeseries import buildTimeseriesFromFrame


def testEmptyFrameReturnsNoTimeseries():
    """빈 source frame은 loader나 synthetic row 없이 honest gap으로 남긴다."""

    assert buildTimeseriesFromFrame(pl.DataFrame()) is None
