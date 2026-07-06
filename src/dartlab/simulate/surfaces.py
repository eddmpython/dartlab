"""표면 레지스트리 : 판독 표면 자동 열거 + 이벤트 타입 정규화 v2 + 방향화 선언 (L2.5 simulate).

표면은 손으로 쓰지 않고 축별로 자동 열거한다 (06 §3, 선별 0). 가격 신호·재무 비율·공시 타입이
각각 SurfaceSpec 으로 등재되고, 방향 불가 표면도 무방향으로 등재된다 (죽은 표면도 목록에서
안 사라진다). 이벤트 타입 정규화는 래퍼 보고서(주요사항보고서 등) 괄호 내 하위타입을
추출한다: 이 정규화 없이는 유상증자·CB발행 같은 핵심 희석 이벤트가 "주요사항보고서" 덩어리에
파묻힌다 (실측: 유상증자결정 972→5,679, 전환사채권발행결정 1→3,567).

Layer: L2.5 simulate. 표면 선언은 하위 엔진 카탈로그(scan·quant guide·allFilings 타입)를
소비해 만들며, 엔진 로직 재구현이 아니라 등재 선언이다.
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate.reading import SurfaceSpec

# 괄호 안이 진짜 타입인 래퍼 보고서 (prefix 만으론 무의미). 손 목록이 아니라 래퍼 집합 선언.
EVENT_WRAPPERS: tuple[str, ...] = (
    "주요사항보고서",
    "기타경영사항",
    "투자판단관련주요경영사항",
    "자율공시",
    "공정공시",
    "거래정지",
)

# 자금조달(희석 사슬) 이벤트 타입 SSOT (profile 축3·credit 피드 공유. 시장별 정규화 타입).
FINANCING_EVENTS: dict[str, tuple[str, ...]] = {
    "KR": ("전환사채권발행결정", "유상증자결정", "신주인수권부사채권발행결정"),
    "US": ("securitiesOffering",),
}

# 가격 축 신호 (quant/scan guide 파생. 방향 규칙: 고 랭크 = 상방 선언, 성적표가 부호 검증).
# maxRet20 = 복권성(MAX, Bali-Cakici-Whitelaw): 고 MAX 는 회피 신호라 성적표가 음 부호로 검증.
_PRICE_SIGNALS: tuple[str, ...] = ("ret5", "mom20x5", "volShock", "high52", "maxRet20")
# 재무 축 비율 (fundDaily 파생. 고 E/P·B/M = 저평가 = 상방 선언).
_FUND_RATIOS: tuple[str, ...] = ("ep", "bm")


def normalizeEventType() -> pl.Expr:
    """report_nm → reportType v2 (래퍼는 하위타입 추출, 나머지는 prefix).

    Returns:
        polars Expr: 대괄호 접두 제거 후, prefix 가 EVENT_WRAPPERS 이고 괄호 하위타입이 있으면
        그 하위타입(앞 24자), 아니면 prefix(앞 24자).
    """
    base = pl.col("report_nm").str.replace_all(r"\[[^\]]*\]", "").str.strip_chars()
    prefix = base.str.replace(r"\(.*$", "").str.strip_chars()
    subtype = base.str.extract(r"\(([^)]+)\)", 1)
    isWrapper = prefix.is_in(list(EVENT_WRAPPERS))
    return pl.when(isWrapper & subtype.is_not_null()).then(subtype.str.slice(0, 24)).otherwise(prefix.str.slice(0, 24))


def priceSurfaces() -> list[SurfaceSpec]:
    """가격 축 표면 선언 (연속, 고 랭크 = 상방)."""
    return [
        SurfaceSpec(
            surface=f"price.{s}",
            axis="price",
            kind="continuous",
            directional={"highIsUp": True},
            naturalHorizon=5,
            provenance=("gather.price", "quant.momentum"),
        )
        for s in _PRICE_SIGNALS
    ]


def fundSurfaces() -> list[SurfaceSpec]:
    """재무 축 표면 선언 (연속, 고 E/P·B/M = 저평가 = 상방)."""
    return [
        SurfaceSpec(
            surface=f"fund.{s}",
            axis="fund",
            kind="continuous",
            directional={"highIsUp": True},
            naturalHorizon=5,
            provenance=("dart.finance", "fundDaily"),
        )
        for s in _FUND_RATIOS
    ]


def eventSurfaces(directionByType: dict[str, int] | None = None) -> list[SurfaceSpec]:
    """이벤트 축 표면 선언 (이산 방향).

    v0 는 방향화 게이트 통과 이벤트 타입을 하나의 희석·거버넌스 방향 표면으로 묶는다. 타입별
    분리 표면은 성적표가 타입 단위 생존을 확인한 뒤 승격한다 (전수 등재 + 사후 태그 원칙).

    Args:
        directionByType: {reportType: +1|-1} 방향 사전 (없으면 무방향 등재).
    """
    return [
        SurfaceSpec(
            surface="event.dilutionGovernance",
            axis="event",
            kind="directional",
            directional=directionByType,
            naturalHorizon=5,
            provenance=("dart.allFilings",),
        )
    ]


def enumerateSurfaces(directionByType: dict[str, int] | None = None) -> list[SurfaceSpec]:
    """전 축 표면 자동 열거 (선별 0). 방향화 사전은 성적표 bootstrap 에서 주입된다."""
    return priceSurfaces() + fundSurfaces() + eventSurfaces(directionByType)
