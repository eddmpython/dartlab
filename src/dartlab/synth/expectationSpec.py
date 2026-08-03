"""Expectation Grid 계약 + 채점 순수수학 : 발행 봉인 행과 분위 기반 채점의 L1.5 SSOT.

기대치 발행 봉인 행(ExpectationSpec)·채점 행(ExpectationScore) frozen dataclass 계약과
분위 5점(p5/p25/p50/p75/p95) 채점 순수수학(pinball=CRPS 근사·PIT 선형보간·coverage·skill)을
stdlib 만으로 제공한다. 시뮬레이터 검증 명세(scenario-simulator 03 §4.4)의 코드화이며,
L2 발행 엔진(macro·analysis·credit·quant)과 L2.5 수집자(simulate)가 함께 쓰는 공용 계산이라
L1.5 synth 에 둔다 (선례 = ``synth.eventStudy``).

원칙:
- 점 예측 금지: quantiles(구간) 또는 direction(확률)만 허용, 비단조 분위는 생성 시점 거부.
- 발행 행 불변: frozen. 채점은 항상 별도 ExpectationScore 행 append.
- 실패도 봉인: actual 조회 실패는 error 행으로 남긴다(생존 편향 차단).
- 표본 미달 = 미검증: ``aggregateCalibration`` 이 n<minN 이면 verified=False 를 강제한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TAUS: dict[int, float] = {5: 0.05, 25: 0.25, 50: 0.50, 75: 0.75, 95: 0.95}
QUANTILE_KEYS: tuple[int, ...] = (5, 25, 50, 75, 95)
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ExpectationSpec:
    """기대치 발행 봉인 행. frozen = 불변 원칙의 코드 표현.

    Args:
        expectationId: 원장 기본키 (``buildExpectationId`` 산출).
        domain: "macro" | "revenue" | "earnings" | "credit" | "price".
        variable: 변수 식별자 (예 ``"KR.CPI"`` · ``"005930.revenue"``).
        unit: 값 단위 ("level" · "%" · "KRW" · "prob" 등).
        freq: 채점 주기 "M" | "Q" | "Y".
        horizon: freq 단위 몇 기 앞 예측인지.
        targetPeriod: 채점 대상 기 (예 ``"2026-08"`` · ``"2026Q3"``).
        issuedAt: 발행 봉인 시각 (UTC ISO). 원장의 심장.
        issuedLive: False = 소급 생성(backfill). 공개 성적표에서 라이브와 혼합 금지.
        asOf: 발행에 사용한 데이터 vintage.
        engine: 산출 엔진 공개 verb 경로.
        engineVersion: 엔진 버전 태그.
        kind: "quantiles" | "direction".
        quantiles: {5,25,50,75,95: 값}. kind="quantiles" 필수·단조 증가 강제.
        direction: {"prob": 0~1, "predicted": "up"|"down"}. kind="direction" 필수.
        baselines: 발행 시 동시 봉인한 naive 기준선 {이름: 분위 dict 또는 점값}.
        sourceRefs: 근거 ref.
        warnings: 발행 시점 한계 라벨.
        schemaVersion: 스키마 버전 (현재 1).

    Raises:
        ValueError: 분위 5점 결손·비단조, direction prob 범위 밖, 미지 kind.
    """

    expectationId: str
    domain: str
    variable: str
    unit: str
    freq: str
    horizon: int
    targetPeriod: str
    issuedAt: str
    issuedLive: bool
    asOf: str
    engine: str
    engineVersion: str
    kind: str
    quantiles: dict[int, float] | None = None
    direction: dict[str, float | str] | None = None
    baselines: dict[str, dict[int, float] | float | None] = field(default_factory=dict)
    sourceRefs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schemaVersion: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.kind == "quantiles":
            q = self.quantiles
            if not q or any(k not in q for k in QUANTILE_KEYS):
                raise ValueError(f"quantiles 5점(p5/p25/p50/p75/p95) 필수: {self.expectationId}")
            vals = [q[k] for k in QUANTILE_KEYS]
            if any(b < a for a, b in zip(vals, vals[1:])):
                raise ValueError(f"분위 비단조: {self.expectationId}")
        elif self.kind == "direction":
            d = self.direction
            if not d or not (0.0 <= float(d.get("prob", -1.0)) <= 1.0):
                raise ValueError(f"direction.prob 는 0~1 필수: {self.expectationId}")
        else:
            raise ValueError(f"kind 는 'quantiles'|'direction' 만 허용: {self.kind}")


@dataclass(frozen=True)
class ExpectationScore:
    """채점 행. 발행 행과 분리 append 하며 재채점은 새 행으로 남긴다(revision 이력).

    Args:
        expectationId: 채점 대상 발행 행 키.
        scoredAt: 채점 시각 (UTC ISO).
        actual: 실제값. 조회 실패 시 None + error.
        actualAsOf: 실제값 조회 vintage.
        revisionPolicy: 실제값 수정 정책 표기 (현 HF macro surface = "latest").
        coverageHit90: actual ∈ [p5, p95].
        coverageHit50: actual ∈ [p25, p75].
        pit: F(actual) 분위 선형보간.
        crps: pinball 5분위 평균 (CRPS 근사).
        crpsBaseline: baseline 이름별 crps.
        skill: 1 - crps/min(crpsBaseline). 가장 센 baseline 대비.
        brier: direction 전용 (prob - outcome)^2.
        error: 실제값 조회 실패 사유 (실패도 봉인).
    """

    expectationId: str
    scoredAt: str
    actual: float | str | None
    actualAsOf: str
    revisionPolicy: str = "latest"
    coverageHit90: bool | None = None
    coverageHit50: bool | None = None
    pit: float | None = None
    crps: float | None = None
    crpsBaseline: dict[str, float] = field(default_factory=dict)
    skill: float | None = None
    brier: float | None = None
    error: str | None = None


def buildExpectationId(domain: str, variable: str, freq: str, horizon: int, targetPeriod: str, issuedAt: str) -> str:
    """원장 기본키 생성 : (도메인·변수·주기·수평선·대상기·발행시각) 재발행은 원장에서 거절된다.

    Args:
        domain: 도메인.
        variable: 변수 식별자.
        freq: 주기.
        horizon: 수평선.
        targetPeriod: 채점 대상 기 (id 에 포함해 같은 분(minute) 내 다른 대상기 충돌 차단).
        issuedAt: 발행 시각 문자열 (구분자 포함 가능, 내부에서 정규화).

    Returns:
        str: ``{domain}.{variable}.{freq}{horizon}.{targetPeriod}@{정규화 발행시각}``.

    Example:
        >>> buildExpectationId("macro", "KR.CPI", "M", 3, "2026-10", "2026-07-03T09:00")
        'macro.KR.CPI.M3.2026-10@20260703T0900'
    """
    stamp = issuedAt.replace("-", "").replace(":", "")[:13]
    return f"{domain}.{variable}.{freq}{horizon}.{targetPeriod}@{stamp}"


def pinballLoss(quantiles: dict[int, float], actual: float) -> float:
    """5분위 pinball 평균 = CRPS 근사 (scenario-simulator 03:215).

    Args:
        quantiles: {5,25,50,75,95: 예측값}.
        actual: 실제값.

    Returns:
        float: 낮을수록 좋음. 점 예측 대비 분포 전체를 채점한다.

    Example:
        >>> round(pinballLoss({5: 1.0, 25: 2.0, 50: 3.0, 75: 4.0, 95: 5.0}, 3.0), 6)
        0.14
    """
    losses = []
    for q, tau in TAUS.items():
        f = float(quantiles[q])
        diff = actual - f
        losses.append(tau * diff if diff >= 0 else (tau - 1.0) * diff)
    return sum(losses) / len(losses)


def pitValue(quantiles: dict[int, float], actual: float) -> float:
    """분위 5점 선형보간 CDF 의 F(actual). 완벽 캘리브레이션이면 Uniform[0,1].

    Args:
        quantiles: {5,25,50,75,95: 예측값}.
        actual: 실제값.

    Returns:
        float: 0.01~0.99 (구간 밖 클램프). 집계 시 10-bin 히스토그램·KS 균등성 검정 입력.
    """
    pts = sorted((float(quantiles[q]), TAUS[q]) for q in TAUS)
    if actual <= pts[0][0]:
        return 0.01
    if actual >= pts[-1][0]:
        return 0.99
    for (x0, p0), (x1, p1) in zip(pts, pts[1:]):
        if x0 <= actual <= x1:
            return p0 if x1 == x0 else p0 + (p1 - p0) * (actual - x0) / (x1 - x0)
    return 0.5


def scoreExpectation(
    spec: ExpectationSpec,
    actual: float | str | None,
    *,
    scoredAt: str,
    actualAsOf: str,
) -> ExpectationScore:
    """봉인된 발행 행 1개를 실제값으로 채점한다. 실제값 None = error 봉인 행.

    Args:
        spec: 발행 봉인 행.
        actual: 실제값 (quantiles=float, direction=범주 문자열). None 이면 실패 봉인.
        scoredAt: 채점 시각 (UTC ISO).
        actualAsOf: 실제값 조회 vintage.

    Returns:
        ExpectationScore: kind 별 지표. quantiles=coverage/PIT/crps/skill, direction=brier.

    Guide:
        skill 은 발행 시 봉인된 baseline 중 crps 최소(가장 센 것) 대비로만 계산한다
        (사후 baseline 선택 논란 차단). baseline 이 없으면 skill=None.
    """
    if actual is None:
        return ExpectationScore(spec.expectationId, scoredAt, None, actualAsOf, error="actual 조회 실패")
    if spec.kind == "direction":
        d = spec.direction or {}
        prob = float(d["prob"])
        outcome = 1.0 if actual == d.get("predicted") else 0.0
        return ExpectationScore(spec.expectationId, scoredAt, actual, actualAsOf, brier=(prob - outcome) ** 2)
    a = float(actual)
    q = spec.quantiles or {}
    crps = pinballLoss(q, a)
    crpsBase = {
        name: (pinballLoss(b, a) if isinstance(b, dict) else abs(a - float(b)))
        for name, b in spec.baselines.items()
        if b is not None
    }
    strongest = min(crpsBase.values()) if crpsBase else None
    return ExpectationScore(
        spec.expectationId,
        scoredAt,
        a,
        actualAsOf,
        coverageHit90=q[5] <= a <= q[95],
        coverageHit50=q[25] <= a <= q[75],
        pit=pitValue(q, a),
        crps=crps,
        crpsBaseline=crpsBase,
        skill=(1.0 - crps / strongest) if strongest and strongest > 0 else None,
    )


def aggregateCalibration(scores: list[ExpectationScore], *, minN: int = 24) -> dict:
    """변수군 채점 행 집계. 표본 미달이면 verified=False ('미검증' 라벨 강제).

    Args:
        scores: 채점 행 목록 (error 행 포함 가능, 분모 정직성 위해 errorRows 로 별도 계수).
        minN: 캘리브레이션 활성 최소 표본.

    Returns:
        dict: n · verified · coverage90 · coverage50 · meanPit · meanCrps · meanSkill · errorRows.
        n=0 이면 {"n": 0, "verified": False}.

    Guide:
        verified=False 인 집계는 화면에서 성과 숫자를 렌더링하지 않는다
        (고정 문구 "발행 n건 축적 중 · 캘리브레이션 미검증"만 허용).
    """
    okC = [s for s in scores if s.error is None and s.crps is not None]  # 연속(분위)
    okB = [s for s in scores if s.error is None and s.brier is not None]  # 이진(방향)
    n = len(okC) + len(okB)
    errorRows = sum(1 for s in scores if s.error is not None)
    if n == 0:
        return {"n": 0, "verified": False, "errorRows": errorRows}
    skills = [s.skill for s in okC if s.skill is not None]
    out: dict = {"n": n, "verified": n >= minN, "errorRows": errorRows}
    if okC:
        out.update(
            coverage90=sum(bool(s.coverageHit90) for s in okC) / len(okC),
            coverage50=sum(bool(s.coverageHit50) for s in okC) / len(okC),
            meanPit=sum(s.pit for s in okC if s.pit is not None) / len(okC),
            meanCrps=sum(s.crps for s in okC if s.crps is not None) / len(okC),
            meanSkill=(sum(skills) / len(skills)) if skills else None,
        )
    if okB:
        out["meanBrier"] = sum(s.brier for s in okB if s.brier is not None) / len(okB)
        out["nDirection"] = len(okB)
    return out
