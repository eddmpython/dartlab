"""scan 라우터 — axis registry + aliases + resolver + EDGAR dispatcher.

`scan/__init__.py` 가 thin facade 가 되도록 본 모듈로 registry/resolver 만 격리
(P-S1). 사용자 facade Scan 클래스는 `scan/scanClass.py` 로 분리 (P-S9).
한글 rename 은 `scan/rename.py` 에 SSOT 격리. Scan 인스턴스는 dartlab 최상위
`__init__.py` 에서 lazy 생성.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass

import polars as pl

# ── Axis Registry ────────────────────────────────────────


@dataclass(frozen=True)
class _AxisEntry:
    """scan 축 레지스트리 엔트리 — 모듈/함수/라벨/설명 등 축별 메타데이터.

    Attributes
    ----------
    module : str — 축 구현 모듈 경로 (dotted)
    fn : str — 모듈 내 호출 함수명
    label : str — 한글 축 이름
    description : str — 축 설명 (가이드 출력용)
    example : str — 사용 예시 문자열
    targetParam : str | None — target 파라미터명 (None 이면 stockCode 필터)
    targetRequired : bool — target 필수 여부
    returnType : str — 반환 타입 ("DataFrame" | "dict")
    listModule : str | None — 목록 반환용 모듈 (target 없이 호출 시)
    listFn : str | None — 목록 반환용 함수명
    """

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
        fn="scanGovernance",
        label="거버넌스",
        description="지배구조 (지분율, 사외이사, 보수비율, 감사의견, 소액주주 분산)",
        example='scan("governance")',
    ),
    "workforce": _AxisEntry(
        module="dartlab.scan.workforce",
        fn="scanWorkforce",
        label="인력/급여",
        description="직원수, 평균급여, 인건비율, 1인당부가가치, 성장률, 고액보수",
        example='scan("workforce")',
    ),
    "capital": _AxisEntry(
        module="dartlab.scan.capital",
        fn="scanCapital",
        label="주주환원",
        description="배당, 자사주(취득/처분/소각), 증자/감자, 환원 분류",
        example='scan("capital")',
    ),
    "debt": _AxisEntry(
        module="dartlab.scan.debt",
        fn="scanDebt",
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
        fn="buildGraph",
        label="네트워크",
        description="상장사 관계 네트워크 (출자/지분/계열)",
        example='scan("network")',
        returnType="dict",
    ),
    "cashflow": _AxisEntry(
        module="dartlab.scan.financial.cashflow",
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
        module="dartlab.scan.financial.quality",
        fn="scanQuality",
        label="이익의 질",
        description="Accrual Ratio + CF/NI 비율 — 이익이 현금 뒷받침되는지",
        example='scan("quality")',
    ),
    "liquidity": _AxisEntry(
        module="dartlab.scan.financial.liquidity",
        fn="scanLiquidity",
        label="유동성",
        description="유동비율 + 당좌비율 — 단기 지급능력",
        example='scan("liquidity")',
    ),
    "growth": _AxisEntry(
        module="dartlab.scan.financial.growth",
        fn="scanGrowth",
        label="성장성",
        description="매출/영업이익/순이익 CAGR + 성장 패턴 분류 (6종)",
        example='scan("growth")',
    ),
    "profitability": _AxisEntry(
        module="dartlab.scan.financial.profitability",
        fn="scanProfitability",
        label="수익성",
        description="영업이익률/순이익률/ROE/ROA + 등급",
        example='scan("profitability")',
    ),
    "efficiency": _AxisEntry(
        module="dartlab.scan.financial.efficiency",
        fn="scanEfficiency",
        label="효율성",
        description="자산/재고/매출채권 회전율 + CCC(현금전환주기) + 등급",
        example='scan("efficiency")',
    ),
    "valuation": _AxisEntry(
        module="dartlab.scan.financial.valuation",
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
        fn="scanMacroBeta",
        label="거시베타",
        description="전종목 GDP/금리/환율 베타 횡단면 (OLS 회귀). 사전 수집: Ecos().series('GDP', enrich=True)",
        example='scan("macroBeta")',
    ),
    "fields": _AxisEntry(
        module="dartlab.scan.builders.kr.fields",
        fn="scanFields",
        label="필드카탈로그",
        description="조건형 스크리닝용 필드 검색 (finance/report/docs/krx/krxIndex)",
        example='scan("fields", "roe")',
        targetParam="query",
        targetRequired=False,
    ),
    "screen": _AxisEntry(
        module="dartlab.scan.screen",
        fn="scanScreen",
        label="스크리닝",
        description="멀티팩터 프리셋 + spec 기반 조건형 스크리닝",
        example='scan("screen", "value") 또는 scan("screen", spec={...})',
        targetParam="target",
        targetRequired=False,
    ),
    "disclosureRisk": _AxisEntry(
        module="dartlab.scan.disclosureRisk",
        fn="scanDisclosureRisk",
        label="공시리스크",
        description="공시 변화 기반 선행 리스크 (우발부채, 감사변경, 계열변화, 사업전환)",
        example='scan("disclosureRisk")',
    ),
    "orders": _AxisEntry(
        module="dartlab.scan.orders",
        fn="scanOrders",
        label="신규수주",
        description="전 상장사 신규수주 flow (book-to-bill, 모멘텀, 계약상대 집중도) — 단일판매·공급계약 선행지표",
        example='scan("orders")',
    ),
    "ipo": _AxisEntry(
        module="dartlab.scan.ipo",
        fn="scanIpo",
        label="신규상장",
        description="최근 신규상장 IPO 발굴 (증권신고서 지분증권) — 공모가밴드·청약일·적용 PER·할인율·항등식 검증",
        example='scan("ipo")',
    ),
    "salesByProduct": _AxisEntry(
        module="dartlab.scan.salesByProduct",
        fn="scanSalesByProduct",
        label="사업부문 매출구성",
        description="전 상장사 사업부문별 매출 비중·집중도(HHI)·다각화 등급 (사업보고서 매출및수주 표). 단위-불변 mix 지표",
        example='scan("salesByProduct")',
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
    # fields
    "필드": "fields",
    "필드카탈로그": "fields",
    "필드검색": "fields",
    # dividendTrend
    "배당추이": "dividendTrend",
    "배당시계열": "dividendTrend",
    "배당트렌드": "dividendTrend",
    # screen
    "스크리닝": "screen",
    "스크린": "screen",
    "필터": "screen",
    # disclosureRisk
    "공시리스크": "disclosureRisk",
    "공시변화": "disclosureRisk",
    # orders
    "신규수주": "orders",
    "수주": "orders",
    "수주현황": "orders",
    "공급계약": "orders",
    # ipo
    "신규상장": "ipo",
    "공모": "ipo",
    "아이피오": "ipo",
    "증권신고서": "ipo",
    # salesByProduct
    "부문별매출": "salesByProduct",
    "사업부문": "salesByProduct",
    "매출구성": "salesByProduct",
    "제품별매출": "salesByProduct",
    "다각화": "salesByProduct",
    "사업다각화": "salesByProduct",
}


def _edgarDispatch(axis: str, kwargs: dict) -> pl.DataFrame | None:
    """EDGAR 전용 scan 축 디스패치.

    Parameters
    ----------
    axis : str
        정규화된 축 이름 (예: "profitability", "account").
    kwargs : dict
        축 함수에 전달할 키워드 인자.

    Returns
    -------
    pl.DataFrame | None
        EDGAR 축 결과 DataFrame. 구현 없는 축이면 None.
    """
    # XBRL 기반 11 축 — edgarScan._DISPATCH 와 1:1. 미라우팅 시 scanClass 가 DART 구현
    # (valuation=네이버 실시간가, audit=DART 감사데이터)으로 잘못 fallback 하므로 전 축을 라우팅한다.
    _EDGAR_XBRL_AXES = {
        "profitability",
        "growth",
        "quality",
        "liquidity",
        "efficiency",
        "cashflow",
        "dividendTrend",
        "capital",
        "debt",
        "valuation",
        "audit",
    }
    if axis in _EDGAR_XBRL_AXES:
        from dartlab.scan.builders.edgar.scan import edgarScan

        return edgarScan(axis, **kwargs)

    # account/ratio — 기존 EDGAR scanAccount 사용
    if axis == "account":
        from dartlab.providers.edgar.finance.scanAccount import scanAccount

        return scanAccount(kwargs.get("snakeId", "sales"), freq=kwargs.get("freq", "Q"))
    if axis == "ratio":
        from dartlab.providers.edgar.finance.scanAccount import scanRatio

        return scanRatio(kwargs.get("ratioName", "roe"), freq=kwargs.get("freq", "Q"))

    return None  # 아직 EDGAR 구현 없는 축


_SCAN_GROUPS: dict[str, list[str]] = {
    "financial": [
        "profitability",
        "growth",
        "efficiency",
        "quality",
        "liquidity",
        "valuation",
        "cashflow",
        "dividendTrend",
    ],
}

_GROUP_ALIASES: dict[str, str] = {
    "재무": "financial",
    "재무분석": "financial",
}


def _resolveGroup(name: str) -> str | None:
    """그룹 이름 또는 alias → 정규 그룹 이름.

    Parameters
    ----------
    name : str
        그룹 이름 또는 한글 alias (예: "financial", "재무").

    Returns
    -------
    str | None
        정규 그룹 이름 (예: "financial"). 그룹이 아니면 None.
    """
    if name in _SCAN_GROUPS:
        return name
    if name in _GROUP_ALIASES:
        return _GROUP_ALIASES[name]
    return None


def _resolveAxis(axis: str) -> str:
    """축 이름 또는 명시 alias → 정규 축 이름.

    consistency_no_alias 원칙: case-insensitive 매칭 ``axis.lower()`` 는 silent
    alias 라 인정하지 않는다. 사용자는 정식 표기 (camelCase: ``"macroBeta"``,
    ``"disclosureRisk"`` 또는 한글 alias) 를 정확히 사용해야 한다.

    Parameters
    ----------
    axis : str
        정식 축 이름 (camelCase) 또는 ``_ALIASES`` 등록 한글 alias.

    Returns
    -------
    str
        정규 축 이름 (예: ``"governance"``, ``"macroBeta"``).

    Raises
    ------
    ValueError
        알 수 없는 축 이름 또는 case 불일치 (예: ``"MacroBeta"``, ``"macrobeta"``).
    """
    if axis in _AXIS_REGISTRY:
        return axis
    if axis in _ALIASES:
        return _ALIASES[axis]
    available = ", ".join(sorted(_AXIS_REGISTRY))
    raise ValueError(
        f"알 수 없는 scan 축: '{axis}'. 가용 축: {available}\n"
        f"  사용법: dartlab.scan() 으로 전체 축 가이드를 확인하세요."
    )


# ── Scan Class ───────────────────────────────────────────


def availableScans() -> list[str]:
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

    Raises:
        없음 — 메모리 dict 정렬만 수행, 외부 호출 없음.

    Example::

        from dartlab.scan import availableScans
        availableScans()   # ['account', 'audit', 'capital', ...]
    """
    return sorted(_AXIS_REGISTRY.keys())
