"""Forward Test 인프라 — 매출 예측 저장 + 사후 평가."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

_FORWARD_TEST_DIR = Path.home() / ".dartlab" / "forward_tests"


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
    """고유 키 생성."""
    dateStr = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{stockCode}_{dateStr}_{horizon}y_{version}"


def saveForecast(record: ForwardTestRecord) -> Path:
    """예측 기록 저장 (opt-in)."""
    _FORWARD_TEST_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _FORWARD_TEST_DIR / f"{record.stockCode}.json"

    # 기존 기록 로드
    records = _loadRaw(filepath)

    # 같은 키 덮어쓰기
    records = [r for r in records if r.get("key") != record.key]
    records.append(asdict(record))

    filepath.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Forward test 저장: %s → %s", record.key, filepath)
    return filepath


def loadRecords(stockCode: str) -> list[ForwardTestRecord]:
    """종목별 저장된 예측 기록 로드."""
    filepath = _FORWARD_TEST_DIR / f"{stockCode}.json"
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
    """예측 vs 실적 비교 평가."""
    projected = record.projected
    n = min(len(projected), len(actualRevenue))
    if n == 0:
        return {"error": "비교할 데이터 없음"}

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
) -> dict | None:  # CalibrationReport from calibrationMetrics
    """저장된 forward test 전체의 캘리브레이션 평가.

    모든 기록에서 directionProbability와 directionActual을 수집하여
    Brier Score + reliability diagram 생성.
    """
    from dartlab.analysis.forecast.calibrationMetrics import generateCalibrationReport

    if stockCodes is None:
        # 모든 종목 파일 스캔
        if not _FORWARD_TEST_DIR.exists():
            return None
        stockCodes = [f.stem for f in _FORWARD_TEST_DIR.glob("*.json")]

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


def _loadRaw(filepath: Path) -> list[dict]:
    """JSON 파일에서 raw dict 리스트 로드."""
    if not filepath.exists():
        return []
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []
