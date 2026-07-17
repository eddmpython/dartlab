"""블로그 HF 미디어 발행기 테스트."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import publishBlogAssets as publisher  # noqa: E402


class FakeApi:
    def __init__(self, *, exists: bool = False) -> None:
        self.exists = exists
        self.commits: list[dict[str, object]] = []

    def file_exists(self, **kwargs: object) -> bool:
        return self.exists

    def create_commit(self, **kwargs: object) -> None:
        self.commits.append(kwargs)


def writePost(root: Path) -> Path:
    postDir = root / "blog" / "08-tech-story" / "01-hf-only"
    assetsDir = postDir / "assets"
    assetsDir.mkdir(parents=True)
    (assetsDir / "hero-scene.webp").write_bytes(b"hero")
    (assetsDir / "mechanism-map.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="4" y="20">원리</text></svg>',
        encoding="utf-8",
    )
    (assetsDir / "CREDITS.md").write_text(
        "- hero-scene: 생성 이미지\n- mechanism-map.svg: 프로젝트 제작 도해\n",
        encoding="utf-8",
    )
    (postDir / "brief.json").write_text(
        json.dumps(
            {
                "contractVersion": 2,
                "imagePlan": [
                    {"assetKey": "hero-scene", "sourcePolicy": "auto", "slot": "hero"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (postDir / "index.md").write_text(
        "---\nogImage: /thumbnails/tech-hf-only.webp\n---\n\n"
        "![hero](./assets/hero-scene.webp)\n\n![원리](./assets/mechanism-map.svg)\n",
        encoding="utf-8",
    )
    thumbDir = root / "landing" / "static" / "thumbnails"
    thumbDir.mkdir(parents=True)
    (thumbDir / "tech-hf-only.webp").write_bytes(b"og")
    (thumbDir / "tech-hf-only-card.webp").write_bytes(b"card")
    return postDir


def test_publish_assets_uploads_hashed_media_and_rewrites_refs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    postDir = writePost(tmp_path)
    api = FakeApi()

    manifest = publisher.publishAssets(postDir, api=api)

    heroSha = hashlib.sha256(b"hero").hexdigest()
    ogSha = hashlib.sha256(b"og").hexdigest()
    cardSha = hashlib.sha256(b"card").hexdigest()
    svgBytes = (postDir / "assets" / "mechanism-map.svg").read_bytes()
    svgSha = hashlib.sha256(svgBytes).hexdigest()
    heroPath = f"objects/sha256/{heroSha[:2]}/{heroSha}.webp"
    ogPath = f"objects/sha256/{ogSha[:2]}/{ogSha}.webp"
    assert manifest["assets"]["hero-scene"]["path"] == heroPath
    assert manifest["og"]["path"] == ogPath
    assert manifest["card"]["path"] == f"objects/sha256/{cardSha[:2]}/{cardSha}.webp"
    assert manifest["diagrams"]["mechanism-map"]["path"] == f"objects/sha256/{svgSha[:2]}/{svgSha}.svg"
    assert len(api.commits) == 1
    assert len(api.commits[0]["operations"]) == 4
    saved = json.loads((tmp_path / "media" / "catalog.json").read_text(encoding="utf-8"))
    assert saved["posts"]["08-tech-story/01-hf-only"]["assets"]["hero-scene"].endswith("hero-scene.webp")
    assert saved["posts"]["08-tech-story/01-hf-only"]["diagrams"]["mechanism-map"].endswith("mechanism-map.svg")
    assert saved["objects"][svgSha]["mediaType"] == "image/svg+xml"
    assert saved["objects"][svgSha]["textNodes"] == 1
    assert set(saved["objects"]) == {heroSha, ogSha, cardSha, svgSha}
    body = (postDir / "index.md").read_text(encoding="utf-8")
    assert "./assets/hero-scene.webp" not in body
    assert heroPath in body
    assert f"objects/sha256/{svgSha[:2]}/{svgSha}.svg" in body
    assert f"ogImage: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/{ogPath}" in body
    assert f"objects/sha256/{cardSha[:2]}/{cardSha}.webp" in body


def test_dry_run_does_not_write_manifest(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    postDir = writePost(tmp_path)

    manifest = publisher.publishAssets(postDir, dryRun=True)

    assert manifest["assets"]
    assert not (tmp_path / "media" / "catalog.json").exists()


def test_dry_run_supports_planned_gif(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    postDir = writePost(tmp_path)
    webp = postDir / "assets" / "hero-scene.webp"
    gif = webp.with_suffix(".gif")
    webp.rename(gif)
    indexPath = postDir / "index.md"
    updated = indexPath.read_text(encoding="utf-8").replace("hero-scene.webp", "hero-scene.gif")
    indexPath.write_text(updated, encoding="utf-8")

    manifest = publisher.publishAssets(postDir, dryRun=True)

    assert manifest["assets"]["hero-scene"]["path"].endswith(".gif")


def test_publish_assets_is_idempotent_without_local_staging(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    postDir = writePost(tmp_path)
    publisher.publishAssets(postDir, api=FakeApi())
    (postDir / "assets" / "hero-scene.webp").unlink()
    (postDir / "assets" / "mechanism-map.svg").unlink()
    (tmp_path / "landing" / "static" / "thumbnails" / "tech-hf-only.webp").unlink()
    (tmp_path / "landing" / "static" / "thumbnails" / "tech-hf-only-card.webp").unlink()
    api = FakeApi(exists=True)

    manifest = publisher.publishAssets(postDir, api=api)

    assert manifest["assets"]["hero-scene"]["path"].startswith("objects/sha256/")
    assert api.commits == []


def test_verify_remote_assets_fails_closed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    postDir = writePost(tmp_path)
    publisher.publishAssets(postDir, api=FakeApi())

    errors = publisher.verifyRemoteAssets(postDir, api=FakeApi(exists=False))

    assert len(errors) == 4
    assert all("HF 미디어 없음" in error for error in errors)
