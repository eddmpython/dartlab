"""KR scan shares-outstanding helper builder.

Capabilities:
    - Runs the optional shares outstanding scan build without failing the full scan build.

Args:
    Public entry point accepts logging options.

Returns:
    Generated shares parquet path or ``None`` when the optional build fails.

Example:
    >>> from dartlab.scan.builders.kr.shares import buildSharesOutstandingSafe
    >>> p = buildSharesOutstandingSafe(verbose=True)

Guide:
    This module is intentionally small because shares are an optional adjunct to the
    scan prebuild, not a full domain tree.

SeeAlso:
    ``core.buildScan`` and ``providers.dart.panel.text.panelXmlTables`` (panel 주식의 총수 표).

Requires:
    panel artifact (providers.dart.panel.text SSOT).

AIContext:
    Keeps optional share-count failure from corrupting or blocking core scan sources.

LLM Specifications:
    AntiPatterns: Do not place broad finance build logic here.
    OutputSchema: ``sharesOutstanding.parquet`` path when generated.
    Prerequisites: Share-capital builder import succeeds.
    Freshness: Rebuilt with the main scan prebuild.
    Dataflow: provider share-capital builder -> scan output path.
    TargetMarkets: KR DART scan adjunct data.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.builders.kr.common import mergeIncremental as _mergeIncremental
from dartlab.scan.builders.kr.common import panelDir as _panelDir
from dartlab.scan.builders.kr.common import releaseNativeMemory as _releaseNativeMemory
from dartlab.scan.builders.kr.common import say as _say
from dartlab.scan.builders.kr.common import scanDir as _scanDir

_SHARES_PATTERN = "주식의 총수"
_OUTPUT_COLUMNS = [
    "stock_code",
    "corp_name",
    "year",
    "rcept_date",
    "rcept_no",
    "report_type",
    "authorizedShares",
    "issuedShares",
    "retiredShares",
    "outstandingShares",
    "treasuryShares",
    "floatingShares",
    "treasuryRatio",
    "preferredIssued",
    "preferredOutstanding",
    "preferredTreasury",
    "preferredFloating",
    "source",
]
_SHARES_SCHEMA = {
    "stock_code": pl.Utf8,
    "corp_name": pl.Utf8,
    "year": pl.Int32,
    "rcept_date": pl.Utf8,
    "rcept_no": pl.Utf8,
    "report_type": pl.Utf8,
    "authorizedShares": pl.Int64,
    "issuedShares": pl.Int64,
    "retiredShares": pl.Int64,
    "outstandingShares": pl.Int64,
    "treasuryShares": pl.Int64,
    "floatingShares": pl.Int64,
    "treasuryRatio": pl.Float64,
    "preferredIssued": pl.Int64,
    "preferredOutstanding": pl.Int64,
    "preferredTreasury": pl.Int64,
    "preferredFloating": pl.Int64,
    "source": pl.Utf8,
}


def _numShares(cell: str | None) -> int | None:
    """주식수 셀(콤마 포함) → int. '-'·빈칸·비숫자는 None."""
    s = (cell or "").replace(",", "").strip()
    return int(s) if s.isdigit() else None


def _parseSharesTable(tables: list[list[list[str]]]) -> dict | None:
    """providers.dart.panel.text.panelXmlTables('주식의 총수') 표 행 → 발행/자기/유통 주식수 (panel XML 표).

    헤더 기반 추출. 격자전개(parsePanelXmlTables)가 '구분' COLSPAN·다단 헤더를 직사각화하므로,
    위치 인덱싱 대신 ``gridToRowDicts`` 로 '보통주'/'우선주'/'합계' 헤더 열을 이름으로 잡는다. 라벨
    (Ⅰ발행할~Ⅵ유통)은 첫 열(구분)에서 매칭.
    """
    from dartlab.providers.dart.panel.text import gridToRowDicts

    for t in tables:
        labels = "".join(row[0] for row in t if row).replace(" ", "")
        if "발행주식의총수" not in labels and "유통주식수" not in labels:
            continue
        # 다단 헤더 대응: '합계' + ('보통주'|'우선주') 가 있는 행을 헤더로.
        headerRow = 0
        for i, row in enumerate(t[:4]):
            joined = "".join(row).replace(" ", "")
            if "합계" in joined and ("보통주" in joined or "우선주" in joined):
                headerRow = i
                break
        rows = gridToRowDicts(t, headerRow=headerRow)
        if not rows:
            continue
        keys = list(rows[0].keys())
        labelKey = keys[0]
        prefKey = next((k for k in keys if k.replace(" ", "") == "우선주"), None)
        totalKey = next((k for k in keys if k.replace(" ", "") == "합계"), None)

        out: dict = {}
        for r in rows:
            label = (r.get(labelKey) or "").replace(" ", "")
            pref = _numShares(r.get(prefKey)) if prefKey else None
            total = _numShares(r.get(totalKey)) if totalKey else None
            if "발행할주식의총수" in label:
                out["authorizedShares"] = total
            elif "현재까지발행한주식" in label:
                out["issuedShares"] = total
                out["preferredIssued"] = pref
            elif "현재까지감소한주식" in label:
                out["retiredShares"] = total
            elif "발행주식의총수" in label:
                out["outstandingShares"] = total
                out["preferredOutstanding"] = pref
            elif "자기주식수" in label:
                out["treasuryShares"] = total
                out["preferredTreasury"] = pref
            elif "유통주식수" in label:
                out["floatingShares"] = total
                out["preferredFloating"] = pref
        if out.get("outstandingShares") or out.get("issuedShares"):
            o = out.get("outstandingShares")
            tr = out.get("treasuryShares")
            out["treasuryRatio"] = (tr / o) if (tr and o) else None
            return out
    return None


def buildSharesOutstandingScan(
    *, write: bool = True, outputPath: "str | Path | None" = None, incremental: bool = False
) -> "object":
    """전 종목 panel 발행주식수 scan (providers.dart.panel.text SSOT).

    Args:
        write: True면 ``sharesOutstanding.parquet`` 저장.
        outputPath: 출력 경로. None이면 ``data/dart/scan/sharesOutstanding.parquet``.
        incremental: True 면 로컬 panel dir(=변경 종목만 seed)에서 재계산한 행을 기존
            parquet 에 ``stock_code`` 단위로 갈아끼운다(:func:`mergeIncremental`).

    Returns:
        발행주식수 DataFrame (stock_code × period, rcept_date desc).

    Raises:
        FileNotFoundError: panel 디렉토리 부재.
        RuntimeError: 추출 결과 0 건.

    Example:
        >>> buildSharesOutstandingScan(write=False)  # doctest: +SKIP
    """
    from dartlab.core.listingResolver import getListingResolver
    from dartlab.providers.dart.panel.text import panelTextRows, parsePanelXmlTables

    panelRoot = _panelDir()
    if not panelRoot.exists():
        raise FileNotFoundError(f"panel 디렉토리 없음: {panelRoot}")
    codes = sorted(p.stem for p in panelRoot.glob("*.parquet"))
    resolver = getListingResolver()
    records: list[dict] = []
    for code in codes:
        texts = panelTextRows(code)
        if texts is None or texts.is_empty():
            continue
        sub = texts.filter(pl.col("sectionLeaf").str.contains(_SHARES_PATTERN))
        if sub.is_empty():
            continue
        corpName = (resolver.codeToName(code) if resolver else None) or ""
        periodMap = dict(zip(sub["period"].to_list(), sub["rceptNo"].to_list(), strict=False))
        for period, rcept in periodMap.items():
            periodRows = sub.filter(pl.col("period") == period)
            tables: list[list[list[str]]] = []
            for content in periodRows["contentRaw"].to_list() if "contentRaw" in periodRows.columns else []:
                if content and "<TR" in content:
                    tables.extend(parsePanelXmlTables(content))
            parsed = _parseSharesTable(tables)
            if parsed is None:
                continue
            year = int(period[:4]) if period[:4].isdigit() else None
            reportType = "annual" if period.endswith("Q4") else period[4:]
            records.append(
                {
                    "stock_code": code,
                    "corp_name": corpName,
                    "year": year,
                    "rcept_date": (rcept or "")[:8],
                    "rcept_no": rcept,
                    "report_type": reportType,
                    "authorizedShares": parsed.get("authorizedShares"),
                    "issuedShares": parsed.get("issuedShares"),
                    "retiredShares": parsed.get("retiredShares"),
                    "outstandingShares": parsed.get("outstandingShares"),
                    "treasuryShares": parsed.get("treasuryShares"),
                    "floatingShares": parsed.get("floatingShares"),
                    "treasuryRatio": parsed.get("treasuryRatio"),
                    "preferredIssued": parsed.get("preferredIssued"),
                    "preferredOutstanding": parsed.get("preferredOutstanding"),
                    "preferredTreasury": parsed.get("preferredTreasury"),
                    "preferredFloating": parsed.get("preferredFloating"),
                    "source": "panel_frame",
                }
            )
        del texts, sub
        if len(records) and len(records) % 200 == 0:
            _releaseNativeMemory()
    if not records:
        raise RuntimeError("발행주식수 추출 결과 0 건")
    out = pl.DataFrame(records, schema_overrides=_SHARES_SCHEMA, infer_schema_length=None).select(_OUTPUT_COLUMNS)
    out = out.sort(["stock_code", "rcept_date"], descending=[False, True])
    if write:
        if outputPath is None:
            outputPath = _scanDir() / "sharesOutstanding.parquet"
        outputPath = Path(outputPath)
        outputPath.parent.mkdir(parents=True, exist_ok=True)
        if incremental and outputPath.exists():
            _mergeIncremental(outputPath, out, key="stock_code")
        else:
            out.write_parquet(str(outputPath), compression="zstd")
    _releaseNativeMemory()
    return out


def buildSharesOutstandingSafe(*, verbose: bool = True, incremental: bool = False) -> Path | None:
    """발행주식수 풀 빌드 — 실패해도 전체 scan 진행.

    Parameters
    ----------
    verbose : bool
        진행 로그 출력 여부.
    incremental : bool
        True 면 변경 종목만 재계산해 기존 parquet 에 ``stock_code`` 단위로 머지.

    Returns
    -------
    Path | None
        생성된 sharesOutstanding.parquet 경로. 실패 시 None.

    Raises
    ------
    없음 — 선택 산출물이므로 내부에서 알려진 실패를 흡수한다.

    Examples
    --------
    >>> buildSharesOutstandingSafe(verbose=False) is None
    True

    Capabilities:
        발행주식수 산출물을 별도 optional step 으로 만들고, 실패 시 전체 scan build 를 계속한다.

    AIContext:
        valuation/share 기반 scan 축에서 보조 데이터로 사용된다. 실패는 핵심 finance/report
        산출물 신뢰도와 분리해서 다룬다.

    Guide:
        이 함수는 보호 wrapper 이다. 실제 수집/계산 책임은 provider shareCapital builder 에 둔다.

    When:
        ``buildScan`` 마지막 단계에서 호출된다.

    How:
        frame 기반 ``buildSharesOutstandingScan`` 을 실행하고, 알려진 런타임/파일 오류는 None 으로 변환한다.

    Requires:
        ``buildSharesOutstandingScan`` (providers.dart.panel.text SSOT, panel 주식의 총수 표).

    SeeAlso:
        ``dartlab.scan.builders.kr.core.buildScan``.
    """
    try:
        if verbose:
            mode = "증분" if incremental else "full"
            _say(f"[shares] 발행주식수 {mode} 빌드 시작 (providers.dart.panel.text SSOT)")
        df = buildSharesOutstandingScan(incremental=incremental)
        if verbose:
            _say(f"[shares] 완료: 재계산 rows={df.height} stocks={df['stock_code'].n_unique()}")
        return _scanDir() / "sharesOutstanding.parquet"
    except (FileNotFoundError, RuntimeError, OSError, ValueError, pl.exceptions.PolarsError) as exc:
        if verbose:
            _say(f"[shares] 실패: {exc}")
        return None
