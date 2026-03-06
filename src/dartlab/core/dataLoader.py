"""데이터 로딩 및 공통 유틸."""

from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "docsData"

PERIOD_KINDS = {
    "y": ["annual"],
    "q": ["Q1", "semi", "Q3", "annual"],
    "h": ["semi", "annual"],
}


def loadData(stockCode: str) -> pl.DataFrame:
    """종목코드 → DataFrame."""
    path = DATA_DIR / f"{stockCode}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{stockCode}.parquet not found in {DATA_DIR}")
    return pl.read_parquet(str(path))


def extractCorpName(df: pl.DataFrame) -> str | None:
    """DataFrame에서 기업명 추출."""
    if "corp_name" in df.columns:
        names = df["corp_name"].unique().to_list()
        if names:
            return names[0]
    return None
