"""블로그 미디어 HF SSOT 커밋 및 CI 게이트 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import blogMediaGate as gate  # noqa: E402


def catalogFor(indexPath: str, sha256: str = "a" * 64) -> dict[str, object]:
    key = gate.postKey(indexPath)
    source = f"{indexPath.removesuffix('index.md')}assets/hero.svg"
    return {
        "repo": gate.HF_REPO,
        "objectPrefix": gate.HF_OBJECT_PREFIX,
        "files": {source: sha256},
        "objects": {
            sha256: {
                "path": f"objects/sha256/{sha256[:2]}/{sha256}.svg",
            }
        },
        "posts": {
            key: {
                "assets": {},
                "diagrams": {"hero": source},
                "og": source,
            }
        },
    }


def installSnapshot(monkeypatch, paths: set[str], texts: dict[str, str]) -> None:
    monkeypatch.setattr(gate, "snapshotPaths", lambda sourceRef: paths)
    monkeypatch.setattr(
        gate,
        "snapshotTexts",
        lambda requestedPaths, sourceRef: {path: texts.get(path) for path in requestedPaths},
    )


def test_tracked_media_is_blocked_anywhere_inside_post() -> None:
    assert gate.isTrackedMediaPath("blog/08-tech-story/01-topic/assets/hero.svg")
    assert gate.isTrackedMediaPath("blog/08-tech-story/01-topic/hero.svg")
    assert gate.isTrackedMediaPath("blog/08-tech-story/01-topic/figures/hero.avif")
    assert gate.isTrackedMediaPath("landing/static/thumbnails/topic.webp")
    assert not gate.isTrackedMediaPath("landing/static/avatar-chart.png")
    assert not gate.isTrackedMediaPath("blog/08-tech-story/01-topic/index.md")


def test_snapshot_rejects_local_rendered_media(monkeypatch) -> None:
    indexPath = "blog/08-tech-story/01-topic/index.md"
    catalog = catalogFor(indexPath)
    texts = {
        indexPath: "---\nogImage: /thumbnails/topic.webp\n---\n![장면](./assets/hero.svg)\n",
        gate.CATALOG_PATH: json.dumps(catalog),
    }
    installSnapshot(monkeypatch, set(texts), texts)

    errors = gate.validateSnapshot("HEAD")

    assert any("/thumbnails/topic.webp" in error for error in errors)
    assert any("./assets/hero.svg" in error for error in errors)


def test_snapshot_accepts_only_mapped_canonical_hf_url(monkeypatch) -> None:
    indexPath = "blog/08-tech-story/01-topic/index.md"
    sha256 = "a" * 64
    catalog = catalogFor(indexPath, sha256)
    url = f"{gate.HF_OBJECT_URL_PREFIX}{sha256[:2]}/{sha256}.svg"
    texts = {
        indexPath: f"---\nogImage: {url}\n---\n![장면]({url})\n",
        gate.CATALOG_PATH: json.dumps(catalog),
    }
    installSnapshot(monkeypatch, set(texts), texts)

    assert gate.validateSnapshot("HEAD") == []


def test_snapshot_rejects_hf_object_outside_post_mapping(monkeypatch) -> None:
    indexPath = "blog/08-tech-story/01-topic/index.md"
    catalog = catalogFor(indexPath)
    otherSha = "b" * 64
    url = f"{gate.HF_OBJECT_URL_PREFIX}{otherSha[:2]}/{otherSha}.svg"
    texts = {
        indexPath: f"![장면]({url})\n",
        gate.CATALOG_PATH: json.dumps(catalog),
    }
    installSnapshot(monkeypatch, set(texts), texts)

    errors = gate.validateSnapshot("HEAD")

    assert any("매핑 밖 HF 객체" in error for error in errors)


def test_shared_ui_avatar_is_the_only_local_rendered_exception(monkeypatch) -> None:
    indexPath = "blog/01-reading-disclosures/01-topic/index.md"
    texts = {
        indexPath: "![안내](/avatar-chart.png)\n",
        gate.CATALOG_PATH: json.dumps(
            {
                "repo": gate.HF_REPO,
                "objectPrefix": gate.HF_OBJECT_PREFIX,
                "files": {},
                "objects": {},
                "posts": {},
            }
        ),
    }
    installSnapshot(monkeypatch, set(texts), texts)

    assert gate.validateSnapshot("HEAD") == []


def test_staged_scope_checks_only_changed_post_unless_catalog_changes(monkeypatch) -> None:
    firstIndex = "blog/08-tech-story/01-first/index.md"
    secondIndex = "blog/08-tech-story/02-second/index.md"
    catalog = catalogFor(firstIndex)
    sha256 = "a" * 64
    firstUrl = f"{gate.HF_OBJECT_URL_PREFIX}{sha256[:2]}/{sha256}.svg"
    texts = {
        firstIndex: f"![첫 장면]({firstUrl})\n",
        secondIndex: "![둘째 장면](./assets/second.svg)\n",
        gate.CATALOG_PATH: json.dumps(catalog),
    }
    installSnapshot(monkeypatch, set(texts), texts)

    scopedErrors = gate.validateSnapshot("INDEX", changedPaths={firstIndex})
    catalogErrors = gate.validateSnapshot("INDEX", changedPaths={gate.CATALOG_PATH})

    assert scopedErrors == []
    assert any("./assets/second.svg" in error for error in catalogErrors)


def test_staged_catalog_deletion_is_blocked(monkeypatch) -> None:
    indexPath = "blog/08-tech-story/01-topic/index.md"
    texts = {indexPath: "![안내](/avatar-chart.png)\n"}
    installSnapshot(monkeypatch, {indexPath}, texts)

    errors = gate.validateSnapshot("INDEX", changedPaths={gate.CATALOG_PATH})

    assert errors == ["media/catalog.json 중앙 카탈로그가 없음"]
