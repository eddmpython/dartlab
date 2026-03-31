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
        description="지배구조 (지분율, 사외이사, 보수비율, 감사의견, 소액주주 분산)",
        example='scan("governance")',
    ),
    "workforce": _AxisEntry(
        module="dartlab.scan.workforce",
        fn="scan_workforce",
        label="인력/급여",
        description="직원수, 평균급여, 인건비율, 1인당부가가치, 성장률, 고액보수",
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
        listModule="dartlab.providers.dart.finance.scanAccount",
        listFn="scanAccountList",
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
    "growth": _AxisEntry(
        module="dartlab.scan.growth",
        fn="scanGrowth",
        label="성장성",
        description="매출/영업이익/순이익 CAGR + 성장 패턴 분류 (6종)",
        example='scan("growth")',
    ),
    "profitability": _AxisEntry(
        module="dartlab.scan.profitability",
        fn="scanProfitability",
        label="수익성",
        description="영업이익률/순이익률/ROE/ROA + 등급",
        example='scan("profitability")',
    ),
    "efficiency": _AxisEntry(
        module="dartlab.scan.efficiency",
        fn="scanEfficiency",
        label="효율성",
        description="자산/재고/매출채권 회전율 + CCC(현금전환주기) + 등급",
        example='scan("efficiency")',
    ),
    "valuation": _AxisEntry(
        module="dartlab.scan.valuation",
        fn="scanValuation",
        label="밸류에이션",
        description="PER/PBR/PSR + 시가총액 + 등급 (네이버 실시간)",
        example='scan("valuation")',
    ),
    "dividendTrend": _AxisEntry(
        module="dartlab.scan.dividendTrend",
        fn="scanDividendTrend",
        label="배당추이",
        description="DPS 3개년 시계열 + 패턴 분류 (연속증가/안정/감소/시작/중단)",
        example='scan("dividendTrend")',
    ),
    "macroBeta": _AxisEntry(
        module="dartlab.scan.macroBeta",
        fn="scan_macroBeta",
        label="거시베타",
        description="전종목 GDP/금리/환율 베타 횡단면 (OLS 회귀). 사전 수집: Ecos().series('GDP', enrich=True)",
        example='scan("macroBeta")',
    ),
    "screen": _AxisEntry(
        module="dartlab.scan.screen",
        fn="scanScreen",
        label="스크리닝",
        description="멀티팩터 스크리닝 (value/dividend/growth/risk/quality 프리셋)",
        example='scan("screen", "value")',
        targetParam="target",
        targetRequired=False,
    ),
}


# ── Aliases ──────────────────────────────────────────────


_ALIASES: dict[str, str] = {
    # governance
    "거버넌스": "governance",
    "지배구조": "governance",
    # workforce
    "인력": "workforce",
    "급여": "workforce",
    "인력/급여": "workforce",
    # capital
    "주주환원": "capital",
    "배당": "capital",
    # debt
    "부채": "debt",
    "부채구조": "debt",
    "사채": "debt",
    # account
    "계정": "account",
    # ratio
    "비율": "ratio",
    # network
    "네트워크": "network",
    "관계": "network",
    # cashflow
    "현금흐름": "cashflow",
    "현금": "cashflow",
    # audit
    "감사": "audit",
    "감사리스크": "audit",
    # insider
    "내부자": "insider",
    "내부자지분": "insider",
    "지분": "insider",
    # quality
    "이익의질": "quality",
    "이익의 질": "quality",
    "이익품질": "quality",
    "어닝퀄리티": "quality",
    # liquidity
    "유동성": "liquidity",
    "유동비율": "liquidity",
    # macroBeta
    "거시베타": "macroBeta",
    "매크로베타": "macroBeta",
    "거시민감도": "macroBeta",
    # growth
    "성장성": "growth",
    "성장": "growth",
    # profitability
    "수익성": "profitability",
    # efficiency
    "효율성": "efficiency",
    "회전율": "efficiency",
    # valuation
    "밸류에이션": "valuation",
    "밸류": "valuation",
    # dividendTrend
    "배당추이": "dividendTrend",
    "배당시계열": "dividendTrend",
    "배당트렌드": "dividendTrend",
    # screen
    "스크리닝": "screen",
    "스크린": "screen",
    "필터": "screen",
}


def _edgarDispatch(axis: str, kwargs: dict) -> pl.DataFrame | None:
    """EDGAR 전용 scan 축 디스패치. 구현 없으면 None 반환."""
    # XBRL 기반 7축 — _edgar_helpers.scan_edgar_accounts 활용
    _EDGAR_XBRL_AXES = {
        "profitability", "growth", "quality", "liquidity",
        "efficiency", "cashflow", "dividendTrend",
        "capital", "debt",
    }
    if axis in _EDGAR_XBRL_AXES:
        from dartlab.scan._edgar_scan import edgarScan

        return edgarScan(axis, **kwargs)

    # account/ratio — 기존 EDGAR scanAccount 사용
    if axis == "account":
        from dartlab.providers.edgar.finance.scanAccount import scanAccount

        return scanAccount(kwargs.get("snakeId", "sales"), annual=kwargs.get("annual", False))
    if axis == "ratio":
        from dartlab.providers.edgar.finance.scanAccount import scanRatio

        return scanRatio(kwargs.get("ratioName", "roe"), annual=kwargs.get("annual", False))

    return None  # 아직 EDGAR 구현 없는 축


def _resolveAxis(axis: str) -> str:
    """축 이름 또는 alias → 정규 축 이름."""
    if axis in _AXIS_REGISTRY:
        return axis
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
    """가용 scan 축 이름 목록.

    Capabilities:
        - 15축 scan 축 이름을 알파벳순 리스트로 반환
        - 프로그래밍 방식으로 가용 축을 탐색할 때 사용

    Requires:
        없음 (레지스트리 메타데이터만 참조)

    AIContext:
        사용자가 "어떤 scan이 있어?" 질문 시 축 목록 제공.

    Guide:
        - "scan 뭐 있어?" -> available_scans()로 축 이름 목록 확인
        - "어떤 분석 가능해?" -> available_scans() + scan() 가이드 조합
        - scan()을 인자 없이 호출하면 설명 포함 가이드 DataFrame 반환.

    SeeAlso:
        - scan: 축 이름으로 실제 횡단분석 실행
        - Scan.__call__: axis=None이면 설명 포함 가이드 DataFrame 반환

    Args:
        없음.

    Returns:
        list[str] — 알파벳순 축 이름 목록 (예: ["account", "audit", ...]).

    Example::

        from dartlab.scan import available_scans
        available_scans()   # ['account', 'audit', 'capital', ...]
    """
    return sorted(_AXIS_REGISTRY.keys())


class Scan:
    """시장 전체 횡단분석 -- 15축, 전부 Polars DataFrame.

    Capabilities:
        - governance: 최대주주 지분, 사외이사, 감사위원회 종합 등급
        - workforce: 임직원 수, 평균급여, 근속연수
        - capital: 배당수익률, 배당성향, 자사주
        - debt: 사채만기, 부채비율, ICR, 위험등급
        - account: 전종목 단일 계정 시계열 (매출액, 영업이익 등)
        - ratio: 전종목 단일 재무비율 시계열 (ROE, 부채비율 등)
        - cashflow: OCF/ICF/FCF + 현금흐름 패턴 분류
        - audit: 감사의견, 감사인변경, 특기사항, 감사독립성
        - insider: 최대주주 지분변동, 자기주식, 경영권 안정성
        - quality: Accrual Ratio + CF/NI -- 이익의 현금 뒷받침
        - liquidity: 유동비율 + 당좌비율 -- 단기 지급능력
        - growth: 매출/영업이익/순이익 CAGR + 성장 패턴 분류
        - profitability: 영업이익률/순이익률/ROE/ROA + 등급
        - digest: 시장 전체 공시 변화 다이제스트
        - network: 상장사 관계 네트워크 (출자/지분/계열)

    Requires:
        데이터: 축별로 다름 (dartlab.downloadAll() 참조)
        - governance/workforce/capital/debt/audit/insider: report
        - account/ratio: finance
        - network/digest: docs

    AIContext:
        시장 전체 비교/순위 질문에 사용. 개별 종목 분석은 Company 메서드 사용.

    Guide:
        - "다른 회사랑 비교 가능해?" -> scan("account") 또는 scan("ratio") 안내
        - "거버넌스 좋은 회사?" -> scan("governance")로 등급 A 필터
        - "배당 많이 주는 회사?" -> scan("capital")로 배당수익률 정렬
        - "ROE 높은 회사?" -> scan("ratio", "roe")로 전종목 비교
        - "삼성전자랑 SK하이닉스 비교" -> scan("account", "sales", code="005930,000660")
        - API 키 불필요. 사전 다운로드 데이터만으로 동작.

    SeeAlso:
        - analysis: 개별 종목 14축 전략분석
        - Company.insights: 단일 종목 7영역 종합 분석
        - gather: 주가/수급 데이터 (모멘텀 보완)

    Args:
        axis: 축 이름. None이면 13축 가이드 반환.
        target: 축별 대상 (종목코드, 계정명, 비율명 등).
        **kwargs: 축별 옵션 (annual, fsPref, market 등).

    Returns:
        pl.DataFrame — 전종목 횡단 데이터. axis=None이면 13축 가이드 DataFrame.

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

        # EDGAR market 디스패치 — XBRL 기반 축은 EDGAR 전용 구현으로 분기
        market = callKwargs.pop("market", None)
        if market in ("edgar", "us", "US"):
            result = _edgarDispatch(resolved, callKwargs)
            if result is not None:
                return result
            # fallback: EDGAR 전용 구현 없으면 기본 함수 호출 (account/ratio 등)

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

        # 종목 필터 후 빈 결과면 사유 안내
        if target and isinstance(result, pl.DataFrame) and result.height == 0 and entry.targetParam is None:
            _MISSING_HINTS = {
                "liquidity": "금융업(은행/보험/증권)은 유동자산/유동부채 계정이 없어 유동성 분석 불가",
                "debt": "해당 종목에 사채/부채 데이터 없음",
                "audit": "해당 종목에 감사의견 데이터 없음",
            }
            hint = _MISSING_HINTS.get(resolved, f"'{target}'에 해당 데이터 없음")
            return pl.DataFrame({"info": [hint]})

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
