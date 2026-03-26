"""CI용 EDGAR docs 수집 래퍼.

흐름:
  1. HuggingFace에서 기존 parquet을 git clone (LFS shallow)
  2. 대상 ticker 목록 로드 (edgarTickers.json)
  3. ticker별 fetchEdgarDocs() 호출 (증분)
  4. 변경된 parquet만 changed.txt에 기록 → uploadData.py가 참조

환경변수:
  EDGAR_TIER: sp500 (기본) — edgarTickers.json의 키
  EDGAR_BATCH_OFFSET: 시작 오프셋 (기본: 0)
  EDGAR_BATCH_SIZE: 한 번에 처리할 ticker 수 (기본: 100)
  DARTLAB_DATA_DIR: 데이터 저장 경로 (기본: ./data)
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TICKERS_FILE = SCRIPT_DIR.parent / "data" / "edgarTickers.json"


def _loadTickers(tier: str) -> list[str]:
    """edgarTickers.json에서 tier별 ticker 목록 로드."""
    if not TICKERS_FILE.exists():
        print(f"[edgarSync] ticker 파일 없음: {TICKERS_FILE}")
        sys.exit(1)
    data = json.loads(TICKERS_FILE.read_text(encoding="utf-8"))
    tickers = data.get(tier, [])
    if not tickers:
        print(f"[edgarSync] tier '{tier}'에 해당하는 ticker 없음")
        sys.exit(1)
    return tickers


def _cloneExisting(dataDir: str) -> int:
    """HuggingFace repo를 shallow clone해서 기존 edgar docs parquet 확보."""
    from dartlab.core.dataConfig import DATA_RELEASES

    dirPath = DATA_RELEASES["edgarDocs"]["dir"]
    localDir = Path(dataDir) / dirPath
    localDir.mkdir(parents=True, exist_ok=True)

    cloneDir = Path(dataDir) / "_hf_clone"
    if cloneDir.exists():
        shutil.rmtree(cloneDir)

    print("[edgarSync] HuggingFace shallow clone 시작...")
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "https://huggingface.co/datasets/eddmpython/dartlab-data", str(cloneDir)],
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        print(f"[edgarSync] clone 실패: {result.stderr}")
        return 0

    print(f"[edgarSync] LFS pull: {dirPath}/*.parquet")
    subprocess.run(
        ["git", "lfs", "pull", "--include", f"{dirPath}/*.parquet"],
        cwd=str(cloneDir),
        capture_output=True,
        text=True,
    )

    srcDir = cloneDir / dirPath
    if srcDir.exists():
        count = 0
        for f in srcDir.glob("*.parquet"):
            dest = localDir / f.name
            if not dest.exists():
                shutil.copy2(f, dest)
                count += 1
        existing = len(list(localDir.glob("*.parquet")))
        print(f"[edgarSync] 복사 완료: {count}개 신규, 총 {existing}개")
    else:
        existing = 0
        print(f"[edgarSync] HF에 {dirPath} 디렉토리 없음")

    shutil.rmtree(cloneDir, ignore_errors=True)
    return existing


def _fileHash(path: Path) -> str:
    """파일 SHA-256 해시 (첫 64KB + 파일크기)."""
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
    tier = os.environ.get("EDGAR_TIER", "sp500")
    batchOffset = int(os.environ.get("EDGAR_BATCH_OFFSET", "0"))
    batchSize = int(os.environ.get("EDGAR_BATCH_SIZE", "100"))

    if "DARTLAB_DATA_DIR" not in os.environ:
        os.environ["DARTLAB_DATA_DIR"] = os.path.join(os.getcwd(), "data")

    dataDir = os.environ["DARTLAB_DATA_DIR"]
    os.makedirs(dataDir, exist_ok=True)

    # ticker 목록 로드 + 배치 슬라이싱
    allTickers = _loadTickers(tier)
    tickers = allTickers[batchOffset : batchOffset + batchSize]

    if not tickers:
        print(f"[edgarSync] offset {batchOffset}에서 처리할 ticker 없음 (전체 {len(allTickers)}개)")
        return

    print(f"[edgarSync] tier={tier} offset={batchOffset} size={batchSize}")
    print(f"[edgarSync] 대상: {len(tickers)}개 / 전체 {len(allTickers)}개")
    print(f"[edgarSync] 범위: {tickers[0]} ~ {tickers[-1]}")

    # 1단계: 기존 데이터 확보
    from dartlab.core.dataConfig import DATA_RELEASES

    dirPath = DATA_RELEASES["edgarDocs"]["dir"]
    localDir = Path(dataDir) / dirPath
    cachedFiles = list(localDir.glob("*.parquet")) if localDir.exists() else []

    if cachedFiles:
        existingCount = len(cachedFiles)
        print(f"[edgarSync] 캐시에서 {existingCount}개 기존 데이터 발견 → clone 생략")
    else:
        existingCount = _cloneExisting(dataDir)

    # 2단계: 수집 전 해시 스냅샷
    beforeHashes = _snapshotHashes(localDir)

    # 3단계: ticker별 수집
    from dartlab.providers.edgar.docs.fetch import fetchEdgarDocs

    start = time.time()
    succeeded = 0
    failed = 0
    skipped = 0
    failedTickers: list[str] = []

    for i, ticker in enumerate(tickers, 1):
        outPath = localDir / f"{ticker}.parquet"

        # 이미 있으면 증분 체크 (기존 파일의 최신 filing 연도 확인)
        if outPath.exists():
            skipped += 1
            continue

        print(f"[edgarSync] [{i}/{len(tickers)}] {ticker} 수집 중...")
        try:
            fetchEdgarDocs(
                ticker,
                outPath,
                showProgress=False,
                strictQuality=False,
            )
            succeeded += 1
            print(f"[edgarSync] {ticker} 완료")
        except (ValueError, KeyError, RuntimeError, OSError, TimeoutError) as e:
            failed += 1
            failedTickers.append(ticker)
            print(f"[edgarSync] {ticker} 실패: {e}")
            continue

    elapsed = time.time() - start

    # 4단계: 변경 파일 감지
    afterHashes = _snapshotHashes(localDir)
    newFiles = [f for f in afterHashes if f not in beforeHashes]
    updatedFiles = [f for f in afterHashes if f in beforeHashes and afterHashes[f] != beforeHashes[f]]
    changedFiles = newFiles + updatedFiles

    # changed.txt 기록
    distDir = Path("dist")
    distDir.mkdir(exist_ok=True)
    changedPath = distDir / "changed.txt"
    changedPath.write_text("\n".join(changedFiles), encoding="utf-8")

    print(f"\n[edgarSync] 완료: {succeeded}개 성공, {skipped}개 스킵, {failed}개 실패, {elapsed:.0f}초")
    print(f"[edgarSync] 변경: 신규 {len(newFiles)}개 + 업데이트 {len(updatedFiles)}개 = {len(changedFiles)}개")

    if failedTickers:
        print(f"[edgarSync] 실패 목록: {', '.join(failedTickers[:20])}")

    # GitHub Actions summary
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if summaryPath:
        with open(summaryPath, "a", encoding="utf-8") as f:
            f.write(f"## EDGAR Docs Sync: {tier}\n\n")
            f.write("| 항목 | 값 |\n|------|----|\n")
            f.write(f"| Tier | {tier} |\n")
            f.write(f"| Batch | offset={batchOffset}, size={batchSize} |\n")
            f.write(f"| 대상 ticker | {len(tickers)}개 |\n")
            f.write(f"| 성공 | {succeeded}개 |\n")
            f.write(f"| 스킵 (기존) | {skipped}개 |\n")
            f.write(f"| 실패 | {failed}개 |\n")
            f.write(f"| 신규 파일 | {len(newFiles)}개 |\n")
            f.write(f"| 소요 시간 | {elapsed:.0f}초 |\n")


if __name__ == "__main__":
    main()
