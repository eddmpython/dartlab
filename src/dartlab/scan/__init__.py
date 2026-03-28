"""시장 전체 횡단분석 통합 엔트리포인트.

Company = 기업 하나. Scan = 기업 밖 전부.

사용법::

    import dartlab

    dartlab.scan("governance")              # 전 상장사 거버넌스
    dartlab.scan("governance", "005930")    # 삼성전자만 필터
    dartlab.scan("ratio", "roe")            # 전종목 ROE
    dartlab.scan.topics()                   # 가용 축 목록
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import polars as pl

from dartlab.scan.builder import buildChanges, buildFinance, buildReport, buildScan  # noqa: F401
from dartlab.scan.payload import build_scan_payload, build_unified_payload  # noqa: F401
from dartlab.scan.snapshot import buildScanSnapshot, getScanPosition  # noqa: F401

# ── Axis Registry ────────────────────────────────────────


@dataclass(frozen=True)
class _AxisEntry:
    """scan 축 메타데이터."""

    module: str
    fn: str
    label: str
    description: str
    targetParam: str | None  # None이면 stockCode 필터
    targetRequired: bool
    returnType: str  # "DataFrame" | "tuple" | "dict" | "list"


_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "governance": _AxisEntry(
        module="dartlab.scan.governance",
        fn="scan_governance",
        label="거버넌스",
        description="지배구조 (지분율, 사외이사, 보수비율, 감사의견)",
        targetParam=None,
        targetRequired=False,
        returnType="DataFrame",
    ),
    "workforce": _AxisEntry(
        module="dartlab.scan.workforce",
        fn="scan_workforce",
        label="인력/급여",
        description="직원수, 평균급여, 성장률, 고액보수",
        targetParam=None,
        targetRequired=False,
        returnType="DataFrame",
    ),
    "capital": _AxisEntry(
        module="dartlab.scan.capital",
        fn="scan_capital",
        label="주주환원",
        description="배당, 자사주, 증자/감자, 환원 분류",
        targetParam=None,
        targetRequired=False,
        returnType="DataFrame",
    ),
    "debt": _AxisEntry(
        module="dartlab.scan.debt",
        fn="scan_debt",
        label="부채구조",
        description="사채만기, 부채비율, ICR, 위험등급",
        targetParam=None,
        targetRequired=False,
        returnType="DataFrame",
    ),
    "account": _AxisEntry(
        module="dartlab.providers.dart.finance.scanAccount",
        fn="scanAccount",
        label="계정",
        description="전종목 단일 계정 시계열 (매출액, 영업이익 등)",
        targetParam="snakeId",
        targetRequired=True,
        returnType="DataFrame",
    ),
    "ratio": _AxisEntry(
        module="dartlab.providers.dart.finance.scanAccount",
        fn="scanRatio",
        label="비율",
        description="전종목 단일 재무비율 시계열 (ROE, 부채비율 등)",
        targetParam="ratioName",
        targetRequired=True,
        returnType="DataFrame",
    ),
    "digest": _AxisEntry(
        module="dartlab.scan.watch.digest",
        fn="build_digest",
        label="다이제스트",
        description="시장 전체 공시 변화 다이제스트",
        targetParam=None,
        targetRequired=False,
        returnType="DataFrame",
    ),
    "network": _AxisEntry(
        module="dartlab.scan.network",
        fn="build_graph",
        label="네트워크",
        description="상장사 관계 네트워크 (출자/지분/계열)",
        targetParam=None,
        targetRequired=False,
        returnType="dict",
    ),
}


# ── Aliases ──────────────────────────────────────────────


_ALIASES: dict[str, str] = {
    "거버넌스": "governance",
    "지배구조": "governance",
    "인력": "workforce",
    "급여": "workforce",
    "주주환원": "capital",
    "배당": "capital",
    "부채": "debt",
    "계정": "account",
    "비율": "ratio",
    "네트워크": "network",
    "관계": "network",
    "다이제스트": "digest",
    "변화": "digest",
}


def _resolveAxis(axis: str) -> str:
    """축 이름 또는 alias → 정규 축 이름."""
    lower = axis.lower()
    if lower in _AXIS_REGISTRY:
        return lower
    if axis in _ALIASES:
        return _ALIASES[axis]
    if lower in _ALIASES:
        return _ALIASES[lower]
    available = ", ".join(sorted(_AXIS_REGISTRY))
    raise ValueError(f"알 수 없는 scan 축: '{axis}'. 가용 축: {available}")


# ── Scan Class ───────────────────────────────────────────


def available_scans() -> list[str]:
    """가용 scan 축 이름 목록."""
    return sorted(_AXIS_REGISTRY.keys())


class Scan:
    """시장 전체 횡단분석 통합 엔트리포인트."""

    def __call__(
        self,
        axis: str,
        target: str | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | Any:
        """축(axis)별 전종목 횡단분석.

        Args:
            axis: scan 축 이름 (governance, ratio, account 등).
            target: 축별 주요 인자 (stockCode 필터, keyword, snakeId 등).
            **kwargs: 축별 추가 파라미터.
        """
        resolved = _resolveAxis(axis)
        entry = _AXIS_REGISTRY[resolved]

        if entry.targetRequired and target is None:
            raise ValueError(f"scan('{resolved}')에는 target이 필요합니다.")

        # target → 파라미터 변환
        callKwargs: dict[str, Any] = dict(kwargs)
        if entry.targetParam and target is not None:
            callKwargs[entry.targetParam] = target

        # lazy import + 호출
        mod = importlib.import_module(entry.module)
        fn = getattr(mod, entry.fn)
        result = fn(**callKwargs)

        # stockCode 필터 (target이 있고 targetParam이 None인 축)
        if target and entry.targetParam is None and isinstance(result, pl.DataFrame):
            for col in ("종목코드", "stockCode", "stock_code"):
                if col in result.columns:
                    result = result.filter(pl.col(col) == target)
                    break

        return result

    def topics(self) -> pl.DataFrame:
        """가용 scan 축 목록."""
        rows = [
            {
                "axis": key,
                "label": entry.label,
                "description": entry.description,
                "returnType": entry.returnType,
            }
            for key, entry in _AXIS_REGISTRY.items()
        ]
        return pl.DataFrame(rows)

    def ratios(self) -> list[str]:
        """사용 가능한 재무비율 식별자."""
        from dartlab.providers.dart.finance.scanAccount import scanRatioList

        return scanRatioList()

    def position(self, stockCode: str) -> dict | None:
        """종목의 시장 내 위치 (percentile)."""
        return getScanPosition(stockCode)

    def __repr__(self) -> str:
        axes = ", ".join(sorted(_AXIS_REGISTRY))
        return f"Scan({axes})"


# 모듈 레벨 인스턴스는 만들지 않는다.
# dartlab.__init__.py에서 lazy로 생성한다.
