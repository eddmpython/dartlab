from __future__ import annotations

import sys
from pathlib import Path

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
