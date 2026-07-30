"""한국 상장사 관계 지도 — 출자/지분/인적 관계 그래프.

Public API:
    buildGraph()        → data dict (전체 파이프라인)
    exportFull(data)    → full JSON dict
    exportOverview(data, full) → overview JSON dict
    exportEgo(data, full, code) → ego JSON dict
"""

from __future__ import annotations

import time

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import polars as pl

from dartlab.scan.network.affiliates import loadAffiliateGroups
from dartlab.scan.network.classifier import classifyBalanced
from dartlab.scan.network.edges import (
    buildHolderEdges,
    buildInvestEdges,
    deduplicateEdges,
    detectCycles,
)
from dartlab.scan.network.export import (
    exportEgo,
    exportFull,
    exportOverview,
)
from dartlab.scan.network.scanner import (
    loadListing,
    scanInvested,
    scanMajorHolders,
)


def buildGraph(*, verbose: bool = True) -> dict:
    """전체 파이프라인 실행 → data dict.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    dict
        listing_meta : dict — 상장사 메타데이터
        code_to_name : dict — 종목코드 → 회사명
        code_to_group : dict — 종목코드 → 그룹명 (재벌/독립)
        invest_edges : pl.DataFrame — 출자 엣지
        corp_edges / person_edges : pl.DataFrame — 법인/개인 엣지
        all_node_ids : set[str] — 분류 대상 종목코드
        cycles : list[list[str]] — 순환출자 경로 목록

    Raises
    ------
    polars.PolarsError
        report parquet (investedCompany · majorHolder) 손상 시.

    Examples
    --------
    >>> from dartlab.scan.network import buildGraph
    >>> data = buildGraph(verbose=True)
    >>> len(data["cycles"])

    Capabilities:
        - 한국 상장사 출자 (invested_company) + 지분 (major_holder) 관계 → 법인/개인 엣지 +
          순환출자 탐지 + 균형 분류 (재벌/독립) 통합 파이프라인. 6 단계 sequential.
        - 종목코드↔회사명 매핑 + 노드 set + cycles list 가 후속 export 함수의 source.

    AIContext:
        Agent 가 ``dartlab.scan("network")`` 호출 시 본 함수 dispatch. 상장사 관계 시각화, 재벌
        구조 분석, 순환출자 watchlist source. 후속 `exportFull`/`exportEgo` 가 본 함수 결과로
        JSON 페이로드 생성.

    Guide:
        - 6 단계 sequential — 한 단계 실패 시 후속도 불가 (try/except 없음, fail-fast).
        - cycles max_length=6 — 6 단계 초과 순환은 noise 로 제외.
        - 계열회사 ground truth는 작은 prebuild artifact만 읽으며 raw panel을 순회하지 않는다.

    When:
        대시보드 network 시각화 빌드 시. 재벌/그룹 관계 분석 시. 매 prebuild 사이클은 아니고
        별도 cron 또는 수동 호출.

    How:
        loadListing → scanInvested → buildInvestEdges + deduplicateEdges → scanMajorHolders →
        buildHolderEdges → all_node_ids 수집 (listing 교집합) → affiliate membership ground truth →
        classifyBalanced → detectCycles → data dict 반환.

    Requires:
        - 로컬 ``data/dart/scan/report/{investedCompany,majorHolder}.parquet``
        - 로컬 ``data/dart/scan/network/affiliateDocs.parquet``
        - KRX listing (``loadListing``)

    SeeAlso:
        - :func:`exportFull` · :func:`exportEgo` · :func:`exportOverview` — 본 함수 결과 소비자
        - :func:`detectCycles` — 순환출자 핵심 알고리즘
        - :func:`classifyBalanced` — 재벌/독립 분류
    """
    t0 = time.perf_counter()

    def _say(msg: str) -> None:
        if verbose:
            _log.info(msg)

    _say("1. 상장사 목록...")
    nameToCode, codeToName, listing_codes, listing_meta = loadListing()

    _say("2. investedCompany 스캔...")
    raw_inv = scanInvested()
    investEdges = buildInvestEdges(raw_inv, nameToCode, codeToName)
    invest_deduped = deduplicateEdges(investEdges)
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))
    _say(f"   → {len(invest_deduped):,} edges")

    _say("3. majorHolder 스캔...")
    raw_mh = scanMajorHolders()
    corpEdges, personEdges = buildHolderEdges(raw_mh, nameToCode)
    _say(f"   → corp {len(corpEdges):,}, person {len(personEdges):,}")

    # 노드 수집
    allNodeIds: set[str] = set()
    listed_only = invest_deduped.filter(pl.col("is_listed") & pl.col("to_code").is_not_null())
    for row in listed_only.iter_rows(named=True):
        allNodeIds.add(row["from_code"])
        allNodeIds.add(row["to_code"])
    matched_corp = corpEdges.filter(pl.col("from_code").is_not_null())
    for row in matched_corp.iter_rows(named=True):
        allNodeIds.add(row["from_code"])
        allNodeIds.add(row["to_code"])
    allNodeIds = allNodeIds & listing_codes

    _say("4. 계열회사 prebuild...")
    docs_gt = loadAffiliateGroups()
    allNodeIds.update(set(docs_gt) & listing_codes)
    _say(f"   → {len(docs_gt)} 종목 매핑, 총 {len(allNodeIds)} 상장사 노드")

    _say("5. 균형 분류...")
    codeToGroup = classifyBalanced(
        invest_deduped,
        corpEdges,
        personEdges,
        allNodeIds,
        codeToName,
        docs_gt,
        verbose=verbose,
    )

    _say("6. 순환출자 탐지...")
    cycles = detectCycles(invest_deduped, codeToName, maxLength=6)
    _say(f"   → {len(cycles)}개")

    elapsed = time.perf_counter() - t0
    _say(f"\n파이프라인 완료: {elapsed:.1f}초")

    return {
        "listing_meta": listing_meta,
        "code_to_name": codeToName,
        "code_to_group": codeToGroup,
        "invest_edges": invest_deduped,
        "corp_edges": corpEdges,
        "person_edges": personEdges,
        "all_node_ids": allNodeIds,
        "cycles": cycles,
    }


__all__ = [
    "buildGraph",
    "exportFull",
    "exportOverview",
    "exportEgo",
]
