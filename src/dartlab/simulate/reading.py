"""판독 계약 : 표면별 주간 판독 봉인 행 + 임계 상수 SSOT (L2.5 simulate).

시뮬레이터 "현재" 축(scenario-simulator/06)의 최소 단위 계약. 매주 전상장사 x 전표면에
대해 방향 판독을 발행하고, 발행 시점에 봉인한 뒤 지평 도래 시 채점한다. ExpectationSpec 이
분위/방향 기대의 계약이라면 Reading 은 횡단면 표면 판독의 계약이며, 스케일이 다르다
(주당 수백만 행). 그래서 per-row JSON 이 아니라 컬럼형 원장(readingLedger)에 담고, 본 모듈은
① Reading dataclass ② SurfaceSpec(표면 등재 선언) ③ 임계 상수(방향화 게이트·표본 게이트·
factor-zoo t 허들)만 소유한다.

원칙 (06 §2~4):
- 모든 회사가 매주 표면마다 "판독/중립/기권" 셋 중 하나로 기록된다 (silent 누락 0).
- 기권(abstain)은 1급 출력: 0 으로 대체 금지, 기권률도 채점 대상.
- 표면은 손 선별 0: 카탈로그 자동 등재, 도태는 성적표(t·표본 게이트)가 한다.
- 방향 불가 표면은 무방향 등재 + 양방향 채점 (죽은 표면도 목록에서 안 사라진다).

Layer: L2.5 simulate 소유 (표면 판독은 simulate 가 하위 엔진 verb 를 소비해 산출하는 것이라
L2 엔진은 본 계약을 import 하지 않는다. 하향 단방향 import 로 구조적 보장).
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 1

# 방향화 게이트 (06 §3, 실측 도출): 이 표본·중앙값 미달 이벤트 타입은 무방향 등재.
DIRECTION_MIN_N = 100
DIRECTION_MIN_ABS_MEDIAN = 0.01
# factor-zoo 허들 (06 §4, Harvey-Liu-Zhu): 주단위 |t| 미달 표면은 "동물원 구분불가" 라벨.
FACTOR_ZOO_T = 3.0
# 표본 게이트 (성적표): 채점 주 수 미달 표면 그룹은 "미검증" 라벨 (성과 숫자 렌더 금지).
SCORECARD_MIN_WEEKS = 20
# 연속/이산 표면 판별: 고유 점수 값이 이 수를 넘으면 연속(분위 채점), 이하면 이산(방향 채점).
CONTINUOUS_DISTINCT_MIN = 10


@dataclass(frozen=True)
class Reading:
    """표면별 주간 판독 봉인 행. frozen = 발행 후 불변.

    Args:
        stockCode: 6자리 종목코드 (KR) 또는 티커 (US).
        market: "KR" | "US". 시장 내 완결 (혼합 순위 금지).
        surface: 표면 id (전수 레지스트리 키. 예 ``"price.mom20x5"`` · ``"fund.ep"`` ·
            ``"event.dilutionGovernance"``).
        week: iso year*100+week 주 식별자 (예 202607).
        asOf: PIT 기준일 'YYYYMMDD' (그 주 마지막 거래일).
        horizon: 거래일 지평 (v0=5, 표면별 자연 지평 다중 가능).
        direction: +1 상방 / -1 하방 / 0 중립·기권.
        score: 강도 0~1 (연속 표면 랭크) 또는 None (기권).
        abstainReason: 기권 사유 (0 대체 금지). None = 판독 발행됨.
    """

    stockCode: str
    market: str
    surface: str
    week: int
    asOf: str
    horizon: int
    direction: int
    score: float | None = None
    abstainReason: str | None = None


@dataclass(frozen=True)
class SurfaceSpec:
    """표면 등재 선언. 카탈로그 자동 열거의 산물이며 방향화 규칙을 담는다.

    Args:
        surface: 표면 id (레지스트리 키).
        axis: 원천 축 "price" | "fund" | "event" | "flow" | "narrative" ....
        kind: "continuous" (분위 채점) | "directional" (상/하 집단 채점).
        directional: 방향 선언. continuous 는 부호 규칙(예 고 E/P = 상방), directional 은
            타입별 방향 사전(방향화 게이트 통과분). None = 무방향(양방향 채점).
        naturalHorizon: 이 표면의 자연 지평(거래일). 다중 지평 표면은 대표값.
        provenance: 소비하는 공개 verb·원천 (refs 자연 기록. 엔진 소유 계약 명시).
    """

    surface: str
    axis: str
    kind: str
    directional: dict | None = None
    naturalHorizon: int = 5
    provenance: tuple[str, ...] = field(default_factory=tuple)
