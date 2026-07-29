"""추출 개념 카탈로그의 불변 타입과 provider 대칭 직렬화 계약."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict

CATEGORIES: tuple[str, ...] = (
    "financialStatement",
    "note",
    "governance",
    "capital",
    "workforce",
    "debt",
    "segment",
    "narrative",
    "filingMeta",
)
AXIS_TYPES: tuple[str, ...] = ("single", "multiAxis", "movement", "text")
VALUE_TYPES: tuple[str, ...] = ("amount", "rate", "text")
_DART_SURFACES = frozenset({"note", "report", "statement", "narrative", "segmentTable"})
_EDGAR_SURFACES = frozenset({"xbrlTag", "deraFacts", "proxy", "item", "statement"})


@dataclass(frozen=True)
class DartSource:
    """DART 추출 표면 참조."""

    surface: str
    key: str

    def __post_init__(self) -> None:
        """잘못된 DART surface와 빈 key를 import 시점에 거부한다."""
        if self.surface not in _DART_SURFACES:
            raise ValueError(f"미등록 DART surface: {self.surface!r}")
        if not self.key.strip():
            raise ValueError("DartSource.key는 비어 있을 수 없습니다")


@dataclass(frozen=True)
class EdgarSource:
    """EDGAR 추출 표면 참조."""

    surface: str
    keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """잘못된 EDGAR surface와 빈 tag/item key를 import 시점에 거부한다."""
        if self.surface not in _EDGAR_SURFACES:
            raise ValueError(f"미등록 EDGAR surface: {self.surface!r}")
        if not self.keys or any(not key.strip() for key in self.keys):
            raise ValueError(f"{self.surface}: EDGAR source key는 비어 있을 수 없습니다")


@dataclass(frozen=True)
class HonestNull:
    """원천에 구조적으로 없는 provider 능력과 그 사유."""

    reason: str

    def __post_init__(self) -> None:
        """빈 사유로 구조적 부재를 가장하지 못하게 한다."""
        if not self.reason.strip():
            raise ValueError("HonestNull.reason은 비어 있을 수 없습니다")


ProviderSource = DartSource | EdgarSource | HonestNull | None


class ProviderSourceDict(TypedDict):
    """provider source JSON projection."""

    surface: str
    key: NotRequired[str]
    keys: NotRequired[list[str]]
    reason: NotRequired[str]


class ExtractionConceptDict(TypedDict):
    """ExtractionConcept JSON projection."""

    conceptId: str
    category: str
    label: str
    axisType: str
    valueType: str
    registered: bool
    narrativeAnchor: list[str] | None
    parity: str
    dart: ProviderSourceDict | None
    edgar: ProviderSourceDict | None


def _sourceToDict(source: ProviderSource) -> ProviderSourceDict | None:
    """provider source를 손실 없는 JSON-compatible projection으로 바꾼다."""
    if isinstance(source, DartSource):
        return {"surface": source.surface, "key": source.key}
    if isinstance(source, EdgarSource):
        return {"surface": source.surface, "keys": list(source.keys)}
    if isinstance(source, HonestNull):
        return {"surface": "honestNull", "reason": source.reason}
    return None


@dataclass(frozen=True)
class ExtractionConcept:
    """DART·EDGAR 추출 가능 개념의 불변 manifest 행."""

    conceptId: str
    category: str
    label: str
    dart: DartSource | HonestNull | None
    edgar: EdgarSource | HonestNull | None
    axisType: str = "single"
    valueType: str = "amount"
    narrativeAnchor: tuple[str, str] | None = None
    registered: bool = False

    def __post_init__(self) -> None:
        """manifest 오타와 잘못된 provider source를 import 시점에 거부한다."""
        if not self.conceptId.strip():
            raise ValueError("ExtractionConcept.conceptId는 비어 있을 수 없습니다")
        if not self.label.strip():
            raise ValueError(f"{self.conceptId}: label은 비어 있을 수 없습니다")
        if self.category not in CATEGORIES:
            raise ValueError(f"{self.conceptId}: 미등록 category {self.category!r}")
        if self.axisType not in AXIS_TYPES:
            raise ValueError(f"{self.conceptId}: 미등록 axisType {self.axisType!r}")
        if self.valueType not in VALUE_TYPES:
            raise ValueError(f"{self.conceptId}: 미등록 valueType {self.valueType!r}")
        if not isinstance(self.dart, (DartSource, HonestNull, type(None))):
            raise TypeError(f"{self.conceptId}: 잘못된 DART source {type(self.dart).__name__}")
        if not isinstance(self.edgar, (EdgarSource, HonestNull, type(None))):
            raise TypeError(f"{self.conceptId}: 잘못된 EDGAR source {type(self.edgar).__name__}")
        if self.registered and self.category != "note":
            raise ValueError(f"{self.conceptId}: registered는 note concept에만 허용됩니다")
        if self.narrativeAnchor is not None and self.category != "narrative":
            raise ValueError(f"{self.conceptId}: narrativeAnchor는 narrative concept에만 허용됩니다")

    def parity(self) -> str:
        """이 개념의 provider parity 상태를 반환한다.

        Capabilities:
            DART와 EDGAR의 실제 source 보유 여부를 4상태로 분류한다.

        AIContext:
            provider coverage를 과장하지 않고 설명하는 근거로 사용한다.

        Guide:
            HonestNull과 None은 추출 가능 source로 계산하지 않는다.

        When:
            concept별 provider 지원 범위를 집계하거나 직렬화할 때 호출한다.

        How:
            두 provider 필드가 각각 DartSource와 EdgarSource인지 판별한다.

        Returns:
            both, dartOnly, edgarOnly, none 중 하나.

        Requires:
            외부 의존성 없음. 현재 불변 concept 값만 사용한다.

        Raises:
            없음.

        Example:
            >>> concept.parity()
            'both'

        SeeAlso:
            ExtractionConcept.toDict
        """
        hasDart = isinstance(self.dart, DartSource)
        hasEdgar = isinstance(self.edgar, EdgarSource)
        if hasDart and hasEdgar:
            return "both"
        if hasDart:
            return "dartOnly"
        if hasEdgar:
            return "edgarOnly"
        return "none"

    def toDict(self) -> ExtractionConceptDict:
        """두 provider의 source 또는 HonestNull 사유를 보존해 직렬화한다.

        Returns:
            provider 대칭 구조와 parity를 포함한 새 typed dict.

        Requires:
            외부 의존성 없음. 현재 불변 concept 값만 사용한다.

        Raises:
            없음.

        Example:
            >>> concept.toDict()["conceptId"]
            'note.tax'
        """
        return {
            "conceptId": self.conceptId,
            "category": self.category,
            "label": self.label,
            "axisType": self.axisType,
            "valueType": self.valueType,
            "registered": self.registered,
            "narrativeAnchor": list(self.narrativeAnchor) if self.narrativeAnchor else None,
            "parity": self.parity(),
            "dart": _sourceToDict(self.dart),
            "edgar": _sourceToDict(self.edgar),
        }


__all__ = [
    "AXIS_TYPES",
    "CATEGORIES",
    "VALUE_TYPES",
    "DartSource",
    "EdgarSource",
    "ExtractionConcept",
    "HonestNull",
]
