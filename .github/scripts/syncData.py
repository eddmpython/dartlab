"""CI용 데이터 수집 래퍼.

흐름:
  1. HuggingFace에서 기존 parquet을 git clone (LFS shallow)
  2. DART API로 증분 수집 (기존 데이터에 없는 기간만)
  3. 변경된 parquet만 changed.txt에 기록 → uploadData.py가 참조

환경변수:
  DART_API_KEYS: DART OpenAPI 키 (쉼표 구분)
  SYNC_CATEGORY: finance / report / docs
  SYNC_MODE: all (전 종목 증분) / new (파일 없는 종목만)
  DARTLAB_DATA_DIR: 데이터 저장 경로 (기본: ./data)
"""

import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _cloneExisting(category: str, dataDir: str) -> int:
    """HuggingFace repo를 shallow clone해서 기존 parquet 확보."""
    from dartlab.core.dataConfig import DATA_RELEASES

    dirPath = DATA_RELEASES[category]["dir"]
    localDir = Path(dataDir) / dirPath
    localDir.mkdir(parents=True, exist_ok=True)

    cloneDir = Path(dataDir) / "_hf_clone"

    if cloneDir.exists():
        shutil.rmtree(cloneDir)

    print(f"[syncData] HuggingFace shallow clone 시작...")
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    result = subprocess.run(
        ["git", "clone", "--depth", "1",
         "https://huggingface.co/datasets/eddmpython/dartlab-data",
         str(cloneDir)],
        capture_output=True, text=True, env=env,
    )

    if result.returncode != 0:
        print(f"[syncData] clone 실패: {result.stderr}")
        return 0

    # 해당 카테고리만 LFS pull
    print(f"[syncData] LFS pull: {dirPath}/*.parquet")
    subprocess.run(
        ["git", "lfs", "pull", "--include", f"{dirPath}/*.parquet"],
        cwd=str(cloneDir), capture_output=True, text=True,
    )

    # clone에서 데이터 디렉토리로 복사
    srcDir = cloneDir / dirPath
    if srcDir.exists():
        count = 0
        for f in srcDir.glob("*.parquet"):
            dest = localDir / f.name
            if not dest.exists():
                shutil.copy2(f, dest)
                count += 1
        existing = len(list(localDir.glob("*.parquet")))
        print(f"[syncData] 복사 완료: {count}개 신규, 총 {existing}개")
    else:
        existing = 0
        print(f"[syncData] HF에 {dirPath} 디렉토리 없음")

    # clone 정리
    shutil.rmtree(cloneDir, ignore_errors=True)
    return existing


def _fileHash(path: Path) -> str:
    """파일 SHA-256 해시 (첫 64KB만 — 빠른 변경 감지용)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(65536))
        h.update(str(path.stat().st_size).encode())
    return h.hexdigest()


def _snapshotHashes(directory: Path) -> dict[str, str]:
    """디렉토리 내 parquet 파일 해시 스냅샷."""
    if not directory.exists():
        return {}
    return {f.name: _fileHash(f) for f in directory.glob("*.parquet")}


def main():
    category = os.environ.get("SYNC_CATEGORY", "finance")
    mode = os.environ.get("SYNC_MODE", "all")
    keys = os.environ.get("DART_API_KEYS", "")

    if not keys:
        print("DART_API_KEYS 환경변수가 필요합니다.")
        sys.exit(1)

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")

    dataDir = os.environ["DARTLAB_DATA_DIR"]
    os.makedirs(dataDir, exist_ok=True)

    print(f"[syncData] category={category} mode={mode} dataDir={dataDir}")
    print(f"[syncData] API 키 {len(keys.split(','))}개 감지")

    # 1단계: 기존 데이터 확보 (캐시 있으면 건너뜀, 없으면 HF clone)
    from dartlab.core.dataConfig import DATA_RELEASES

    dirPath = DATA_RELEASES[category]["dir"]
    localDir = Path(dataDir) / dirPath
    cachedFiles = list(localDir.glob("*.parquet")) if localDir.exists() else []

    if cachedFiles:
        existingCount = len(cachedFiles)
        print(f"[syncData] 캐시에서 {existingCount}개 기존 데이터 발견 → clone 생략")
    else:
        existingCount = _cloneExisting(category, dataDir)
    print(f"[syncData] 기존 데이터 {existingCount}개 확보 → 증분 수집 시작")

    # 2단계: 수집 전 해시 스냅샷
    beforeHashes = _snapshotHashes(localDir)

    # 3단계: 증분 수집
    start = time.time()

    from dartlab.engines.company.dart.openapi.batch import batchCollectAll

    results = batchCollectAll(
        categories=[category],
        mode=mode,
        incremental=True,
        showProgress=False,
    )

    elapsed = time.time() - start

    # 4단계: 변경 파일 감지
    afterHashes = _snapshotHashes(localDir)
    newFiles = [f for f in afterHashes if f not in beforeHashes]
    updatedFiles = [
        f for f in afterHashes
        if f in beforeHashes and afterHashes[f] != beforeHashes[f]
    ]
    changedFiles = newFiles + updatedFiles

    # changed.txt 기록 → uploadData.py가 참조
    distDir = Path("dist")
    distDir.mkdir(exist_ok=True)
    changedPath = distDir / "changed.txt"
    changedPath.write_text("\n".join(changedFiles), encoding="utf-8")

    totalRows = sum(r.get(category, 0) for r in results.values())
    print(f"[syncData] 완료: {len(results)}개 종목 수집, {totalRows}행, {elapsed:.0f}초")
    print(f"[syncData] 변경: 신규 {len(newFiles)}개 + 업데이트 {len(updatedFiles)}개 = {len(changedFiles)}개")

    # GitHub Actions summary
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if summaryPath:
        with open(summaryPath, "a", encoding="utf-8") as f:
            f.write(f"## Data Sync: {category}\n\n")
            f.write(f"| 항목 | 값 |\n|------|----|\n")
            f.write(f"| 모드 | {mode} (incremental) |\n")
            f.write(f"| 기존 데이터 | {existingCount}개 |\n")
            f.write(f"| 수집 대상 종목 | {len(results)}개 |\n")
            f.write(f"| 신규 파일 | {len(newFiles)}개 |\n")
            f.write(f"| 업데이트 파일 | {len(updatedFiles)}개 |\n")
            f.write(f"| 변경 없음 | {len(afterHashes) - len(changedFiles)}개 |\n")
            f.write(f"| 총 행 수 | {totalRows:,} |\n")
            f.write(f"| 소요 시간 | {elapsed:.0f}초 |\n")


if __name__ == "__main__":
    main()
