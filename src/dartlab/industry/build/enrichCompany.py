"""회사 JSON 데이터 통합 — AI insights + 블로그 + 재무 시계열 + 신용등급.

기존 companies/{code}.json에 풍부한 메타데이터를 추가한다.
한 번 빌드해서 landing static으로 배포.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

logger = logging.getLogger(__name__)

_BLOG_DIR = Path(__file__).resolve().parents[4] / "blog" / "05-company-reports"


def _parseFrontmatter(mdText: str) -> dict:
    """마크다운 파일의 YAML frontmatter 를 dict 로 파싱.

    ``---`` 로 감싼 YAML 블록을 추출하여 safe_load 한다.
    blog/05-company-reports 의 포스트에서 verdict/direction/archetype 등을 읽는 데 사용.

    Parameters
    ----------
    mdText : str
        마크다운 전체 텍스트.

    Returns
    -------
    dict
        YAML 파싱 결과. frontmatter 없거나 파싱 실패 시 빈 dict.
    """
    import yaml

    m = re.match(r"^---\n(.*?)\n---", mdText, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception as exc:
        _log.warning("frontmatter 파싱 실패로 빈 dict 반환: %s: %s", type(exc).__name__, exc)
        return {}


def _loadBlogIndex() -> dict[str, list[dict]]:
    """blog/05-company-reports의 포스트를 stockCode로 인덱싱.

    Returns
    -------
    dict[str, list[dict]]
        {stockCode: [{slug, title, verdict, grade, strengths, weaknesses, ...}]}
    """
    index: dict[str, list[dict]] = {}
    if not _BLOG_DIR.exists():
        return index

    for postDir in _BLOG_DIR.iterdir():
        if not postDir.is_dir():
            continue
        indexFile = postDir / "index.md"
        if not indexFile.exists():
            continue
        try:
            text = indexFile.read_text(encoding="utf-8")
        except OSError:
            continue

        fm = _parseFrontmatter(text)
        stockCode = str(fm.get("stockCode", "")).strip()
        if not stockCode:
            continue

        ai = fm.get("ai", {}) or {}
        entry = {
            "slug": re.sub(r"^\d+-", "", postDir.name),
            "title": fm.get("title", ""),
            "description": fm.get("description", ""),
            "date": str(fm.get("date", "")),
            "grade": fm.get("grade", ""),
            "storyTemplate": fm.get("storyTemplate", ""),
            "verdict": ai.get("verdict", ""),
            "direction": ai.get("direction", ""),
            "confidence": ai.get("confidence", ""),
            "archetype": ai.get("archetype", ""),
            "strengths": ai.get("strengths", []) or [],
            "weaknesses": ai.get("weaknesses", []) or [],
            "keyMetrics": ai.get("keyMetrics", {}) or {},
            "thumbnail": fm.get("thumbnail", ""),
            "ogImage": fm.get("ogImage", ""),
        }
        index.setdefault(stockCode, []).append(entry)

    # 날짜 내림차순
    for code in index:
        index[code].sort(key=lambda x: x["date"], reverse=True)

    return index


def _getAIInsight(stockCode: str, loader: Callable[[str], dict | None] | None = None) -> dict | None:
    """호출자가 주입한 loader로 AI 분석 인사이트 조회.

    dartlab.ask() 실행 시 축적된 회사별 분석 결과(narrative, strengths,
    weaknesses)를 SQLite DB 에서 읽어온다.

    Parameters
    ----------
    stockCode : str
        6자리 종목코드.

    Returns
    -------
    dict | None
        narrative : str — AI 분석 서술 (500~1000자)
        strengths : list[str] — 강점 (최대 4개)
        weaknesses : list[str] — 약점 (최대 4개)
        sector : str — 섹터명
        source : str — 분석 소스 (모델명)
        createdAt : str — 생성 일시
        인사이트 없으면 None.
    """
    if loader is None:
        return None
    try:
        return loader(stockCode)
    except Exception as e:
        logger.debug("AI insight 조회 실패 (%s): %s", stockCode, e)
        return None


def _getFinancials5y(stockCode: str) -> list[dict]:
    """scan/finance.parquet에서 최근 10년 연간 재무 추출.

    이름은 5y 유지(하위호환). 실제로는 **10년까지** 확장. 프런트는
    `financials5y` 배열 길이 기반으로 sparkline 길이 자동 조정.
    """
    try:
        import polars as pl

        from dartlab.core.dataConfig import DATA_RELEASES
        from dartlab.core.dataLoader import _getDataRoot

        finPath = _getDataRoot() / DATA_RELEASES["scan"]["dir"] / "finance.parquet"
        if not finPath.exists():
            return []

        # 최근 10년 자동 계산 (현재 연도 기준)
        from datetime import datetime

        thisYear = datetime.now().year
        years = [str(y) for y in range(thisYear - 9, thisYear + 1)]

        df = (
            pl.scan_parquet(str(finPath))
            .filter(pl.col("stockCode") == stockCode)
            .filter(pl.col("reprt_nm") == "4분기")  # 연간 누적
            .filter(pl.col("account_id_std").is_in(["sales", "operating_profit", "net_profit", "total_assets"]))
            .filter(pl.col("bsns_year").is_in(years))
            .select(["bsns_year", "fs_div", "account_id_std", "thstrm_amount"])
            .collect(engine="streaming")
        )

        if df.height == 0:
            return []

        df = df.with_columns(
            pl.col("thstrm_amount").str.replace_all(",", "").cast(pl.Float64, strict=False).alias("amount")
        )

        # CFS 우선, OFS fallback 계정별
        result: list[dict] = []
        for year in years:
            year_df = df.filter(pl.col("bsns_year") == year)
            if year_df.height == 0:
                continue

            entry: dict = {"year": year}
            for acct in ["sales", "operating_profit", "net_profit", "total_assets"]:
                subset = year_df.filter(pl.col("account_id_std") == acct)
                cfs_rows = subset.filter(pl.col("fs_div") == "CFS")
                if cfs_rows.height > 0:
                    val = cfs_rows["amount"][0]
                else:
                    ofs_rows = subset.filter(pl.col("fs_div") == "OFS")
                    val = ofs_rows["amount"][0] if ofs_rows.height > 0 else None
                entry[acct] = val

            if any(entry.get(k) for k in ["sales", "operating_profit"]):
                result.append(entry)

        return result
    except Exception as e:
        logger.debug("재무 추출 실패 (%s): %s", stockCode, e)
        return []


def enrichCompanyData(
    stockCode: str,
    egoData: dict,
    edges: list[Any],
    nodes: list[Any],
    blogIndex: dict[str, list[dict]] | None = None,
    hop2Data: dict[str, dict] | None = None,
    aiInsightLoader: Callable[[str], dict | None] | None = None,
) -> dict:
    """기존 ego JSON에 추가 데이터를 병합.

    Capabilities:
        egograph (1-hop 그래프) 에 calcSupplyInsights / AI insight / 5y financials / blog posts /
        상위 공급사 10 + 고객사 10 + 2-hop 정보를 합성한 enriched company dict 반환.
        Industry().__call__ 결과 카드의 본체 데이터.

    Parameters
    ----------
    stockCode : str
        대상 회사 코드.
    egoData : dict
        ``buildCompanyEgograph(stockCode)`` 결과.
    edges : list
        전체 IndustryEdge.
    nodes : list
        전체 IndustryNode.
    blogIndex : dict | None
        블로그 인덱스 (없으면 로드).
    hop2Data : dict | None
        ``computeHop2()`` 결과.

    Returns
    -------
    dict
        ego 기본 키 + insights/aiInsight/financials5y/blogPosts/topSuppliers/topCustomers/hop2

    Raises:
        없음 — 누락 소스는 빈 dict / 빈 list 로 폴백.

    Example:
        >>> from dartlab.industry.build.enrichCompany import enrichCompanyData
        >>> from dartlab.industry.build.pipeline import loadNodes, loadEdges, buildCompanyEgograph
        >>> data = enrichCompanyData("005930", buildCompanyEgograph("005930"), loadEdges(), loadNodes())
        >>> data["insights"]["hhiRisk"]
        '분산'

    Guide:
        ``Industry().__call__`` 의 회사 카드 표시 데이터. 단일 호출이 dict 키 12+ 결합 — 부분
        키만 cite 권장.

    When:
        AI 회사 카드 답변 생성 시. 운영자가 manifest 빌드 후 enriched cache 갱신할 때.

    How:
        egoData 기반 + supply insights (calcSupplyInsights) + AI insight (DB 룩업) + financials5y
        + 블로그 + 상위 공급/고객사 + hop2 → 단일 dict 합성.

    Requires:
        - L1.5 frame: nodes + edges + ego 그래프 (buildCompanyEgograph 산출)
        - L1.5 scan: finance.parquet (5y financials)
        - L4 ai: 호출자가 주입한 AI insight loader (선택)
        - blog: blogs/{code}.json (선택)

    See Also:
        - ``dartlab.industry.calcs.concentration.calcSupplyInsights`` : 공급망 종합
        - ``dartlab.industry.build.hop2.computeHop2`` : 2-hop 데이터
        - ``dartlab.industry.Industry.__call__`` : 본 함수 결과 사용자

    AIContext:
        회사 카드 답변의 단일 진입점. 답변 길이가 매우 길어질 수 있으므로 ``insights.hhiRisk`` +
        ``topSuppliers[:3]`` + ``aiInsight.summary`` 핵심 3 키만 발췌 권장.
    """
    from dartlab.industry.calcs.concentration import calcSupplyInsights

    if blogIndex is None:
        blogIndex = _loadBlogIndex()

    supplyInsights = calcSupplyInsights(stockCode, edges, nodes)
    aiInsight = _getAIInsight(stockCode, aiInsightLoader)
    financials5y = _getFinancials5y(stockCode)
    blogPosts = blogIndex.get(stockCode, [])

    # 상위 공급사 10 (엣지 기반)
    supplierEdges = sorted(
        [e for e in edges if e.toCode == stockCode and e.edgeType == "supplier"],
        key=lambda e: e.amount or 0,
        reverse=True,
    )[:10]
    suppliers = []
    nodeByCode = {n.stockCode: n for n in nodes}
    for e in supplierEdges:
        fromNode = nodeByCode.get(e.fromCode)
        suppliers.append(
            {
                "stockCode": e.fromCode,
                "corpName": e.fromName or (fromNode.corpName if fromNode else ""),
                "product": e.product,
                "amount": e.amount,
                "ratio": e.ratio,
                "confidence": e.confidence,
                "source": e.source,
            }
        )

    # 상위 고객사 10
    customerEdges = sorted(
        [e for e in edges if e.fromCode == stockCode and e.edgeType in ("customer", "supplier")],
        key=lambda e: e.amount or 0,
        reverse=True,
    )[:10]
    customers = []
    for e in customerEdges:
        toNode = nodeByCode.get(e.toCode)
        customers.append(
            {
                "stockCode": e.toCode,
                "corpName": e.toName or (toNode.corpName if toNode else ""),
                "product": e.product,
                "amount": e.amount,
                "type": e.edgeType,
                "confidence": e.confidence,
            }
        )

    # 동종사 상위 5 (같은 산업, 매출 순)
    ego = egoData.get("ego", {})
    industryId = ego.get("industry", "")
    peers: list[dict] = []
    if industryId:
        industryNodes = [n for n in nodes if n.industry == industryId and n.stockCode != stockCode and n.revenue]
        industryNodes.sort(key=lambda n: n.revenue or 0, reverse=True)
        for n in industryNodes[:5]:
            peers.append(
                {
                    "stockCode": n.stockCode,
                    "corpName": n.corpName,
                    "stage": n.stage,
                    "revenue": round((n.revenue or 0) / 1e8),  # 억
                }
            )

    # 2-hop 공급망 (선택적)
    hop2 = (hop2Data or {}).get(stockCode, {}) if hop2Data else {}

    return {
        **egoData,
        "aiInsight": aiInsight,
        "blogPosts": blogPosts,
        "financials5y": financials5y,  # 이름 유지 (하위호환), 실제 최대 10년
        "supplyInsights": supplyInsights,
        "suppliers": suppliers,
        "customers": customers,
        "peers": peers,
        "hop2": hop2,  # {hop2Neighbors, hop2Edges, hub, direct1HopCount}
    }
