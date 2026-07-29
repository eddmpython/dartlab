"""미매핑 계정 후보의 5 신호 평가.

`core/accounts/mappingLedger.py`가 누적한 관측을 그룹화한 뒤 각
``(accountId, accountNm)`` 후보의 자동 제안 가능성을 계산한다. 결과는
운영자 검토용 staging 데이터일 뿐이며 prod 매핑을 수정할 권한은 없다.

신호:
    S1 빈도: occurrenceCount 합이 5 이상.
    S2 회사 분산: 고유 stockCode가 3개 이상.
    S3 한글명: 표준 korName과 Levenshtein 유사도가 0.85 이상.
    S4 직접 매핑: accountId 또는 accountNm이 mappings에 1 hop으로 존재.
    S5 오타 거부: 표준 korName과 자모 1개 차이면 운영자 확인 대상으로 거부.

``SignalIndex``는 표준 계정명과 mappings의 비교 키를 한 번만 계산한다.
compactor는 그룹마다 3천여 표준계정을 다시 정규화하지 않고 같은 인덱스를
재사용한다.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection, Mapping
from dataclasses import dataclass

from dartlab.core.accounts.normalize import stripPrefix

MIN_FREQUENCY = 5
MIN_CORPORATE_DISPERSION = 3
KOR_MATCH_THRESHOLD = 0.85
TYPO_JAMO_DISTANCE = 1
SUFFIX_TAIL_CHARS = 3

_KOR_COMPARISON_RE = re.compile(r"[\s()\[\]/.,\-_]")


@dataclass(frozen=True)
class _KorCandidate:
    ordinal: int
    snakeId: str
    korName: str
    normalized: str
    tail: str
    jamo: str


@dataclass(frozen=True)
class SignalIndex:
    """한 compaction 실행 동안 재사용하는 불변 비교 인덱스."""

    candidatesByTail: Mapping[str, tuple[_KorCandidate, ...]]
    typoCandidatesByLength: Mapping[int, tuple[_KorCandidate, ...]]
    normalizedMappings: Mapping[str, str]
    snakeIds: frozenset[str]


@dataclass(frozen=True)
class SignalResult:
    """단일 ``(accountId, accountNm)`` 그룹의 5 신호 결과."""

    accountId: str
    accountNm: str
    occurrenceCount: int
    corporateDispersion: int
    s1Frequency: bool
    s2Dispersion: bool
    s3KorMatchScore: float
    s3KorMatchSnakeId: str | None
    s4IfrsSynonymSnakeId: str | None
    s4GhostSnakeId: str | None
    s5TypoSuspect: bool
    s5SuggestedFix: str | None
    autoEligible: bool
    suggestedSnakeId: str | None
    confidence: float

    def breakdown(self) -> dict[str, object]:
        """5 신호의 원시 결과를 JSON 직렬화 가능한 dict로 반환.

        Args:
            없음.

        Returns:
            각 신호의 bool, 점수, 후보 snakeId를 담은 dict.

        Example:
            >>> result.breakdown()["s1"]  # doctest: +SKIP
            True

        Raises:
            없음.
        """
        return {
            "s1": self.s1Frequency,
            "s2": self.s2Dispersion,
            "s3Score": self.s3KorMatchScore,
            "s3Snake": self.s3KorMatchSnakeId,
            "s4Snake": self.s4IfrsSynonymSnakeId,
            "s4GhostSnake": self.s4GhostSnakeId,
            "s5Typo": self.s5TypoSuspect,
            "s5Fix": self.s5SuggestedFix,
        }


def _normalizeKor(name: str) -> str:
    """한글명에서 비교 의미가 없는 구분 문자를 제거한다."""
    return _KOR_COMPARISON_RE.sub("", name or "")


def _boundedLevenshtein(a: str, b: str, maxDistance: int) -> int:
    """``maxDistance`` band 밖을 계산하지 않는 Levenshtein 거리."""
    if maxDistance < 0:
        raise ValueError("maxDistance must not be negative")
    if a == b:
        return 0
    if abs(len(a) - len(b)) > maxDistance:
        return maxDistance + 1
    if not a:
        return len(b) if len(b) <= maxDistance else maxDistance + 1
    if not b:
        return len(a) if len(a) <= maxDistance else maxDistance + 1

    limit = maxDistance + 1
    bLength = len(b)
    previous = [limit] * (bLength + 1)
    for column in range(min(bLength, maxDistance) + 1):
        previous[column] = column

    for row, aChar in enumerate(a, 1):
        current = [limit] * (bLength + 1)
        if row <= maxDistance:
            current[0] = row
        firstColumn = max(1, row - maxDistance)
        lastColumn = min(bLength, row + maxDistance)
        rowMinimum = limit
        for column in range(firstColumn, lastColumn + 1):
            substitutionCost = 0 if aChar == b[column - 1] else 1
            current[column] = min(
                current[column - 1] + 1,
                previous[column] + 1,
                previous[column - 1] + substitutionCost,
            )
            rowMinimum = min(rowMinimum, current[column])
        if rowMinimum > maxDistance:
            return limit
        previous = current

    distance = previous[bLength]
    return distance if distance <= maxDistance else limit


def _levenshtein(a: str, b: str) -> int:
    """제한 없는 Levenshtein 거리. 작은 독립 호출의 호환용."""
    return _boundedLevenshtein(a, b, max(len(a), len(b)))


def _jamoDistance(a: str, b: str) -> int:
    """NFD 자모 단위 Levenshtein 거리."""
    aJamo = unicodedata.normalize("NFD", a or "")
    bJamo = unicodedata.normalize("NFD", b or "")
    return _levenshtein(aJamo, bJamo)


def _normalizedMappingIndex(mappings: Mapping[str, str]) -> dict[str, str]:
    """구분 문자만 다른 mapping key를 모으되 충돌 키는 후보에서 제외한다."""
    normalized: dict[str, str] = {}
    ambiguous: set[str] = set()
    for key, snakeId in mappings.items():
        comparisonKey = _normalizeKor(key)
        if not comparisonKey or comparisonKey in ambiguous:
            continue
        existing = normalized.get(comparisonKey)
        if existing is not None and existing != snakeId:
            normalized.pop(comparisonKey, None)
            ambiguous.add(comparisonKey)
            continue
        normalized[comparisonKey] = snakeId
    return normalized


def buildSignalIndex(
    standardAccounts: Mapping[str, Mapping[str, object]],
    mappings: Mapping[str, str] | None = None,
) -> SignalIndex:
    """표준 계정과 직접 mapping의 반복 비교용 인덱스를 한 번 생성한다.

    Args:
        standardAccounts: snakeId별 korName metadata.
        mappings: accountId 또는 accountNm에서 snakeId로 가는 직접 mapping.

    Returns:
        한 compaction 실행에서 재사용할 ``SignalIndex``.

    Example:
        >>> buildSignalIndex({"total_assets": {"korName": "자산총계"}}).snakeIds
        frozenset({'total_assets'})

    Raises:
        TypeError: standardAccounts 또는 mappings의 schema가 잘못된 경우.
        ValueError: 표준 계정의 snakeId나 korName이 빈 문자열인 경우.
    """
    candidatesByTail: dict[str, list[_KorCandidate]] = {}
    typoCandidatesByLength: dict[int, list[_KorCandidate]] = {}
    for ordinal, (snakeId, meta) in enumerate(standardAccounts.items()):
        if not isinstance(snakeId, str) or not snakeId:
            raise ValueError("standardAccounts snakeId must be a non-empty string")
        if not isinstance(meta, Mapping):
            raise TypeError(f"standardAccounts[{snakeId!r}] must be a mapping")
        korName = meta.get("korName")
        if not isinstance(korName, str):
            raise TypeError(f"standardAccounts[{snakeId!r}].korName must be str")
        normalized = _normalizeKor(korName)
        if not normalized:
            raise ValueError(f"standardAccounts[{snakeId!r}].korName must not be empty")
        tail = normalized[-SUFFIX_TAIL_CHARS:]
        candidate = _KorCandidate(
            ordinal=ordinal,
            snakeId=snakeId,
            korName=korName,
            normalized=normalized,
            tail=tail,
            jamo=unicodedata.normalize("NFD", korName),
        )
        candidatesByTail.setdefault(tail, []).append(candidate)
        typoCandidatesByLength.setdefault(len(candidate.jamo), []).append(candidate)

    rawMappings = mappings or {}
    for key, value in rawMappings.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("mappings keys and values must be str")

    return SignalIndex(
        candidatesByTail={key: tuple(values) for key, values in candidatesByTail.items()},
        typoCandidatesByLength={key: tuple(values) for key, values in typoCandidatesByLength.items()},
        normalizedMappings=_normalizedMappingIndex(rawMappings),
        snakeIds=frozenset(standardAccounts),
    )


def signalFrequency(occurrenceCount: int) -> bool:
    """총 관측 횟수가 자동 제안 최소 빈도 이상인지 반환한다.

    Args:
        occurrenceCount: 그룹의 총 관측 횟수.

    Returns:
        5회 이상이면 True.

    Example:
        >>> signalFrequency(5)
        True

    Raises:
        없음.
    """
    return occurrenceCount >= MIN_FREQUENCY


def signalCorporateDispersion(stockCodes: Collection[str]) -> bool:
    """빈 코드를 제외한 고유 회사 수가 최소 분산 이상인지 반환한다.

    Args:
        stockCodes: 관측된 종목코드 collection.

    Returns:
        고유한 비어 있지 않은 종목코드가 3개 이상이면 True.

    Example:
        >>> signalCorporateDispersion({"005930", "000660", "035720"})
        True

    Raises:
        없음.
    """
    return len({code for code in stockCodes if code}) >= MIN_CORPORATE_DISPERSION


def signalKorNameMatch(
    accountNm: str,
    standardAccounts: Mapping[str, Mapping[str, object]],
    *,
    signalIndex: SignalIndex | None = None,
) -> tuple[str | None, float]:
    """동일 액션 접미를 가진 표준 korName 중 0.85 이상인 최적 후보를 반환한다.

    Args:
        accountNm: 비교할 미매핑 한글 계정명.
        standardAccounts: snakeId별 korName metadata.
        signalIndex: 같은 standardAccounts로 미리 만든 재사용 인덱스.

    Returns:
        임계치를 통과한 ``(snakeId, score)``. 없으면 ``(None, 0.0)``.

    Example:
        >>> sa = {"other_financial_assets": {"korName": "기타금융자산"}}
        >>> signalKorNameMatch("기타의금융자산", sa)[0]
        'other_financial_assets'

    Raises:
        TypeError: 인덱스를 새로 만들 때 standardAccounts schema가 잘못된 경우.
        ValueError: 인덱스를 새로 만들 때 필수 문자열이 비어 있는 경우.
    """
    if not accountNm or not standardAccounts:
        return None, 0.0
    index = signalIndex or buildSignalIndex(standardAccounts)
    needle = _normalizeKor(accountNm)
    if not needle:
        return None, 0.0
    needleTail = needle[-SUFFIX_TAIL_CHARS:]

    bestId: str | None = None
    bestScore = 0.0
    for candidate in index.candidatesByTail.get(needleTail, ()):
        maxLength = max(len(needle), len(candidate.normalized))
        maxDistance = int((1.0 - KOR_MATCH_THRESHOLD) * maxLength + 1e-12)
        distance = _boundedLevenshtein(needle, candidate.normalized, maxDistance)
        if distance > maxDistance:
            continue
        score = 1.0 - distance / maxLength
        if score > bestScore:
            bestScore = score
            bestId = candidate.snakeId
    return bestId, bestScore


def signalIfrsSynonym(
    accountId: str,
    accountNm: str,
    mappings: Mapping[str, str],
    *,
    normalizedMappings: Mapping[str, str] | None = None,
) -> str | None:
    """accountId 또는 accountNm의 모호하지 않은 1 hop mapping을 반환한다.

    Args:
        accountId: DART XBRL account_id.
        accountNm: DART 한글 계정명.
        mappings: 직접 mapping 사전.
        normalizedMappings: 구분 문자를 제거해 미리 만든 mapping index.

    Returns:
        직접 연결된 snakeId. 매칭이 없거나 정규화 충돌이면 None.

    Example:
        >>> signalIfrsSynonym("", "자산 총계", {"자산총계": "total_assets"})
        'total_assets'

    Raises:
        없음.
    """
    if not mappings:
        return None
    if accountId and accountId in mappings:
        return mappings[accountId]
    strippedId = stripPrefix(accountId) if accountId else ""
    if strippedId and strippedId in mappings:
        return mappings[strippedId]
    if accountNm and accountNm in mappings:
        return mappings[accountNm]
    normalizedName = _normalizeKor(accountNm)
    if not normalizedName:
        return None
    normalizedIndex = normalizedMappings or _normalizedMappingIndex(mappings)
    return normalizedIndex.get(normalizedName)


def signalTypoReject(
    accountNm: str,
    standardAccounts: Mapping[str, Mapping[str, object]],
    *,
    signalIndex: SignalIndex | None = None,
) -> tuple[bool, str | None]:
    """표준 korName과 자모 하나 차이인 후보를 오타 의심으로 반환한다.

    Args:
        accountNm: 검사할 한글 계정명.
        standardAccounts: snakeId별 korName metadata.
        signalIndex: 같은 standardAccounts로 미리 만든 재사용 인덱스.

    Returns:
        ``(오타 의심 여부, 표준 korName 제안)``.

    Example:
        >>> sa = {"controlling": {"korName": "지배기업소유주지분"}}
        >>> signalTypoReject("지배지업소유주지분", sa)
        (True, '지배기업소유주지분')

    Raises:
        TypeError: 인덱스를 새로 만들 때 standardAccounts schema가 잘못된 경우.
        ValueError: 인덱스를 새로 만들 때 필수 문자열이 비어 있는 경우.
    """
    if not accountNm or not standardAccounts:
        return False, None
    index = signalIndex or buildSignalIndex(standardAccounts)
    needleJamo = unicodedata.normalize("NFD", accountNm)
    bestCandidate: _KorCandidate | None = None
    for length in range(
        len(needleJamo) - TYPO_JAMO_DISTANCE,
        len(needleJamo) + TYPO_JAMO_DISTANCE + 1,
    ):
        for candidate in index.typoCandidatesByLength.get(length, ()):
            if candidate.korName == accountNm:
                continue
            distance = _boundedLevenshtein(needleJamo, candidate.jamo, TYPO_JAMO_DISTANCE)
            if 0 < distance <= TYPO_JAMO_DISTANCE:
                if bestCandidate is None or candidate.ordinal < bestCandidate.ordinal:
                    bestCandidate = candidate
    if bestCandidate is None:
        return False, None
    return True, bestCandidate.korName


def evaluate(
    accountId: str,
    accountNm: str,
    occurrenceCount: int,
    stockCodes: Collection[str],
    standardAccounts: Mapping[str, Mapping[str, object]],
    mappings: Mapping[str, str],
    *,
    signalIndex: SignalIndex | None = None,
) -> SignalResult:
    """단일 그룹에 5 신호를 적용하고 ghost mapping을 hard reject한다.

    Args:
        accountId: DART XBRL account_id.
        accountNm: DART 한글 계정명.
        occurrenceCount: 그룹의 총 관측 횟수.
        stockCodes: 그룹이 관측된 고유 또는 중복 종목코드.
        standardAccounts: snakeId별 korName metadata.
        mappings: 직접 mapping 사전.
        signalIndex: 동일 SSOT로 미리 만든 재사용 인덱스.

    Returns:
        5개 신호, 제안 snakeId, confidence를 담은 ``SignalResult``.

    Example:
        >>> sa = {"total_assets": {"korName": "자산총계"}}
        >>> result = evaluate("", "자산총계", 5, {"005930", "000660", "035720"},
        ...                   sa, {"자산총계": "total_assets"})
        >>> result.autoEligible
        True

    Raises:
        TypeError: 인덱스를 새로 만들 때 입력 mapping schema가 잘못된 경우.
        ValueError: 인덱스를 새로 만들 때 필수 문자열이 비어 있는 경우.
    """
    index = signalIndex or buildSignalIndex(standardAccounts, mappings)
    s1 = signalFrequency(occurrenceCount)
    s2 = signalCorporateDispersion(stockCodes)
    rawS4Snake = signalIfrsSynonym(
        accountId,
        accountNm,
        mappings,
        normalizedMappings=index.normalizedMappings,
    )
    s4Snake = rawS4Snake if rawS4Snake in index.snakeIds else None
    s4GhostSnake = rawS4Snake if rawS4Snake is not None and s4Snake is None else None
    s3Snake, s3Score = signalKorNameMatch(accountNm, standardAccounts, signalIndex=index)
    s5Reject, s5Fix = signalTypoReject(accountNm, standardAccounts, signalIndex=index)

    suggested = s4Snake or s3Snake
    hasValidMatch = s4Snake is not None or s3Snake is not None
    autoEligible = bool(s1 and s2 and hasValidMatch and not s5Reject)
    confidence = 1.0 if s4Snake is not None else s3Score

    return SignalResult(
        accountId=accountId,
        accountNm=accountNm,
        occurrenceCount=occurrenceCount,
        corporateDispersion=len({code for code in stockCodes if code}),
        s1Frequency=s1,
        s2Dispersion=s2,
        s3KorMatchScore=s3Score,
        s3KorMatchSnakeId=s3Snake,
        s4IfrsSynonymSnakeId=s4Snake,
        s4GhostSnakeId=s4GhostSnake,
        s5TypoSuspect=s5Reject,
        s5SuggestedFix=s5Fix,
        autoEligible=autoEligible,
        suggestedSnakeId=suggested,
        confidence=confidence,
    )
