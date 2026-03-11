"""데이터 로딩 및 공통 유틸."""

import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen, urlretrieve

import polars as pl

from dartlab.core.dataConfig import (
    DATA_RELEASES,
    releaseApiUrl,
    releaseBaseUrl,
    shardAllTags,
)


def _getDataRoot() -> Path:
    from dartlab import config
    return Path(config.dataDir)

_DOWNLOAD_TIMEOUT = 30
_MAX_RETRIES = 3

PERIOD_KINDS = {
    "y": ["annual"],
    "q": ["Q1", "semi", "Q3", "annual"],
    "h": ["semi", "annual"],
}


def _dataDir(category: str = "docs") -> Path:
    return _getDataRoot() / DATA_RELEASES[category]["dir"]


def _downloadWithRetry(url: str, dest: Path) -> None:
    """URL → dest 다운로드. 최대 3회 재시도 (2초, 4초 대기)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    lastErr = None
    for attempt in range(_MAX_RETRIES):
        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(_DOWNLOAD_TIMEOUT)
            urlretrieve(url, dest)
            return
        except (URLError, socket.timeout, OSError) as e:
            lastErr = e
            if dest.exists():
                dest.unlink()
            if attempt < _MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
        finally:
            socket.setdefaulttimeout(old_timeout)
    raise lastErr


def _download(stockCode: str, dest: Path, category: str = "docs") -> None:
    url = f"{releaseBaseUrl(category, stockCode=stockCode)}/{stockCode}.parquet"
    _downloadWithRetry(url, dest)


def loadData(stockCode: str, category: str = "docs") -> pl.DataFrame:
    """종목코드 → DataFrame. 로컬에 없으면 릴리즈에서 자동 다운로드."""
    dataDir = _dataDir(category)
    path = dataDir / f"{stockCode}.parquet"
    if not path.exists():
        label = DATA_RELEASES[category]["label"]
        print(f"[dartlab] {stockCode}.parquet ({label}) 로컬에 없음 → GitHub Release에서 다운로드...")
        try:
            _download(stockCode, path, category)
            print(f"[dartlab] 저장 완료: {path}")
        except (URLError, socket.timeout, OSError) as e:
            if path.exists():
                path.unlink()
            raise RuntimeError(
                f"데이터 다운로드 실패 ({stockCode}): {e}\n"
                f"  해결 방법:\n"
                f"  1. 네트워크 연결 확인\n"
                f"  2. `dartlab download {stockCode}` 명령으로 수동 다운로드\n"
                f"  3. GitHub Releases 페이지에서 직접 다운로드 후 {dataDir}/ 에 배치"
            ) from e
    return pl.read_parquet(str(path))


def _fetchAssets(tag: str) -> list[dict]:
    """릴리즈 태그에서 에셋 목록 + updated_at 조회."""
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(_DOWNLOAD_TIMEOUT)
        with urlopen(releaseApiUrl(tag=tag)) as resp:
            data = json.loads(resp.read())
    finally:
        socket.setdefaulttimeout(old_timeout)
    return [a for a in data["assets"] if a["name"].endswith(".parquet")]


def _isOutdated(localPath: Path, remoteUpdatedAt: str) -> bool:
    """로컬 파일이 원격보다 오래됐는지 확인."""
    if not localPath.exists():
        return True
    localMtime = datetime.fromtimestamp(localPath.stat().st_mtime, tz=timezone.utc)
    remoteTime = datetime.fromisoformat(remoteUpdatedAt.replace("Z", "+00:00"))
    return localMtime < remoteTime


def downloadAll(category: str = "docs", *, forceUpdate: bool = False) -> None:
    """GitHub Release의 전체 parquet을 한번에 다운로드.

    Args:
        category: "docs", "finance", "report".
        forceUpdate: True면 로컬 파일이 있어도 원격 업데이트 일자가 더 최신이면 재다운로드.
    """
    from alive_progress import alive_bar

    dataDir = _dataDir(category)
    dataDir.mkdir(parents=True, exist_ok=True)
    label = DATA_RELEASES[category]["label"]

    conf = DATA_RELEASES[category]
    if "shards" in conf:
        tags = shardAllTags(category)
    else:
        tags = [conf["tag"]]

    allAssets: list[dict] = []
    print(f"[dartlab] {label} — GitHub Release 에셋 목록 조회 중... ({len(tags)}개 태그)")
    for tag in tags:
        assets = _fetchAssets(tag)
        allAssets.extend(assets)
        print(f"  {tag}: {len(assets)}개")

    toDownload = []
    skipped = 0
    for asset in allAssets:
        dest = dataDir / asset["name"]
        if forceUpdate and _isOutdated(dest, asset["updated_at"]):
            toDownload.append(asset)
        elif not dest.exists():
            toDownload.append(asset)
        else:
            skipped += 1

    if not toDownload:
        print(f"[dartlab] 전체 {len(allAssets)}종목 이미 최신 ({dataDir})")
        return

    action = "다운로드 (신규+업데이트)" if forceUpdate else "신규 다운로드"
    print(f"[dartlab] {action}: {len(toDownload)}종목 (스킵: {skipped})")

    failed = 0
    with alive_bar(len(toDownload), title="다운로드") as bar:
        for asset in toDownload:
            dest = dataDir / asset["name"]
            try:
                _downloadWithRetry(asset["browser_download_url"], dest)
            except (URLError, socket.timeout, OSError) as e:
                print(f"\n[dartlab] {asset['name']} 다운로드 실패 (3회 재시도 후): {e}")
                if dest.exists():
                    dest.unlink()
                failed += 1
            bar()

    if failed:
        print(f"[dartlab] 완료 → {dataDir} (실패: {failed}건)")
    else:
        print(f"[dartlab] 완료 → {dataDir}")


def download(stockCode: str) -> None:
    """특정 종목의 docs + finance 데이터를 모두 다운로드."""
    for category in DATA_RELEASES:
        dataDir = _dataDir(category)
        dest = dataDir / f"{stockCode}.parquet"
        label = DATA_RELEASES[category]["label"]
        if dest.exists():
            print(f"[dartlab] {stockCode} ({label}) 이미 존재")
            continue
        print(f"[dartlab] {stockCode} ({label}) 다운로드 중...")
        try:
            _download(stockCode, dest, category)
            print(f"[dartlab] 저장 완료: {dest}")
        except (URLError, socket.timeout, OSError) as e:
            if dest.exists():
                dest.unlink()
            print(f"[dartlab] {stockCode} ({label}) 다운로드 실패 (3회 재시도 후): {e}")


DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="


def buildIndex(category: str = "docs") -> pl.DataFrame:
    """로컬 parquet 전체를 스캔해서 종목 인덱스 생성.

    Returns:
        DataFrame (stockCode, corpName, rows, yearFrom, yearTo, nDocs)
        로컬에 파일이 없으면 빈 DataFrame.
    """
    dataDir = _dataDir(category)
    files = sorted(dataDir.glob("*.parquet"))
    if not files:
        return pl.DataFrame(
            schema={
                "stockCode": pl.Utf8,
                "corpName": pl.Utf8,
                "rows": pl.Int64,
                "yearFrom": pl.Utf8,
                "yearTo": pl.Utf8,
                "nDocs": pl.Int64,
            }
        )

    from alive_progress import alive_bar

    records = []
    with alive_bar(len(files), title="종목 스캔") as bar:
        for f in files:
            df = pl.read_parquet(str(f))
            code = f.stem
            name = extractCorpName(df)
            years = sorted(df["year"].unique().to_list())
            nDocs = df["rcept_no"].n_unique()
            records.append({
                "stockCode": code,
                "corpName": name,
                "rows": df.height,
                "yearFrom": years[0] if years else None,
                "yearTo": years[-1] if years else None,
                "nDocs": nDocs,
            })
            bar()

    return pl.DataFrame(records)


def extractCorpName(df: pl.DataFrame) -> str | None:
    """DataFrame에서 기업명 추출."""
    if "corp_name" in df.columns:
        names = df["corp_name"].unique().to_list()
        if names:
            return names[0]
    return None
