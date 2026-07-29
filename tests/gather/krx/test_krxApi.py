"""dartlab.gather.krx.krxApi real unit test (A 트랙 T3).

KRX raw 응답 ↔ quant 표준 컬럼 매핑 일관성 + _normalizeDate 헬퍼 검증.
"""

from __future__ import annotations

import datetime as dt
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.krx.krxApi`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.krx.krxApi")


def test_FIELD_MAP_alias_consistency() -> None:
    """_FIELD_MAP — quant 표준 (close/open/high/low) 와 짧은 alias (mktcap/shares 등) 양립."""
    from dartlab.gather.krx import krxApi as krxApiMod

    fieldMap = krxApiMod._FIELD_MAP
    # 표준 컬럼
    assert fieldMap["close"] == "TDD_CLSPRC"
    assert fieldMap["open"] == "TDD_OPNPRC"
    assert fieldMap["high"] == "TDD_HGPRC"
    assert fieldMap["low"] == "TDD_LWPRC"
    assert fieldMap["volume"] == "ACC_TRDVOL"
    # 짧은 alias
    assert fieldMap["mktcap"] == fieldMap["marketCap"]
    assert fieldMap["shares"] == fieldMap["listShares"]
    assert fieldMap["fluc"] == fieldMap["fluctuationRate"]


def test_KRX_TO_STD_rename_consistency() -> None:
    """_KRX_TO_STD — KRX raw → quant 표준 1:1 rename."""
    from dartlab.gather.krx import krxApi as krxApiMod

    rename = krxApiMod._KRX_TO_STD
    assert rename["BAS_DD"] == "date"
    assert rename["ISU_CD"] == "stockCode"
    assert rename["TDD_CLSPRC"] == "close"
    assert rename["MKTCAP"] == "marketCap"
    # raw 키 ↔ FIELD_MAP value 일관성: rename 의 value 가 FIELD_MAP 의 key 와 매칭
    from dartlab.gather.krx.krxApi import _FIELD_MAP

    for raw, std in rename.items():
        if std in {
            "close",
            "open",
            "high",
            "low",
            "volume",
            "amount",
            "marketCap",
            "listShares",
            "fluctuationRate",
            "priceChange",
        }:
            assert _FIELD_MAP[std] == raw


def test_normalizeDate_three_formats() -> None:
    """_normalizeDate — YYYY-MM-DD / YYYYMMDD / date 객체 → YYYYMMDD."""
    from dartlab.gather.krx.krxApi import _normalizeDate

    assert _normalizeDate("2026-05-12") == "20260512"
    assert _normalizeDate("20260512") == "20260512"
    assert _normalizeDate(dt.date(2026, 5, 12)) == "20260512"

    with pytest.raises(ValueError, match="날짜 포맷"):
        _normalizeDate("2026/05/12")


def test_isFinalized_future_blocks() -> None:
    """_isFinalized — 미래 날짜 False (target > today)."""
    from dartlab.gather.krx.krxApi import _isFinalized

    today = dt.date.today()
    future = (today + dt.timedelta(days=10)).strftime("%Y%m%d")
    past = (today - dt.timedelta(days=10)).strftime("%Y%m%d")

    assert _isFinalized(past) is True
    assert _isFinalized(future) is False


def test_gatherKrx_unknown_market_raises_before_loading() -> None:
    """오타 market을 ALL로 확대하지 않고 즉시 거부한다."""
    from dartlab.gather.krx.krxApi import gatherKrx

    with pytest.raises(ValueError, match="알 수 없는 market"):
        gatherKrx(start="2026-01-01", end="2026-01-02", market="KRXX")
