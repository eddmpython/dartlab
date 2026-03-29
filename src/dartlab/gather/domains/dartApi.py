"""DART OpenAPI gather 어댑터 -- 임원거래 + 대량보유.

기존 providers/dart/openapi/dart.py의 Dart 클래스를 asyncio.to_thread()로 래핑.
API 키 없으면 None 반환 (graceful degradation).
"""

from __future__ import annotations

import asyncio
import logging

from ..types import InsiderTrade, MajorHolder

log = logging.getLogger(__name__)


def _getDart():
    """Dart 인스턴스 lazy 생성. API 키 없으면 None."""
    try:
        from dartlab.providers.dart.openapi.dart import Dart

        return Dart()
    except (ImportError, ValueError, OSError) as exc:
        log.debug("DART API 사용 불가: %s", exc)
        return None


async def fetchInsiderTrading(stockCode: str) -> list[InsiderTrade]:
    """임원/주요주주 주식 거래 내역 -- DART elestock.json."""
    dart = _getDart()
    if dart is None:
        return []
    try:
        df = await asyncio.to_thread(dart.executiveShares, stockCode)
        if df is None or df.is_empty():
            return []
        result = []
        for row in df.iter_rows(named=True):
            result.append(InsiderTrade(
                date=str(row.get("rcept_dt", "")),
                name=str(row.get("repror", row.get("nm", ""))),
                position=str(row.get("ofcps", "")),
                tradeType=str(row.get("sp_stock_lmp_cnt", "")),
                changeShares=_safeInt(row.get("sp_stock_lmp_cnt", 0)),
                afterShares=_safeInt(row.get("sp_stock_lmp_irds_cnt", 0)),
                reason=str(row.get("ctr_motive", "")),
                source="dart",
            ))
        return result
    except (ValueError, OSError, KeyError, TypeError) as exc:
        log.warning("DART executiveShares 실패 (%s): %s", stockCode, exc)
        return []


async def fetchMajorShareholders(stockCode: str) -> list[MajorHolder]:
    """5% 이상 대량보유 변동 -- DART majorstock.json."""
    dart = _getDart()
    if dart is None:
        return []
    try:
        df = await asyncio.to_thread(dart.majorShareholders, stockCode)
        if df is None or df.is_empty():
            return []
        result = []
        for row in df.iter_rows(named=True):
            result.append(MajorHolder(
                holderName=str(row.get("report_nm", row.get("nm", ""))),
                shares=_safeInt(row.get("stkqy", 0)),
                ratio=_safeFloat(row.get("stkrt", 0)),
                changeDate=str(row.get("rcept_dt", "")),
                changeType=str(row.get("change_on", "")),
                source="dart",
            ))
        return result
    except (ValueError, OSError, KeyError, TypeError) as exc:
        log.warning("DART majorShareholders 실패 (%s): %s", stockCode, exc)
        return []


def _safeInt(val) -> int:
    """안전한 int 변환."""
    if val is None:
        return 0
    try:
        return int(str(val).replace(",", "").replace("+", "").strip() or "0")
    except (ValueError, TypeError):
        return 0


def _safeFloat(val) -> float:
    """안전한 float 변환."""
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(",", "").replace("+", "").strip() or "0")
    except (ValueError, TypeError):
        return 0.0
