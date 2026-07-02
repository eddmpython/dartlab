"""EDGAR scan 감사인 빌더. 10-K 본문(edgar/panel contentRaw)에서 edgar/scan/report/auditor.parquet 생성.

감사인(auditTrail)은 SEC XBRL 집계(companyfacts)에 없어(dei:AuditorName 은 문서 인라인 전용, 실측 404)
10-K 감사보고서 텍스트에서만 얻는다. ``employeeBuild`` 동형 트랙: panel contentRaw 를 lazy 푸시다운으로
읽어 canonical 법인명 + 재임시작연도(auditor since)를 추출한다.

파싱 단일 SSOT 는 providers(L1) ``auditorText.extractAuditorFromText``, 본 scan(L1.5)이 downward import.
실측(auditorProbe): 대형 10사 firm 10/10 · since 9/10, 전부 공지 실제값(KO EY 1921·CAT PwC 1925).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

AUDITOR_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "auditor": pl.Utf8,
    "sinceYear": pl.Int64,
}

_HF_REPO = "eddmpython/dartlab-data"
_HF_AUDITOR_PATH = "edgar/scan/report/auditor.parquet"
_BLOB_CAP = 400_000  # 기당 감사 블록 연결 상한(대형 10-K 방어)


def _loadPriorAuditor() -> pl.DataFrame | None:
    """기존 발행본 auditor.parquet(HF) 시드 로드. 누적 병합용(employeeBuild 동형). 실패 시 None."""
    try:
        import os

        from huggingface_hub import hf_hub_download

        fp = hf_hub_download(_HF_REPO, _HF_AUDITOR_PATH, repo_type="dataset", token=os.environ.get("HF_TOKEN"))
        return pl.read_parquet(fp)
    except Exception:  # noqa: BLE001 (네트워크/부재 모두 graceful None)
        return None


def auditorRowsFromPanel(panel: pl.DataFrame, ticker: str) -> list[dict]:
    """단일 회사 panel(10-K 감사 블록)에서 연도별 감사인 행 추출.

    ``period`` 앞 4자리를 회계연도로 보고, 기(period)별 감사 블록을 연결해 법인명·since 를 뽑는다.
    법인명 미검출 연도는 제외(정직 null 미표시).

    Args:
        panel: ``period``·``contentRaw`` 컬럼(10-K 감사 블록 필터 후) DataFrame.
        ticker: stockCode.

    Returns:
        list[dict]. 연도별 감사인 행(stockCode·year·auditor·sinceYear).
    """
    from dartlab.providers.edgar.report.auditorText import extractAuditorFromText

    byYear: dict[str, tuple[str, int | None]] = {}
    grouped: dict[str, list[str]] = {}
    for period, text in zip(panel["period"].to_list(), panel["contentRaw"].to_list()):
        year = str(period or "")[:4]
        if not year.isdigit():
            continue
        grouped.setdefault(year, []).append(str(text or ""))
    for year, blocks in grouped.items():
        firm, since = extractAuditorFromText(" ".join(blocks)[:_BLOB_CAP])
        if firm:
            byYear[year] = (firm, since)
    return [{"stockCode": ticker, "year": y, "auditor": f, "sinceYear": s} for y, (f, s) in sorted(byYear.items())]


def buildEdgarAuditor(*, verbose: bool = False) -> Path:
    """전종목 edgar/panel 에서 edgar/scan/report/auditor.parquet 생성. 10-K 감사인 순수 텍스트 추출.

    edgar/panel/{ticker}.parquet 만 순회(별도 수집 0). lazy 푸시다운(chapter='10-K' + 감사 키워드)으로
    무관 텍스트를 안 읽는다. 기존 HF 발행본 시드 병합으로 CI 부분 캐시에서도 커버리지 유지(employeeBuild 동형).

    Parameters
    ----------
    verbose : bool
        진행 로그.

    Returns
    -------
    Path
        edgar/scan/report/auditor.parquet 경로.

    Raises
    ------
    없음. panel 부재/공백이면 빈 parquet(보조 소스, scan 빌드 무중단).

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.report.auditorBuild import buildEdgarAuditor
    >>> p = buildEdgarAuditor(verbose=True)  # doctest: +SKIP
    >>> p.name
    'auditor.parquet'

    Capabilities:
        - 연도별 감사법인(canonical)·재임시작연도 추출. 실측 대형 10사 firm 10/10·since 9/10.
          미검출 기업/연도는 빈 행(패널 자연 미표시).

    AIContext:
        ``scan`` US auditTrail 의 source. 런타임 reportSource 가 market 분기로 KR
        (dart/scan/report/auditOpinion 파생)과 분리 소비.

    Guide:
        - edgarSync edgarPanel 갱신 직후 호출(buildEdgarEmployee 와 함께). 발행은 deployEdgarToHF 자동.
        - 전 유니버스 1회 백필은 HF panel 스트리밍 runner(scratchpad, backfillEmployee 동형)로 수행.

    When:
        edgarSync scan 프리빌드 단계. 직접 호출은 드물다.

    How:
        panel 마다 lazy scan + chapter='10-K' & 감사 키워드 푸시다운 후 auditorRowsFromPanel
        (기별 블록 연결 → canonical 매칭)로 누적, 시드 병합해 단일 parquet.

    Requires:
        - edgar/panel/{ticker}.parquet (edgarPanel stage 산출)
        - providers.edgar.report.auditorText (파싱 SSOT)

    SeeAlso:
        - :func:`dartlab.scan.builders.edgar.report.employeeBuild.buildEdgarEmployee` (동형 panel 텍스트 트랙)
        - :func:`dartlab.providers.edgar.report.auditorText.extractAuditorFromText` (파싱 SSOT)
    """
    from dartlab import config as _cfg

    panelDir = Path(_cfg.dataDir) / "edgar" / "panel"
    outDir = Path(_cfg.dataDir) / "edgar" / "scan" / "report"
    outDir.mkdir(parents=True, exist_ok=True)
    parquets = sorted(panelDir.glob("*.parquet")) if panelDir.exists() else []
    if not parquets and verbose:
        _log.info("[edgarReport] auditor: edgar/panel 부재. 빈 parquet 생성")

    rows: list[dict] = []
    for fp in parquets:
        ticker = fp.stem.upper()
        try:
            sub = (
                pl.scan_parquet(fp)
                .filter(
                    (pl.col("chapter") == "10-K")
                    & pl.col("contentRaw").str.contains("(?i)accounting firm|auditor|audit report")
                )
                .select(["period", "contentRaw"])
                .collect()
            )
        except (OSError, pl.exceptions.PolarsError):
            continue
        if sub.is_empty():
            continue
        rows.extend(auditorRowsFromPanel(sub, ticker))

    out = pl.DataFrame(rows, schema=AUDITOR_COLS) if rows else pl.DataFrame(schema=AUDITOR_COLS)
    prior = _loadPriorAuditor()
    if prior is not None and not prior.is_empty():
        prior = prior.select(list(AUDITOR_COLS.keys())).cast(AUDITOR_COLS)
        out = pl.concat([out, prior], how="vertical_relaxed").unique(subset=["stockCode", "year"], keep="first")
    out = out.sort(["stockCode", "year"])
    outPath = outDir / "auditor.parquet"
    out.write_parquet(str(outPath), compression="zstd")
    if verbose:
        _log.info(f"[edgarReport] auditor: {out.height}행 ({out['stockCode'].n_unique()}종목) 생성 {outPath}")
    return outPath


__all__ = ["AUDITOR_COLS", "auditorRowsFromPanel", "buildEdgarAuditor"]
