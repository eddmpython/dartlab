"""
실험 ID: 057-010
실험명: 10-Q split 패턴 조사

목적:
- 현재 로컬 docs의 10-Q filing URL을 다시 읽어 실제 split 가능성을 측정한다.
- 본문 inline title형과 standalone header형이 모두 처리되는지 확인한다.

가설:
1. 10-Q는 Full Document만 존재하는 것이 아니라 Part/Item 구조가 실제로 존재한다.
2. body 시작점과 item header 라인만 안정적으로 잡으면 구조화가 가능하다.

방법:
1. 로컬 docs parquet에서 10-Q filing URL을 수집한다.
2. 대표 filing을 다시 내려받아 `_htmlToText()` 후 `_splitItems(..., '10-Q')`를 적용한다.
3. filing당 section 수, split 성공 여부, title 분포를 집계한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab import config
from dartlab.providers.edgar.docs.fetch import _downloadHtml, _htmlToText, _splitItems


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    if not files:
        raise RuntimeError("EDGAR docs parquet 없음")

    filingRows: list[dict[str, object]] = []
    for filePath in files:
        df = pl.read_parquet(filePath)
        qDf = df.filter(pl.col("form_type") == "10-Q").select(["accession_no", "filing_url"]).unique()
        for row in qDf.iter_rows(named=True):
            filingRows.append({
                "ticker": filePath.stem,
                "accession_no": row["accession_no"],
                "filing_url": row["filing_url"],
            })

    records: list[dict[str, object]] = []
    for row in filingRows[:30]:
        html = _downloadHtml(str(row["filing_url"]))
        text = _htmlToText(html)
        items = _splitItems(text, "10-Q")
        records.append({
            "ticker": row["ticker"],
            "accession_no": row["accession_no"],
            "n_items": len(items),
            "split_success": len(items) > 1,
            "first_title": items[0]["title"] if items else None,
        })

    result = pl.DataFrame(records)
    print("=" * 72)
    print("057-010 quarterly split survey")
    print("=" * 72)
    print(result)
    if result.height > 0:
        print()
        print(result.group_by("split_success").len().sort("split_success"))


if __name__ == "__main__":
    main()
