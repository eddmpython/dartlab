"""시뮬 작업대 : 엔진별 데이터 피드 레지스트리 (등록 = 표면 자동 등재, L2.5 simulate).

운영자 요구 "모든 엔진의 데이터를 엔진별로 받는 작업대 + 나중에 엔진/데이터가 추가돼도 자동흡수"
의 메커니즘. 어떤 엔진이든 (code, week, 수치컬럼...) 를 내는 provider 를 `registerCompanyFeed`
1줄로 등록하면, 라이브 사이클(issueReadings)이 자동 소비하고 opine 이 컬럼마다
"<axis>.<col>" 표면을 자동 등재하며, 성적표·인증 깔때기·격자·board 가 무수정으로 흡수한다
(손 선별 0, 도태는 측정이 = 06 §3).

핵심 3축(price·fund·event)은 table 이 床 로 이미 서 있고(_buildMatrices), 본 레지스트리는 그
너머의 확장축이다: 새 엔진(예 quant 파생·industry 모멘텀·credit 스코어)이 붙을 자리. 피드 실패는
그 축 결측(스킵)으로 기록하고 사이클을 죽이지 않는다 (feedErrors 로 정직 노출, silent 삼킴 금지).

매크로 팩터 자동흡수는 별도 축 = factors.registerMacroFactor (베타·격자·시나리오 흡수).

Layer: L2.5 simulate. polars 만 의존 (하향). 레지스트리 = 순수 선언.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import polars as pl


@dataclass(frozen=True)
class CompanyFeed:
    """엔진 데이터 피드 1건 계약. 등록 = 표면 자동 등재.

    Args:
        axis: 표면 접두 축 id (surface = "<axis>.<col>"). 예 "quant"·"credit"·"industryMom".
        provider: ctx dict -> (code, week, 수치컬럼...) DataFrame. ctx = {"weekMap","weekEnd",
            "dataDir","market"} (床 재사용). 수치 컬럼마다 표면 1개.
        markets: 이 피드가 유효한 시장 튜플 (기본 KR).
    """

    axis: str
    provider: Callable[[dict], pl.DataFrame]
    markets: tuple[str, ...] = ("KR",)


_FEEDS: dict[str, CompanyFeed] = {}


def registerCompanyFeed(feed: CompanyFeed) -> None:
    """피드 등록 (자동흡수 진입점, 같은 axis 재등록 = 교체·멱등).

    등록 즉시 라이브 사이클(issueReadings matrices=None 경로)이 소비 → opine 자동 표면 →
    성적표/인증/격자 무수정 흡수. 새 엔진 연결 = 이 1줄.
    """
    _FEEDS[feed.axis] = feed


def unregisterCompanyFeed(axis: str) -> None:
    """피드 해제 (대칭 관리. 표면 이력은 원장에 남고 신규 발행만 중단)."""
    _FEEDS.pop(axis, None)


def companyFeeds() -> list[CompanyFeed]:
    """등록 피드 전수 (axis 정렬 = 결정론 순회)."""
    return [_FEEDS[k] for k in sorted(_FEEDS)]


def extraFeedMatrices(ctx: dict) -> tuple[dict[str, pl.DataFrame], dict[str, str]]:
    """등록 피드 전수 실행 → ({axis: 행렬}, {axis: 오류}). 실패 축은 결측 + 오류 명시 (silent 0).

    Args:
        ctx: {"weekMap","weekEnd","dataDir","market"} 床 컨텍스트.

    Returns:
        (matrices, errors). matrices 는 opine(extraMatrices=...) 직결. errors 는 호출자가 로그/
        블록에 기록 (피드 하나가 죽어도 주간 사이클은 계속, 결번 금지 규율과 동형).
    """
    out: dict[str, pl.DataFrame] = {}
    errors: dict[str, str] = {}
    market = ctx.get("market", "KR")
    for feed in companyFeeds():
        if market not in feed.markets:
            continue
        try:
            m = feed.provider(ctx)
        except Exception as e:  # noqa: BLE001 - 피드 격리: 한 피드 실패가 사이클을 못 죽임 (오류는 명시 반환)
            errors[feed.axis] = f"{type(e).__name__}: {e}"
            continue
        if m is None or m.height == 0 or "code" not in m.columns or "week" not in m.columns:
            errors[feed.axis] = "빈 산출 또는 (code, week) 스키마 미충족"
            continue
        out[feed.axis] = m
    return out, errors
