"""
실험 ID: 058-001
실험명: Company ratio surface 업종별 샘플 매트릭스

목적:
- `Company.index / show("ratios") / trace("ratios")`가 다양한 업종에서 일관되게 동작하는지 확인
- 일반 업종과 금융업에서 row 수/연도 수 차이를 측정
- ratio surface를 `Company` 공개 표면에 올리는 방향이 맞는지 검증

가설:
1. 대표 샘플 19개 종목 모두에서 `show("ratios")`는 DataFrame으로 반환된다
2. `trace("ratios")`는 전 종목에서 `finance`를 primary source로 반환한다
3. 일반 업종은 대체로 30행 이상, 금융업은 더 적은 row 수를 보인다

방법:
1. 업종 대표 샘플 19개 종목 선정
2. `dartlab.Company(code)` 생성
3. `index`에서 `ratios` row 확인
4. `show("ratios")`의 shape, 연도 범위, row 수 기록
5. `trace("ratios")` 결과 기록

결과 (실험 후 작성):
- 성공: 19 / 19
- 공통:
  - `index`에 `ratios` 존재
  - chapter = `III. 재무에 관한 사항`
  - source = `finance`
- 일반 업종:
  - 대부분 35행, 일부 플랫폼/통신은 31행
  - 유통은 35행 11년, 나머지는 대체로 13열
- 금융업:
  - 은행/지주는 12~13행
  - 증권은 19행
  - 보험은 13행
  - 인터넷은행은 12행

결론:
- `ratios`를 `Company` 표면에 올린 방향은 맞다
- 일반 업종에서는 충분히 읽을 만한 시계열 비율표가 형성된다
- 금융업은 일반기업용 유동성/차입 중심 비율을 의도적으로 제거한 curated surface로 보는 편이 맞다
- financial alias account (`revenue`, `net_income`, `operating_income`) 지원으로 금융업 coverage가 추가 개선됐다
- 장기적으로는 금융업 전용 ratio template 검토가 필요하다

실험일: 2026-03-13
"""

from __future__ import annotations

import polars as pl

from _common import ratioSurfaceFrame


SAMPLES: list[tuple[str, str]] = [
    ("005930", "제조"),
    ("000660", "반도체"),
    ("035420", "플랫폼"),
    ("068270", "바이오"),
    ("034730", "지주"),
    ("086520", "소재"),
    ("282330", "유통"),
    ("017670", "통신"),
    ("000720", "건설"),
    ("010950", "에너지"),
    ("005380", "자동차"),
    ("051910", "화학"),
    ("018260", "IT서비스"),
    ("047050", "상사"),
    ("003230", "식품"),
    ("105560", "은행"),
    ("323410", "인터넷은행"),
    ("006800", "증권"),
    ("000810", "보험"),
]


def main():
    import dartlab

    dartlab.verbose = False

    rows: list[dict[str, object]] = []
    for code, sector in SAMPLES:
        c = dartlab.Company(code)
        indexRow = c.index.filter(pl.col("topic") == "ratios")
        ratioDf = c.show("ratios")
        traced = c.trace("ratios")

        years = []
        if isinstance(ratioDf, pl.DataFrame):
            years = [col for col in ratioDf.columns if col not in ("분류", "항목")]

        rows.append({
            "sector": sector,
            "stockCode": code,
            "corpName": c.corpName,
            "indexOk": indexRow.height == 1,
            "chapter": indexRow.item(0, "chapter") if indexRow.height == 1 else None,
            "source": traced["primarySource"] if traced is not None else None,
            "rows": ratioDf.height if isinstance(ratioDf, pl.DataFrame) else None,
            "cols": ratioDf.width if isinstance(ratioDf, pl.DataFrame) else None,
            "yearStart": years[0] if years else None,
            "yearEnd": years[-1] if years else None,
        })

    df = pl.DataFrame(rows)
    print(df)
    print()
    print(
        df.select([
            pl.len().alias("count"),
            pl.col("indexOk").all().alias("allIndexOk"),
            (pl.col("source") == "finance").all().alias("allFinance"),
            pl.col("rows").min().alias("minRows"),
            pl.col("rows").max().alias("maxRows"),
        ])
    )


if __name__ == "__main__":
    main()
