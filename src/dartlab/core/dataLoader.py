"""데이터 로딩 및 공통 유틸."""

import json
from pathlib import Path
from urllib.request import urlopen, urlretrieve

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "docsData"

RELEASE_BASE = "https://github.com/eddmpython/dartlab/releases/download/data-v1"
RELEASE_API = "https://api.github.com/repos/eddmpython/dartlab/releases/tags/data-v1"

PERIOD_KINDS = {
    "y": ["annual"],
    "q": ["Q1", "semi", "Q3", "annual"],
    "h": ["semi", "annual"],
}


def _download(stockCode: str, dest: Path) -> None:
    url = f"{RELEASE_BASE}/{stockCode}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, dest)


def loadData(stockCode: str) -> pl.DataFrame:
    """종목코드 → DataFrame. 로컬에 없으면 릴리즈에서 자동 다운로드."""
    path = DATA_DIR / f"{stockCode}.parquet"
    if not path.exists():
        print(f"[dartlab] {stockCode}.parquet 로컬에 없음 → GitHub Release에서 다운로드...")
        _download(stockCode, path)
        print(f"[dartlab] 저장 완료: {path}")
    return pl.read_parquet(str(path))


def downloadAll() -> None:
    """GitHub Release의 전체 parquet을 한번에 다운로드."""
    from alive_progress import alive_bar

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("[dartlab] GitHub Release 에셋 목록 조회 중...")
    with urlopen(RELEASE_API) as resp:
        data = json.loads(resp.read())
    assets = [a for a in data["assets"] if a["name"].endswith(".parquet")]

    existing = {p.name for p in DATA_DIR.glob("*.parquet")}
    toDownload = [a for a in assets if a["name"] not in existing]

    if not toDownload:
        print(f"[dartlab] 전체 {len(assets)}종목 이미 다운로드 완료 ({DATA_DIR})")
        return

    print(f"[dartlab] 신규 {len(toDownload)}종목 다운로드 (기존 {len(existing)}종목 스킵)")

    with alive_bar(len(toDownload), title="다운로드") as bar:
        for asset in toDownload:
            dest = DATA_DIR / asset["name"]
            urlretrieve(asset["browser_download_url"], dest)
            bar()

    print(f"[dartlab] 완료 → {DATA_DIR}")


DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="


def buildIndex() -> pl.DataFrame:
    """로컬 parquet 전체를 스캔해서 종목 인덱스 생성.

    Returns:
        DataFrame (stockCode, corpName, rows, yearFrom, yearTo, nDocs)
        로컬에 파일이 없으면 빈 DataFrame.
    """
    files = sorted(DATA_DIR.glob("*.parquet"))
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
