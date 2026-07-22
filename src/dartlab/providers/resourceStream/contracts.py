"""Pageable provider resource의 immutable contracts와 strict JSON identity."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, cast

IntegrityMode = Literal["full", "footerFast"]
PredicateOperator = Literal["eq", "ne", "gt", "ge", "lt", "le", "isin"]


def _strictJsonValue(value: object, path: str = "$") -> object:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"strict JSON은 non-finite float를 허용하지 않습니다: {path}")
        return value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _strictJsonValue(getattr(value, field.name), f"{path}.{field.name}")
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        normalized = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"strict JSON mapping key는 str이어야 합니다: {path}")
            normalized[key] = _strictJsonValue(item, f"{path}.{key}")
        return normalized
    if isinstance(value, (tuple, list)):
        return [_strictJsonValue(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise TypeError(f"strict JSON으로 직렬화할 수 없는 값입니다: {path} ({type(value).__name__})")


def canonicalJsonBytes(value: object) -> bytes:
    """값을 strict canonical JSON bytes로 변환한다.

    Capabilities:
        dataclass, string-key mapping, finite scalar, tuple과 list만 허용해 identity hash를 만든다.
        ``default=str`` 같은 암묵적 타입 손실은 사용하지 않는다.

    Args:
        value: strict JSON-compatible value.

    Returns:
        UTF-8 canonical JSON bytes.

    Raises:
        TypeError: 지원하지 않는 타입 또는 non-string mapping key일 때.
        ValueError: NaN 또는 infinity일 때.

    Example:
        ``canonicalJsonBytes({"b": 2, "a": 1})``.

    Guide:
        source pin, query pin, cache manifest integrity에 같은 함수를 사용한다.

    SeeAlso:
        ResourceReadRequest.queryPin.

    Requires:
        날짜와 decimal은 호출자가 명시적 string 또는 number로 정규화한다.

    AIContext:
        query identity에서 Python repr 또는 locale-dependent string 변환을 차단한다.

    LLM Specifications:
        AntiPatterns:
            - json.dumps(default=str)로 알 수 없는 타입을 숨김
            - NaN을 JSON number로 hash
        Freshness:
            입력 값에만 의존하는 deterministic encoding이다.
    """
    normalized = _strictJsonValue(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ResourcePredicate:
    """DuckDB reader로 pushdown할 strict typed predicate다.

    Capabilities:
        eq, ne, gt, ge, lt, le, isin만 허용하고 value의 strict JSON 가능성을 즉시 검증한다.

    Args:
        column: parquet column 이름.
        operator: predicate operator.
        value: strict JSON scalar, collection 또는 mapping.

    Returns:
        immutable predicate.

    Raises:
        ValueError: column 또는 operator가 유효하지 않을 때.
        TypeError: value가 strict JSON으로 표현되지 않을 때.

    Example:
        ``ResourcePredicate("fy", "ge", 2024)``.

    Guide:
        date는 ISO string으로 명시하고 Python object를 암묵 변환하지 않는다.

    SeeAlso:
        ResourceReadRequest.

    Requires:
        isin value는 tuple이어야 한다.

    AIContext:
        외부 Mapping query가 임의 SQL string 없이 filter를 표현하게 한다.

    LLM Specifications:
        AntiPatterns:
            - Python lambda filter
            - SQL fragment를 value로 실행
        Freshness:
            query value에만 의존한다.
    """

    column: str
    operator: PredicateOperator
    value: object

    def __post_init__(self) -> None:
        if not isinstance(self.column, str) or not isinstance(self.operator, str):
            raise TypeError("predicate column과 operator는 str이어야 합니다")
        column = self.column.strip()
        if not column:
            raise ValueError("predicate column이 비었습니다")
        if self.operator not in {"eq", "ne", "gt", "ge", "lt", "le", "isin"}:
            raise ValueError("predicate operator가 유효하지 않습니다")
        if self.operator == "isin" and not isinstance(self.value, tuple):
            raise ValueError("isin value는 tuple이어야 합니다")
        _strictJsonValue(self.value, "$.predicate.value")
        object.__setattr__(self, "column", column)

    def toMapping(self) -> dict[str, object]:
        """Predicate를 strict JSON-compatible mapping으로 반환한다.

        Requires:
            value가 construction 시 검증된 strict JSON 값이어야 한다.

        Raises:
            TypeError: value가 지원하지 않는 타입으로 훼손됐을 때.

        Example:
            ``ResourcePredicate("fy", "ge", 2024).toMapping()``.
        """
        return {"column": self.column, "operator": self.operator, "value": _strictJsonValue(self.value)}

    @classmethod
    def fromMapping(cls, value: Mapping[str, object]) -> ResourcePredicate:
        """동형 Mapping에서 predicate를 만든다.

        Capabilities:
            JSON에서 복원된 isin list를 immutable tuple로 정규화한다.

        AIContext:
            외부 Data Workbench query body를 SQL fragment 없이 typed predicate로 바꾼다.

        Guide:
            column, operator, value 세 key를 가진 mapping을 전달한다.

        When:
            process 또는 HTTP 경계를 지난 request를 복원할 때 호출한다.

        How:
            operator별 value를 정규화한 뒤 constructor validation을 재사용한다.

        Requires:
            column과 operator key가 존재해야 한다.

        Raises:
            KeyError: 필수 key가 없을 때.
            ValueError: operator 또는 value shape이 유효하지 않을 때.
            TypeError: value가 strict JSON 타입이 아닐 때.

        Example:
            ``ResourcePredicate.fromMapping({"column": "fy", "operator": "ge", "value": 2024})``.

        SeeAlso:
            ResourceReadRequest.fromMapping.
        """
        column = value["column"]
        operator = value["operator"]
        if not isinstance(column, str) or not isinstance(operator, str):
            raise TypeError("predicate column과 operator는 str이어야 합니다")
        predicateValue = value.get("value")
        if operator == "isin" and isinstance(predicateValue, list):
            predicateValue = tuple(predicateValue)
        return cls(column, cast(PredicateOperator, operator), predicateValue)


@dataclass(frozen=True, slots=True)
class ResourceReadRequest:
    """Provider resource projection, filter, paging과 budget 계약이다.

    Capabilities:
        Mapping 입력, deterministic query pin, pinned startRow resume, raw content opt-in을 제공한다.

    Args:
        columns: storage projection column.
        predicates: AND predicate tuple.
        companyIds: 비면 manifest 전체, 있으면 선택 shard.
        batchRows: RecordBatch row 상한.
        maxRows: page 전체 row 상한.
        maxBytes: page 전체 Arrow logical byte 상한.
        includeSourcePath: root 상대 sourcePath 포함 여부.
        startRow: filter와 projection 뒤 logical result offset.
        expectedSourcePin: resume이 결박된 full source pin.
        expectedQueryPin: resume이 결박된 query pin.
        allowRawContent: contentRaw 명시 opt-in.

    Returns:
        immutable read request.

    Raises:
        ValueError: 예산, startRow 또는 resume pin이 유효하지 않을 때.

    Example:
        ``ResourceReadRequest(("cik", "tag", "val"), maxRows=10000)``.

    Guide:
        다음 page는 이전 receipt의 nextRow, sourcePin, queryPin을 그대로 전달한다.

    SeeAlso:
        ResourceReadReceipt, ResourceManifest.

    Requires:
        startRow가 0보다 크면 두 expected pin이 모두 필요하다.

    AIContext:
        lower owner가 Mapping으로 받아 Data Workbench에 Arrow batch를 공급할 수 있는 경계다.

    LLM Specifications:
        AntiPatterns:
            - pin 없는 offset resume
            - contentRaw를 전시장 기본 projection에 포함
        Freshness:
            queryPin은 projection, predicates, companyIds, sourcePath, raw opt-in에 고정된다.
        OutputSchema:
            - startRow : int, logical resume offset
            - expectedSourcePin : str, full payload source identity
            - expectedQueryPin : str, query semantics identity
    """

    columns: tuple[str, ...]
    predicates: tuple[ResourcePredicate, ...] = ()
    companyIds: tuple[str, ...] = ()
    batchRows: int = 4_096
    maxRows: int = 50_000
    maxBytes: int = 16 * 1024 * 1024
    includeSourcePath: bool = True
    startRow: int = 0
    expectedSourcePin: str | None = None
    expectedQueryPin: str | None = None
    allowRawContent: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.columns, (tuple, list)) or any(not isinstance(column, str) for column in self.columns):
            raise TypeError("columns는 str sequence여야 합니다")
        columns = tuple(column.strip() for column in self.columns)
        if not columns or any(not column for column in columns):
            raise ValueError("columns가 비었습니다")
        if len(columns) != len(set(columns)):
            raise ValueError("columns는 고유해야 합니다")
        if not isinstance(self.predicates, (tuple, list)) or any(
            not isinstance(predicate, ResourcePredicate) for predicate in self.predicates
        ):
            raise TypeError("predicates는 ResourcePredicate sequence여야 합니다")
        predicates = tuple(self.predicates)
        if not isinstance(self.companyIds, (tuple, list)) or any(
            not isinstance(companyId, str) for companyId in self.companyIds
        ):
            raise TypeError("companyIds는 str sequence여야 합니다")
        companyIds = tuple(sorted({companyId.strip() for companyId in self.companyIds if companyId.strip()}))
        for name in ("batchRows", "maxRows", "maxBytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name}는 int여야 합니다")
            if value <= 0:
                raise ValueError(f"{name}는 양수여야 합니다")
        if isinstance(self.startRow, bool) or not isinstance(self.startRow, int):
            raise TypeError("startRow는 int여야 합니다")
        if self.startRow < 0:
            raise ValueError("startRow는 0 이상이어야 합니다")
        for name in ("expectedSourcePin", "expectedQueryPin"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{name}은 str 또는 None이어야 합니다")
        if not isinstance(self.includeSourcePath, bool) or not isinstance(self.allowRawContent, bool):
            raise TypeError("includeSourcePath와 allowRawContent는 bool이어야 합니다")
        if self.startRow > 0 and (not self.expectedSourcePin or not self.expectedQueryPin):
            raise ValueError("resume startRow에는 expectedSourcePin과 expectedQueryPin이 필요합니다")
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "predicates", predicates)
        object.__setattr__(self, "companyIds", companyIds)

    def queryPin(self, resourceId: str) -> str:
        """Paging budget과 offset을 제외한 query semantics pin을 반환한다.

        Requires:
            resourceId가 caller의 stable catalog identity여야 한다.

        Raises:
            TypeError: predicate value가 strict JSON identity를 만들 수 없을 때.

        Example:
            ``request.queryPin("resource.edgar")``.
        """
        payload = {
            "resourceId": resourceId,
            "columns": self.columns,
            "predicates": [predicate.toMapping() for predicate in self.predicates],
            "companyIds": self.companyIds,
            "includeSourcePath": self.includeSourcePath,
            "allowRawContent": self.allowRawContent,
        }
        return f"resource-query:{hashlib.sha256(canonicalJsonBytes(payload)).hexdigest()}"

    def toMapping(self) -> dict[str, object]:
        """Request를 외부 process용 strict JSON-compatible mapping으로 반환한다.

        Requires:
            request가 constructor validation을 통과한 immutable instance여야 한다.

        Raises:
            TypeError: predicate value가 strict JSON 타입이 아닐 때.

        Example:
            ``request.toMapping()``.
        """
        return {
            "columns": list(self.columns),
            "predicates": [predicate.toMapping() for predicate in self.predicates],
            "companyIds": list(self.companyIds),
            "batchRows": self.batchRows,
            "maxRows": self.maxRows,
            "maxBytes": self.maxBytes,
            "includeSourcePath": self.includeSourcePath,
            "startRow": self.startRow,
            "expectedSourcePin": self.expectedSourcePin,
            "expectedQueryPin": self.expectedQueryPin,
            "allowRawContent": self.allowRawContent,
        }

    def toBytes(self) -> bytes:
        """Request를 strict canonical JSON bytes로 반환한다.

        Requires:
            모든 predicate value가 strict JSON-compatible이어야 한다.

        Raises:
            TypeError: 지원하지 않는 value 타입이 있을 때.

        Example:
            ``request.toBytes()``.
        """
        return canonicalJsonBytes(self.toMapping())

    @classmethod
    def fromMapping(cls, value: Mapping[str, object]) -> ResourceReadRequest:
        """외부 process의 동형 Mapping에서 request를 만든다.

        Capabilities:
            projection, typed predicates, paging budgets와 continuation pin을 복원한다.

        AIContext:
            JSON body를 provider-owned request로 바꾸는 lower owner adapter 경계다.

        Guide:
            canonical ``toMapping`` 출력 또는 동형 JSON mapping을 전달한다.

        When:
            외부 process가 Data Workbench resource reader를 호출할 때 사용한다.

        How:
            predicate mapping을 먼저 복원한 뒤 constructor가 나머지 invariant를 검증한다.

        Requires:
            columns가 sequence이고 predicates가 sequence여야 한다.

        Raises:
            TypeError: predicate collection 또는 item shape이 유효하지 않을 때.
            ValueError: budget이나 continuation contract가 유효하지 않을 때.

        Example:
            ``ResourceReadRequest.fromMapping({"columns": ["cik", "val"]})``.

        SeeAlso:
            ResourcePredicate.fromMapping, ResourceReadRequest.toMapping.
        """
        predicateValues = value.get("predicates", ())
        if not isinstance(predicateValues, (tuple, list)):
            raise TypeError("predicates는 sequence여야 합니다")
        predicatesList = []
        for item in predicateValues:
            if isinstance(item, ResourcePredicate):
                predicatesList.append(item)
            elif isinstance(item, Mapping):
                predicatesList.append(ResourcePredicate.fromMapping(item))
            else:
                raise TypeError("predicate item은 ResourcePredicate 또는 Mapping이어야 합니다")
        predicates = tuple(predicatesList)
        columns = value.get("columns", ())
        companyIds = value.get("companyIds", ())
        if not isinstance(columns, (tuple, list)):
            raise TypeError("columns는 sequence여야 합니다")
        if not isinstance(companyIds, (tuple, list)):
            raise TypeError("companyIds는 sequence여야 합니다")
        return cls(
            columns=tuple(cast(str, item) for item in columns),
            predicates=predicates,
            companyIds=tuple(cast(str, item) for item in companyIds),
            batchRows=cast(int, value.get("batchRows", 4_096)),
            maxRows=cast(int, value.get("maxRows", 50_000)),
            maxBytes=cast(int, value.get("maxBytes", 16 * 1024 * 1024)),
            includeSourcePath=cast(bool, value.get("includeSourcePath", True)),
            startRow=cast(int, value.get("startRow", 0)),
            expectedSourcePin=cast(str | None, value.get("expectedSourcePin")),
            expectedQueryPin=cast(str | None, value.get("expectedQueryPin")),
            allowRawContent=cast(bool, value.get("allowRawContent", False)),
        )


@dataclass(frozen=True, slots=True)
class ResourceShard:
    """Manifest가 고정한 company parquet shard identity다."""

    companyId: str
    relativePath: str
    byteSize: int
    mtimeNs: int
    integrityDigest: str

    def toMapping(self) -> dict[str, object]:
        """Shard identity를 strict JSON mapping으로 반환한다.

        Requires:
            shard가 manifest builder에서 생성된 immutable instance여야 한다.

        Raises:
            None.

        Example:
            ``shard.toMapping()``.
        """
        return dataclasses.asdict(self)


@dataclass(frozen=True, slots=True)
class ResourceManifest:
    """Provider resource payload와 cache validation 상태를 결박한다.

    Capabilities:
        full-file SHA-256 source pin, benchmark-only footer pin, schema와 shard identity를 보존한다.

    Args:
        resourceId: catalog resource ID.
        rootPath: local execution root. public mapping에는 노출하지 않는다.
        shards: sorted company shard tuple.
        schemaFields: Arrow schema name과 type.
        commonSchemaFields: 모든 shard에 같은 type으로 존재하는 fast-path fields.
        totalBytes: payload byte 합계.
        integrityMode: full 또는 footerFast.
        sourcePin: manifest source identity.
        cacheHit: persistent cache 재사용 여부.
        cacheValidation: cache hit 검증 수준의 정확한 이름.

    Returns:
        immutable manifest.

    Example:
        ``manifest.sourcePin``.

    Guide:
        continuation은 full manifest만 사용하고 동일 manifest instance를 page 사이에 재사용한다.

    SeeAlso:
        dartlab.providers.resourceStream.manifest.loadResourceManifest.

    Requires:
        cache hit은 file set, size, mtimeNs, cache document SHA-256이 모두 같아야 한다.

    AIContext:
        size와 mtime을 보존한 payload 변조는 cache hit에서 재검출하지 못한다. 강한 재검증은 cache bypass다.

    LLM Specifications:
        AntiPatterns:
            - footerFast를 payload integrity라고 표현
            - size와 mtime cache validation을 full rehash와 동일시
        Freshness:
            sourcePin 생성 시 payload 또는 footer bytes에 고정된다.
        OutputSchema:
            - sourcePin : str, source identity
            - cacheValidation : str, cache freshness contract
    """

    resourceId: str
    rootPath: str
    shards: tuple[ResourceShard, ...]
    schemaFields: tuple[tuple[str, str], ...]
    totalBytes: int
    integrityMode: IntegrityMode
    sourcePin: str
    commonSchemaFields: tuple[tuple[str, str], ...] = ()
    cacheHit: bool = False
    cacheValidation: str = "fileSet+size+mtimeNs+cacheDocumentSha256"

    def toMapping(self) -> dict[str, object]:
        """Absolute root를 제외한 manifest를 strict JSON-compatible mapping으로 반환한다.

        Requires:
            manifest가 loadResourceManifest에서 생성됐어야 한다.

        Raises:
            None.

        Example:
            ``manifest.toMapping()``.
        """
        return {
            "resourceId": self.resourceId,
            "shards": [shard.toMapping() for shard in self.shards],
            "schemaFields": [list(field) for field in self.schemaFields],
            "commonSchemaFields": [list(field) for field in self.commonSchemaFields],
            "totalBytes": self.totalBytes,
            "integrityMode": self.integrityMode,
            "sourcePin": self.sourcePin,
            "cacheHit": self.cacheHit,
            "cacheValidation": self.cacheValidation,
        }

    def toBytes(self) -> bytes:
        """Manifest를 strict canonical JSON bytes로 반환한다.

        Requires:
            shard와 schema identity가 strict JSON-compatible이어야 한다.

        Raises:
            TypeError: manifest 값이 strict JSON 타입이 아닐 때.

        Example:
            ``manifest.toBytes()``.
        """
        return canonicalJsonBytes(self.toMapping())


@dataclass(frozen=True, slots=True)
class ResourceReadReceipt:
    """Page 결과의 source, query, offset과 budget 사용량이다.

    Capabilities:
        다음 page가 필요한 full source pin, query pin, nextRow와 truncation을 보존한다.

    Args:
        sourcePin: manifest source identity.
        queryPin: query semantics identity.
        integrityMode: source integrity mode.
        startRow: 이번 page 시작 offset.
        nextRow: 다음 page 시작 offset.
        batchCount: 반환 RecordBatch 수.
        rowCount: 반환 row 수.
        byteCount: 반환 Arrow logical bytes.
        truncated: budget으로 절단됐는지 여부.

    Returns:
        immutable receipt.

    Example:
        ``nextRequest = {"startRow": receipt.nextRow}``.

    Guide:
        full sourcePin과 queryPin도 nextRow와 함께 전달한다.

    SeeAlso:
        ResourceReadRequest.

    Requires:
        continuation은 integrityMode full일 때만 허용된다.

    AIContext:
        Mapping과 bytes로 외부 data consumer에 그대로 전달할 수 있다.

    LLM Specifications:
        AntiPatterns:
            - nextRow만 저장
            - truncated를 complete로 표시
        Freshness:
            sourcePin과 queryPin에 고정된다.
    """

    sourcePin: str
    queryPin: str
    integrityMode: IntegrityMode
    startRow: int
    nextRow: int
    batchCount: int
    rowCount: int
    byteCount: int
    truncated: bool

    def toMapping(self) -> dict[str, object]:
        """Receipt를 strict JSON-compatible mapping으로 반환한다.

        Requires:
            reader가 생성한 immutable receipt여야 한다.

        Raises:
            None.

        Example:
            ``receipt.toMapping()``.
        """
        return dataclasses.asdict(self)

    def toBytes(self) -> bytes:
        """Receipt를 strict canonical JSON bytes로 반환한다.

        Requires:
            receipt fields가 strict JSON scalar여야 한다.

        Raises:
            TypeError: receipt 값이 strict JSON 타입이 아닐 때.

        Example:
            ``receipt.toBytes()``.
        """
        return canonicalJsonBytes(self.toMapping())
