"""시뮬 종류 확장 계약 : 고정 목록 금지, 레지스트리 (L2.5 simulate).

경제·재무·가격·퀀트는 첫 등재 4건이지 고정 분류가 아니다 (06 §5b, 운영자 2026-07-05). 시뮬
종류도 표면과 같은 레지스트리이며, 새 시뮬은 4계약을 채우면 등재된다: ① 원천 계보(소비 데이터·
공개 verb, refs), ② 가정 축(AssumptionLedgerRow 로 이 시뮬의 if 선언), ③ 산출 계약(기본형 =
원천 동형 시계열 연장, 연장 행에 simulated 라벨 필수), ④ 채점 규칙(실제값 도착 시 무엇으로
채점). 채점 불가 탐색용 시뮬은 등재 가능하되 영구 "unscorable" 라벨. 불변은 이 4계약 + 원장
(봉인·채점·도태는 성적)뿐. 종류 추가에 엔진 재설계 0. 시간축과 시뮬 종류 축은 직교한다.

- ``SimTypeSpec`` : 시뮬 종류 4계약 선언.
- ``SIMTYPE_REGISTRY`` / ``registerSimType`` / ``listSimTypes`` : 레지스트리.

Layer: L2.5 simulate. 순수 선언 (부작용 0).
"""

from __future__ import annotations

from dataclasses import dataclass

# 산출 계약 종류. 기본형 = 원천 동형 시계열 연장. 횡단 판독처럼 연장 아닌 산출은 예외형 명시.
OUTPUT_EXTENSION = "sourceIsomorphicExtension"  # 원천 스키마·격자로 미래 구간 연장 (월/분기/일 path)
OUTPUT_CROSS_SECTIONAL = "crossSectionalReading"  # 횡단면 판독 (연장 아님, 예외형)


@dataclass(frozen=True)
class SimTypeSpec:
    """시뮬 종류 1행 4계약 (06 §5b). 등재 = 4계약을 채움.

    Args:
        simTypeId: 시뮬 종류 식별자.
        sourceLineage: 소비 데이터·공개 verb (원천 연장선, refs 기록).
        assumptionAxis: 이 시뮬의 if 를 AssumptionLedgerRow dimension 으로 (가정 축).
        outputContract: OUTPUT_EXTENSION(원천 동형 연장) | OUTPUT_CROSS_SECTIONAL(예외형).
        scoringRule: 실제값 도착 시 채점 방식. "unscorable" = 채점 불가 탐색용 (영구 미채점 라벨).
        status: "wired"(실배선) | "roadmap"(설계).
    """

    simTypeId: str
    sourceLineage: tuple[str, ...]
    assumptionAxis: tuple[str, ...]
    outputContract: str
    scoringRule: str
    status: str = "wired"


# 첫 등재 4건 (예시, 고정 아님) + 판독 엔진(이 세션 실장).
SIMTYPE_REGISTRY: dict[str, SimTypeSpec] = {
    "economy": SimTypeSpec(
        "economy",
        ("macro.scenarios", "getPresetScenarios"),
        ("regime", "namedPreset"),
        OUTPUT_EXTENSION,
        "실측 매크로 도착 시 같은 월 격자 1:1 (issueMacro 분위 봉인)",
    ),
    "finance": SimTypeSpec(
        "finance",
        ("Company.panel", "proforma"),
        ("driverElasticity", "marginNormalization"),
        OUTPUT_EXTENSION,
        "실측 분기 재무 도착 시 같은 분기 행 1:1 (proforma 연장)",
    ),
    "price": SimTypeSpec(
        "price",
        ("gather.price", "conformal"),
        ("volRegime", "pathSeed"),
        OUTPUT_EXTENSION,
        "실측 일 가격 도착 시 conformal 밴드 커버리지 채점 (ACI)",
    ),
    "quant": SimTypeSpec(
        "quant",
        ("simulate.reading", "assume.grid"),
        ("weightScheme", "consensusTopK", "horizon"),
        OUTPUT_CROSS_SECTIONAL,
        "5거래일 지평 도래 시 버킷 중립 초과 채점 (readingScorecard)",
    ),
    "reading": SimTypeSpec(
        "reading",
        ("simulate.table", "opine", "levers", "profile"),
        ("weightScheme", "gateStrength", "consensusTopK", "horizon", "scenarioPreset"),
        OUTPUT_CROSS_SECTIONAL,
        "지평 도래 시 net-of-cost 버킷 중립 초과 + 인증 깔때기 (backtest·runweek)",
    ),
}

_EXTRA: dict[str, SimTypeSpec] = {}


def registerSimType(spec: SimTypeSpec) -> None:
    """새 시뮬 종류 등재 (4계약 충족 검증). 종류 추가에 엔진 재설계 0."""
    if not (spec.simTypeId and spec.sourceLineage and spec.assumptionAxis and spec.outputContract and spec.scoringRule):
        raise ValueError(f"시뮬 종류 4계약 미충족: {spec.simTypeId} (원천·가정·산출·채점 전부 필수)")
    if spec.outputContract not in (OUTPUT_EXTENSION, OUTPUT_CROSS_SECTIONAL):
        raise ValueError(f"산출 계약 미지정: {spec.outputContract} (연장 아닌 산출은 예외형 명시)")
    _EXTRA[spec.simTypeId] = spec


def listSimTypes() -> dict[str, SimTypeSpec]:
    """등재 시뮬 종류 전체 (기본 5 + 등재분). 시간축과 직교."""
    return {**SIMTYPE_REGISTRY, **_EXTRA}


def isScorable(simTypeId: str) -> bool:
    """이 시뮬 종류가 채점 가능한가 (unscorable = 탐색 전용, 영구 미채점 라벨)."""
    spec = listSimTypes().get(simTypeId)
    return bool(spec) and spec.scoringRule != "unscorable"
