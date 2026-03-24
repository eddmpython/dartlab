"""CI용 데이터 수집 래퍼.

흐름:
  1. HuggingFace에서 기존 parquet을 git clone (LFS shallow)
  2. DART API로 증분 수집 (기존 데이터에 없는 기간만)
  3. 변경된 parquet 업로드 (uploadData.py가 담당)

환경변수:
  DART_API_KEYS: DART OpenAPI 키 (쉼표 구분)
  SYNC_CATEGORY: finance / report / docs
  SYNC_MODE: new / all
  DARTLAB_DATA_DIR: 데이터 저장 경로 (기본: ./data)
"""

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


def main():
    category = os.environ.get("SYNC_CATEGORY", "finance")
    mode = os.environ.get("SYNC_MODE", "new")
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

    # 2단계: 증분 수집
    start = time.time()

    from dartlab.engines.company.dart.openapi.batch import batchCollectAll

    results = batchCollectAll(
        categories=[category],
        mode=mode,
        incremental=True,
        showProgress=False,
    )

    elapsed = time.time() - start
    totalRows = sum(r.get(category, 0) for r in results.values())
    print(f"[syncData] 완료: {len(results)}개 종목 수집, {totalRows}행, {elapsed:.0f}초")

    # GitHub Actions summary
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if summaryPath:
        with open(summaryPath, "a", encoding="utf-8") as f:
            f.write(f"## Data Sync: {category}\n\n")
            f.write(f"- **모드**: {mode}\n")
            f.write(f"- **기존 데이터 (HF)**: {existingCount}개\n")
            f.write(f"- **신규 수집**: {len(results)}개 종목\n")
            f.write(f"- **총 행 수**: {totalRows:,}\n")
            f.write(f"- **소요 시간**: {elapsed:.0f}초\n")


if __name__ == "__main__":
    main()
