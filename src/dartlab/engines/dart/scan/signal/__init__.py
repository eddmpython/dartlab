"""서술형 공시 시장 시그널 — docs 텍스트에서 키워드 트렌드 추출.

전체 docs parquet를 횡으로 스캔하여 시장 단위 키워드/리스크 트렌드를 탐지한다.
현재 결과는 로컬 docs corpus에 존재하는 기업 범위에 한정된다.

Example::

    import dartlab
    df = dartlab.signal()          # 전체 키워드 트렌드
    df = dartlab.signal("AI")      # 특정 키워드 추이
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import polars as pl

# 키워드 사전
KEYWORDS: dict[str, list[str]] = {
    "트렌드": [
        "AI",
        "인공지능",
        "ESG",
        "탄소중립",
        "수소",
        "전기차",
        "자율주행",
        "메타버스",
        "블록체인",
        "클라우드",
        "데이터센터",
        "로봇",
        "2차전지",
        "배터리",
        "반도체",
        "바이오",
        "디지털전환",
        "플랫폼",
    ],
    "리스크": [
        "환율",
        "금리",
        "인플레이션",
        "경기침체",
        "공급망",
        "원자재",
        "유가",
        "지정학",
        "규제",
        "소송",
        "유동성",
        "파산",
        "구조조정",
        "감사의견",
    ],
    "기회": [
        "수출",
        "수주",
        "신규사업",
        "M&A",
        "시장점유율",
        "해외진출",
        "신약",
        "FDA",
        "특허",
    ],
}

_ALL_KEYWORDS: dict[str, str] = {kw: cat for cat, kws in KEYWORDS.items() for kw in kws}


def _read_signal_text(path: Path) -> pl.DataFrame | None:
    """signal 스캔에 필요한 최소 컬럼(year + text)만 읽는다."""
    for text_col in ("section_content", "content"):
        try:
            return pl.read_parquet(
                str(path),
                columns=["year", text_col],
            ).rename({text_col: "text"})
        except pl.exceptions.ColumnNotFoundError:
            continue
        except (OSError, pl.exceptions.ComputeError):
            return None
    return None


def scan_signal(
    keyword: str | None = None,
    *,
    verbose: bool = True,
) -> pl.DataFrame:
    """전체 docs parquet에서 키워드 트렌드 추출.

    Args:
        keyword: 특정 키워드만 필터. None이면 전체.

    Returns:
        DataFrame (year, keyword, category, companies, totalMentions).
        현재 local docs corpus 기준으로만 집계된다.
    """
    from dartlab import config

    docsDir = Path(config.dataDir) / "dart" / "docs"
    files = sorted(docsDir.glob("*.parquet"))

    if verbose:
        print(f"[dartlab] 서술형 시그널 스캔: {len(files)}사")

    targetKws = _ALL_KEYWORDS
    if keyword is not None:
        targetKws = {k: v for k, v in _ALL_KEYWORDS.items() if k == keyword}
        if not targetKws:
            raise ValueError(f"알 수 없는 키워드: '{keyword}'. 사용 가능: {list(_ALL_KEYWORDS.keys())}")

    targetItems = list(targetKws.items())

    # 기업 × 연도 × 키워드 빈도 수집
    rows: list[dict] = []

    for fi, path in enumerate(files):
        df = _read_signal_text(path)
        if df is None or df.is_empty():
            continue

        stockCode = path.stem

        # 연도별 텍스트 결합
        periodTexts: dict[str, list[str]] = defaultdict(list)
        for yearVal, textVal in df.iter_rows():
            period = str(yearVal) if yearVal is not None else ""
            text = str(textVal) if textVal is not None else ""
            year = period[:4] if len(period) >= 4 else period
            if year and text:
                periodTexts[year].append(text)

        for year, textChunks in periodTexts.items():
            text = " ".join(textChunks)
            if not text.strip():
                continue
            for kw, cat in targetItems:
                count = text.count(kw)
                if count > 0:
                    rows.append(
                        {
                            "stockCode": stockCode,
                            "year": year,
                            "keyword": kw,
                            "category": cat,
                            "count": count,
                        }
                    )

        if verbose and (fi + 1) % 100 == 0:
            print(f"  [signal] {fi + 1}/{len(files)}")

    if not rows:
        return pl.DataFrame(
            schema={
                "year": pl.Utf8,
                "keyword": pl.Utf8,
                "category": pl.Utf8,
                "companies": pl.UInt32,
                "totalMentions": pl.Int64,
            }
        )

    raw = pl.DataFrame(rows)

    # 연도 × 키워드 집계
    result = (
        raw.group_by(["year", "keyword", "category"])
        .agg(
            [
                pl.col("stockCode").n_unique().alias("companies"),
                pl.col("count").sum().alias("totalMentions"),
            ]
        )
        .sort(["keyword", "year"])
    )

    if verbose:
        nHits = raw.shape[0]
        nCompanies = raw["stockCode"].n_unique()
        print(f"  [signal] {nHits}건 히트, {nCompanies}사, {result['keyword'].n_unique()}키워드")

    return result


def keywords() -> dict[str, list[str]]:
    """사용 가능한 키워드 목록.

    Returns:
        {카테고리: [키워드...]} dict.
    """
    return KEYWORDS.copy()
