"""Forward Test 인프라 : 매출 예측 저장 + 사후 평가.

저장 위치 (2026-07-03 승격, scenario-simulator 09 §10.2 P9b + expectation-grid 00 §9 A2):
``~/.dartlab``(ephemeral) 폐기. ``DARTLAB_DATA_DIR`` env > ``./data`` 아래 ``forwardTests/``.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


def _forwardTestDir() -> Path:
    """기록 루트: DARTLAB_DATA_DIR env > ./data. (옛 ~/.dartlab 저장 폐기, A2)."""
    root = os.environ.get("DARTLAB_DATA_DIR")
    return (Path(root) if root else Path("data")) / "forwardTests"


@dataclass
class ForwardTestRecord:
    """단일 예측 기록."""

    key: str  # {stockCode}_{date}_{horizon}_{version}
    stockCode: str
    forecastDate: str  # ISO format
    version: str  # "v3"
    horizon: int
    projected: list[float]  # 예측 매출 (원)
    scenarios: dict[str, list[float]]  # Base/Bull/Bear
    sourcesUsed: list[str]  # 사용된 소스 목록
    assumptions: list[str]  # 예측 가정
    actual: list[float | None] = field(default_factory=list)  # 실적 (나중에 채움)
    evaluation: dict | None = None  # 평가 결과
    # v4: 방향 예측 캘리브레이션용
    directionProbability: float | None = None  # 매출 방향 예측 확률 (0~1)
    directionPredicted: str | None = None  # "up" | "down"
    directionActual: str | None = None  # 사후 채움


def generateKey(stockCode: str, horizon: int, version: str = "v3") -> str:
    """Forward test 고유 키 생성.

    Parameters
    ----------
    stockCode : str
        종목코드.
    horizon : int
        예측 기간 (년).
    version : str
        예측 버전 (기본 "v3").

    Returns
    -------
    str
        "{stockCode}_{YYYYMMDD}_{horizon}y_{version}" 형태의 키.

    Requires:
        없음. 호출 시각 UTC 사용.

    Raises:
        없음.

    Example:
        >>> generateKey("005930", 3).endswith("_3y_v3")
        True
    """
    dateStr = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{stockCode}_{dateStr}_{horizon}y_{version}"


def saveForecast(record: ForwardTestRecord) -> Path:
    """예측 기록을 로컬 JSON에 저장 (opt-in).

    Capabilities:
        - 예측 기록을 종목별 JSON 파일에 누적 저장
        - 동일 key 자동 덮어쓰기

    Parameters
    ----------
    record : ForwardTestRecord
        저장할 예측 기록.

    Returns
    -------
    Path
        저장된 파일 경로 (기록 루트[DARTLAB_DATA_DIR > ./data] 아래 forwardTests/{stockCode}.json).

    Guide:
        예측 실행 직후 호출해 사후 평가용 ground truth 와 비교 자료 누적.

    When:
        예측 결과를 캘리브레이션·forward test 평가용으로 보관할 때.

    How:
        forecastAll/scenarioAnalysis 결과를 ForwardTestRecord 로 묶어 호출.

    Requires:
        쓰기 가능한 홈 디렉토리.

    Raises:
        OSError : 파일 쓰기 실패 시.

    Example:
        >>> p = saveForecast(record)
        >>> p.suffix
        '.json'

    See Also:
        - loadRecords : 기록 조회
        - evaluate : 사후 평가

    AIContext:
        AI 답변 시 forward test 누적 후 캘리브레이션 점수 트래킹에 사용.
    """
    baseDir = _forwardTestDir()
    baseDir.mkdir(parents=True, exist_ok=True)
    filepath = baseDir / f"{record.stockCode}.json"

    # 기존 기록 로드
    records = _loadRaw(filepath)

    # 같은 키 덮어쓰기
    records = [r for r in records if r.get("key") != record.key]
    records.append(asdict(record))

    filepath.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Forward test 저장: %s → %s", record.key, filepath)
    return filepath


def loadRecords(stockCode: str) -> list[ForwardTestRecord]:
    """종목별 저장된 예측 기록 로드.

    Capabilities:
        - 종목 단일 JSON 파일에서 모든 예측 기록 복원
        - 깨진 레코드는 debug 로그 후 스킵

    Parameters
    ----------
    stockCode : str
        종목코드.

    Returns
    -------
    list[ForwardTestRecord]
        해당 종목의 모든 예측 기록. 파일 없으면 빈 리스트.

    Guide:
        evaluate 또는 evaluateCalibration 의 입력 소스.

    When:
        과거 예측 결과를 다시 평가하거나 통계 집계할 때.

    How:
        _loadRaw → dict → dataclass 복원. 깨진 레코드는 debug 로그 후 스킵.

    Requires:
        기록 루트(DARTLAB_DATA_DIR > ./data) 아래 forwardTests/ 디렉토리 읽기 가능.

    Raises:
        없음. 파일 없으면 빈 리스트.

    Example:
        >>> records = loadRecords("005930")
        >>> isinstance(records, list)
        True

    See Also:
        - saveForecast : 기록 저장
        - evaluate : 단일 기록 평가

    AIContext:
        AI 답변 시 과거 예측 회수 → 사후 평가용 데이터 소스.
    """
    filepath = _forwardTestDir() / f"{stockCode}.json"
    raw = _loadRaw(filepath)
    results = []
    for r in raw:
        try:
            results.append(ForwardTestRecord(**r))
        except TypeError:
            log.debug("Forward test 기록 파싱 실패: %s", r.get("key", "?"))
    return results


def evaluate(
    record: ForwardTestRecord,
    actualRevenue: list[float],
) -> dict:
    """예측 vs 실적 비교 평가.

    Capabilities:
        - MAE·MAPE·방향 정확도·시나리오 적중을 한 번에 계산
        - 결과를 record.evaluation 에 in-place 기록

    Parameters
    ----------
    record : ForwardTestRecord
        평가할 예측 기록.
    actualRevenue : list[float]
        실제 매출 시계열 (원).

    Returns
    -------
    dict
        mae : int — 평균 절대 오차 (원)
        mape : float — 평균 절대 백분율 오차 (%)
        directionAccuracy : float — 방향(증/감) 정확도 (%)
        scenarioHit : str — 시나리오 적중 범위 ("within_range" | "above_bull" | "below_bear")
        nCompared : int — 비교 기간 수
        evaluatedAt : str — 평가 시각 (ISO 8601)

    Guide:
        실적이 들어온 시점에 호출. record.evaluation 에 in-place 기록.

    When:
        예측 horizon 경과 후 실적 수치를 확보했을 때.

    How:
        projected vs actualRevenue 페어를 zip 비교, 시나리오 범위 적중률 계산.

    Requires:
        actualRevenue 최소 1 기.

    Raises:
        없음. n=0 이면 error dict 반환.

    Example:
        >>> r = evaluate(record, [1e9, 1.1e9, 1.2e9])
        >>> "mape" in r
        True

    See Also:
        - evaluateCalibration : 전체 통계 집계
        - generateCalibrationReport : 캘리브레이션 리포트

    AIContext:
        AI 답변 시 사후 정확도 MAPE/방향 정확도 표로 인용.
    """
    from dartlab.core.messagingHandlers import missingDataHint

    projected = record.projected
    n = min(len(projected), len(actualRevenue))
    if n == 0:
        return {"error": missingDataHint("비교", detail="projected · actualRevenue 최소 1기 필요")}

    # MAE, MAPE
    errors = []
    pctErrors = []
    directionHits = 0
    for i in range(n):
        p, a = projected[i], actualRevenue[i]
        if a is None or a <= 0:
            continue
        err = abs(p - a)
        errors.append(err)
        pctErrors.append(err / a * 100)
        # 방향성: 이전 대비 증감 일치
        if i > 0 and actualRevenue[i - 1] and actualRevenue[i - 1] > 0:
            predDir = p > projected[i - 1] if i < len(projected) else True
            actDir = a > actualRevenue[i - 1]
            if predDir == actDir:
                directionHits += 1

    mae = sum(errors) / len(errors) if errors else 0
    mape = sum(pctErrors) / len(pctErrors) if pctErrors else 0
    directionAccuracy = directionHits / max(n - 1, 1) * 100

    # 시나리오 히트: 실적이 어느 시나리오 범위에 들어갔는지
    scenarioHit = _checkScenarioHit(record.scenarios, actualRevenue)

    result = {
        "mae": round(mae),
        "mape": round(mape, 2),
        "directionAccuracy": round(directionAccuracy, 1),
        "scenarioHit": scenarioHit,
        "nCompared": n,
        "evaluatedAt": datetime.now(timezone.utc).isoformat(),
    }

    # 방향 실적 자동 설정 (캘리브레이션용)
    if record.directionPredicted and len(actualRevenue) >= 2:
        record.directionActual = "up" if actualRevenue[-1] > actualRevenue[0] else "down"

    # 기록 업데이트
    record.actual = actualRevenue[:n]
    record.evaluation = result
    return result


def _checkScenarioHit(
    scenarios: dict[str, list[float]],
    actual: list[float],
) -> str:
    """실적이 어느 시나리오 범위에 있는지 판정."""
    if not scenarios or not actual:
        return "unknown"

    bull = scenarios.get("bull", [])
    bear = scenarios.get("bear", [])

    hits: dict[str, int] = {"within_range": 0, "above_bull": 0, "below_bear": 0}
    n = min(len(actual), len(bull), len(bear))

    for i in range(n):
        a = actual[i]
        if a is None or a <= 0:
            continue
        hi = bull[i] if i < len(bull) else float("inf")
        lo = bear[i] if i < len(bear) else 0
        if a > hi:
            hits["above_bull"] += 1
        elif a < lo:
            hits["below_bear"] += 1
        else:
            hits["within_range"] += 1

    if not any(hits.values()):
        return "unknown"

    return max(hits, key=hits.get)  # type: ignore[arg-type]


def evaluateCalibration(
    stockCodes: list[str] | None = None,
) -> dict | None:
    """저장된 forward test 전체의 캘리브레이션 평가.

    모든 기록에서 directionProbability와 directionActual을 수집하여
    Brier Score + reliability diagram 생성.

    Capabilities:
        - 다종목·다버전 forward test 누적 기록 통합 캘리브레이션
        - directionProbability·directionActual 자동 수집

    Parameters
    ----------
    stockCodes : list[str], optional
        평가할 종목코드 목록. None이면 전체 스캔.

    Returns
    -------
    dict | None
        CalibrationReport dict (brierScore, reliabilityBins 등).
        데이터 5건 미만 시 None.

    Guide:
        주기적으로 호출해 dartlab 전체 예측 품질 트래킹 데이터 산출.

    When:
        시스템 전체의 확률 보정도를 평가할 때 (월/분기 단위).

    How:
        loadRecords 로 종목별 기록 → directionProbability/Actual 수집 → generateCalibrationReport.

    Requires:
        forward_tests 디렉토리에 5 건 이상 기록.

    Raises:
        없음. 데이터 부족 시 None.

    Example:
        >>> r = evaluateCalibration(["005930"])
        >>> r is None or "brierScore" in r
        True

    See Also:
        - generateCalibrationReport : 단일 리포트 생성
        - loadRecords : 종목별 기록 로드

    AIContext:
        AI 답변 시 시스템 전체 캘리브레이션 점수로 인용.
    """
    from dartlab.analysis.forecast.calibrationMetrics import generateCalibrationReport

    if stockCodes is None:
        # 모든 종목 파일 스캔
        baseDir = _forwardTestDir()
        if not baseDir.exists():
            return None
        stockCodes = [f.stem for f in baseDir.glob("*.json")]

    predictions: list[float] = []
    outcomes: list[int] = []

    for code in stockCodes:
        for r in loadRecords(code):
            if r.directionProbability is not None and r.directionActual is not None:
                predictions.append(r.directionProbability)
                outcomes.append(1 if r.directionActual == "up" else 0)

    if len(predictions) < 5:
        return None

    return generateCalibrationReport(predictions, outcomes)


def recordForecast(
    *,
    stockCode: str,
    horizon: int,
    projected: list[float],
    scenarios: dict[str, list[float]],
    sourcesUsed: list[str],
    assumptions: list[str],
    version: str = "v3",
    directionProbability: float | None = None,
    directionPredicted: str | None = None,
) -> Path:
    """예측 봉인 write-end : thin facade (새 저장 메커니즘 0, ForwardTestRecord+saveForecast 재사용).

    Capabilities:
        forecast 산출물을 발행 시각(now UTC)과 함께 ForwardTestRecord 로 봉인 저장.
        scenario-simulator 09 §10.2 P9c 티켓의 구현 : forward-test 루프의 write-end.

    Parameters
    ----------
    stockCode : str
        6자리 종목코드.
    horizon : int
        예측 연 수.
    projected : list[float]
        연도별 예측 매출 (원).
    scenarios : dict[str, list[float]]
        Base/Bull/Bear 경로.
    sourcesUsed : list[str]
        사용 소스 목록.
    assumptions : list[str]
        예측 가정.
    version : str
        기록 스키마 버전 태그 (기본 "v3").
    directionProbability : float | None
        매출 방향 예측 확률 (v4 캘리브레이션용).
    directionPredicted : str | None
        "up" | "down".

    Returns
    -------
    Path
        저장된 종목 JSON 경로.

    Guide:
        발행 즉시 호출한다. 사후 채점은 ``evaluate``, 캘리브레이션 집계는
        ``evaluateCalibration`` 이 닫는다 (write→evaluate→calibration 루프).

    When:
        expectation-grid 수집자(issueRevenue)·forecast 파이프라인이 예측을 낼 때마다.

    How:
        generateKey + now(UTC) 로 ForwardTestRecord 구성 → saveForecast 위임.

    Raises:
        없음. 저장 실패는 saveForecast 의 OSError 전파.

    Example:
        >>> recordForecast(stockCode="005930", horizon=3, projected=[1.0],
        ...                scenarios={}, sourcesUsed=[], assumptions=[])  # doctest: +SKIP

    See Also:
        - saveForecast : 저장 본체
        - evaluate / evaluateCalibration : 루프의 read-end

    Requires:
        쓰기 가능한 DARTLAB_DATA_DIR (기본 ./data).
    """
    record = ForwardTestRecord(
        key=generateKey(stockCode, horizon, version),
        stockCode=stockCode,
        forecastDate=datetime.now(timezone.utc).isoformat(),
        version=version,
        horizon=horizon,
        projected=list(projected),
        scenarios=dict(scenarios),
        sourcesUsed=list(sourcesUsed),
        assumptions=list(assumptions),
        directionProbability=directionProbability,
        directionPredicted=directionPredicted,
    )
    return saveForecast(record)


def _loadRaw(filepath: Path) -> list[dict]:
    """JSON 파일에서 raw dict 리스트 로드."""
    if not filepath.exists():
        return []
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []
