"""변화 감지 스캐너.

단일 기업 또는 로컬 docs corpus 전체를 순회하며
sections diff + 중요도 스코어링을 실행한다.

사용법::

    from dartlab.scan.watch.scanner import scan_company, scan_market

    # 단일 기업 (Company 객체)
    result = scan_company(company)

    # 시장 전체 (로컬에 있는 docs parquet 기준)
    top = scan_market(sector="반도체", top_n=20)
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from dartlab.core.docs.diff import DiffResult, sectionsDiff
from dartlab.scan.watch.scorer import ScoredChange, score_changes, scored_to_dataframe


@dataclass
class ScanResult:
    """단일 기업 스캔 결과."""

    stockCode: str
    corpName: str | None
    diffResult: DiffResult
    scored: list[ScoredChange]

    @property
    def topScore(self) -> float:
        """감지된 변화 중 최고 점수 반환."""
        if not self.scored:
            return 0.0
        return self.scored[0].score

    def to_dataframe(self) -> pl.DataFrame:
        """스코어링 결과를 DataFrame으로."""
        df = scored_to_dataframe(self.scored)
        if df.height > 0:
            df = df.with_columns(
                pl.lit(self.stockCode).alias("stockCode"),
                pl.lit(self.corpName or "").alias("corpName"),
            )
        return df


def scan_company(
    company: object,
    *,
    topic: str | None = None,
) -> ScanResult | None:
    """단일 기업의 sections diff + 중요도 스코어링.

    Args:
        company: dartlab Company 객체 (docs.sections 속성 필요).
        topic: 특정 topic만 필터링 (None이면 전체).

    Returns:
        ScanResult 또는 sections가 없으면 None.
    """
    docs_sections = getattr(getattr(company, "docs", None), "sections", None)
    if docs_sections is None:
        return None

    if topic is not None and "topic" in docs_sections.columns:
        docs_sections = docs_sections.filter(pl.col("topic") == topic)
        if docs_sections.height == 0:
            return None

    diff_result = sectionsDiff(docs_sections)
    if not diff_result.summaries:
        return None

    scored = score_changes(diff_result, sections=docs_sections)

    stock_code = getattr(company, "stockCode", "")
    corp_name = getattr(company, "corpName", None)

    return ScanResult(
        stockCode=stock_code,
        corpName=corp_name,
        diffResult=diff_result,
        scored=scored,
    )


def _list_local_docs() -> list[str]:
    """로컬에 다운로드된 docs parquet 종목코드 목록."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _getDataRoot

    docs_dir = _getDataRoot() / DATA_RELEASES["docs"]["dir"]
    if not docs_dir.exists():
        return []
    return sorted(p.stem for p in docs_dir.glob("*.parquet"))


def scan_market(
    *,
    sector: str | None = None,
    top_n: int = 20,
    min_score: float = 10.0,
    stock_codes: list[str] | None = None,
    verbose: bool = False,
) -> pl.DataFrame:
    """시장 전체 또는 섹터별 변화 감지 스캔.

    로컬에 다운로드된 docs parquet을 순회하며 각 기업의
    sections diff → 중요도 스코어링을 실행한 뒤 상위 변화를 집계한다.

    Args:
        sector: 섹터 필터 (예: "반도체", "IT"). None이면 전체.
        top_n: 상위 N개 결과만 반환.
        min_score: 이 점수 이상만 포함.
        stock_codes: 직접 종목코드 목록 지정 (sector 무시).
        verbose: True이면 진행 상황 출력.

    Returns:
        stockCode, corpName, topic, score, changeRate, reason 등 컬럼의 DataFrame.
    """
    if stock_codes is None:
        codes = _list_local_docs()
    else:
        codes = list(stock_codes)

    if not codes:
        from dartlab.core.guidance import emit

        emit("hint:market_data_needed", category="docs", fn="digest")
        return pl.DataFrame(
            schema={
                "stockCode": pl.Utf8,
                "corpName": pl.Utf8,
                "topic": pl.Utf8,
                "score": pl.Float64,
                "changeRate": pl.Float64,
                "deltaBytes": pl.Int64,
                "latestPeriod": pl.Utf8,
                "reason": pl.Utf8,
            }
        )

    # 섹터 필터링
    if sector is not None and stock_codes is None:
        codes = _filter_by_sector(codes, sector)

    from dartlab.providers.dart.company import Company as DartCompany

    frames: list[pl.DataFrame] = []
    scanned = 0

    for code in codes:
        try:
            c = DartCompany(code)
            result = scan_company(c)
            if result is not None and result.scored:
                df = result.to_dataframe()
                if df.height > 0:
                    frames.append(df)
            scanned += 1
            if verbose and scanned % 50 == 0:
                print(f"[watch] {scanned}/{len(codes)} 스캔 완료...")
        except (FileNotFoundError, ValueError, KeyError, OSError):
            continue

    if not frames:
        return pl.DataFrame(
            schema={
                "stockCode": pl.Utf8,
                "corpName": pl.Utf8,
                "topic": pl.Utf8,
                "score": pl.Float64,
                "changeRate": pl.Float64,
                "deltaBytes": pl.Int64,
                "latestPeriod": pl.Utf8,
                "reason": pl.Utf8,
            }
        )

    combined = pl.concat(frames, how="diagonal_relaxed")
    combined = combined.filter(pl.col("score") >= min_score)
    combined = combined.sort("score", descending=True).head(top_n)

    if verbose:
        print(f"[watch] 스캔 완료: {scanned}개 기업, {combined.height}개 변화 감지")

    return combined


def _filter_by_sector(codes: list[str], sector: str) -> list[str]:
    """종목코드 목록에서 특정 섹터에 해당하는 것만 필터."""
    try:
        from dartlab.core.sector.classifier import classify

        filtered = []
        for code in codes:
            try:
                from dartlab.gather.listing import codeToName

                name = codeToName(code)
                if name is None:
                    continue
                info = classify(name)
                if sector in (info.sector.value, info.industryGroup.value):
                    filtered.append(code)
            except (ValueError, KeyError, ImportError):
                continue
        return filtered if filtered else codes
    except ImportError:
        return codes
