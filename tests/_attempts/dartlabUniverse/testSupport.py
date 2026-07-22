"""Universe U0 unit test가 공유하는 deterministic authority fixture."""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any


class FakeHttpError(RuntimeError):
    """HTTP status를 노출하는 HF API test error."""

    def __init__(self, statusCode: int):
        super().__init__(f"HTTP {statusCode}")
        self.response = SimpleNamespace(status_code=statusCode)


class FakeHfApi:
    """`repo_info(files_metadata=True)`만 제공하는 metadata-only fake."""

    def __init__(self, repositories: dict[str, dict[str, Any]], failures: dict[str, Exception] | None = None):
        self.repositories = repositories
        self.failures = failures or {}
        self.calls: list[tuple[str, str, bool]] = []
        self._lock = threading.Lock()

    def repo_info(self, repoId: str, *, repo_type: str, files_metadata: bool, revision: str | None = None):
        with self._lock:
            self.calls.append((repoId, repo_type, files_metadata))
        if repoId in self.failures:
            raise self.failures[repoId]
        spec = self.repositories[repoId]
        if revision is not None and revision != spec["revision"]:
            raise FakeHttpError(404)
        siblings = tuple(
            SimpleNamespace(
                rfilename=path,
                size=size,
                blob_id=hashlib.sha256(path.encode("utf-8")).hexdigest(),
                lfs=None,
            )
            for path, size in spec["files"]
        )
        return SimpleNamespace(
            sha=spec["revision"],
            last_modified=datetime(2026, 7, 18, tzinfo=timezone.utc),
            private=bool(spec.get("private", False)),
            siblings=siblings,
        )


def fakeConfig(*, extraRepo: str | None = None) -> SimpleNamespace:
    """동적 configured repo mutation을 지원하는 최소 설정."""
    releases = {
        "panel": {"dir": "dart/panel", "public": True},
        "privateNews": {"dir": "news/private", "repo": "fixture/private", "public": False},
    }
    if extraRepo:
        releases["extra"] = {"dir": "extra/data", "repo": extraRepo, "public": False}
    return SimpleNamespace(
        HF_REPO="fixture/data",
        HF_MEDIA_REPO="fixture/media",
        DATA_RELEASES=releases,
    )


def fakeHfApi(repoRoot: Path, *, extraRepo: str | None = None) -> FakeHfApi:
    """실제 media catalog object 전체를 포함한 deterministic fake tree."""
    catalog = json.loads((repoRoot / "media" / "catalog.json").read_text(encoding="utf-8"))
    mediaFiles = tuple(
        sorted((str(metadata["path"]), int(metadata["bytes"])) for metadata in catalog["objects"].values())
    )
    repositories = {
        "fixture/data": {
            "revision": "a" * 40,
            "files": (
                (".gitattributes", 100),
                ("dart/panel/005930.parquet", 200),
                ("live/orphan.mystery", 300),
            ),
        },
        "fixture/media": {
            "revision": "b" * 40,
            "files": mediaFiles,
        },
        "fixture/private": {
            "revision": "c" * 40,
            "private": True,
            "files": (("news/private/item.json", 400),),
        },
    }
    if extraRepo:
        repositories[extraRepo] = {
            "revision": "d" * 40,
            "private": True,
            "files": (("extra/data/item.json", 500),),
        }
    return FakeHfApi(repositories)
