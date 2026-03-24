"""수집된 parquet을 HuggingFace 또는 GitHub Releases에 업로드.

사용법:
  python uploadData.py --target hf    # HuggingFace 업로드
  python uploadData.py --target gh    # GitHub Releases 업로드

환경변수:
  HF_TOKEN: HuggingFace write 토큰 (--target hf)
  GH_TOKEN: GitHub 토큰 (--target gh, Actions에서 자동 제공)
  SYNC_CATEGORY: finance / report / docs
  DARTLAB_DATA_DIR: 데이터 경로 (기본: ./data)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _dataDir(category: str) -> Path:
    """수집된 parquet 디렉토리."""
    from dartlab.core.dataConfig import DATA_RELEASES

    base = Path(os.environ.get("DARTLAB_DATA_DIR", os.path.join(os.getcwd(), "data")))
    return base / DATA_RELEASES[category]["dir"]


def _uploadHf(category: str) -> None:
    """HuggingFace에 카테고리 폴더 업로드."""
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        print("[uploadData] HF_TOKEN 환경변수가 필요합니다.")
        sys.exit(1)

    from huggingface_hub import HfApi

    from dartlab.core.dataConfig import DATA_RELEASES, HF_REPO

    api = HfApi(token=token)
    dirPath = DATA_RELEASES[category]["dir"]
    localDir = _dataDir(category)

    files = list(localDir.glob("*.parquet"))
    if not files:
        print(f"[uploadData] {localDir}에 업로드할 파일 없음")
        return

    print(f"[uploadData] HuggingFace 업로드: {len(files)}개 파일 → {HF_REPO}/{dirPath}/")

    api.upload_folder(
        repo_id=HF_REPO,
        repo_type="dataset",
        folder_path=str(localDir),
        path_in_repo=dirPath,
        commit_message=f"sync {category}: {len(files)} files",
    )

    print(f"[uploadData] HuggingFace 업로드 완료")


def _uploadGh(category: str) -> None:
    """GitHub Releases에 shard별 업로드."""
    from dartlab.core.dataConfig import DATA_RELEASES, shardTag

    conf = DATA_RELEASES[category]
    localDir = _dataDir(category)
    files = list(localDir.glob("*.parquet"))

    if not files:
        print(f"[uploadData] {localDir}에 업로드할 파일 없음")
        return

    if "shards" in conf:
        # shard별 분류
        shardFiles: dict[str, list[Path]] = {}
        for f in files:
            stockCode = f.stem
            tag = shardTag(stockCode, category)
            shardFiles.setdefault(tag, []).append(f)

        for tag, tagFiles in shardFiles.items():
            print(f"[uploadData] GitHub Release {tag}: {len(tagFiles)}개 파일")
            _ghReleaseUpload(tag, tagFiles)
    else:
        tag = conf["tag"]
        print(f"[uploadData] GitHub Release {tag}: {len(files)}개 파일")
        _ghReleaseUpload(tag, files)

    print(f"[uploadData] GitHub Releases 업로드 완료")


def _ghReleaseUpload(tag: str, files: list[Path]) -> None:
    """gh CLI로 릴리즈에 파일 업로드. 릴리즈가 없으면 생성."""
    # 릴리즈 존재 확인
    check = subprocess.run(
        ["gh", "release", "view", tag],
        capture_output=True, text=True,
    )
    if check.returncode != 0:
        subprocess.run(
            ["gh", "release", "create", tag,
             "--title", f"Data: {tag}",
             "--notes", f"자동 데이터 동기화 ({tag})",
             "--latest=false"],
            check=True,
        )

    # 배치 업로드 (gh release upload은 여러 파일 한번에 가능)
    batchSize = 50
    for i in range(0, len(files), batchSize):
        batch = files[i:i + batchSize]
        cmd = ["gh", "release", "upload", tag, "--clobber"] + [str(f) for f in batch]
        subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=["hf", "gh"])
    args = parser.parse_args()

    category = os.environ.get("SYNC_CATEGORY", "finance")

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")

    if args.target == "hf":
        _uploadHf(category)
    else:
        _uploadGh(category)


if __name__ == "__main__":
    main()
