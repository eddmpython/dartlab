from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import consolidateHfMedia as migration  # noqa: E402


def test_semanticKeyRemovesOnlyLegacyHashSuffix() -> None:
    assert migration.semanticKey("cleanroom.ab12cd34.webp") == "cleanroom"
    assert migration.semanticKey("cleanroom.webp") == "cleanroom"
    assert migration.semanticKey("scene-01.webp") == "scene-01"


def test_rewriteCarouselsUsesOnlyObjectPaths() -> None:
    companySha = "a" * 64
    issueSha = "b" * 64
    companyPath = f"objects/sha256/aa/{companySha}.webp"
    issuePath = f"objects/sha256/bb/{issueSha}.webp"
    catalog = {
        "objects": {
            companySha: {"path": companyPath},
            issueSha: {"path": issuePath},
        }
    }
    collections = {"companies": {"005930": {"assets": {"fab": companySha}}}}
    legacy = {
        "posts": [
            {"slug": "company", "code": "005930", "slides": [{"image": "fab"}]},
            {"slug": "issue", "code": "", "slides": [{"image": "issues/x/cover.12345678.webp"}]},
        ]
    }

    rewritten = migration.rewriteCarousels(
        legacy,
        collections,
        {"issues/x/cover.12345678.webp": issueSha},
        catalog,
    )

    assert rewritten["version"] == 3
    assert rewritten["posts"][0]["slides"][0]["image"] == companyPath
    assert rewritten["posts"][1]["slides"][0]["image"] == issuePath


def test_collectionCollisionFailsInsteadOfOverwriting() -> None:
    target = {"hero": "a" * 64}
    with pytest.raises(ValueError, match="semantic key 충돌"):
        migration.ensureCollectionAsset(target, "hero", "b" * 64, "companies/005930/hero.webp")


def test_liveCutoverFollowsBundlesAndRequiresCanonicalConsumers() -> None:
    base = "https://example.test/dartlab"
    pages = {
        f"{base}/cards/": 'import("/dartlab/_app/immutable/entry/app.abc.js")',
        f"{base}/_app/immutable/entry/app.abc.js": (
            'import "../chunks/runtime.js";'
            'const routes={"/blog":[7,[2]],"/cards":[11],"/terminal":[50],"/unused":[99]};'
            'const nodes=[()=>import("../nodes/0.root.js"),()=>import("../nodes/2.layout.js"),'
            '()=>import("../nodes/7.blog.js"),()=>import("../nodes/11.cards.js"),'
            '()=>import("../nodes/50.terminal.js"),()=>import("../nodes/99.unused.js")];'
        ),
        f"{base}/_app/immutable/chunks/runtime.js": "const runtime=true;",
        f"{base}/_app/immutable/nodes/0.root.js": "const root=true;",
        f"{base}/_app/immutable/nodes/2.layout.js": "const layout=true;",
        f"{base}/_app/immutable/nodes/7.blog.js": "const blog=true;",
        f"{base}/_app/immutable/nodes/11.cards.js": 'import "../chunks/media.def.js";',
        f"{base}/_app/immutable/nodes/50.terminal.js": 'import "../chunks/media.def.js";',
        f"{base}/_app/immutable/chunks/media.def.js": (
            'const companies="manifests/companies.json";const carousels="manifests/carousels.json";'
        ),
    }

    assert migration.liveCutoverErrors(base, fetchText=pages.__getitem__) == []


def test_liveCutoverRejectsLegacyBundleReference() -> None:
    base = "https://example.test/dartlab"
    pages = {
        f"{base}/cards/": 'import("/dartlab/_app/immutable/entry/start.abc.js")',
        f"{base}/_app/immutable/entry/start.abc.js": (
            'const a="manifests/companies.json";const b="manifests/carousels.json";const old="companies/index.json";'
        ),
    }

    assert migration.liveCutoverErrors(base, fetchText=pages.__getitem__) == ["라이브에 회사 레거시 index 참조 잔존"]


def test_canonicalManifestErrorsRejectsMissingAndLegacyObjects() -> None:
    sha256 = "a" * 64
    canonical = f"objects/sha256/aa/{sha256}.webp"
    companies = {
        "version": 3,
        "companies": {"005930": {"assets": [{"path": canonical, "sha256": sha256}]}},
    }
    carousels = {
        "version": 3,
        "posts": [{"slug": "x", "slides": [{"image": "companies/005930/hero.webp"}]}],
    }

    errors = migration.canonicalManifestErrors(companies, carousels, {canonical})

    assert errors == ["런타임 manifest 비정규 객체 경로: companies/005930/hero.webp"]


def test_canonicalManifestErrorsRejectsCompanyShaMismatch() -> None:
    sha256 = "a" * 64
    canonical = f"objects/sha256/aa/{sha256}.webp"
    companies = {
        "version": 3,
        "companies": {"005930": {"assets": [{"path": canonical, "sha256": "b" * 64}]}},
    }
    carousels = {"version": 3, "posts": [{"slug": "x", "slides": []}]}

    errors = migration.canonicalManifestErrors(companies, carousels, {canonical})

    assert errors == [f"회사 manifest SHA-256 계약 위반: 005930 -> {canonical}"]


def test_mainAcceptsIdempotentCanonicalOnlyState(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    sha256 = "a" * 64
    canonical = f"objects/sha256/aa/{sha256}.webp"
    rows = [
        SimpleNamespace(path=canonical),
        SimpleNamespace(path=migration.COMPANIES_MANIFEST),
        SimpleNamespace(path=migration.CAROUSELS_MANIFEST),
        SimpleNamespace(path=".gitattributes"),
    ]
    catalog = {"objects": {sha256: {"path": canonical}}}
    companies = {
        "version": 3,
        "companies": {"005930": {"assets": [{"path": canonical, "sha256": sha256}]}},
    }
    carousels = {"version": 3, "posts": [{"slug": "x", "slides": []}]}

    monkeypatch.setattr(
        migration,
        "parseArgs",
        lambda: SimpleNamespace(
            apply=True,
            delete_legacy=True,
            live_base="https://example.test",
            batch_size=100,
            repo="example/media",
        ),
    )
    monkeypatch.setattr(migration, "loadMediaCatalog", lambda _path: (catalog, []))
    monkeypatch.setattr(migration, "HfApi", lambda: object())
    monkeypatch.setattr(migration, "listRemoteFiles", lambda _api, _repo: rows)
    monkeypatch.setattr(
        migration,
        "loadRemoteJson",
        lambda _repo, path: companies if path == migration.COMPANIES_MANIFEST else carousels,
    )
    monkeypatch.setattr(migration, "liveCutoverErrors", lambda _base: [])

    migration.main()

    assert "레거시 0개" in capsys.readouterr().out
