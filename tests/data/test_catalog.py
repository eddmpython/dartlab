"""Unified Data Workbench federated catalog tests."""

from __future__ import annotations

import importlib
from types import SimpleNamespace

from dartlab.data import CatalogQuery


def testCatalogCoversEveryCurrentLowerLayerRegistryAndResource():
    import dartlab

    result = dartlab.data("catalog")
    assets = result.assets

    assert result.status == "ok"
    assert len(result.gaps) == 0
    assert sum(asset.executorKind == "engineAxis" for asset in assets) == 146
    assert sum(asset.owner == "analysis" and asset.executorKind == "engineAxis" for asset in assets) == 22
    simulationInputs = next(asset for asset in assets if asset.assetId == "analysis.simulationInputs")
    assert simulationInputs.executorKind == "callable"
    assert simulationInputs.temporalSupport == ("latest", "validAt")
    edgarFeatures = next(asset for asset in assets if asset.assetId == "analysis.edgarFinancialFeatures")
    assert edgarFeatures.executorKind == "callable"
    assert edgarFeatures.measureParam == "measures"
    assert edgarFeatures.temporalSupport == ("knownAt",)
    assert edgarFeatures.executionMode == "subjectFanout"
    assert edgarFeatures.concurrencyGroup is None
    assert edgarFeatures.universeKind == "listedEquity"
    assert edgarFeatures.universeMarkets == ("US",)
    featureMetadata = dict(edgarFeatures.metadata)
    assert featureMetadata["observationPIT"] is True
    assert featureMetadata["continuationSourceAssetId"] == "resource.edgar"
    assert featureMetadata["continuationSourceCategory"] == "edgar"
    assert featureMetadata["sourceEntityParam"] == "sourceEntityId"
    assert featureMetadata["sourcePayloadParam"] == "sourcePayload"
    assert featureMetadata["sourceIntegrityParam"] == "sourceIntegrityDigest"
    assert featureMetadata["pageMaxEntities"] == 8
    dartFeatures = next(asset for asset in assets if asset.assetId == "analysis.dartFinancialFeatures")
    assert dartFeatures.executorKind == "callable"
    assert dartFeatures.temporalSupport == ("knownAt",)
    assert dartFeatures.executionMode == "subjectFanout"
    assert dartFeatures.concurrencyGroup is None
    assert dartFeatures.universeKind == "listedEquity"
    assert dartFeatures.universeMarkets == ("KR",)
    dartFeatureMetadata = dict(dartFeatures.metadata)
    assert dartFeatureMetadata["continuationSourceAssetId"] == "resource.finance"
    assert dartFeatureMetadata["continuationSourceCategory"] == "finance"
    assert dartFeatureMetadata["entityParamMap"] == (("fiscalYearEndMonth", "fiscalYearEndMonth"),)
    assert dartFeatureMetadata["observationPIT"] is True
    assert dartFeatureMetadata["pageMaxEntities"] == 8
    assert sum(asset.kind == "resource" for asset in assets) == 42
    assert sum(asset.assetId.startswith("concept.") for asset in assets) == 88
    assert sum(asset.assetId.startswith("providers.Company") for asset in assets) == 64
    assert {asset.owner for asset in assets if asset.assetId.startswith("owner.")} == {
        "analysis",
        "credit",
        "frame",
        "gather",
        "industry",
        "macro",
        "providers",
        "quant",
        "reference",
        "scan",
        "synth",
    }


def testCatalogFiltersWithoutExecutingAsset(monkeypatch):
    import dartlab

    called = False

    def failIfCalled(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("catalog discovery가 값을 실행함")

    monkeypatch.setattr(dartlab, "scan", failIfCalled)
    result = dartlab.data("catalog", query=CatalogQuery(owners=("scan",), search="ratio"))

    assert result.status == "ok"
    assert any(asset.assetId == "scan.ratio" for asset in result.assets)
    assert not called


def testCatalogSnapshotIsDeterministic():
    import dartlab

    first = dartlab.data("catalog")
    second = dartlab.data("catalog")
    assert first.snapshotId == second.snapshotId
    assert [(asset.assetId, asset.assetVersionId) for asset in first.assets] == [
        (asset.assetId, asset.assetVersionId) for asset in second.assets
    ]


def testEveryQueryableAssetHasResolvableExecutor():
    import dartlab

    assets = [asset for asset in dartlab.data("catalog").assets if asset.queryable]
    assert len(assets) == 172
    for asset in assets:
        if asset.executorKind == "engineAxis":
            assert callable(getattr(dartlab, asset.owner))
            assert asset.executorAxis
        elif asset.executorKind == "callable":
            module = importlib.import_module(asset.executorModule or "")
            assert callable(getattr(module, asset.executorAttribute or ""))
        elif asset.executorKind == "resource":
            assert asset.executorAxis
            assert asset.selectorKind == "subject"
        else:
            raise AssertionError(f"queryable executorKind가 유효하지 않음: {asset.assetId}")


def testPrivateResourceIsCataloguedButNotQueryable():
    import dartlab

    result = dartlab.data("catalog", query=CatalogQuery(search="forwardTests"))
    asset = next(item for item in result.assets if item.assetId == "resource.forwardTests")
    assert asset.visibility == "PRIVATE"
    assert not asset.queryable


def testDartAndEdgarResourcesDeclareTheirUniverseMarkets():
    import dartlab

    assets = {asset.assetId: asset for asset in dartlab.data("catalog").assets}

    assert assets["resource.finance"].universeMarkets == ("KR",)
    assert assets["resource.edgar"].universeMarkets == ("US",)
    assert dict(assets["resource.finance"].metadata)["sourceProvider"] == "dart"
    assert dict(assets["resource.edgar"].metadata)["sourceProvider"] == "edgar"


def testDeprecatedRegistryAxisIsCataloguedButNotQueryable():
    import dartlab

    asset = next(item for item in dartlab.data("catalog").assets if item.assetId == "gather.calendar")
    assert asset.hidden
    assert not asset.queryable
    assert asset.executorKind == "catalog"


def testNewOwnerProviderNeedsNoCentralEngineList(monkeypatch):
    from dartlab.reference.capability import dataProducts

    descriptor = {"owner": "future", "layer": "L2", "registries": ()}
    monkeypatch.setattr(
        dataProducts.pkgutil,
        "iter_modules",
        lambda paths: [SimpleNamespace(name="future", ispkg=True)],
    )
    monkeypatch.setattr(dataProducts.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(
        dataProducts.importlib,
        "import_module",
        lambda name: SimpleNamespace(DATA_PRODUCT_DESCRIPTOR=descriptor),
    )

    providers, errors = dataProducts.discoverDataProductProviders(layers=frozenset({"L2"}))

    assert providers == (descriptor,)
    assert errors == ()


def testDeclaredCallableVersionBindsExecutorAndTransitiveSourceDigests(monkeypatch):
    import dartlab.data.discovery as discovery

    provider = {
        "owner": "analysis",
        "layer": "L2",
        "assets": (
            {
                "assetId": "analysis.featureProbe",
                "executor": {"module": "owner.executor", "attribute": "run"},
                "sourceModules": ("owner.definition",),
            },
        ),
    }
    digests = {"owner.executor": "a" * 64, "owner.definition": "b" * 64}
    monkeypatch.setattr(discovery.importlib, "import_module", lambda name: SimpleNamespace(name=name))
    monkeypatch.setattr(discovery, "_sourceDigest", lambda module: digests[module.name])

    first = tuple(discovery._declaredAssets(provider))[0]
    digests["owner.definition"] = "c" * 64
    second = tuple(discovery._declaredAssets(provider))[0]

    assert first.assetVersionId != second.assetVersionId
