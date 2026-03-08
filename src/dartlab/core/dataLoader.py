"""데이터 로딩 및 공통 유틸."""

import json
from pathlib import Path
from urllib.request import urlopen, urlretrieve

import polars as pl

from dartlab.core.dataConfig import DATA_RELEASES, releaseBaseUrl, releaseApiUrl

_DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


def _dataDir(category: str = "docs") -> Path:
    return _DATA_ROOT / DATA_RELEASES[category]["dir"]

PERIOD_KINDS = {
    "y": ["annual"],
    "q": ["Q1", "semi", "Q3", "annual"],
    "h": ["semi", "annual"],
}


def _download(stockCode: str, dest: Path, category: str = "docs") -> None:
    url = f"{releaseBaseUrl(category)}/{stockCode}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, dest)


def loadData(stockCode: str, category: str = "docs") -> pl.DataFrame:
    """종목코드 → DataFrame. 로컬에 없으면 릴리즈에서 자동 다운로드."""
    dataDir = _dataDir(category)
    path = dataDir / f"{stockCode}.parquet"
    if not path.exists():
        label = DATA_RELEASES[category]["label"]
        print(f"[dartlab] {stockCode}.parquet ({label}) 로컬에 없음 → GitHub Release에서 다운로드...")
        _download(stockCode, path, category)
        print(f"[dartlab] 저장 완료: {path}")
    return pl.read_parquet(str(path))


def downloadAll(category: str = "docs") -> None:
    """GitHub Release의 전체 parquet을 한번에 다운로드."""
    from alive_progress import alive_bar

    dataDir = _dataDir(category)
    dataDir.mkdir(parents=True, exist_ok=True)
    label = DATA_RELEASES[category]["label"]

    print(f"[dartlab] {label} — GitHub Release 에셋 목록 조회 중...")
    with urlopen(releaseApiUrl(category)) as resp:
        data = json.loads(resp.read())
    assets = [a for a in data["assets"] if a["name"].endswith(".parquet")]

    existing = {p.name for p in dataDir.glob("*.parquet")}
    toDownload = [a for a in assets if a["name"] not in existing]

    if not toDownload:
        print(f"[dartlab] 전체 {len(assets)}종목 이미 다운로드 완료 ({dataDir})")
        return

    print(f"[dartlab] 신규 {len(toDownload)}종목 다운로드 (기존 {len(existing)}종목 스킵)")

    with alive_bar(len(toDownload), title="다운로드") as bar:
        for asset in toDownload:
            dest = dataDir / asset["name"]
            urlretrieve(asset["browser_download_url"], dest)
            bar()

    print(f"[dartlab] 완료 → {dataDir}")


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
