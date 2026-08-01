"""Owner-declared provider를 자동 발견해 federated asset catalog를 만든다."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, cast

from dartlab.dataHub.contracts import DataAssetDescriptor, DataGap

_ALLOWED_LAYERS = frozenset({"L1", "L1.5", "L2"})
_EXECUTION_MODES = frozenset(
    {
        "ownerBulk",
        "ownerBatch",
        "subjectFanout",
        "resourceCompanyShard",
        "resourceBulk",
        "unsupported",
    }
)
_SelectorKind = Literal["none", "subject", "measure"]
_ExecutionMode = Literal[
    "ownerBulk",
    "ownerBatch",
    "subjectFanout",
    "resourceCompanyShard",
    "resourceBulk",
    "unsupported",
]


def _canonical(value: Any) -> bytes:
    def serializeDefault(item: Any) -> Any:
        """카탈로그 계약 값을 결정적 JSON 표현으로 변환한다."""

        if dataclasses.is_dataclass(item):
            return dataclasses.asdict(cast(Any, item))
        if isinstance(item, (set, frozenset, tuple)):
            return list(item)
        return str(item)

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=serializeDefault
    ).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sourceDigest(module: object) -> str:
    raw = getattr(module, "__file__", None)
    if not raw:
        return "runtime"
    path = Path(raw)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "runtime"


def _declared(entry: Any) -> dict[str, Any]:
    if not dataclasses.is_dataclass(entry):
        return {}
    ignored = {"module", "fn", "listModule", "calcs"}
    out: dict[str, Any] = {}
    for field in dataclasses.fields(entry):
        if field.name in ignored:
            continue
        value = _metadataValue(getattr(entry, field.name, None))
        if value is None:
            continue
        out[field.name] = value
    return out


def _metadataValue(value: Any) -> Any:
    """Descriptor hash와 metadata에 보존 가능한 immutable 값을 선별한다."""

    if isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, (tuple, list)):
        converted = tuple(_metadataValue(item) for item in value)
        return converted if all(item is not None for item in converted) else None
    return None


def _requireTemporalDeclarationMatchesExecutor(
    assetId: str,
    *,
    temporalSupport: tuple[str, ...],
    validTimeParam: Any,
    knowledgeTimeParam: Any,
) -> None:
    """선언한 시점 지원과 executor 가 실제로 받을 수 있는 인자가 맞는지 검증한다.

    Capabilities:
        owner 가 `knownAt` 지원을 선언하고도 그 값을 받을 인자가 없어 조용히 버리는
        경로를 catalog 단계에서 차단한다.

    Args:
        assetId: 검증할 asset 식별자.
        temporalSupport: owner 가 선언한 시점 지원 목록.
        validTimeParam: executor 가 valid time 을 받을 인자 이름.
        knowledgeTimeParam: executor 가 knowledge time 을 받을 인자 이름.

    Raises:
        ValueError: 선언과 인자가 어긋날 때.

    Example:
        ``_requireTemporalDeclarationMatchesExecutor(assetId, temporalSupport=("knownAt",), ...)``.

    Guide:
        선언만 믿으면 D05 가 owner 규율에만 의존하게 된다. 기계로 고정한다.

    When:
        descriptor 를 만들기 직전에 호출한다.

    How:
        선언한 축마다 대응 인자가 실제로 존재하는지 확인한다.

    See Also:
        ``_temporalGap``.

    Requires:
        `latest` 는 인자를 요구하지 않는다.

    AI Context:
        인자가 없으면 시점이 조용히 버려지고 query cutoff 가 관측 시점으로 둔갑한다.
        그것이 정확히 D05 가 금지한 경로다.
    """

    if "knownAt" in temporalSupport and not knowledgeTimeParam:
        raise ValueError(f"{assetId}: knownAt을 선언했지만 executor가 받을 인자가 없습니다")
    if "validAt" in temporalSupport and not validTimeParam:
        raise ValueError(f"{assetId}: validAt을 선언했지만 executor가 받을 인자가 없습니다")


def _executorParams(
    assetId: str,
    *,
    subjectParam: Any = None,
    measureParam: Any = None,
    validTimeParam: Any = None,
    knowledgeTimeParam: Any = None,
    marketParam: Any = None,
) -> dict[str, str | None]:
    """Owner callable keyword 선언을 검증하고 이름 충돌을 차단한다."""

    raw = {
        "subjectParam": subjectParam,
        "measureParam": measureParam,
        "validTimeParam": validTimeParam,
        "knowledgeTimeParam": knowledgeTimeParam,
        "marketParam": marketParam,
    }
    invalid = tuple(
        name for name, value in raw.items() if value is not None and (type(value) is not str or not value.strip())
    )
    if invalid:
        raise TypeError(f"{assetId} executor parameter 선언이 유효하지 않음: {', '.join(invalid)}")
    normalized = {name: value.strip() if isinstance(value, str) else None for name, value in raw.items()}
    names = tuple(value for value in normalized.values() if value is not None)
    if len(names) != len(set(names)):
        raise ValueError(f"{assetId} executor parameter 이름이 충돌함")
    return normalized


def discoverOwnerProviders() -> tuple[tuple[Mapping[str, Any], ...], tuple[DataGap, ...]]:
    """Installed dartlab package에서 metadata-only dataProduct provider를 자동 발견한다.

    Capabilities:
        새 owner는 자기 package에 ``dataProduct.py``와 ``DATA_PRODUCT_DESCRIPTOR``만 두면 중앙
        목록 수정 없이 다음 catalog에 나타난다. descriptor가 잘못되면 조용히 누락하지 않고 gap이다.

    Returns:
        검증된 descriptor mapping tuple과 discovery gap tuple.

    Raises:
        없음. provider 단위 오류는 gap으로 격리한다.
    """
    from dartlab.reference.capability.dataProducts import discoverDataProductProviders

    providers, errors = discoverDataProductProviders(layers=_ALLOWED_LAYERS)
    gaps = tuple(DataGap("PROVIDER_DISCOVERY_FAILED", error, error.split(":", 1)[0], systemic=True) for error in errors)
    return providers, gaps


def _registryAssets(provider: Mapping[str, Any]) -> Iterable[DataAssetDescriptor]:
    owner = str(provider["owner"])
    layer = str(provider["layer"])
    for registrySpec in provider.get("registries", ()):
        module = importlib.import_module(str(registrySpec["module"]))
        registry = getattr(module, str(registrySpec["attribute"]))
        if not isinstance(registry, Mapping):
            raise TypeError(f"{registrySpec['module']} registry가 mapping이 아님")
        sourceDigest = _sourceDigest(module)
        for axis, entry in registry.items():
            declared = _declared(entry)
            selectorKind = registrySpec.get("selectorKind")
            if selectorKind is None:
                selectorKind = (
                    "subject"
                    if registrySpec.get("subjectParam")
                    else "measure"
                    if "targetParam" in declared
                    else "none"
                )
            if selectorKind not in {"none", "subject", "measure"}:
                raise ValueError(f"{owner}.{axis} selectorKind가 유효하지 않음")
            configuredRequired = registrySpec.get("selectorRequired")
            selectorRequired = (
                bool(configuredRequired)
                if configuredRequired is not None
                else bool(declared.get("stockRequired") or declared.get("targetRequired"))
            )
            concurrencyGroup = (
                declared.get("concurrencyGroup")
                or registrySpec.get("concurrencyGroup")
                or provider.get("concurrencyGroup")
            )
            executionMode = str(declared.get("executionMode") or registrySpec.get("executionMode") or "unsupported")
            if executionMode not in _EXECUTION_MODES:
                raise ValueError(f"{owner}.{axis} executionMode가 유효하지 않음")
            typedExecutionMode = cast(_ExecutionMode, executionMode)
            universeMarkets = tuple(
                str(market).upper()
                for market in (declared.get("universeMarkets") or registrySpec.get("universeMarkets") or ())
            )
            marketUnits = tuple(
                (str(market).upper(), str(unit))
                for market, unit in (declared.get("marketUnits") or registrySpec.get("marketUnits") or ())
            )
            universeKind = str(declared.get("universeKind") or registrySpec.get("universeKind") or "none")
            marketParam = declared.get("marketParam") or registrySpec.get("marketParam")
            measureParam = (
                declared.get("measureParam") if "measureParam" in declared else registrySpec.get("measureParam")
            )
            executorParams = _executorParams(
                f"{owner}.{axis}",
                subjectParam=registrySpec.get("subjectParam"),
                measureParam=measureParam,
                marketParam=marketParam,
            )
            label = str(getattr(entry, "label", None) or getattr(entry, "section", None) or axis)
            description = str(getattr(entry, "description", None) or label)
            hidden = bool(getattr(entry, "hidden", False))
            payload = {
                "owner": owner,
                "axis": str(axis),
                "declared": declared,
                "registryContract": {
                    "kind": registrySpec.get("kind", "native"),
                    "selectorKind": selectorKind,
                    "selectorRequired": selectorRequired,
                    "subjectParam": registrySpec.get("subjectParam"),
                    "measureParam": measureParam,
                    "concurrencyGroup": concurrencyGroup,
                    "executionMode": executionMode,
                    "universeKind": universeKind,
                    "universeMarkets": universeMarkets,
                    "marketParam": marketParam,
                    "marketUnits": marketUnits,
                },
                "sourceDigest": sourceDigest,
            }
            yield DataAssetDescriptor(
                assetId=f"{owner}.{axis}",
                assetVersionId=f"asset:{_digest(payload)}",
                owner=owner,
                layer=layer,
                kind=str(registrySpec.get("kind", "native")),
                label=label,
                description=description,
                sourceRef=f"python:{registrySpec['module']}:{registrySpec['attribute']}",
                queryable=bool(declared.get("queryable", True)),
                hidden=hidden,
                temporalSupport=("latest",),
                executorKind="engineAxis" if declared.get("queryable", True) else "catalog",
                executorAxis=str(axis) if declared.get("queryable", True) else None,
                subjectParam=executorParams["subjectParam"],
                measureParam=executorParams["measureParam"],
                selectorKind=selectorKind,
                selectorRequired=selectorRequired,
                concurrencyGroup=str(concurrencyGroup) if concurrencyGroup else None,
                executionMode=typedExecutionMode,
                universeKind=universeKind,
                universeMarkets=universeMarkets,
                marketParam=executorParams["marketParam"],
                marketUnits=marketUnits,
                metadata=tuple(sorted(declared.items())),
            )


def _declaredAssets(provider: Mapping[str, Any]) -> Iterable[DataAssetDescriptor]:
    """Owner가 registry 밖의 stable data asset으로 선언한 callable을 반영한다."""
    owner = str(provider["owner"])
    layer = str(provider["layer"])
    for spec in provider.get("assets", ()):
        if not isinstance(spec, Mapping):
            raise TypeError(f"{owner} asset descriptor가 mapping이 아님")
        assetId = str(spec["assetId"])
        if not assetId.startswith(f"{owner}."):
            raise ValueError(f"{assetId}가 owner namespace 밖에 있음")
        executor = spec.get("executor")
        if not isinstance(executor, Mapping):
            raise TypeError(f"{assetId} executor가 mapping이 아님")
        concurrencyGroup = (
            spec.get("concurrencyGroup") if "concurrencyGroup" in spec else provider.get("concurrencyGroup")
        )
        rawSourceModules = spec.get("sourceModules", ())
        if not isinstance(rawSourceModules, (tuple, list)) or any(type(item) is not str for item in rawSourceModules):
            raise TypeError(f"{assetId} sourceModules가 string sequence가 아님")
        sourceModules = tuple(dict.fromkeys((str(executor["module"]), *rawSourceModules)))
        sourceDigests = tuple(
            (moduleName, _sourceDigest(importlib.import_module(moduleName))) for moduleName in sourceModules
        )
        payload = {
            "owner": owner,
            "layer": layer,
            "spec": spec,
            "concurrencyGroup": concurrencyGroup,
            "sourceDigests": sourceDigests,
        }
        metadata = spec.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise TypeError(f"{assetId} metadata가 mapping이 아님")
        selectorKind = str(spec.get("selectorKind") or ("subject" if spec.get("subjectParam") else "none"))
        if selectorKind not in {"none", "subject", "measure"}:
            raise ValueError(f"{assetId} selectorKind가 유효하지 않음")
        typedSelectorKind = cast(_SelectorKind, selectorKind)
        executionMode = str(spec.get("executionMode") or "unsupported")
        if executionMode not in _EXECUTION_MODES:
            raise ValueError(f"{assetId} executionMode가 유효하지 않음")
        typedExecutionMode = cast(_ExecutionMode, executionMode)
        executorParams = _executorParams(
            assetId,
            subjectParam=spec.get("subjectParam"),
            measureParam=spec.get("measureParam"),
            validTimeParam=spec.get("validTimeParam"),
            knowledgeTimeParam=spec.get("knowledgeTimeParam"),
            marketParam=spec.get("marketParam"),
        )
        _requireTemporalDeclarationMatchesExecutor(
            assetId,
            temporalSupport=tuple(str(item) for item in spec.get("temporalSupport", ("latest",))),
            validTimeParam=executorParams["validTimeParam"],
            knowledgeTimeParam=executorParams["knowledgeTimeParam"],
        )
        visibility = str(spec.get("visibility", "LOCAL"))
        yield DataAssetDescriptor(
            assetId=assetId,
            assetVersionId=f"asset:{_digest(payload)}",
            owner=owner,
            layer=layer,
            kind=str(spec.get("kind", "native")),
            label=str(spec.get("label", assetId)),
            description=str(spec.get("description", spec.get("label", assetId))),
            sourceRef=f"python:{executor['module']}:{executor['attribute']}",
            queryable=visibility != "PRIVATE",
            hidden=bool(spec.get("hidden", False)),
            visibility=visibility,
            licenseRef=str(spec["licenseRef"]) if spec.get("licenseRef") else None,
            temporalSupport=tuple(str(item) for item in spec.get("temporalSupport", ("latest",))),
            executorKind="callable",
            executorModule=str(executor["module"]),
            executorAttribute=str(executor["attribute"]),
            subjectParam=executorParams["subjectParam"],
            measureParam=executorParams["measureParam"],
            validTimeParam=executorParams["validTimeParam"],
            knowledgeTimeParam=executorParams["knowledgeTimeParam"],
            selectorKind=typedSelectorKind,
            selectorRequired=bool(spec.get("selectorRequired", metadata.get("stockRequired", False))),
            concurrencyGroup=str(concurrencyGroup) if concurrencyGroup else None,
            executionMode=typedExecutionMode,
            universeKind=str(spec.get("universeKind") or "none"),
            universeMarkets=tuple(str(market).upper() for market in spec.get("universeMarkets", ())),
            marketParam=executorParams["marketParam"],
            marketUnits=tuple((str(market).upper(), str(unit)) for market, unit in spec.get("marketUnits", ())),
            metadata=tuple(sorted((str(key), value) for key, value in metadata.items())),
        )


def _ownerAssets(providers: Iterable[Mapping[str, Any]]) -> Iterable[DataAssetDescriptor]:
    for provider in providers:
        owner = str(provider["owner"])
        payload = {"owner": owner, "layer": provider["layer"]}
        yield DataAssetDescriptor(
            assetId=f"owner.{owner}",
            assetVersionId=f"asset:{_digest(payload)}",
            owner=owner,
            layer=str(provider["layer"]),
            kind="owner",
            label=owner,
            description=f"{owner} package data product owner",
            sourceRef=f"python:dartlab.{owner}.dataProduct:DATA_PRODUCT_DESCRIPTOR",
            queryable=False,
        )


def _resourceOwner(category: str, directory: str) -> tuple[str, str, bool]:
    if category in {"expectations", "forwardTests"}:
        return "simulate", "L2.5+", False
    if directory.startswith("landing/"):
        return "product", "L3+", False
    if directory.startswith("ai/"):
        return "ai", "L4", False
    if directory.endswith("/scan") or category in {"scan", "edgarScan"}:
        return "scan", "L1.5", True
    if directory.startswith(("dart/", "edgar/", "original/", "edinet/")):
        return "providers", "L1", True
    return "gather", "L1", True


def _resourceMarkets(directory: str) -> tuple[str, ...]:
    if directory.startswith("dart/"):
        return ("KR",)
    if directory.startswith("edgar/"):
        return ("US",)
    return ()


def _resourceSourceProvider(directory: str) -> str | None:
    if directory.startswith("dart/"):
        return "dart"
    if directory.startswith("edgar/"):
        return "edgar"
    return None


def _resourceAssets() -> Iterable[DataAssetDescriptor]:
    from dartlab.core.dataConfig import DATA_RELEASES, downloadCatalog

    shardKinds = {entry["dir"]: entry["shardKind"] for entry in downloadCatalog()}

    for category, spec in DATA_RELEASES.items():
        directory = str(spec.get("dir", category))
        owner, layer, inScope = _resourceOwner(category, directory)
        public = bool(spec.get("public"))
        shardKind = shardKinds.get(directory, "bulk")
        executionMode = "resourceCompanyShard" if shardKind == "company" else "resourceBulk"
        universeMarkets = _resourceMarkets(directory)
        sourceProvider = _resourceSourceProvider(directory)
        payload = {
            "category": category,
            "spec": spec,
            "owner": owner,
            "layer": layer,
            "shardKind": shardKind,
            "executionMode": executionMode,
            "universeMarkets": universeMarkets,
            "sourceProvider": sourceProvider,
        }
        queryable = inScope and public and not spec.get("nested") and not spec.get("deprecated")
        yield DataAssetDescriptor(
            assetId=f"resource.{category}",
            assetVersionId=f"asset:{_digest(payload)}",
            owner=owner,
            layer=layer,
            kind="resource",
            label=str(spec.get("label", category)),
            description=f"DATA_RELEASES[{category}]",
            sourceRef=f"dataRelease:{category}:{directory}",
            queryable=queryable,
            visibility="PUBLIC" if public else "PRIVATE",
            licenseRef=str(spec.get("licenseRef")) if spec.get("licenseRef") else None,
            temporalSupport=("latest",),
            executorKind="resource" if queryable else "catalog",
            executorAxis=category if queryable else None,
            subjectParam="subject",
            selectorKind="subject",
            selectorRequired=False,
            executionMode=executionMode,
            universeMarkets=universeMarkets,
            metadata=tuple(
                sorted(
                    [(str(key), value) for key, value in spec.items() if isinstance(value, (str, bool, int, float))]
                    + [("shardKind", shardKind)]
                    + ([("sourceProvider", sourceProvider)] if sourceProvider is not None else [])
                )
            ),
        )


def _conceptAssets() -> Iterable[DataAssetDescriptor]:
    from dartlab.core.extractionCatalog import getExtractionConcepts

    for concept in getExtractionConcepts():
        payload = dataclasses.asdict(concept)
        yield DataAssetDescriptor(
            assetId=f"concept.{concept.conceptId}",
            assetVersionId=f"asset:{_digest(payload)}",
            owner="frame",
            layer="L1.5",
            kind="narrative" if concept.narrativeAnchor else "concept",
            label=concept.label,
            description=f"{concept.category} extraction concept",
            sourceRef=f"extractionConcept:{concept.conceptId}",
            queryable=False,
            metadata=(
                ("axisType", concept.axisType),
                ("registered", concept.registered),
                ("valueType", concept.valueType),
            ),
        )


def _companyAssets() -> Iterable[DataAssetDescriptor]:
    from dartlab.reference.capability import loadCapabilities

    for key, entry in loadCapabilities().items():
        if key != "Company" and not key.startswith("Company."):
            continue
        payload = {"key": key, "entry": entry}
        yield DataAssetDescriptor(
            assetId=f"providers.{key}",
            assetVersionId=f"asset:{_digest(payload)}",
            owner="providers",
            layer="L1",
            kind=str(entry.get("kind", "companySurface")) if isinstance(entry, Mapping) else "companySurface",
            label=key,
            description=str(entry.get("summary", key)) if isinstance(entry, Mapping) else key,
            sourceRef=f"capability:{key}",
            queryable=False,
        )


def discoverAssets() -> tuple[tuple[DataAssetDescriptor, ...], tuple[DataGap, ...]]:
    """L1, L1.5, L2 owner와 runtime resource를 하나의 deduplicated catalog로 만든다."""
    providers, gaps = discoverOwnerProviders()
    assets: list[DataAssetDescriptor] = list(_ownerAssets(providers))
    for provider in providers:
        try:
            assets.extend(_registryAssets(provider))
            assets.extend(_declaredAssets(provider))
        except Exception as exc:
            gaps = (
                *gaps,
                DataGap(
                    "OWNER_ASSET_DISCOVERY_FAILED",
                    f"{provider['owner']}: {type(exc).__name__}",
                    str(provider["owner"]),
                    systemic=True,
                ),
            )
    assets.extend(_resourceAssets())
    assets.extend(_conceptAssets())
    assets.extend(_companyAssets())
    byId: dict[str, DataAssetDescriptor] = {}
    for asset in assets:
        if asset.assetId in byId and byId[asset.assetId] != asset:
            gaps = (*gaps, DataGap("DUPLICATE_ASSET_ID", asset.assetId, asset.assetId, systemic=True))
            continue
        byId[asset.assetId] = asset
    return tuple(sorted(byId.values(), key=lambda item: item.assetId)), tuple(gaps)


def catalogSnapshotId(assets: Iterable[DataAssetDescriptor]) -> str:
    """Asset version set을 deterministic catalog snapshot ID로 결박한다."""
    pairs = tuple((asset.assetId, asset.assetVersionId) for asset in assets)
    return f"data-snapshot:{_digest(pairs)}"
