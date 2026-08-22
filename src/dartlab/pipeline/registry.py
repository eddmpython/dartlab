"""STAGES 레지스트리 — category → StageSpec(run 함수) 매핑 SSOT.

각 stage 모듈이 ``run*`` 함수를 제공하고, 본 레지스트리가 category 명으로 묶는다.
orchestrator/CLI/__main__ 이 이 레지스트리만 보고 dispatch — 새 stage 추가는 여기
한 줄 등록이면 끝. 순환 회피 위해 stage 모듈은 lazy import(함수 내부).
"""

from __future__ import annotations

from dartlab.pipeline.types import StageSpec

# recent set — `dartlab sync`(인자 없음) 기본 수집 카테고리.
# DART 공시 본문은 panel SSOT 이므로 finance/report/panel 만 유지.
RECENT_SET: tuple[str, ...] = ("finance", "report", "panel")


def buildRegistry() -> dict[str, StageSpec]:
    """전 stage 를 lazy import 해 {category: StageSpec} 레지스트리 구성.

    Returns:
        category → StageSpec dict.

    Raises:
        없음.

    Example:
        >>> "finance" in buildRegistry()
        True
    """
    # krx 스테이지는 운영 OFF (gov 로 대체, 저작권). `stages/krx.py` 코드는 보존 — 미import 로 unwire.
    from dartlab.pipeline.stages import (
        allFilings,
        brokerageReports,
        dart,
        dartZip,
        edgar,
        edgarPanel,
        macro,
        news,
        panelRceptReconcile,
        prebuild,
        reconcile,
    )

    specs: list[StageSpec] = [
        StageSpec("finance", run=dart.runDartRecent, uploadCategories=("finance",), label="DART 재무 (증분)"),
        StageSpec("report", run=dart.runDartRecent, uploadCategories=("report",), label="DART 보고서 (증분)"),
        StageSpec(
            "allFilings",
            run=allFilings.runAllFilings,
            uploadCategories=("allFilings",),
            label="DART 비정기 공시 일별 parquet (forward 7일 증분)",
        ),
        StageSpec(
            "allFilingsReconcile",
            run=allFilings.runAllFilingsReconcile,
            uploadCategories=("allFilings",),
            label="DART allFilings 로컬↔HF 양방향 reconcile (운영자 트리거)",
        ),
        StageSpec(
            "allFilingsBackfill",
            run=allFilings.runAllFilingsBackfill,
            uploadCategories=("allFilings",),
            label="DART allFilings 과거 백필 (2개월/run, floor 2015-01)",
        ),
        StageSpec("full", run=dart.runDartFull, uploadCategories=("finance", "report"), label="DART 88분기 전수"),
        StageSpec(
            "newStocks",
            run=dart.runDartNewStocks,
            uploadCategories=("finance", "report"),
            label="DART 신규상장 부트스트랩",
        ),
        StageSpec("panel", run=dart.runDartPanel, uploadCategories=("panel",), label="DART panel 수평화"),
        StageSpec(
            "dartZip",
            run=dartZip.runDartZip,
            uploadCategories=("dartOriginal", "panel"),
            label="DART 정기 원본 zip archive + panel 빌드 (Job 1, 증분)",
        ),
        StageSpec(
            "panelRceptReconcile",
            run=panelRceptReconcile.runPanelRceptReconcile,
            uploadCategories=("dartOriginal", "panel"),
            label="DART panel rcept 단위(파일내) 자가치유 — DART 정기 rcept vs panel 누락분 fetch+merge",
        ),
        StageSpec(
            "edgarPanel",
            run=edgarPanel.runEdgarPanel,
            uploadCategories=("edgarPanel",),
            label="EDGAR panel per-filing 증분 (Job 3, daily-index 발견→append)",
        ),
        StageSpec(
            "panelReconcile",
            run=reconcile.runPanelReconcile,
            uploadCategories=("panel",),
            label="DART panel 로컬↔HF 양방향 reconcile (운영자 트리거)",
        ),
        StageSpec(
            "edgarPanelReconcile",
            run=reconcile.runEdgarPanelReconcile,
            uploadCategories=("edgarPanel",),
            label="EDGAR panel 로컬↔HF 양방향 reconcile (운영자 트리거)",
        ),
        # krx / krxIndex 스테이지 운영 OFF (2026-06-11, gov 로 완전 대체 — 저작권상 공개 데이터는 gov 소스).
        # 코드(stages/krx.py·gather/krx/*·buildKrxData.py)는 보존 — 재가동 시 본 2줄 복원이면 끝.
        StageSpec(
            "macro",
            run=macro.runMacro,
            uploadCategories=("macroFred", "macroEcos", "macroCustoms"),
            label="거시 FRED/ECOS/관세청",
        ),
        StageSpec(
            "macroJson",
            run=prebuild.runMacroJson,
            online=False,
            label="macro.json (offline prebuild — cycle/regime → landing 대시보드 v20)",
        ),
        StageSpec(
            "brokerageReports",
            run=brokerageReports.runBrokerageReports,
            uploadCategories=("brokerageReports",),
            label="증권사 리서치 메타 인덱스 (일별 증분, 서버렌더 3개사)",
        ),
        StageSpec("news", run=news.runNewsHeadlines, uploadCategories=("newsHeadlines",), label="뉴스 헤드라인"),
        StageSpec(
            "newsEnrich",
            run=news.runNewsEnrich,
            uploadCategories=("newsEnriched",),
            label="뉴스 감성/토픽 enrich (Phase B, 로컬 headlines→enriched)",
        ),
        StageSpec(
            "gdeltForward",
            run=news.runGdeltForward,
            uploadCategories=("newsGdelt",),
            label="GDELT GKG forward 일별 (Phase D, yesterday 까지 lookback upsert)",
        ),
        StageSpec(
            "naverNews",
            run=news.runNaverNews,
            uploadCategories=("newsNaver",),
            label="네이버 뉴스 (private, KR 제목+스니펫 → 비공개 캐시 repo)",
        ),
        StageSpec(
            "edgar",
            run=edgar.runEdgar,
            uploadCategories=("edgar", "edgarMeta"),
            label="EDGAR 벌크+분기(companyfacts/sub/pre/tag)",
        ),
    ]
    return {s.category: s for s in specs}
