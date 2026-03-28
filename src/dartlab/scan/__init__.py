"""시장 전체 횡단분석 통합 엔트리포인트.

Company = 기업 하나. Scan = 기업 밖 전부.

사용법::

    import dartlab

    dartlab.scan()                          # 가이드 (축 목록 + 사용법)
    dartlab.scan("governance")              # 전 상장사 거버넌스
    dartlab.scan("governance", "005930")    # 삼성전자만 필터
    dartlab.scan("ratio")                   # 가용 비율 목록
    dartlab.scan("ratio", "roe")            # 전종목 ROE
    dartlab.scan("account", "매출액")       # 전종목 매출액 시계열
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
    example: str
    targetParam: str | None = None  # None이면 stockCode 필터
    targetRequired: bool = False
    returnType: str = "DataFrame"
    listModule: str | None = None  # target 없이 호출 시 목록 반환용
    listFn: str | None = None


_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "governance": _AxisEntry(
        module="dartlab.scan.governance",
        fn="scan_governance",
        label="거버넌스",
        description="지배구조 (지분율, 사외이사, 보수비율, 감사의견)",
        example='scan("governance")',
    ),
    "workforce": _AxisEntry(
        module="dartlab.scan.workforce",
        fn="scan_workforce",
        label="인력/급여",
        description="직원수, 평균급여, 성장률, 고액보수",
        example='scan("workforce")',
    ),
    "capital": _AxisEntry(
        module="dartlab.scan.capital",
        fn="scan_capital",
        label="주주환원",
        description="배당, 자사주(취득/처분/소각), 증자/감자, 환원 분류",
        example='scan("capital")',
    ),
    "debt": _AxisEntry(
        module="dartlab.scan.debt",
        fn="scan_debt",
        label="부채구조",
        description="사채만기, 부채비율, ICR, 위험등급",
        example='scan("debt")',
    ),
    "account": _AxisEntry(
        module="dartlab.providers.dart.finance.scanAccount",
        fn="scanAccount",
        label="계정",
        description="전종목 단일 계정 시계열 (매출액, 영업이익 등)",
        example='scan("account", "매출액")',
        targetParam="snakeId",
        targetRequired=True,
    ),
    "ratio": _AxisEntry(
        module="dartlab.providers.dart.finance.scanAccount",
        fn="scanRatio",
        label="비율",
        description="전종목 단일 재무비율 시계열 (ROE, 부채비율 등)",
        example='scan("ratio", "roe")',
        targetParam="ratioName",
        targetRequired=True,
        listModule="dartlab.providers.dart.finance.scanAccount",
        listFn="scanRatioList",
    ),
    "digest": _AxisEntry(
        module="dartlab.scan.watch.digest",
        fn="build_digest",
        label="다이제스트",
        description="시장 전체 공시 변화 다이제스트",
        example='scan("digest")',
    ),
    "network": _AxisEntry(
        module="dartlab.scan.network",
        fn="build_graph",
        label="네트워크",
        description="상장사 관계 네트워크 (출자/지분/계열)",
        example='scan("network")',
        returnType="dict",
    ),
    "cashflow": _AxisEntry(
        module="dartlab.scan.cashflow",
        fn="scanCashflow",
        label="현금흐름",
        description="OCF/ICF/FCF + 현금흐름 패턴 분류 (8종)",
        example='scan("cashflow")',
    ),
    "audit": _AxisEntry(
        module="dartlab.scan.audit",
        fn="scanAudit",
        label="감사리스크",
        description="감사의견, 감사인변경, 특기사항, 감사독립성비율",
        example='scan("audit")',
    ),
    "insider": _AxisEntry(
        module="dartlab.scan.insider",
        fn="scanInsider",
        label="내부자지분",
        description="최대주주 지분변동, 자기주식 현황, 경영권 안정성",
        example='scan("insider")',
    ),
    "quality": _AxisEntry(
        module="dartlab.scan.quality",
        fn="scanQuality",
        label="이익의 질",
        description="Accrual Ratio + CF/NI 비율 — 이익이 현금 뒷받침되는지",
        example='scan("quality")',
    ),
    "liquidity": _AxisEntry(
        module="dartlab.scan.liquidity",
        fn="scanLiquidity",
        label="유동성",
        description="유동비율 + 당좌비율 — 단기 지급능력",
        example='scan("liquidity")',
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
    "현금흐름": "cashflow",
    "현금": "cashflow",
    "감사": "audit",
    "감사리스크": "audit",
    "내부자": "insider",
    "지분": "insider",
    "이익의질": "quality",
    "이익품질": "quality",
    "어닝퀄리티": "quality",
    "유동성": "liquidity",
    "유동비율": "liquidity",
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
    """시장 전체 횡단분석 — 13축, 전부 Polars DataFrame.

    Capabilities:
        - governance: 최대주주 지분, 사외이사, 감사위원회
        - workforce: 임직원 수, 평균급여, 근속연수
        - capital: 배당수익률, 배당성향, 자사주
        - debt: 부채비율, 차입금 의존도, 이자보상
        - account: 전종목 단일 계정 시계열 (매출액, 영업이익 등)
        - ratio: 전종목 단일 재무비율 시계열 (ROE, 영업이익률 등)
        - screen: 재무 조건 스크리닝
        - peer: 동종업계 피어 그룹
        - audit: 감사의견, 감사인 변경
        - insider: 최대주주 변동, 자기주식
        - network: 기업 관계 네트워크
        - watch: 공시 변화 모니터링
        - digest: 시장 전체 변화 다이제스트

    AIContext:
        - ask()/chat()에서 시장 전체 데이터를 컨텍스트로 주입
        - 종목간 비교 분석의 데이터 소스

    Args:
        axis: 축 이름. None이면 13축 가이드 반환.
        target: 축별 대상 (종목코드, 계정명, 비율명 등).
        **kwargs: 축별 옵션 (annual, fsPref, market 등).

    Returns:
        pl.DataFrame — 전종목 횡단 데이터. axis=None이면 13축 가이드 DataFrame.

    Requires:
        데이터: 축별로 다름 (dartlab.downloadAll() 참조)
        - governance/workforce/capital/debt/audit/insider: report
        - account/ratio/screen: finance
        - network/watch/digest: docs

    Example::

        import dartlab
        dartlab.scan()                           # 가이드
        dartlab.scan("governance")               # 전종목 지배구조
        dartlab.scan("account", "매출액")          # 전종목 매출액
        dartlab.scan("ratio", "roe")             # 전종목 ROE
    """

    def __call__(
        self,
        axis: str | None = None,
        target: str | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | Any:
        """축(axis)별 전종목 횡단분석."""
        if axis is None:
            return self._guide()

        resolved = _resolveAxis(axis)
        entry = _AXIS_REGISTRY[resolved]

        # target 없으면 목록 반환 (targetRequired 축)
        if entry.targetRequired and target is None:
            return self._listForAxis(resolved, entry)

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

    def _guide(self) -> pl.DataFrame:
        """축 목록 + 사용법 가이드."""
        rows = [
            {
                "axis": key,
                "label": entry.label,
                "description": entry.description,
                "example": entry.example,
            }
            for key, entry in _AXIS_REGISTRY.items()
        ]
        return pl.DataFrame(rows)

    def _listForAxis(self, axis: str, entry: _AxisEntry) -> pl.DataFrame | list:
        """target 필수 축의 가용 목록 반환."""
        if entry.listModule and entry.listFn:
            mod = importlib.import_module(entry.listModule)
            fn = getattr(mod, entry.listFn)
            result = fn()
            if isinstance(result, list) and result and isinstance(result[0], dict):
                return pl.DataFrame(result)
            return result
        return pl.DataFrame({"info": [f"scan('{axis}', '<target>') 형태로 사용하세요."]})

    def __repr__(self) -> str:
        lines = [f"Scan -- {len(_AXIS_REGISTRY)}축 시장 횡단분석"]
        for key, entry in _AXIS_REGISTRY.items():
            lines.append(f"  {key:12s} {entry.label} -- {entry.description}")
        lines.append("")
        lines.append("사용법: scan(), scan('축'), scan('축', '대상')")
        return "\n".join(lines)


# 모듈 레벨 인스턴스는 만들지 않는다.
# dartlab.__init__.py에서 lazy로 생성한다.
