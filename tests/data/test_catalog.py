"""Unified Data Workbench federated catalog tests."""

from __future__ import annotations

from types import SimpleNamespace

from dartlab.data import CatalogQuery


def testCatalogCoversEveryCurrentLowerLayerRegistryAndResource():
    import dartlab

    result = dartlab.data("catalog")
    assets = result.assets

    assert result.status == "ok"
    assert len(result.gaps) == 0
    assert sum(asset.executorKind == "engineAxis" for asset in assets) == 147
    assert sum(asset.owner == "analysis" and asset.executorKind == "engineAxis" for asset in assets) == 22
    simulationInputs = next(asset for asset in assets if asset.assetId == "analysis.simulationInputs")
    assert simulationInputs.executorKind == "callable"
    assert simulationInputs.temporalSupport == ("latest", "validAt")
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


def testPrivateResourceIsCataloguedButNotQueryable():
    import dartlab

    result = dartlab.data("catalog", query=CatalogQuery(search="forwardTests"))
    asset = next(item for item in result.assets if item.assetId == "resource.forwardTests")
    assert asset.visibility == "PRIVATE"
    assert not asset.queryable


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
