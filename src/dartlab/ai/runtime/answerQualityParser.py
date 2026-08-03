"""답변 품질 게이트의 근거 메타데이터와 산문 파싱 도우미."""

from __future__ import annotations

import re
from typing import Any

_UNAVAILABLE_MARKERS = frozenset(
    {"", "-", "n/a", "na", "nan", "none", "null", "unknown", "unavailable", "미상", "미지정", "없음"}
)
_TARGET_KEYS = frozenset({"stockCode", "target", "code", "ticker", "corpCode", "companyName", "corpName", "targetName"})
_TARGET_LABEL_NOISE = frozenset(
    "값 결과 기업 대상 분기 사업보고서 실적 연도 재무제표 종목 질문 회사 answer company date document python result table".split()
)
_METRIC_SPECS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "operating_cash_flow",
        ("영업활동현금흐름", "영업현금흐름", "operating cash flow"),
        ("영업활동현금흐름", "영업현금흐름", "operating cash flow", "operatingcashflow"),
    ),
    (
        "free_cash_flow",
        ("잉여현금흐름", "free cash flow", "fcf"),
        ("잉여현금흐름", "free cash flow", "freecashflow", "fcf"),
    ),
    (
        "operating_margin",
        ("영업이익률", "영업마진", "operating margin"),
        ("영업이익률", "영업마진", "operating margin", "operatingmargin", "opm"),
    ),
    (
        "revenue_growth",
        ("매출성장률", "매출 성장률", "revenue growth", "sales growth"),
        ("매출성장률", "매출 성장률", "revenue growth", "sales growth", "salesgrowth", "revenuegrowth"),
    ),
    (
        "operating_profit",
        ("영업이익", "영업손익", "operating profit", "operating income"),
        ("영업이익", "영업손익", "operating profit", "operating income", "operatingprofit"),
    ),
    (
        "net_income",
        ("당기순이익", "순이익", "net income", "net profit"),
        ("당기순이익", "순이익", "net income", "net profit", "netincome", "netprofit"),
    ),
    (
        "revenue",
        ("매출액", "매출", "revenue", "sales"),
        ("매출액", "매출", "revenue", "sales"),
    ),
    (
        "total_assets",
        ("자산총계", "총자산", "total assets"),
        ("자산총계", "총자산", "total assets", "totalassets"),
    ),
    (
        "total_liabilities",
        ("부채총계", "총부채", "total liabilities"),
        ("부채총계", "총부채", "total liabilities", "totalliabilities"),
    ),
    (
        "total_equity",
        ("자본총계", "총자본", "total equity"),
        ("자본총계", "총자본", "total equity", "totalequity"),
    ),
    ("roe", ("roe", "자기자본이익률"), ("roe", "자기자본이익률")),
    ("eps", ("eps", "주당순이익"), ("eps", "주당순이익")),
    ("per", ("per", "주가수익비율"), ("per", "주가수익비율")),
    ("pbr", ("pbr", "주가순자산비율"), ("pbr", "주가순자산비율")),
)


def _metricId(ref: dict[str, Any]) -> str | None:
    """valueRef의 canonical metric ID를 반환하고 구형 ref는 alias로 보완한다."""
    payload = _payload(ref)
    canonical = payload.get("canonicalMetricId")
    if isinstance(canonical, str) and canonical.strip():
        return canonical.strip().casefold()
    semantic = " ".join(_refSemanticParts(ref))
    for name, _questionAliases, evidenceAliases in _METRIC_SPECS:
        if _matchesAnyAlias(semantic, evidenceAliases):
            return name
    return None


def _targetCodes(ref: dict[str, Any]) -> set[str]:
    return set(re.findall(r"(?<!\d)\d{6}(?!\d)", " ".join(_refSemanticParts(ref))))


def _targetLabels(ref: dict[str, Any]) -> set[str]:
    payload = _payload(ref)
    labels: set[str] = set()
    for key in _TARGET_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and not re.fullmatch(r"\d{6}", value.strip()):
            compact = _compactSemantic(value)
            if len(compact) >= 2:
                labels.add(compact)
    title = str(ref.get("title") or "").strip()
    titleHead = re.match(r"([A-Za-z가-힣][A-Za-z0-9가-힣&.]{1,40})(?=\s|\()", title)
    if titleHead:
        candidate = _compactSemantic(titleHead.group(1))
        if _isPlausibleTargetLabel(candidate):
            labels.add(candidate)
    return labels


def _questionTargetLabels(question: str) -> set[str]:
    """한국어 조사 앞의 명시적 회사명 후보를 추출하되 일반 재무 단어는 제외한다."""
    labels: set[str] = set()
    pattern = r"(?<![A-Za-z0-9가-힣])([A-Za-z가-힣][A-Za-z0-9가-힣&.]{1,40}?)(?:의|와|과|은|는|에서)"
    for match in re.finditer(pattern, question):
        candidate = _compactSemantic(match.group(1))
        if _isPlausibleTargetLabel(candidate):
            labels.add(candidate)
    return labels


def _isPlausibleTargetLabel(value: str) -> bool:
    if len(value) < 2 or value in _TARGET_LABEL_NOISE:
        return False
    metricAliases = tuple(
        alias for _name, questionAliases, _evidenceAliases in _METRIC_SPECS for alias in questionAliases
    )
    return not _matchesAnyAlias(value, metricAliases)


def _coversQuestionMetrics(question: str, cited: list[dict[str, Any]]) -> bool:
    """질문에 명시된 각 핵심 지표가 usable valueRef 하나 이상과 맞는지 확인한다."""
    requested = _requestedMetrics(question)
    if not requested:
        return True
    valueRefs = [ref for ref in cited if ref.get("kind") == "valueRef"]
    for name, aliases in requested:
        if not any(
            _metricId(ref) == name or _matchesAnyAlias(" ".join(_refSemanticParts(ref)), aliases) for ref in valueRefs
        ):
            return False
    return True


def _requestedMetrics(question: str) -> list[tuple[str, tuple[str, ...]]]:
    requested: list[tuple[int, str, tuple[str, ...]]] = []
    matchedSpecific: set[str] = set()
    for name, questionAliases, evidenceAliases in _METRIC_SPECS:
        if not _matchesAnyAlias(question, questionAliases):
            continue
        if name == "revenue" and "revenue_growth" in matchedSpecific:
            continue
        if name == "operating_profit" and "operating_margin" in matchedSpecific:
            continue
        requested.append((_firstAliasPosition(question, questionAliases), name, evidenceAliases))
        matchedSpecific.add(name)
    return [(name, aliases) for _position, name, aliases in sorted(requested)]


def _firstAliasPosition(value: str, aliases: tuple[str, ...]) -> int:
    """질문에 먼저 등장한 metric 순서를 안정적인 표 순서로 보존한다."""
    folded = value.casefold()
    positions = [folded.find(alias.casefold()) for alias in aliases]
    matched = [position for position in positions if position >= 0]
    return min(matched) if matched else len(folded)


def _matchesAnyAlias(value: str, aliases: tuple[str, ...]) -> bool:
    folded = value.casefold()
    compact = _compactSemantic(value)
    for alias in aliases:
        normalized = _compactSemantic(alias)
        if not normalized:
            continue
        if normalized.isascii() and len(normalized) <= 3:
            if re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", folded):
                return True
        elif normalized in compact:
            return True
    return False


def _refSemanticParts(ref: dict[str, Any]) -> list[str]:
    parts = [str(ref.get(key) or "") for key in ("id", "title", "source")]
    payload = _payload(ref)
    for key in ("canonicalMetricId", "metric", "key", "snakeId", "item", "label", "name"):
        value = payload.get(key)
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            parts.append(str(value))
    for key in _TARGET_KEYS:
        value = payload.get(key)
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            parts.append(str(value))
    return parts


def _compactSemantic(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", value.casefold())


def _questionPeriods(question: str) -> set[str]:
    periods: set[str] = set()
    for periodRange in re.finditer(r"(?<!\d)(20\d{2})\s*(?:-|~|부터)\s*(20\d{2})(?!\d)", question):
        start, end = (int(value) for value in periodRange.groups())
        if start <= end and end - start < 20:
            periods.update(str(year) for year in range(start, end + 1))
    for match in re.finditer(r"(?<!\d)(20\d{2})(?:\s*년)?(?:\s*(?:Q([1-4])|([1-4])\s*분기))?", question):
        year = match.group(1)
        quarter = match.group(2) or match.group(3)
        periods.add(f"{year}Q{quarter}" if quarter else year)
    return periods


def _evidencePeriods(cited: list[dict[str, Any]]) -> set[str]:
    periods: set[str] = set()
    for ref in cited:
        payload = _payload(ref)
        values: list[Any] = []
        for key in ("period", "periods", "basePeriod", "year"):
            value = payload.get(key)
            values.extend(value if isinstance(value, list) else [value])
        for value in values:
            if isinstance(value, int) and 1900 <= value <= 2200:
                periods.add(str(value))
            elif isinstance(value, str):
                parsed = _questionPeriods(value)
                periods.update(parsed)
                periods.update(period[:4] for period in parsed if re.fullmatch(r"20\d{2}Q[1-4]", period))
    return periods


def _payload(ref: dict[str, Any]) -> dict[str, Any]:
    value = ref.get("payload")
    return value if isinstance(value, dict) else {}


def _valueCandidates(value: str | int | float) -> set[str]:
    text = str(value).strip()
    candidates = {_compactNumberText(text)}
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return {candidate for candidate in candidates if candidate}
    if number.is_integer():
        integer = int(number)
        candidates.add(str(integer))
        candidates.add(f"{integer:,}".replace(",", ""))
    else:
        candidates.add(format(number, ".15g").replace(",", ""))
    return {candidate for candidate in candidates if candidate}


def _qualitativeValueBinds(prose: str, value: str) -> bool:
    """대표 판단 라벨의 구두점 차이와 제한적 서술 변형을 허용한다."""
    normalizedProse = _compactSemantic(prose)
    normalizedValue = _compactSemantic(value)
    if normalizedValue and normalizedValue in normalizedProse:
        return True
    tokens = [token for token in re.findall(r"[0-9a-z가-힣]+", value.casefold()) if len(token) >= 2]
    if len(tokens) < 3:
        return False
    required = max(2, (len(tokens) * 3 + 3) // 4)
    return sum(_compactSemantic(token) in normalizedProse for token in tokens) >= required


def _financialAmounts(prose: str) -> list[tuple[float, float]]:
    """한국 공시 답변의 원, 만, 억, 조 표기를 값과 표시 반올림 허용폭으로 바꾼다."""
    scales = {"만": 10_000.0, "억": 100_000_000.0, "조": 1_000_000_000_000.0}
    amounts: list[tuple[float, float]] = []

    def parse(numberText: str, scale: float) -> tuple[float, float]:
        """표시 숫자를 원 단위 값과 자릿수 기반 허용 오차로 변환한다."""
        number = float(numberText.replace(",", ""))
        decimals = len(numberText.rsplit(".", 1)[1]) if "." in numberText else 0
        tolerance = scale * 0.5 * (10**-decimals)
        return number * scale, max(tolerance, 1e-9)

    termPattern = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*(조|억|만)\s*원?")
    for match in termPattern.finditer(prose):
        amounts.append(parse(match.group(1), scales[match.group(2)]))

    compoundPattern = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*조\s*(\d[\d,]*(?:\.\d+)?)\s*억\s*원?")
    for match in compoundPattern.finditer(prose):
        major, _majorTolerance = parse(match.group(1), scales["조"])
        minor, minorTolerance = parse(match.group(2), scales["억"])
        amounts.append((major + minor, minorTolerance))

    rangePattern = re.compile(
        r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*(?:~|〜|\u2013|\u2014)\s*"
        r"(-?\d[\d,]*(?:\.\d+)?)\s*(조|억|만)?\s*원"
    )
    for match in rangePattern.finditer(prose):
        scale = scales.get(match.group(3) or "", 1.0)
        amounts.append(parse(match.group(1), scale))
        amounts.append(parse(match.group(2), scale))

    wonPattern = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*원")
    for match in wonPattern.finditer(prose):
        amounts.append(parse(match.group(1), 1.0))
    return amounts


def _dateCandidates(value: str) -> set[str]:
    compact = _compactText(value)
    candidates = {compact}
    fiscalYear = re.fullmatch(r"(\d{4})(?:fy|y)", compact)
    if fiscalYear:
        year = fiscalYear.group(1)
        candidates.update({_compactText(year), _compactText(f"{year}년"), _compactText(f"{year} 연간")})
    quarter = re.fullmatch(r"(\d{4})q([1-4])", compact)
    if quarter:
        year, number = quarter.groups()
        candidates.update({_compactText(f"{year}년 {number}분기"), _compactText(f"{year} {number}분기")})
    date = re.fullmatch(r"(\d{4})[-./]?(\d{1,2})[-./]?(\d{1,2})", value.strip())
    if date:
        year, month, day = date.groups()
        candidates.update(
            {
                _compactText(f"{year}-{int(month):02d}-{int(day):02d}"),
                _compactText(f"{year}.{int(month):02d}.{int(day):02d}"),
                _compactText(f"{year}년 {int(month)}월 {int(day)}일"),
            }
        )
    isoPrefix = re.match(r"(\d{4})-(\d{2})-(\d{2})", value.strip())
    if isoPrefix:
        year, month, day = isoPrefix.groups()
        candidates.update(
            {
                _compactText(f"{year}-{month}-{day}"),
                _compactText(f"{year}년 {int(month)}월 {int(day)}일"),
            }
        )
    return {candidate for candidate in candidates if candidate}


def _isConcreteScalar(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return value == value
    if not isinstance(value, str):
        return False
    return value.strip().casefold() not in _UNAVAILABLE_MARKERS


def _compactText(value: str) -> str:
    return re.sub(r"\s+", "", value.casefold())


def _compactNumberText(value: str) -> str:
    return re.sub(r"[\s,_]", "", value.casefold())
