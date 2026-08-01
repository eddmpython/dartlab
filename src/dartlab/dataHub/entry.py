"""Public callable entry for the Unified Data Workbench."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import polars as pl

from dartlab.dataHub.catalog import buildCatalog
from dartlab.dataHub.contracts import (
    CatalogQuery,
    DataQuery,
    DataRequest,
    FactorProjection,
    GraphProjection,
    NarrativeProjection,
    NativeProjection,
    QueryBudget,
    RecordsProjection,
    ResourceProjection,
    TimeContext,
    UniverseSelection,
)
from dartlab.dataHub.execution import executeDataQuery
from dartlab.dataHub.materialization import parseMaterializationDirective


@dataclass(frozen=True, slots=True)
class _AxisEntry:
    label: str
    description: str
    returnType: str


_AXIS_REGISTRY = {
    "catalog": _AxisEntry("카탈로그", "L1, L1.5, L2 asset metadata 발견", "DataCatalogResult"),
    "query": _AxisEntry(
        "질의",
        "원천, factor, 시뮬레이터 입력 materialization과 전종목 이어읽기",
        "DataResult",
    ),
}


def _tupleField(payload: dict[str, Any], key: str) -> None:
    """JSON array만 tuple field로 바꾸고 scalar string의 문자 분해를 막는다."""

    if key not in payload:
        return
    value = payload[key]
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{key}는 sequence여야 합니다")
    payload[key] = tuple(value)


def _projectionFromMapping(value: Any):
    if not isinstance(value, Mapping):
        return value
    payload = dict(value)
    kind = str(payload.pop("kind", "native"))
    constructors = {
        "native": NativeProjection,
        "records": RecordsProjection,
        "factor": FactorProjection,
        "graph": GraphProjection,
        "narrative": NarrativeProjection,
        "resource": ResourceProjection,
    }
    constructor = constructors.get(kind)
    if constructor is None:
        raise ValueError(f"알 수 없는 projection kind: {kind}")
    _tupleField(payload, "measures")
    return constructor(**payload)


def _catalogQuery(value: Any) -> CatalogQuery | None:
    if value is None or isinstance(value, CatalogQuery):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("catalog axis는 CatalogQuery 또는 mapping을 요구합니다")
    payload = dict(value)
    for key in ("layers", "owners", "kinds"):
        _tupleField(payload, key)
    return CatalogQuery(**payload)


def _dataRequestFromMapping(value: Any) -> DataRequest:
    if isinstance(value, DataRequest):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("requests 항목은 DataRequest 또는 mapping이어야 합니다")
    payload = dict(value)
    for key in ("subjects", "measures"):
        _tupleField(payload, key)
    if "projection" in payload:
        payload["projection"] = _projectionFromMapping(payload["projection"])
    if isinstance(payload.get("time"), Mapping):
        payload["time"] = TimeContext(**dict(payload["time"]))
    if isinstance(payload.get("universe"), Mapping):
        universe = dict(payload["universe"])
        for key in ("markets", "explicitIds"):
            _tupleField(universe, key)
        payload["universe"] = UniverseSelection(**universe)
    return DataRequest(**payload)


def _dataQuery(value: Any) -> DataQuery | None:
    if value is None or isinstance(value, DataQuery):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("query axis는 DataQuery 또는 mapping을 요구합니다")
    payload = dict(value)
    for key in ("subjects", "measures"):
        _tupleField(payload, key)
    if "projection" in payload:
        payload["projection"] = _projectionFromMapping(payload["projection"])
    if isinstance(payload.get("time"), Mapping):
        payload["time"] = TimeContext(**dict(payload["time"]))
    if isinstance(payload.get("universe"), Mapping):
        universe = dict(payload["universe"])
        for key in ("markets", "explicitIds"):
            _tupleField(universe, key)
        payload["universe"] = UniverseSelection(**universe)
    if isinstance(payload.get("budget"), Mapping):
        payload["budget"] = QueryBudget(**dict(payload["budget"]))
    if "requests" in payload:
        _tupleField(payload, "requests")
        payload["requests"] = tuple(_dataRequestFromMapping(item) for item in payload["requests"])
    if "materialization" in payload:
        payload["materialization"] = parseMaterializationDirective(payload["materialization"])
    return DataQuery(**payload)


def guide() -> pl.DataFrame:
    """고정된 두 public axis와 역할을 반환한다."""
    return pl.DataFrame(
        {
            "axis": ["catalog", "query"],
            "역할": ["L1, L1.5, L2 asset 발견", "원천, factor, 시뮬레이터 입력의 bounded materialization"],
            "예시": [
                'dartlab.dataHub("catalog", query=CatalogQuery(layers=("L2",)))',
                'dartlab.dataHub("query", query={"requests": [{"assetId": "resource.finance"}, '
                '{"assetId": "resource.edgar"}]})',
            ],
        }
    )


class DataHub:
    """L1, L1.5, L2 전체를 아우르는 federated data platform engine.

    Capabilities:
        metadata-only catalog와 bounded query 두 축을 제공한다. query는 native, records, factor,
        graph, narrative, resource projection을 사용한다. DataRequest를 쓰면 한 query에서 서로 다른
        projection을 함께 실행하고 result에 snapshot, gap, lineage, quality, receipt를 결박한다.
        DART와 EDGAR 전종목 원천 및 계산 feature는 서로 다른 schema를 유지한 채 한 continuation
        chain으로 순회한다. immutable generation은 같은 query axis의 materialization 정책으로 쓴다.

    Guide:
        먼저 ``dataHub("catalog")``로 AssetRef를 찾고, 같은 asset ID를 ``dataHub("query")``에 전달한다.
        factor store 용도는 새 API가 아니라 ``FactorProjection``을 사용한다. quant와 technical 계산은
        원래 owner가 수행하고 data는 해당 결과를 factor view로 투영한다.
        partial result는 ``dataHub("query", query={"continuation": result.continuation})``으로 재개한다.
        다른 process 재생은 ``materialization={"mode": "offline", "receipt": receipt}``를 사용한다.

    Requires:
        query axis는 owner asset이 요구하는 데이터와 자격 증명을 그대로 요구한다.

    AIContext:
        Data Workbench는 data owner가 아니다. source와 calculation은 lower engine이 소유하며,
        historical PIT 미지원 asset은 latest 값을 과거 label로 바꾸지 않고 거부한다.
    """

    def __call__(
        self,
        axis: str | None = None,
        target: str | CatalogQuery | DataQuery | None = None,
        *,
        assets: str | Sequence[str] | None = None,
        query: CatalogQuery | DataQuery | None = None,
        _runtimeBindings: Mapping[str, Mapping[str, Any]] | None = None,
        **kwargs: Any,
    ):
        """Data Workbench의 catalog 또는 query axis를 실행한다.

        Capabilities:
            no-arg guide, metadata-only catalog, stable asset ID 기반 query, typed result, token-only
            resume, receipt 기반 immutable replay를 제공한다.

        Args:
            axis: ``catalog`` 또는 ``query``.
            target: catalog query, data query, 또는 query의 단일 asset ID.
            assets: query할 단일 asset ID 또는 ID sequence.
            query: CatalogQuery 또는 DataQuery.
            **kwargs: 간단 호출을 위한 query constructor keyword.

        Returns:
            no-arg면 guide DataFrame, catalog면 DataCatalogResult, query면 DataResult.

        Raises:
            KeyError: 알 수 없는 axis.
            TypeError: axis와 query type이 맞지 않을 때.
            ValueError: query asset이 없거나 budget을 초과할 때.

        Example:
            ``dartlab.dataHub("query", "scan.ratio", query=DataQuery(measures=("roe",)))``.

        Guide:
            catalog 결과의 stable assetId를 query에 그대로 사용한다.

        SeeAlso:
            ``dartlab.capabilities``와 ``DataQuery``.
        """
        if axis is None:
            return guide()
        if axis == "catalog":
            active = query if query is not None else target
            if active is None and kwargs:
                active = kwargs
            active = _catalogQuery(active)
            return buildCatalog(active)
        if axis == "query":
            activeQuery = query if query is not None else target if isinstance(target, (DataQuery, Mapping)) else None
            if activeQuery is None:
                activeQuery = kwargs
            activeQuery = _dataQuery(activeQuery)
            assert activeQuery is not None
            assetValue = assets
            if assetValue is None and isinstance(target, str):
                assetValue = target
            assetIds = (assetValue,) if isinstance(assetValue, str) else tuple(assetValue or ())
            if activeQuery.continuation is not None and assetIds:
                raise ValueError("continuation query는 target 또는 assets override를 허용하지 않습니다")
            return executeDataQuery(assetIds, activeQuery, runtimeBindings=_runtimeBindings)
        raise KeyError("dataHub axis는 'catalog' 또는 'query'여야 합니다")


Data = DataHub
dataHub = DataHub()
data = dataHub
