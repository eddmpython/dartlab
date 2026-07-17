"""중앙 카탈로그가 가리키는 HF 블로그 미디어를 로컬 staging으로 복원한다."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from blogMedia import loadMediaCatalog, mediaRecord
from huggingface_hub import hf_hub_download

from dartlab.core.dataConfig import HF_MEDIA_REPO

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "media" / "catalog.json"


def selectedSources(catalog: dict[str, object], post: str | None) -> list[str]:
    files = catalog.get("files")
    posts = catalog.get("posts")
    if not isinstance(files, dict) or not isinstance(posts, dict):
        raise ValueError("media/catalog.json files/posts 계약 위반")
    if post is None:
        return sorted(str(source) for source in files)
    normalized = post.replace("\\", "/").strip("/")
    if normalized.startswith("blog/"):
        normalized = normalized.removeprefix("blog/")
    entry = posts.get(normalized)
    if not isinstance(entry, dict):
        raise ValueError(f"media/catalog.json에 글 매핑 없음: {normalized}")
    sources = set(str(source) for source in entry.get("staging", []) if source)
    if entry.get("og"):
        sources.add(str(entry["og"]))
    if entry.get("card"):
        sources.add(str(entry["card"]))
    return sorted(sources)


def seed(catalog: dict[str, object], sources: list[str], *, force: bool = False) -> int:
    copied = 0
    for source in sources:
        target = (REPO_ROOT / source).resolve()
        try:
            target.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"저장소 밖 staging 경로: {source}") from exc
        record = mediaRecord(catalog, source)
        if record is None:
            raise ValueError(f"media/catalog.json 객체 매핑 없음: {source}")
        if target.is_file() and not force:
            continue
        cached = hf_hub_download(repo_id=HF_MEDIA_REPO, repo_type="dataset", filename=record["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cached, target)
        copied += 1
    return copied


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HF 블로그 미디어를 무시된 로컬 staging 파일로 복원한다.")
    parser.add_argument("--post", help="blog 기준 category/post 또는 저장소 기준 blog/category/post")
    parser.add_argument("--all", action="store_true", help="카탈로그의 모든 staging 파일 복원")
    parser.add_argument("--force", action="store_true", help="이미 있는 staging 파일도 덮어씀")
    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    if bool(args.post) == bool(args.all):
        raise SystemExit("--post 또는 --all 중 하나만 지정해야 함")
    catalog, errors = loadMediaCatalog(CATALOG_PATH)
    if catalog is None or errors:
        raise SystemExit("; ".join(errors))
    sources = selectedSources(catalog, args.post if args.post else None)
    copied = seed(catalog, sources, force=args.force)
    print(f"HF staging 복원: 선택 {len(sources)}개, 내려받음 {copied}개")


if __name__ == "__main__":
    main()
