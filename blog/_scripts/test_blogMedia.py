"""블로그 중앙 미디어 카탈로그와 일괄 이관 회귀 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import migrateBlogMedia as migration  # noqa: E402
import seedBlogMedia as seeder  # noqa: E402
from blogMedia import loadMediaManifest, mediaUrl, saveMediaCatalog  # noqa: E402


def writeLegacyPost(root: Path, category: str, name: str, payload: bytes) -> tuple[Path, Path, Path, Path]:
    postDir = root / "blog" / category / name
    assetsDir = postDir / "assets"
    assetsDir.mkdir(parents=True)
    assetPath = assetsDir / "hero.webp"
    assetPath.write_bytes(payload)
    thumbPath = root / "landing" / "static" / "thumbnails" / f"{name}.webp"
    thumbPath.parent.mkdir(parents=True, exist_ok=True)
    thumbPath.write_bytes(payload)
    cardPath = thumbPath.with_name(f"{thumbPath.stem}-card.webp")
    cardPath.write_bytes(payload)
    (postDir / "index.md").write_text(
        f"---\nogImage: /thumbnails/{name}.webp\nthumbnail: /thumbnails/{name}.webp\n---\n"
        "\n![장면](./assets/hero.webp)\n",
        encoding="utf-8",
    )
    return postDir, assetPath, thumbPath, cardPath


def test_migration_deduplicates_bytes_and_builds_central_views(monkeypatch, tmp_path: Path) -> None:
    firstPost, firstAsset, firstThumb, firstCard = writeLegacyPost(tmp_path, "08-tech-story", "01-first", b"same")
    secondPost, secondAsset, secondThumb, secondCard = writeLegacyPost(
        tmp_path, "05-company-reports", "01-second", b"same"
    )
    monkeypatch.setattr(migration, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(migration, "CATALOG_PATH", tmp_path / "media" / "catalog.json")

    catalog, localByRemote, rewritten = migration.buildCatalog(
        [firstAsset, firstThumb, firstCard, secondAsset, secondThumb, secondCard]
    )

    assert len(catalog["objects"]) == 1
    assert len(catalog["files"]) == 6
    assert len(localByRemote) == 1
    saveMediaCatalog(tmp_path / "media" / "catalog.json", catalog)
    firstManifest, errors = loadMediaManifest(firstPost)
    assert errors == []
    assert firstManifest is not None
    objectUrl = mediaUrl(firstManifest["assets"]["hero"]["path"])
    assert objectUrl in rewritten[firstPost / "index.md"]
    assert objectUrl in rewritten[secondPost / "index.md"]
    assert "/thumbnails/" not in rewritten[firstPost / "index.md"]
    assert "cardPreview: https://" in rewritten[firstPost / "index.md"]
    assert catalog["posts"]["08-tech-story/01-first"]["card"].endswith("-card.webp")


def test_migration_keeps_avatar_thumbnail_local(monkeypatch, tmp_path: Path) -> None:
    postDir, assetPath, thumbPath, cardPath = writeLegacyPost(tmp_path, "08-tech-story", "01-first", b"image")
    indexPath = postDir / "index.md"
    indexPath.write_text(
        indexPath.read_text(encoding="utf-8").replace(
            "thumbnail: /thumbnails/01-first.webp", "thumbnail: /avatar-study.png"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(migration, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(migration, "CATALOG_PATH", tmp_path / "media" / "catalog.json")

    _, _, rewritten = migration.buildCatalog([assetPath, thumbPath, cardPath])

    assert "thumbnail: /avatar-study.png" in rewritten[indexPath]


def test_seed_restores_post_staging_from_catalog(monkeypatch, tmp_path: Path) -> None:
    postDir, assetPath, thumbPath, cardPath = writeLegacyPost(tmp_path, "08-tech-story", "01-first", b"image")
    monkeypatch.setattr(migration, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(migration, "CATALOG_PATH", tmp_path / "media" / "catalog.json")
    catalog, _, _ = migration.buildCatalog([assetPath, thumbPath, cardPath])
    source = assetPath.relative_to(tmp_path).as_posix()
    cached = tmp_path / "cache.webp"
    cached.write_bytes(b"image")
    assetPath.unlink()
    monkeypatch.setattr(seeder, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(seeder, "hf_hub_download", lambda **_: str(cached))

    copied = seeder.seed(catalog, [source])

    assert copied == 1
    assert assetPath.read_bytes() == b"image"
    assert postDir.is_dir()
