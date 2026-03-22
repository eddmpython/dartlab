"""Forward Test 인프라 — 매출 예측 저장 + 사후 평가.

예측 시점의 결과를 JSON으로 저장하고, 실적 확정 후 자동 비교.
저장 경로: ~/.dartlab/forward_tests/{stock_code}.json

사용 흐름:
1. 예측 생성 시: save_forecast() — opt-in으로 저장
2. 실적 확정 후: evaluate() — 자동 비교
3. 이력 조회: load_records() — 저장된 예측 목록
"""

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

    key: str  # {stock_code}_{date}_{horizon}_{version}
    stock_code: str
    forecast_date: str  # ISO format
    version: str  # "v3"
    horizon: int
    projected: list[float]  # 예측 매출 (원)
    scenarios: dict[str, list[float]]  # Base/Bull/Bear
    sources_used: list[str]  # 사용된 소스 목록
    assumptions: list[str]  # 예측 가정
    actual: list[float | None] = field(default_factory=list)  # 실적 (나중에 채움)
    evaluation: dict | None = None  # 평가 결과


def generate_key(stock_code: str, horizon: int, version: str = "v3") -> str:
    """고유 키 생성."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{stock_code}_{date_str}_{horizon}y_{version}"


def save_forecast(record: ForwardTestRecord) -> Path:
    """예측 기록 저장 (opt-in).

    Returns:
        저장된 파일 경로.
    """
    _FORWARD_TEST_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _FORWARD_TEST_DIR / f"{record.stock_code}.json"

    # 기존 기록 로드
    records = _load_raw(filepath)

    # 같은 키 덮어쓰기
    records = [r for r in records if r.get("key") != record.key]
    records.append(asdict(record))

    filepath.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Forward test 저장: %s → %s", record.key, filepath)
    return filepath


def load_records(stock_code: str) -> list[ForwardTestRecord]:
    """종목별 저장된 예측 기록 로드."""
    filepath = _FORWARD_TEST_DIR / f"{stock_code}.json"
    raw = _load_raw(filepath)
    results = []
    for r in raw:
        try:
            results.append(ForwardTestRecord(**r))
        except TypeError:
            log.debug("Forward test 기록 파싱 실패: %s", r.get("key", "?"))
    return results


def evaluate(
    record: ForwardTestRecord,
    actual_revenue: list[float],
) -> dict:
    """예측 vs 실적 비교 평가.

    Args:
        actual_revenue: 실제 매출 리스트 (원 단위, 연도순).

    Returns:
        evaluation dict: mae, mape, direction_accuracy, scenario_hit.
    """
    projected = record.projected
    n = min(len(projected), len(actual_revenue))
    if n == 0:
        return {"error": "비교할 데이터 없음"}

    # MAE, MAPE
    errors = []
    pct_errors = []
    direction_hits = 0
    for i in range(n):
        p, a = projected[i], actual_revenue[i]
        if a is None or a <= 0:
            continue
        err = abs(p - a)
        errors.append(err)
        pct_errors.append(err / a * 100)
        # 방향성: 이전 대비 증감 일치
        if i > 0 and actual_revenue[i - 1] and actual_revenue[i - 1] > 0:
            pred_dir = p > projected[i - 1] if i < len(projected) else True
            act_dir = a > actual_revenue[i - 1]
            if pred_dir == act_dir:
                direction_hits += 1

    mae = sum(errors) / len(errors) if errors else 0
    mape = sum(pct_errors) / len(pct_errors) if pct_errors else 0
    direction_accuracy = direction_hits / max(n - 1, 1) * 100

    # 시나리오 히트: 실적이 어느 시나리오 범위에 들어갔는지
    scenario_hit = _check_scenario_hit(record.scenarios, actual_revenue)

    result = {
        "mae": round(mae),
        "mape": round(mape, 2),
        "direction_accuracy": round(direction_accuracy, 1),
        "scenario_hit": scenario_hit,
        "n_compared": n,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    # 기록 업데이트
    record.actual = actual_revenue[:n]
    record.evaluation = result
    return result


def _check_scenario_hit(
    scenarios: dict[str, list[float]],
    actual: list[float],
) -> str:
    """실적이 어느 시나리오 범위에 있는지 판정."""
    if not scenarios or not actual:
        return "unknown"

    bull = scenarios.get("bull", [])
    bear = scenarios.get("bear", [])
    base = scenarios.get("base", [])

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


def _load_raw(filepath: Path) -> list[dict]:
    """JSON 파일에서 raw dict 리스트 로드."""
    if not filepath.exists():
        return []
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []
