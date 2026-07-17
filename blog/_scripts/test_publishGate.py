"""단일 블로그 발행 게이트 테스트."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import publishGate as pg  # noqa: E402


def test_post_dirs_from_paths_keeps_only_content_posts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pg, "REPO_ROOT", tmp_path)
    postDir = tmp_path / "blog" / "08-tech-story" / "14-new-tech"
    postDir.mkdir(parents=True)
    (postDir / "index.md").write_text("---\ncategory: tech-story\n---\n", encoding="utf-8")

    posts = pg.postDirsFromPaths(
        [
            "blog/08-tech-story/14-new-tech/index.md",
            "blog/08-tech-story/14-new-tech/assets/hero.webp",
            "blog/PIPELINE.md",
            "landing/src/routes/+page.svelte",
        ]
    )

    assert posts == [postDir]


def test_validate_post_combines_hard_gate_and_seo(monkeypatch, tmp_path: Path) -> None:
    captured: list[bool] = []

    def fakeAudit(postDir: Path, *, requireContractV2: bool) -> list[str]:
        captured.append(requireContractV2)
        return ["하드 게이트 실패"]

    monkeypatch.setattr(pg, "auditPublishGate", fakeAudit)
    monkeypatch.setattr(pg, "scorePost", lambda _: {"pct": 94})

    errors = pg.validatePost(tmp_path, requireContractV2=True)

    assert captured == [True]
    assert errors == ["하드 게이트 실패", "SEO 점수 94% < 95%"]


def test_validate_post_passes_at_95(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pg, "auditPublishGate", lambda *args, **kwargs: [])
    monkeypatch.setattr(pg, "scorePost", lambda _: {"pct": 95})

    assert pg.validatePost(tmp_path, requireContractV2=False) == []


def test_validate_post_includes_hf_remote_errors(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pg, "auditPublishGate", lambda *args, **kwargs: [])
    monkeypatch.setattr(pg, "scorePost", lambda _: {"pct": 95})
    monkeypatch.setattr(pg, "verifyRemoteAssets", lambda _: ["HF 미디어 없음: blog/x/hero.12345678.webp"])

    errors = pg.validatePost(tmp_path, requireContractV2=True)

    assert errors == ["HF 미디어 없음: blog/x/hero.12345678.webp"]


def test_changed_posts_include_deleted_assets(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pg, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pg, "_normalizeBase", lambda baseRef, headRef: "base-sha")
    postDir = tmp_path / "blog" / "08-tech-story" / "14-new-tech"
    postDir.mkdir(parents=True)
    (postDir / "index.md").write_text("---\ncategory: tech-story\n---\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def fakeGit(*args: str, check: bool = True):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="blog/08-tech-story/14-new-tech/assets/hero.webp\n")

    monkeypatch.setattr(pg, "_git", fakeGit)

    baseRef, posts = pg.changedPostDirs("before", "after")

    assert baseRef == "base-sha"
    assert posts == [postDir]
    assert "--diff-filter=ACDMRT" in calls[0]


def test_existed_at_ref_uses_index_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pg, "REPO_ROOT", tmp_path)
    postDir = tmp_path / "blog" / "08-tech-story" / "14-new-tech"
    calls: list[tuple[str, ...]] = []

    def fakeGit(*args: str, check: bool = True):
        calls.append(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(pg, "_git", fakeGit)

    assert pg.existedAtRef(postDir, "base-sha")
    assert calls == [("cat-file", "-e", "base-sha:blog/08-tech-story/14-new-tech/index.md")]


def test_tracked_binary_errors_blocks_v2_git_images(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pg, "REPO_ROOT", tmp_path)
    postDir = tmp_path / "blog" / "08-tech-story" / "14-new-tech"
    assetsDir = postDir / "assets"
    assetsDir.mkdir(parents=True)
    (assetsDir / "media.json").write_text("{}", encoding="utf-8")

    def fakeGit(*args: str, check: bool = True):
        return SimpleNamespace(returncode=0, stdout="blog/08-tech-story/14-new-tech/assets/hero.webp\n")

    monkeypatch.setattr(pg, "_git", fakeGit)

    errors = pg.trackedBinaryErrors(postDir)

    assert errors == [
        "contract v2 바이너리는 Git 추적 금지, HF에만 발행: blog/08-tech-story/14-new-tech/assets/hero.webp"
    ]
