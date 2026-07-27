"""공개 분석 렌즈의 공통 제품 계약.

각 L2 엔진은 고유한 기존 결과 키와 의미를 유지한다. 대표 축만 기존 결과에
``product`` 블록을 additive 하게 붙이고, Story, Ask, Terminal 같은 소비자는
이 블록을 공통 진입점으로 사용한다.

이 모듈은 계산하거나 결론을 만들지 않는다. 타입과 구조, 시간 경계, 기존
결과와의 최소 정합성만 검증한다. 엔진별 의미를 공통 helper 안에 숨기지 않는
것이 핵심 규율이다.
"""

from __future__ import annotations

import hashlib
import re
from calendar import monthrange
from datetime import date, datetime
from typing import Any, Literal, NotRequired, TypedDict

LensEngine = Literal["analysis", "credit", "industry", "quant", "macro"]
LensStatus = Literal["usable", "partial", "blocked", "notApplicable"]
ConfidenceLevel = Literal["high", "medium", "low", "blocked", "unknown"]
LensClaimDirection = Literal["supportive", "neutral", "adverse", "unknown"]
LensClaimStatus = Literal["observed", "derived", "estimated", "missing", "blocked"]

_ENGINES = frozenset({"analysis", "credit", "industry", "quant", "macro"})
_STATUSES = frozenset({"usable", "partial", "blocked", "notApplicable"})
_CONFIDENCE_LEVELS = frozenset({"high", "medium", "low", "blocked", "unknown"})
_GAP_STATUSES = frozenset({"missing", "partial", "blocked", "stale", "unsupported", "notApplicable"})
_EVIDENCE_STATUSES = frozenset({"observed", "derived", "estimated", "missing", "blocked"})
_CLAIM_DIRECTIONS = frozenset({"supportive", "neutral", "adverse", "unknown"})
_CLAIM_STATUSES = frozenset({"observed", "derived", "estimated", "missing", "blocked"})
_ACTIVE_EVIDENCE_STATUSES = frozenset({"observed", "derived", "estimated"})
_TENSION_PATTERNS = (
    "fundamentalPriceDivergence",
    "earningsCashDivergence",
    "growthCreditTradeoff",
    "industryExecutionCounterforce",
    "macroCompanyCounterforce",
)
_TENSION_KINDS = {
    "fundamentalPriceDivergence": "divergence",
    "earningsCashDivergence": "divergence",
    "growthCreditTradeoff": "tradeoff",
    "industryExecutionCounterforce": "counterforce",
    "macroCompanyCounterforce": "counterforce",
}


class LensIdentity(TypedDict):
    """대표 렌즈 결과의 안정된 식별 정보."""

    target: str
    market: str
    engine: LensEngine
    axis: str
    version: str


class LensTime(TypedDict):
    """결정시점과 데이터시점 경계."""

    asOf: str | None
    dataAsOf: str | dict[str, Any] | None
    period: str | None
    knowledgeBoundary: str | None


class LensConclusion(TypedDict):
    """사용자가 첫 화면에서 읽는 대표 판단."""

    label: str
    summary: str


class LensConfidence(TypedDict):
    """대표 판단의 근거 충족도와 산출 방법. 예측 성공 확률이 아니다."""

    level: ConfidenceLevel
    score: float | None
    method: str


class LensEvidence(TypedDict, total=False):
    """대표 판단이 가리키는 관측 또는 계산 근거."""

    id: str
    kind: str
    sourceRef: str
    status: Literal["observed", "derived", "estimated", "missing", "blocked"]
    observedAt: str | None
    detail: str


class LensGap(TypedDict, total=False):
    """결손, 차단, 신선도 위험을 숨기지 않는 항목."""

    id: str
    status: Literal["missing", "partial", "blocked", "stale", "unsupported", "notApplicable"]
    reason: str
    sourceRef: str


class LensClaim(TypedDict, total=False):
    """Story가 문구 추론 없이 비교할 수 있는 렌즈의 타입화된 주장."""

    id: str
    label: str
    comparisonKey: str
    basis: str
    direction: LensClaimDirection
    horizon: str
    asOf: str
    dataAsOf: str | dict[str, Any] | None
    period: str | None
    status: LensClaimStatus
    sourceRef: str
    evidenceRefs: list[str]
    falsifierRefs: list[str]
    value: Any
    unit: str
    relation: str


class LensProduct(TypedDict):
    """다섯 공개 렌즈가 공유하는 제품 결과 문법 v1."""

    schemaVersion: int
    identity: LensIdentity
    time: LensTime
    status: LensStatus
    conclusion: LensConclusion
    confidence: LensConfidence
    drivers: list[dict[str, Any]]
    claims: NotRequired[list[LensClaim]]
    evidence: list[LensEvidence]
    assumptions: list[dict[str, Any]]
    gaps: list[LensGap]
    scenarios: list[dict[str, Any]]
    falsifiers: list[dict[str, Any]]
    payload: dict[str, Any]


_REQUIRED_KEYS = frozenset(
    {
        "schemaVersion",
        "identity",
        "time",
        "status",
        "conclusion",
        "confidence",
        "drivers",
        "evidence",
        "assumptions",
        "gaps",
        "scenarios",
        "falsifiers",
        "payload",
    }
)
_LIST_KEYS = ("drivers", "evidence", "assumptions", "gaps", "scenarios", "falsifiers")
_CLAIM_REQUIRED_KEYS = (
    "id",
    "label",
    "comparisonKey",
    "basis",
    "direction",
    "horizon",
    "asOf",
    "dataAsOf",
    "period",
    "status",
    "sourceRef",
    "evidenceRefs",
    "falsifierRefs",
)


def validateLensProduct(product: dict[str, Any], *, legacy: dict[str, Any] | None = None) -> None:
    """렌즈 ``product`` 블록 v1을 엄격하게 검증한다.

    Args:
        product: 대표 축이 만든 공통 제품 블록.
        legacy: ``product``를 붙일 기존 결과 dict. 지정하면 target, market,
            asOf와 payload block 참조가 기존 결과와 충돌하지 않는지 확인한다.

    Returns:
        없음. 유효하지 않으면 예외를 발생시킨다.

    Raises:
        TypeError: dict, list 또는 scalar 타입이 계약과 다를 때.
        ValueError: 필수 키, 상태, 시간 경계 또는 기존 결과 정합성이 깨질 때.

    Example:
        >>> validateLensProduct(result["product"], legacy=result)
    """
    if not isinstance(product, dict):
        raise TypeError("lens product 는 dict 여야 합니다.")

    missing = _REQUIRED_KEYS - set(product)
    if missing:
        raise ValueError(f"lens product 필수 키 누락: {sorted(missing)}")
    if product.get("schemaVersion") != 1:
        raise ValueError("lens product schemaVersion 은 1 이어야 합니다.")

    identity = _requireDict(product, "identity")
    _requireNonEmptyStrings(identity, ("target", "market", "engine", "axis", "version"), "identity")
    if identity["engine"] not in _ENGINES:
        raise ValueError(f"지원하지 않는 lens engine: {identity['engine']!r}")

    time = _requireDict(product, "time")
    for key in ("asOf", "dataAsOf", "period", "knowledgeBoundary"):
        if key not in time:
            raise ValueError(f"lens product time.{key} 누락")
    _validateTime(time)

    status = product.get("status")
    if status not in _STATUSES:
        raise ValueError(f"지원하지 않는 lens status: {status!r}")

    conclusion = _requireDict(product, "conclusion")
    _requireNonEmptyStrings(conclusion, ("label", "summary"), "conclusion")

    confidence = _requireDict(product, "confidence")
    _requireNonEmptyStrings(confidence, ("level", "method"), "confidence")
    if confidence["level"] not in _CONFIDENCE_LEVELS:
        raise ValueError(f"지원하지 않는 confidence level: {confidence['level']!r}")
    score = confidence.get("score")
    if score is not None:
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError("lens product confidence.score 는 숫자 또는 None 이어야 합니다.")
        if not 0 <= float(score) <= 100:
            raise ValueError("lens product confidence.score 는 0 이상 100 이하여야 합니다.")

    for key in _LIST_KEYS:
        value = product.get(key)
        if not isinstance(value, list):
            raise TypeError(f"lens product {key} 는 list 여야 합니다.")
        if any(not isinstance(row, dict) for row in value):
            raise TypeError(f"lens product {key} 항목은 모두 dict 여야 합니다.")

    payload = product.get("payload")
    if not isinstance(payload, dict):
        raise TypeError("lens product payload 는 dict 여야 합니다.")

    _validateEvidence(product["evidence"])
    _validateGaps(product["gaps"])
    _validateClaims(product)
    if status == "usable" and not product["evidence"]:
        raise ValueError("usable lens product 는 evidence 가 1개 이상이어야 합니다.")
    if status in {"partial", "blocked", "notApplicable"} and not product["gaps"]:
        raise ValueError(f"{status} lens product 는 gaps 가 1개 이상이어야 합니다.")

    if legacy is not None:
        _validateLegacyConsistency(product, legacy)


def _requireDict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise TypeError(f"lens product {key} 는 dict 여야 합니다.")
    return value


def _requireNonEmptyStrings(parent: dict[str, Any], keys: tuple[str, ...], path: str) -> None:
    for key in keys:
        value = parent.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"lens product {path}.{key} 는 비어 있지 않은 문자열이어야 합니다.")


def _validateTime(time: dict[str, Any]) -> None:
    for key in ("asOf", "period", "knowledgeBoundary"):
        value = time.get(key)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"lens product time.{key} 는 문자열 또는 None 이어야 합니다.")
    dataAsOf = time.get("dataAsOf")
    if dataAsOf is not None and not isinstance(dataAsOf, (str, dict)):
        raise TypeError("lens product time.dataAsOf 는 문자열, dict 또는 None 이어야 합니다.")

    asOf = _isoDate(time.get("asOf"), path="time.asOf")
    knowledgeBoundary = _isoDate(time.get("knowledgeBoundary"), path="time.knowledgeBoundary")
    if asOf is not None and knowledgeBoundary is not None and asOf > knowledgeBoundary:
        raise ValueError("lens product asOf 는 knowledgeBoundary 이후일 수 없습니다.")
    dataDates = _dataAsOfDates(dataAsOf)
    if knowledgeBoundary is not None and any(value > knowledgeBoundary for value in dataDates):
        raise ValueError("lens product dataAsOf 는 knowledgeBoundary 이후일 수 없습니다.")


def _isoDate(value: Any, *, path: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError(f"lens product {path} 는 YYYY-MM-DD 형식이어야 합니다.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"lens product {path} 는 유효한 YYYY-MM-DD 날짜여야 합니다.") from exc


def _temporalUpperBound(value: str) -> date | None:
    """날짜와 회계 기간 표기를 비교 가능한 마지막 날짜로 정규화한다."""
    normalized = value.strip().upper()
    if not normalized:
        return None

    isoMatch = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2})(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?", normalized
    )
    if isoMatch:
        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    compactDate = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", normalized)
    if compactDate:
        try:
            return date(*(int(part) for part in compactDate.groups()))
        except ValueError:
            return None

    quarter = re.fullmatch(r"(\d{4})\s*[-./ ]?\s*Q([1-4])", normalized)
    if quarter is None:
        quarter = re.fullmatch(r"(\d{4})년\s*([1-4])분기", normalized)
    if quarter:
        year, quarterNumber = (int(part) for part in quarter.groups())
        month = quarterNumber * 3
        return date(year, month, monthrange(year, month)[1])

    half = re.fullmatch(r"(\d{4})\s*[-./ ]?\s*H([12])", normalized)
    if half:
        year, halfNumber = (int(part) for part in half.groups())
        month = halfNumber * 6
        return date(year, month, monthrange(year, month)[1])

    monthMatch = re.fullmatch(r"(\d{4})[-./](\d{1,2})", normalized)
    if monthMatch is None:
        monthMatch = re.fullmatch(r"(\d{4})(\d{2})", normalized)
    if monthMatch:
        year, month = (int(part) for part in monthMatch.groups())
        if 1 <= month <= 12:
            return date(year, month, monthrange(year, month)[1])
        return None

    yearMatch = re.fullmatch(r"(?:FY)?(\d{4})(?:FY)?", normalized)
    if yearMatch:
        return date(int(yearMatch.group(1)), 12, 31)
    return None


# 값이 "언제 알았나"(시점)를 뜻하는 키. 그 시점이 knowledge boundary 뒤면 look-ahead 다.
_INSTANT_KEYS = frozenset(
    {"date", "dataasof", "observedat", "retrievedat", "sourcedataasof", "marketasof", "financialasof"}
)

# 값이 "어디까지 담았나"(범위)를 뜻하는 키. 회계 기간 표기가 들어온다.
#
# 범위는 시점처럼 다루면 안 된다. `latestPeriod: "2026"` 을 2026-12-31 로 읽으면, 2026 년
# 7 월에 2026 년 반기까지 받은 지극히 정상적인 결과가 "미래 자료를 봤다"로 걸린다. 실제로
# `Company.analysis("종합평가")` 가 그 이유로 통째로 죽고 있었다.
#
# 범위에서 look-ahead 는 그 기간이 *시작하기도 전*에 담았다고 할 때 생긴다. 그래서 끝이
# 아니라 시작으로 잰다. `latestPeriod: "2027"` 은 2027-01-01 이 경계보다 뒤라 그대로 걸린다.
_COVERAGE_KEYS = frozenset({"latestperiod"})


def _temporalLowerBound(value: str) -> date | None:
    """기간 표기를 그 기간이 시작하는 날로 정규화한다. 날짜는 그대로 둔다.

    범위형 값의 look-ahead 판정에 쓴다. 기간이 경계보다 늦게 시작했으면 그 자료는 아직
    존재할 수 없다. 반대로 이미 시작한 기간을 부분적으로 담는 것은 정상이라 걸리면 안 된다.
    """
    upper = _temporalUpperBound(value)
    if upper is None:
        return None
    normalized = value.strip().upper()
    if re.fullmatch(r"(?:FY)?(\d{4})(?:FY)?", normalized):
        return date(upper.year, 1, 1)
    if re.fullmatch(r"(\d{4})\s*[-./ ]?\s*Q[1-4]", normalized) or re.fullmatch(r"(\d{4})년\s*[1-4]분기", normalized):
        return date(upper.year, upper.month - 2, 1)
    if re.fullmatch(r"(\d{4})\s*[-./ ]?\s*H[12]", normalized):
        return date(upper.year, upper.month - 5, 1)
    if re.fullmatch(r"(\d{4})[-./](\d{1,2})", normalized) or re.fullmatch(r"(\d{4})(\d{2})", normalized):
        return date(upper.year, upper.month, 1)
    return upper


def _dataAsOfDates(value: Any) -> list[date]:
    if isinstance(value, str):
        parsed = _temporalUpperBound(value)
        if parsed is None:
            raise ValueError("lens product dataAsOf 시간 형식을 해석할 수 없습니다.")
        return [parsed]
    if not isinstance(value, dict):
        return []
    dates: list[date] = []
    temporalKeys = _INSTANT_KEYS | _COVERAGE_KEYS
    foundTemporalValue = False
    for key, raw in value.items():
        if str(key).lower() not in temporalKeys or raw is None or raw == "":
            continue
        foundTemporalValue = True
        if not isinstance(raw, str):
            raise ValueError(f"lens product dataAsOf.{key} 는 문자열이어야 합니다.")
        isCoverage = str(key).lower() in _COVERAGE_KEYS
        parsed = _temporalLowerBound(raw) if isCoverage else _temporalUpperBound(raw)
        if parsed is None:
            raise ValueError(f"lens product dataAsOf.{key} 시간 형식을 해석할 수 없습니다.")
        dates.append(parsed)
    if value and not foundTemporalValue:
        raise ValueError("lens product dataAsOf dict에 해석 가능한 시간 필드가 없습니다.")
    return dates


def _validateEvidence(rows: list[dict[str, Any]]) -> None:
    for index, row in enumerate(rows):
        _requireNonEmptyStrings(row, ("id", "kind", "sourceRef", "status"), f"evidence[{index}]")
        if row["status"] not in _EVIDENCE_STATUSES:
            raise ValueError(f"지원하지 않는 evidence status: {row['status']!r}")


def _validateGaps(rows: list[dict[str, Any]]) -> None:
    for index, row in enumerate(rows):
        _requireNonEmptyStrings(row, ("id", "status", "reason"), f"gaps[{index}]")
        if row["status"] not in _GAP_STATUSES:
            raise ValueError(f"지원하지 않는 gap status: {row['status']!r}")


def _validateClaims(product: dict[str, Any]) -> None:
    claims = product.get("claims")
    if claims is None:
        return
    if not isinstance(claims, list):
        raise TypeError("lens product claims 는 list 여야 합니다.")
    if any(not isinstance(row, dict) for row in claims):
        raise TypeError("lens product claims 항목은 모두 dict 여야 합니다.")

    evidenceById = {str(row["id"]): row for row in product["evidence"] if row.get("id")}
    falsifierIds = {str(row["id"]) for row in product["falsifiers"] if row.get("id")}
    productTime = product["time"]
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        missing = [key for key in _CLAIM_REQUIRED_KEYS if key not in claim]
        if missing:
            raise ValueError(f"lens product claims[{index}] 필수 키 누락: {missing}")
        _requireNonEmptyStrings(
            claim,
            ("id", "label", "comparisonKey", "basis", "direction", "horizon", "asOf", "status", "sourceRef"),
            f"claims[{index}]",
        )
        claimId = str(claim["id"])
        if claimId in seen:
            raise ValueError(f"lens product claim id 중복: {claimId}")
        seen.add(claimId)
        if claim["direction"] not in _CLAIM_DIRECTIONS:
            raise ValueError(f"지원하지 않는 claim direction: {claim['direction']!r}")
        if claim["status"] not in _CLAIM_STATUSES:
            raise ValueError(f"지원하지 않는 claim status: {claim['status']!r}")
        if claim["asOf"] != productTime.get("asOf"):
            raise ValueError("lens product claim asOf 는 product time.asOf 와 같아야 합니다.")
        if claim["period"] is not None and not isinstance(claim["period"], str):
            raise TypeError("lens product claim period 는 문자열 또는 None 이어야 합니다.")
        if claim["dataAsOf"] is not None and not isinstance(claim["dataAsOf"], (str, dict)):
            raise TypeError("lens product claim dataAsOf 는 문자열, dict 또는 None 이어야 합니다.")
        knowledgeBoundary = _isoDate(productTime.get("knowledgeBoundary"), path="time.knowledgeBoundary")
        claimDataDates = _dataAsOfDates(claim["dataAsOf"])
        if knowledgeBoundary is not None and any(value > knowledgeBoundary for value in claimDataDates):
            raise ValueError("lens product claim dataAsOf 는 knowledgeBoundary 이후일 수 없습니다.")
        _validateClaimRefs(
            claim,
            index=index,
            evidenceById=evidenceById,
            falsifierIds=falsifierIds,
        )


def _validateClaimRefs(
    claim: dict[str, Any],
    *,
    index: int,
    evidenceById: dict[str, dict[str, Any]],
    falsifierIds: set[str],
) -> None:
    evidenceRefs = claim["evidenceRefs"]
    falsifierRefs = claim["falsifierRefs"]
    if not isinstance(evidenceRefs, list) or any(not isinstance(ref, str) or not ref for ref in evidenceRefs):
        raise TypeError(f"lens product claims[{index}].evidenceRefs 는 문자열 list 여야 합니다.")
    if not isinstance(falsifierRefs, list) or any(not isinstance(ref, str) or not ref for ref in falsifierRefs):
        raise TypeError(f"lens product claims[{index}].falsifierRefs 는 문자열 list 여야 합니다.")
    if claim["status"] in {"observed", "derived", "estimated"} and not evidenceRefs:
        raise ValueError(f"lens product claims[{index}] 활성 claim은 evidenceRefs가 필요합니다.")
    if claim["status"] in {"observed", "derived", "estimated"} and not falsifierRefs:
        raise ValueError(f"lens product claims[{index}] 활성 claim은 falsifierRefs가 필요합니다.")
    missingEvidence = sorted(set(evidenceRefs) - set(evidenceById))
    if missingEvidence:
        raise ValueError(f"lens product claims[{index}] evidenceRefs가 evidence에 없음: {missingEvidence}")
    missingFalsifiers = sorted(set(falsifierRefs) - falsifierIds)
    if missingFalsifiers:
        raise ValueError(f"lens product claims[{index}] falsifierRefs가 falsifiers에 없음: {missingFalsifiers}")
    referencedEvidence = [evidenceById[ref] for ref in evidenceRefs]
    if claim["status"] in {"observed", "derived", "estimated"} and any(
        row.get("status") not in _ACTIVE_EVIDENCE_STATUSES for row in referencedEvidence
    ):
        raise ValueError(f"lens product claims[{index}] 활성 claim은 활성 evidence만 참조해야 합니다.")
    referencedSources = {str(row.get("sourceRef")) for row in referencedEvidence if row.get("sourceRef")}
    if claim["sourceRef"] not in referencedSources:
        raise ValueError(
            f"lens product claims[{index}].sourceRef가 evidenceRefs의 직접 근거와 연결되지 않음: {claim['sourceRef']}"
        )


def validatePublicLensBundle(bundle: dict[str, Any]) -> None:
    """브라우저와 API로 나가는 공개 Lens bundle 전체를 런타임 검증한다."""
    if not isinstance(bundle, dict):
        raise TypeError("public lens bundle은 dict여야 합니다.")
    required = {
        "schemaVersion",
        "target",
        "market",
        "engines",
        "products",
        "tensions",
        "statusCounts",
        "gaps",
        "noComposite",
    }
    missing = required - set(bundle)
    if missing:
        raise ValueError(f"public lens bundle 필수 키 누락: {sorted(missing)}")
    if "results" in bundle:
        raise ValueError("공개 lens bundle에 내부 results가 포함될 수 없습니다.")
    if bundle.get("schemaVersion") != 1 or bundle.get("noComposite") is not True:
        raise ValueError("public lens bundle은 schemaVersion=1, noComposite=true여야 합니다.")

    target = bundle.get("target")
    market = bundle.get("market")
    if not isinstance(target, str) or not target.strip():
        raise ValueError("public lens bundle target은 비어 있지 않은 문자열이어야 합니다.")
    if not isinstance(market, str) or not market.strip():
        raise ValueError("public lens bundle market은 비어 있지 않은 문자열이어야 합니다.")

    engines = bundle.get("engines")
    if not isinstance(engines, list) or any(engine not in _ENGINES for engine in engines):
        raise ValueError("public lens bundle engines가 지원 목록과 다릅니다.")
    if len(engines) != len(set(engines)):
        raise ValueError("public lens bundle engines는 중복될 수 없습니다.")

    products = bundle.get("products")
    if not isinstance(products, dict):
        raise TypeError("public lens bundle products는 dict여야 합니다.")
    if set(products) - set(engines):
        raise ValueError("public lens bundle products의 engine이 요청 목록 밖에 있습니다.")
    for engine, product in products.items():
        validateLensProduct(product)
        identity = product["identity"]
        if identity["engine"] != engine:
            raise ValueError("public lens product의 key와 identity.engine이 다릅니다.")
        if identity["target"] != target or identity["market"].upper() != market.upper():
            raise ValueError("public lens product의 target 또는 market이 bundle과 다릅니다.")

    statusCounts = bundle.get("statusCounts")
    if not isinstance(statusCounts, dict):
        raise TypeError("public lens bundle statusCounts는 dict여야 합니다.")
    expectedCounts: dict[str, int] = {}
    for product in products.values():
        status = str(product["status"])
        expectedCounts[status] = expectedCounts.get(status, 0) + 1
    if statusCounts != expectedCounts:
        raise ValueError("public lens bundle statusCounts가 products와 다릅니다.")

    gaps = bundle.get("gaps")
    if not isinstance(gaps, list) or any(not isinstance(row, dict) for row in gaps):
        raise TypeError("public lens bundle gaps는 dict 항목의 list여야 합니다.")
    for index, row in enumerate(gaps):
        _requireNonEmptyStrings(row, ("engine", "status", "reason"), f"bundle.gaps[{index}]")
        if row["engine"] not in _ENGINES:
            raise ValueError(f"지원하지 않는 bundle gap engine: {row['engine']!r}")

    _validateTensionBundle(bundle["tensions"], products=products, target=target)


def _validateTensionBundle(tensions: Any, *, products: dict[str, Any], target: str) -> None:
    if not isinstance(tensions, dict):
        raise TypeError("public lens tensions는 dict여야 합니다.")
    if tensions.get("schemaVersion") != 1 or tensions.get("noComposite") is not True:
        raise ValueError("public lens tensions는 schemaVersion=1, noComposite=true여야 합니다.")
    items = tensions.get("items")
    evaluations = tensions.get("evaluations")
    if not isinstance(items, list) or any(not isinstance(row, dict) for row in items):
        raise TypeError("public lens tension items는 dict 항목의 list여야 합니다.")
    if not isinstance(evaluations, list) or any(not isinstance(row, dict) for row in evaluations):
        raise TypeError("public lens tension evaluations는 dict 항목의 list여야 합니다.")

    evaluationByPattern: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(evaluations):
        _requireNonEmptyStrings(row, ("patternId", "status", "reason"), f"tensions.evaluations[{index}]")
        patternId = row["patternId"]
        if patternId not in _TENSION_PATTERNS or patternId in evaluationByPattern:
            raise ValueError(f"잘못되거나 중복된 tension patternId: {patternId!r}")
        if row["status"] not in {"active", "clear", "blocked"}:
            raise ValueError(f"지원하지 않는 tension evaluation status: {row['status']!r}")
        evaluationByPattern[patternId] = row
    if tuple(evaluationByPattern) != _TENSION_PATTERNS:
        raise ValueError("public lens tension evaluations는 고정된 다섯 규칙 순서를 모두 포함해야 합니다.")

    seenIds: set[str] = set()
    activePatterns: set[str] = set()
    for index, item in enumerate(items):
        _validateTensionItem(item, index=index, products=products, target=target)
        itemId = str(item["id"])
        patternId = str(item["patternId"])
        if itemId in seenIds or patternId in activePatterns:
            raise ValueError("public lens tension item id 또는 patternId가 중복됩니다.")
        seenIds.add(itemId)
        activePatterns.add(patternId)
    expectedActive = {key for key, row in evaluationByPattern.items() if row["status"] == "active"}
    if activePatterns != expectedActive:
        raise ValueError("public lens tension active items와 evaluations가 다릅니다.")


def _validateTensionItem(
    item: dict[str, Any],
    *,
    index: int,
    products: dict[str, Any],
    target: str,
) -> None:
    required = {
        "schemaVersion",
        "id",
        "target",
        "patternId",
        "kind",
        "status",
        "asOf",
        "headline",
        "mechanism",
        "question",
        "sides",
        "falsifiers",
        "gaps",
        "algorithmVersion",
        "noComposite",
    }
    missing = required - set(item)
    if missing:
        raise ValueError(f"public lens tension items[{index}] 필수 키 누락: {sorted(missing)}")
    _requireNonEmptyStrings(
        item,
        ("id", "target", "patternId", "kind", "status", "asOf", "algorithmVersion"),
        f"tensions.items[{index}]",
    )
    if item["schemaVersion"] != 1 or item["noComposite"] is not True or item["status"] != "active":
        raise ValueError("active tension item의 버전, 상태 또는 noComposite가 잘못되었습니다.")
    if item["target"] != target or item["patternId"] not in _TENSION_PATTERNS:
        raise ValueError("active tension item의 target 또는 patternId가 bundle과 다릅니다.")
    if item["kind"] != _TENSION_KINDS[item["patternId"]]:
        raise ValueError("active tension item kind가 patternId와 다릅니다.")
    for key in ("headline", "mechanism", "question"):
        localized = item[key]
        if not isinstance(localized, dict):
            raise TypeError(f"active tension item {key}는 dict여야 합니다.")
        _requireNonEmptyStrings(localized, ("kr", "en"), f"tensions.items[{index}].{key}")

    sides = item["sides"]
    if not isinstance(sides, list) or len(sides) != 2 or any(not isinstance(side, dict) for side in sides):
        raise ValueError("active tension item은 정확히 두 side를 가져야 합니다.")
    for sideIndex, side in enumerate(sides):
        _validateTensionSide(side, index=sideIndex, item=item, products=products)
    claimKeys = sorted(f"{side['engine']}:{side['claimId']}" for side in sides)
    identity = "|".join([target, item["patternId"], *claimKeys])
    expectedId = f"{item['patternId']}:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:12]}"
    if item["id"] != expectedId:
        raise ValueError("active tension item id가 안정 ID 규칙과 다릅니다.")

    falsifiers = item["falsifiers"]
    if not isinstance(falsifiers, list) or not falsifiers or any(not isinstance(row, dict) for row in falsifiers):
        raise ValueError("active tension item은 falsifier를 1개 이상 가져야 합니다.")
    for rowIndex, row in enumerate(falsifiers):
        _requireNonEmptyStrings(row, ("id", "condition"), f"tensions.items[{index}].falsifiers[{rowIndex}]")
        engine, separator, sourceId = str(row["id"]).partition(".")
        product = products.get(engine) if separator else None
        source = next(
            (
                candidate
                for candidate in (product or {}).get("falsifiers", [])
                if isinstance(candidate, dict) and str(candidate.get("id")) == sourceId
            ),
            None,
        )
        if source is None or str(source.get("condition")) != row["condition"]:
            raise ValueError("active tension falsifier가 원본 product와 연결되지 않습니다.")
        for key in ("sourceRef", "driverRef"):
            if key in row and str(source.get(key)) != row[key]:
                raise ValueError(f"active tension falsifier.{key}가 원본 product와 다릅니다.")

    gaps = item["gaps"]
    if not isinstance(gaps, list) or any(not isinstance(row, dict) for row in gaps):
        raise TypeError("active tension item gaps는 dict 항목의 list여야 합니다.")
    for rowIndex, row in enumerate(gaps):
        _requireNonEmptyStrings(row, ("id", "status", "reason"), f"tensions.items[{index}].gaps[{rowIndex}]")
        engine, separator, sourceId = str(row["id"]).partition(".")
        product = products.get(engine) if separator else None
        source = next(
            (
                candidate
                for candidate in (product or {}).get("gaps", [])
                if isinstance(candidate, dict) and str(candidate.get("id") or "gap") == sourceId
            ),
            None,
        )
        if source is None or str(source.get("status")) != row["status"] or str(source.get("reason")) != row["reason"]:
            raise ValueError("active tension gap이 원본 product와 연결되지 않습니다.")
        if "sourceRef" in row and str(source.get("sourceRef")) != row["sourceRef"]:
            raise ValueError("active tension gap.sourceRef가 원본 product와 다릅니다.")


def _validateTensionSide(
    side: dict[str, Any],
    *,
    index: int,
    item: dict[str, Any],
    products: dict[str, Any],
) -> None:
    required = (
        "engine",
        "claimId",
        "label",
        "comparisonKey",
        "basis",
        "direction",
        "horizon",
        "asOf",
        "dataAsOf",
        "period",
        "status",
        "sourceRef",
        "evidenceRefs",
    )
    missing = [key for key in required if key not in side]
    if missing:
        raise ValueError(f"active tension side[{index}] 필수 키 누락: {missing}")
    _requireNonEmptyStrings(
        side,
        ("engine", "claimId", "label", "comparisonKey", "basis", "direction", "horizon", "asOf", "status", "sourceRef"),
        f"tension.side[{index}]",
    )
    engine = side["engine"]
    product = products.get(engine)
    if not isinstance(product, dict):
        raise ValueError(f"active tension side engine의 product가 없음: {engine!r}")
    claims = product.get("claims")
    claim = next(
        (row for row in claims or [] if isinstance(row, dict) and row.get("id") == side["claimId"]),
        None,
    )
    if claim is None:
        raise ValueError("active tension side claim이 원본 product에 없습니다.")
    for key in required:
        if key == "engine":
            continue
        claimKey = "id" if key == "claimId" else key
        if key == "evidenceRefs":
            if set(side[key]) != set(claim[claimKey]):
                raise ValueError("active tension side.evidenceRefs가 원본 claim과 다릅니다.")
            continue
        if side[key] != claim[claimKey]:
            raise ValueError(f"active tension side.{key}가 원본 claim과 다릅니다.")
    if side["asOf"] != item["asOf"]:
        raise ValueError("active tension side.asOf가 item.asOf와 다릅니다.")


def _validateLegacyConsistency(product: dict[str, Any], legacy: dict[str, Any]) -> None:
    if not isinstance(legacy, dict):
        raise TypeError("legacy lens result 는 dict 여야 합니다.")
    identity = product["identity"]
    time = product["time"]

    legacyTarget = legacy.get("target") or legacy.get("stockCode")
    if legacyTarget is not None and str(legacyTarget) != identity["target"]:
        raise ValueError("lens product identity.target 과 기존 결과 target 이 다릅니다.")
    legacyMarket = legacy.get("market")
    if legacyMarket is not None and str(legacyMarket).upper() != identity["market"].upper():
        raise ValueError("lens product identity.market 과 기존 결과 market 이 다릅니다.")
    legacyAsOf = legacy.get("asOf")
    if legacyAsOf is not None and time["asOf"] is not None and str(legacyAsOf) != time["asOf"]:
        raise ValueError("lens product time.asOf 와 기존 결과 asOf 가 다릅니다.")

    blockRefs = product["payload"].get("blockRefs")
    if blockRefs is not None:
        if not isinstance(blockRefs, list) or any(not isinstance(ref, str) or not ref for ref in blockRefs):
            raise TypeError("lens product payload.blockRefs 는 비어 있지 않은 문자열 list 여야 합니다.")
        missingRefs = [ref for ref in blockRefs if ref not in legacy]
        if missingRefs:
            raise ValueError(f"lens product payload.blockRefs 가 기존 결과에 없음: {missingRefs}")


__all__ = [
    "ConfidenceLevel",
    "LensConclusion",
    "LensClaim",
    "LensClaimDirection",
    "LensClaimStatus",
    "LensConfidence",
    "LensEngine",
    "LensEvidence",
    "LensGap",
    "LensIdentity",
    "LensProduct",
    "LensStatus",
    "LensTime",
    "validatePublicLensBundle",
    "validateLensProduct",
]
