"""KR scan prebuild public facade.

Capabilities:
    - Exposes the historically public KR scan builder functions.
    - Orchestrates the main scan prebuild sequence.

Args:
    Public entry points accept prebuild window and logging options.

Returns:
    Builder outputs from domain modules.

Example:
    >>> from dartlab.scan.builders.kr.core import buildScan
    >>> result = buildScan(sinceYear=2021, verbose=True)

Guide:
    Keep this module thin. Domain implementation belongs in ``docs``, ``financeBuild``,
    ``report.build``, ``valuationBuild``, and ``shares``.

SeeAlso:
    ``docs.changes``, ``financeBuild``, ``financeLite``, ``report.build``, and
    ``valuationBuild``.

Requires:
    Domain builder modules import successfully.

AIContext:
    This is the stable compatibility surface for scripts and user imports. New build
    behavior should be added to domain modules first, then re-exported here.

LLM Specifications:
    AntiPatterns: Do not add raw finance/report/docs transformation logic here.
    OutputSchema: Delegated builder outputs.
    Prerequisites: Raw data exists under the configured data root for concrete builds.
    Freshness: Follows the scan prebuild workflow schedule.
    Dataflow: public facade -> domain build module -> parquet outputs.
    TargetMarkets: KR DART scan prebuild.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from dartlab.scan.builders.kr.common import BATCH_SIZE as _BATCH
from dartlab.scan.builders.kr.common import financeDir as _financeDir
from dartlab.scan.builders.kr.common import mergeBatchFiles as _mergeBatchFiles
from dartlab.scan.builders.kr.common import releaseNativeMemory as _releaseNativeMemory
from dartlab.scan.builders.kr.common import reportDir as _reportDir
from dartlab.scan.builders.kr.common import say as _say
from dartlab.scan.builders.kr.common import scanDir as _scanDir
from dartlab.scan.builders.kr.docs.changes import buildChanges as buildChanges
from dartlab.scan.builders.kr.financeBuild import _loadAccountMap as _loadAccountMap
from dartlab.scan.builders.kr.financeBuild import _sanityCheckCalendarYears as _sanityCheckCalendarYears
from dartlab.scan.builders.kr.financeBuild import buildFinance as buildFinance
from dartlab.scan.builders.kr.financeLite import buildFinanceLite as buildFinanceLite
from dartlab.scan.builders.kr.fiscal import _FISCAL_Q_MAP as _FISCAL_Q_MAP
from dartlab.scan.builders.kr.fiscal import _calendarizeFiscalColumns as _calendarizeFiscalColumns
from dartlab.scan.builders.kr.fiscal import _estimateFiscalMonthFromAnnualFiling as _estimateFiscalMonthFromAnnualFiling
from dartlab.scan.builders.kr.fiscal import _fiscalMonthMap as _fiscalMonthMap
from dartlab.scan.builders.kr.fiscal import _loadCorpProfileMap as _loadCorpProfileMap
from dartlab.scan.builders.kr.fiscal import _toCalendarPeriod as _toCalendarPeriod
from dartlab.scan.builders.kr.narrativeMetrics import buildNarrativeMetricsSafe as _buildNarrativeMetricsSafe
from dartlab.scan.builders.kr.network import buildAffiliateDocs as buildAffiliateDocs
from dartlab.scan.builders.kr.notes import buildNotesSafe as _buildNotesSafe
from dartlab.scan.builders.kr.report.build import SCAN_API_TYPES as SCAN_API_TYPES
from dartlab.scan.builders.kr.report.build import buildReport as buildReport
from dartlab.scan.builders.kr.salesByProduct import buildSalesByProductSafe as _buildSalesByProductSafe
from dartlab.scan.builders.kr.shares import buildSharesOutstandingSafe as _buildSharesOutstandingSafe
from dartlab.scan.builders.kr.valuationBuild import buildValuation as buildValuation


def buildScan(
    *,
    sinceYear: int = 2021,
    reportSinceYear: int = 2016,
    verbose: bool = True,
    incremental: bool = False,
    changedCodes: Iterable[str] | None = None,
    removedCodes: Iterable[str] = (),
) -> dict[str, Path | list[Path] | None]:
    """scan 프리빌드 통합 (finance, report, panel 파생 artifact).

    ``.github/scripts/prebuildData.py`` 가 매 prebuild 사이클 (KST 03:00 / 15:00) 에 호출하는
    파사드. 하위 6 단계를 순서대로 실행하며, ``buildValuation`` 은 별도 cron 이므로 본 함수에
    포함하지 않는다.

    Parameters
    ----------
    sinceYear : int
        시작 연도 (``buildFinance`` / ``buildChanges`` 공통). 기본 2021.
        ``buildFinanceLite`` 는 ``LITE_SINCE_YEAR`` 자체 기본값 (2022) 사용.
    reportSinceYear : int
        ``buildReport`` 전용 시작 연도. 기본 2016 — 정기보고서 정량 시계열(인력·배당·
        보수·지배구조 등)은 raw 수집 시작 연도(2016)까지 전 기간 노출한다. finance/
        changes 와 분리한 이유: 그 둘은 스크리너 신선도 용도라 2021 컷이 적정하고,
        전역 확장 시 산출물이 약 2배로 불어난다.
    verbose : bool
        진행 로그 출력 여부.
    incremental : bool
        True 면 panel 을 읽는 단계(``changes`` · ``sharesOutstanding``)가 로컬 panel
        dir(=변경 종목만 seed 된 상태)에서 재계산한 행만 기존 parquet 에 종목 단위로
        머지한다. finance/report 는 입력이 full 캐시이므로 항상 full 빌드(증분 무관).
        전 종목 panel(11GB) seed 없이 일일 prebuild 의 OOM/디스크 고갈을 막는 경로.

    Returns
    -------
    dict[str, Path | list[Path] | None]
        - changes : Path | None — ``changes.parquet`` 경로
        - finance : Path | None — ``finance.parquet`` 경로
        - finance_lite : Path | None — ``finance-lite.parquet`` 경로
        - report : list[Path] — apiType별 parquet 경로 목록
        - affiliateDocs : Path — 계열회사 ground truth 경로
        - sharesOutstanding : Path | None — ``sharesOutstanding.parquet`` 경로

    Raises
    ------
    polars.PolarsError
        하위 ``buildChanges`` · ``buildFinance`` · ``buildReport`` 가 발생시키는 예외 전파.
        ``_buildSharesOutstandingSafe`` 는 자체 catch 라 전파 안 됨.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.core import buildScan
    >>> result = buildScan(sinceYear=2021, verbose=True)
    >>> result["finance"].exists() if result["finance"] else "no data"
    True

    Capabilities:
        - 5 산출물 (changes / finance / finance-lite / report 12 / sharesOutstanding) 의
          단일 호출 파사드. 호출자는 본 함수 1 회로 모든 prebuild 출력을 얻는다.
        - 단계 간 의존: finance-lite ← finance (재빌드 아닌 필터만). 다른 단계는 독립.

    AIContext:
        prebuild 파이프라인의 main entry. AI 가 "scan 프리빌드 어떻게 만들지?" 질문 시 본
        함수 호출만 알려주면 충분하며, 세부 구현은 각 도메인 모듈을 참조한다.

    Guide:
        - 호출 직전에 ``.github/scripts/meta/buildCorpProfile.py`` 실행 권장 (결산월 SSOT 최신화).
        - 실행 후 산출 합계 (MB) 로깅. HF 업로드는 호출자 (``prebuildData.py``) 책임.
        - valuation 은 네트워크 rate-limit 성격이 달라 별도 ``buildValuation`` cron 이 담당.

    When:
        매 prebuild 사이클 — Data Sync workflow 직후 KST 03:00 / 15:00. 로컬 수동 실행은
        raw 데이터 충분히 갖춘 환경에서 디버깅 / 검증 용도.

    How:
        1) ``buildChanges`` → 2) ``buildFinance`` (결산월 환원 + sanity check 자동) →
        3) ``buildFinanceLite`` (finance.parquet 직후 파생) → 4) ``buildReport`` (apiType 분할)
        → 5) ``_buildSharesOutstandingSafe`` → 6) ``_buildSalesByProductSafe``
        → 7) ``_buildNotesSafe`` (full 모드만, note 횡단 카탈로그 구동)
        (마지막 3 개는 별도 try/except wrapper, panel 파싱 위임).

    Requires:
        - 로컬 ``data/dart/{docs,finance,report}/{stockCode}.parquet`` (Data Sync 결과)
        - 출력 디렉토리 쓰기 권한 (``data/dart/scan/``)

    SeeAlso:
        - :func:`buildChanges` · :func:`buildFinance` · :func:`buildFinanceLite` ·
          :func:`buildReport` · :func:`_buildSharesOutstandingSafe`
        - :func:`buildValuation` — 본 함수에 포함 안 됨 (별도 cron 트리거)
        - ``.github/scripts/prebuildData.py`` — 호출자 + HF 업로드 + 품질 검증
    """
    if verbose:
        _say(f"전종목 scan 프리빌드 시작 (sinceYear={sinceYear})")
        _say("=" * 60)

    results: dict[str, Path | list[Path] | None] = {}

    results["changes"] = buildChanges(sinceYear=sinceYear, verbose=verbose, incremental=incremental)
    _releaseNativeMemory()
    results["finance"] = buildFinance(sinceYear=sinceYear, verbose=verbose)
    _releaseNativeMemory()
    results["finance_lite"] = buildFinanceLite(verbose=verbose)
    _releaseNativeMemory()
    results["report"] = buildReport(sinceYear=reportSinceYear, verbose=verbose)
    _releaseNativeMemory()
    results["affiliateDocs"] = buildAffiliateDocs(
        verbose=verbose,
        incremental=incremental,
        changedCodes=changedCodes,
        removedCodes=removedCodes,
    )
    _releaseNativeMemory()
    results["sharesOutstanding"] = _buildSharesOutstandingSafe(verbose=verbose, incremental=incremental)
    _releaseNativeMemory()
    results["salesByProduct"] = _buildSalesByProductSafe(verbose=verbose, incremental=incremental)
    _releaseNativeMemory()

    # note 횡단은 full 모드 전용 (annual 노트라 주간 신선도 충분 + 증분 부분시드 데이터손실 회피).
    if not incremental:
        results["notes"] = _buildNotesSafe(verbose=verbose)
        _releaseNativeMemory()
        # 서술 지표(수주잔고·가동률)도 full 전용 (annual 서술 표).
        results["narrativeMetrics"] = _buildNarrativeMetricsSafe(verbose=verbose)
        _releaseNativeMemory()

    if verbose:
        _say("=" * 60)
        scanDir = _scanDir()
        if scanDir.exists():
            totalMb = sum(f.stat().st_size for f in scanDir.rglob("*.parquet")) / 1024 / 1024
            _say(f"scan 전체: {totalMb:.1f}MB")

    return results


__all__ = [
    "SCAN_API_TYPES",
    "_BATCH",
    "_FISCAL_Q_MAP",
    "_buildNarrativeMetricsSafe",
    "_buildNotesSafe",
    "_buildSalesByProductSafe",
    "_buildSharesOutstandingSafe",
    "_calendarizeFiscalColumns",
    "_estimateFiscalMonthFromAnnualFiling",
    "_financeDir",
    "_fiscalMonthMap",
    "_loadAccountMap",
    "_loadCorpProfileMap",
    "_mergeBatchFiles",
    "_releaseNativeMemory",
    "_reportDir",
    "_sanityCheckCalendarYears",
    "_scanDir",
    "_say",
    "_toCalendarPeriod",
    "buildAffiliateDocs",
    "buildChanges",
    "buildFinance",
    "buildFinanceLite",
    "buildReport",
    "buildScan",
    "buildValuation",
]
