"""
실험 ID: 057-001
실험명: EDGAR 섹션맵 모집단 및 로컬 커버리지 조사

목적:
- 057_edgarSectionMap의 시작점으로 모집단 정의와 현재 docs 커버리지를 확인한다.
- listed universe와 로컬 docs 보유 현황을 분리해 기록한다.

가설:
1. listed universe는 7천개 수준이고, 현재 로컬 docs는 초기 샘플 수준이다.
2. 10-K/10-Q/20-F section map 연구는 listed universe를 기준으로 단계적으로 확장하는 방식이 적절하다.

방법:
1. data/edgar/listedUniverse.parquet를 읽어 전체 수, exchange listed 수, OTC 수를 집계한다.
2. data/edgar/docs/*.parquet를 스캔해 현재 보유 ticker 수를 계산한다.
3. 보유 docs에서 form_type 분포, year 범위, section row 수를 집계한다.

결과 (실험 후 작성):
- listed universe total: 10,416
- exchange listed: 7,525
- OTC: 2,561
- current local docs: 배치 다운로드 진행 중이라 실행 시점에 따라 변동

결론:
- 057의 1차 모집단은 exchange listed 7,525개로 둔다.
- 전수조사는 로컬 docs가 충분히 쌓인 뒤 title frequency와 item coverage 분석으로 이어진다.

실험일: 2026-03-12
"""

from pathlib import Path

import polars as pl

from dartlab import config


def main() -> None:
    dataRoot = Path(config.dataDir)
    universePath = dataRoot / "edgar" / "listedUniverse.parquet"
    docsDir = dataRoot / "edgar" / "docs"

    universeDf = pl.read_parquet(universePath)
    totalUniverse = universeDf.height
    exchangeListed = universeDf.filter(pl.col("is_exchange_listed")).height
    otc = universeDf.filter(pl.col("is_otc")).height

    docFiles = sorted(docsDir.glob("*.parquet"))
    print(f"listed universe total: {totalUniverse}")
    print(f"exchange listed: {exchangeListed}")
    print(f"otc: {otc}")
    print(f"local docs files: {len(docFiles)}")

    if not docFiles:
        return

    records = []
    for filePath in docFiles:
        df = pl.read_parquet(filePath)
        years = sorted(df["year"].drop_nulls().unique().to_list()) if "year" in df.columns else []
        forms = sorted(df["form_type"].drop_nulls().unique().to_list()) if "form_type" in df.columns else []
        records.append({
            "ticker": filePath.stem,
            "rows": df.height,
            "year_from": years[0] if years else None,
            "year_to": years[-1] if years else None,
            "forms": ",".join(forms),
        })

    summaryDf = pl.DataFrame(records).sort("ticker")
    print(summaryDf)

    if "form_type" in pl.read_parquet(docFiles[0]).columns:
        formCounts = []
        for filePath in docFiles:
            df = pl.read_parquet(filePath)
            formCounts.append(df.select(pl.col("form_type")).drop_nulls())
        print(pl.concat(formCounts).group_by("form_type").len().sort("len", descending=True))


if __name__ == "__main__":
    main()
