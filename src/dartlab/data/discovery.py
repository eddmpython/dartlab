"""Owner-declared provider를 자동 발견해 federated asset catalog를 만든다."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from dartlab.data.contracts import DataAssetDescriptor, DataGap

_ALLOWED_LAYERS = frozenset({"L1", "L1.5", "L2"})


def _canonical(value: Any) -> bytes:
    def serializeDefault(item: Any) -> Any:
        """카탈로그 계약 값을 결정적 JSON 표현으로 변환한다."""

        if dataclasses.is_dataclass(item):
            return dataclasses.asdict(item)
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
        value = getattr(entry, field.name, None)
        if value is None or not isinstance(value, (str, bool, int, float)):
            continue
        out[field.name] = value
    return out


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
            label = str(getattr(entry, "label", None) or getattr(entry, "section", None) or axis)
            description = str(getattr(entry, "description", None) or label)
            hidden = bool(getattr(entry, "hidden", False))
            payload = {
                "owner": owner,
                "axis": str(axis),
                "declared": declared,
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
                queryable=True,
                hidden=hidden,
                temporalSupport=("latest",),
                executorKind="engineAxis",
                executorAxis=str(axis),
                subjectParam=registrySpec.get("subjectParam"),
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
        payload = {"owner": owner, "layer": layer, "spec": spec}
        metadata = spec.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise TypeError(f"{assetId} metadata가 mapping이 아님")
        yield DataAssetDescriptor(
            assetId=assetId,
            assetVersionId=f"asset:{_digest(payload)}",
            owner=owner,
            layer=layer,
            kind=str(spec.get("kind", "native")),
            label=str(spec.get("label", assetId)),
            description=str(spec.get("description", spec.get("label", assetId))),
            sourceRef=f"python:{executor['module']}:{executor['attribute']}",
            queryable=True,
            hidden=bool(spec.get("hidden", False)),
            visibility=str(spec.get("visibility", "LOCAL")),
            licenseRef=str(spec["licenseRef"]) if spec.get("licenseRef") else None,
            temporalSupport=tuple(str(item) for item in spec.get("temporalSupport", ("latest",))),
            executorKind="callable",
            executorModule=str(executor["module"]),
            executorAttribute=str(executor["attribute"]),
            subjectParam=str(spec["subjectParam"]) if spec.get("subjectParam") else None,
            validTimeParam=str(spec["validTimeParam"]) if spec.get("validTimeParam") else None,
            knowledgeTimeParam=str(spec["knowledgeTimeParam"]) if spec.get("knowledgeTimeParam") else None,
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


def _resourceAssets() -> Iterable[DataAssetDescriptor]:
    from dartlab.core.dataConfig import DATA_RELEASES, downloadCatalog

    shardKinds = {entry["dir"]: entry["shardKind"] for entry in downloadCatalog()}

    for category, spec in DATA_RELEASES.items():
        directory = str(spec.get("dir", category))
        owner, layer, inScope = _resourceOwner(category, directory)
        public = bool(spec.get("public"))
        shardKind = shardKinds.get(directory, "bulk")
        payload = {"category": category, "spec": spec, "owner": owner, "layer": layer}
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
            metadata=tuple(
                sorted(
                    [(str(key), value) for key, value in spec.items() if isinstance(value, (str, bool, int, float))]
                    + [("shardKind", shardKind)]
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
