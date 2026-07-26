from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response
from sse_starlette.sse import EventSourceResponse

import dartlab
from dartlab.core.polarsUtil import isEmptyDf

_PERIOD_COL_RE = re.compile(r"^\d{4}(Q[1-4])?$")

from ..services.aiAnalysis import streamTopicSummary
from ..services.companyApi import (
    buildPanelGrid,
    buildToc,
    getCompany,
    safeTopicLabel,
    splitSectionKey,
)
from .common import (
    HANDLED_API_ERRORS,
    etagResponse,
    guideDetail,
    normalizeProviderName,
    serializePayload,
)

router = APIRouter()

get_company = getCompany
stream_topic_summary = streamTopicSummary


def _panelTextWide(company):
    """Return DART panel text wide view for compatibility endpoints."""

    loader = getattr(company, "_panelTextWide", None)
    if loader is None:
        return None
    return loader()


@router.get("/api/search")
def apiSearch(q: str = Query(..., min_length=1)):
    """종목 검색 - 회사명 substring + KIND 주요제품 substring 합집합. 둘 다 0 이면 fuzzy.

    "HBM" → SK하이닉스, "메모리" → 삼성전자/SK하이닉스 등 *제품 키워드* 로
    회사 찾기 지원. KIND parquet 의 `주요제품` 컬럼이 SSOT (kindlist 1 회 룩업).
    결과 row 에 sector + products 노출 → 사용자 즉시 회사 정체성 인지.
    """
    import polars as pl

    try:
        # 1. 회사명 substring (dartlab.searchName)
        df = dartlab.searchName(q)
        name_rows = df.to_dicts() if len(df) > 0 else []

        # 2. 주요제품 substring - KIND listing parquet 의 `주요제품` 컬럼.
        #    회사명 매칭에 못 잡힌 회사만 추가 (dedup by 종목코드).
        product_rows: list[dict] = []
        try:
            listing_df = dartlab.listing()
            if not isEmptyDf(listing_df) and "주요제품" in listing_df.columns:
                mask = pl.col("주요제품").cast(pl.Utf8).str.contains(q, literal=True)
                product_rows = listing_df.filter(mask).head(40).to_dicts()
        except (AttributeError, OSError, RuntimeError, ValueError):
            pass

        seen = {str(r.get("종목코드", r.get("stockCode", ""))).zfill(6) for r in name_rows}
        combined = list(name_rows)
        for r in product_rows:
            code = str(r.get("종목코드", r.get("stockCode", ""))).zfill(6)
            if code in seen:
                continue
            seen.add(code)
            combined.append(r)

        fuzzy_used = False
        # 3. 회사명·제품 둘 다 0 → 초성/Levenshtein fuzzy fallback.
        if not combined:
            from dartlab.gather.krx.listing import fuzzySearch

            df = fuzzySearch(q, maxResults=20)
            combined = df.to_dicts() if len(df) > 0 else []
            fuzzy_used = bool(combined)

        mapped = []
        for row in combined[:20]:
            mapped.append(
                {
                    "corpName": row.get("회사명", row.get("corpName", "")),
                    "stockCode": row.get("종목코드", row.get("stockCode", "")),
                    "market": row.get("시장구분", ""),
                    "sector": row.get("업종", ""),
                    "products": row.get("주요제품", ""),
                }
            )
        return {"results": mapped, "fuzzy": fuzzy_used}
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=400, detail=guideDetail(exc)) from exc


_BLOG_REPORTS_DIR = "blog/05-company-reports"


_BLOG_BASE_URL = "https://eddmpython.github.io/dartlab/blog"


def _findBlogPosts(stockCode: str) -> list[dict[str, str]]:
    """blog/05-company-reports/{NN}-{CODE}-{slug}/ 의 frontmatter 확인 후 발간 link.

    발간 판정: frontmatter 의 `title` + `date` + `category: company-reports` 박혀있으면 발간.
    URL 우선순위:
      1. frontmatter publishedUrl / permalink / url (http 시작)
      2. fallback - landing route `/blog/{slug}` 추정 URL (NN-CODE-{slug} 의 slug 부분).
    """
    from pathlib import Path

    base = Path(__file__).resolve().parents[4] / _BLOG_REPORTS_DIR
    if not base.exists():
        return []
    posts: list[dict[str, str]] = []
    code_pad = str(stockCode).zfill(6)
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        name = child.name  # NN-CODE-slug
        parts = name.split("-", 2)
        if len(parts) < 3:
            continue
        if parts[1] != code_pad:
            continue
        # landing route /blog/[slug] 의 slug 형식은 `CODE-slug` (예: 000660-skhynix).
        # landing src/routes/blog/[slug]/+page.ts normalizePath 와 일치.
        # backend 가 `skhynix` 단독으로 보내면 landing 에서 404 - 회귀 차단 (2026-05-19).
        slug = f"{parts[1]}-{parts[2]}"
        md = None
        for candidate in ("index.md", "page.md", "README.md"):
            p = child / candidate
            if p.exists():
                md = p
                break
        if md is None:
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text.startswith("---"):
            continue
        fm_end = text.find("---", 3)
        if fm_end < 0:
            continue
        fm = text[3:fm_end]
        # frontmatter 핵심 필드 추출.
        title = ""
        category = ""
        has_date = False
        published_url = ""
        for line in fm.splitlines():
            stripped = line.strip()
            if not title and stripped.startswith("title:"):
                title = stripped[len("title:") :].strip().strip('"').strip("'")
            elif not category and stripped.startswith("category:"):
                category = stripped[len("category:") :].strip().strip('"').strip("'")
            elif not has_date and stripped.startswith("date:"):
                has_date = True
            elif not published_url:
                for key in ("publishedUrl:", "permalink:", "url:"):
                    if stripped.startswith(key):
                        v = stripped[len(key) :].strip().strip('"').strip("'")
                        if v.startswith("http"):
                            published_url = v
                        break
        # 발간 판정 - title + date + company-reports 카테고리.
        if not (title and has_date and category == "company-reports"):
            continue
        # URL 결정 - frontmatter publishedUrl 우선, 없으면 추정.
        url = published_url or f"{_BLOG_BASE_URL}/{slug}"
        posts.append({"title": title, "slug": slug, "url": url})
    return posts


def _findCorpMeta(stockCode: str) -> dict[str, str]:
    """KRX listing 1 회 룩업으로 corpName + sector + market 동시 추출.

    Company 객체 초기화 (rawFinance LazyFrame collect = 200~500MB) 우회. kindlist
    parquet 단일 룩업만으로 회사 헤더 표시에 필요한 전 메타 반환 (0~5ms).
    """
    code_pad = str(stockCode).zfill(6)
    out = {"corpName": "", "sector": "", "market": ""}
    try:
        df = dartlab.searchName(str(stockCode))
        if not isEmptyDf(df):
            rows = df.to_dicts()
            hit = None
            for r in rows:
                sc = str(r.get("종목코드", r.get("stockCode", "")))
                if sc.zfill(6) == code_pad:
                    hit = r
                    break
            r = hit or rows[0]
            out["corpName"] = str(r.get("회사명", r.get("corpName", "")) or "")
            out["sector"] = str(r.get("업종", r.get("sector", "")) or "")
            out["market"] = str(r.get("시장구분", r.get("market", "")) or "")
            if hit is not None:
                return out
    except Exception:  # noqa: BLE001
        pass
    # fallback - listing() 전수에서 종목코드 직접 매칭.
    try:
        df = dartlab.listing()
        if isEmptyDf(df):
            return out
        rows = df.to_dicts()
        for r in rows:
            sc = str(r.get("종목코드", r.get("stockCode", "")))
            if sc.zfill(6) == code_pad:
                out["corpName"] = out["corpName"] or str(r.get("회사명", r.get("corpName", "")) or "")
                out["sector"] = out["sector"] or str(r.get("업종", r.get("sector", "")) or "")
                out["market"] = out["market"] or str(r.get("시장구분", r.get("market", "")) or "")
                return out
    except Exception:  # noqa: BLE001
        pass
    return out


_PRODUCT_TAG_BLOCKLIST = {"전자공시", "투자", "주식", "재무제표", "공시", "분석"}


def _findProductsFromBlog(stockCode: str) -> list[str]:
    """blog frontmatter tags 에서 제품 후보 추출 - 회사명/종목코드/blocklist 제외.

    _PRODUCT_MAP 미커버 회사 fallback. tags 의 첫 N 개 (회사명/종목코드 제외).
    """
    from pathlib import Path

    base = Path(__file__).resolve().parents[4] / _BLOG_REPORTS_DIR
    if not base.exists():
        return []
    code_pad = str(stockCode).zfill(6)
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        parts = child.name.split("-", 2)
        if len(parts) < 3 or parts[1] != code_pad:
            continue
        md = None
        for candidate in ("index.md", "page.md", "README.md"):
            p = child / candidate
            if p.exists():
                md = p
                break
        if md is None:
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text.startswith("---"):
            continue
        fm_end = text.find("---", 3)
        if fm_end < 0:
            continue
        fm = text[3:fm_end]
        # tags: 또는 tags:\n  - ... 두 형태 지원.
        in_tags = False
        tags: list[str] = []
        for line in fm.splitlines():
            stripped = line.strip()
            if stripped.startswith("tags:"):
                in_tags = True
                inline = stripped[len("tags:") :].strip()
                if inline.startswith("[") and inline.endswith("]"):
                    inline = inline[1:-1]
                    for t in inline.split(","):
                        v = t.strip().strip('"').strip("'")
                        if v:
                            tags.append(v)
                    in_tags = False
                continue
            if in_tags:
                if stripped.startswith("- "):
                    v = stripped[2:].strip().strip('"').strip("'")
                    if v:
                        tags.append(v)
                elif stripped and not stripped.startswith("-"):
                    in_tags = False
        # 회사명 / 종목코드 / blocklist 제외, 첫 4 개만.
        out: list[str] = []
        for t in tags:
            if t == code_pad or t in _PRODUCT_TAG_BLOCKLIST:
                continue
            # 회사명 후보 (보통 첫 tag, 한글) 제외 - frontmatter 의 corpName 매칭 시 skip.
            if "corpName:" in fm:
                # rough: corpName 줄 추출.
                for line in fm.splitlines():
                    if line.strip().startswith("corpName:"):
                        corp = line.split(":", 1)[1].strip().strip('"').strip("'")
                        if t == corp:
                            t = None  # type: ignore[assignment]
                        break
            if t is None:
                continue
            if t not in out:
                out.append(t)
            if len(out) >= 4:
                break
        return out
    return []


# 주요 회사 제품 mock map - 사업보고서 "주요제품" 추출 자동화 전 임시.
# P-DASH-V1 D14 - 헤더 라벨 가시화 목적. 실제 추출은 후속 PR.
_PRODUCT_MAP: dict[str, list[str]] = {
    "005930": ["메모리", "디스플레이", "파운드리", "스마트폰"],
    "000660": ["DRAM", "NAND", "HBM"],
    "035420": ["검색", "쇼핑", "콘텐츠", "AI"],
    "035720": ["메신저", "콘텐츠", "AI", "모빌리티"],
    "005380": ["승용차", "상용차", "수소"],
    "051910": ["석유화학", "배터리", "생명과학"],
    "207940": ["바이오시밀러", "위탁생산"],
    "068270": ["바이오시밀러"],
    "373220": ["배터리"],
    "006400": ["배터리", "전자재료"],
    "066570": ["가전", "TV", "디스플레이"],
    "012330": ["자동차부품", "모빌리티"],
}


@router.get("/api/company/{code}/meta")
def apiCompanyMeta(code: str):
    """회사 헤더 확장 메타 - corpName + 시장 + 섹터 + 제품 + 블로그 글.

    kindlist parquet 단일 룩업만으로 응답 (Company.rawFinance collect 우회).
    회사 페이지 진입 시 부모 layout 의 corpName 도 본 endpoint 가 SSOT -
    회사명 한 글자 받자고 `/api/viz/dashboard/{code}` 전체 빌드하던 회귀 차단
    (P-DASH-V2, 2026-05-19).

    제품: _PRODUCT_MAP 우선, 미존재 시 blog frontmatter tags fallback.
    """
    corp = _findCorpMeta(code)
    blog_posts = _findBlogPosts(code)
    products = _PRODUCT_MAP.get(str(code).zfill(6)) or _findProductsFromBlog(code)
    return {
        "stockCode": code,
        "corpName": corp["corpName"],
        "market": corp["market"],
        "sector": corp["sector"],
        "products": products,
        "blogPosts": blog_posts,
    }


@router.get("/api/company/{code}")
def apiCompany(code: str):
    """종목 기본 정보 + 사용 가능 API surface 목록."""
    try:
        company = get_company(code)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "surface": {
                "index": f"/api/company/{company.stockCode}/index",
                "show": f"/api/company/{company.stockCode}/show/{{topic}}",
                "trace": f"/api/company/{company.stockCode}/trace/{{topic}}",
            },
            "profile": {
                "status": "roadmap",
                "description": "변화 지점을 문서처럼 읽는 company report view가 추후 추가될 예정입니다.",
            },
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/lenses")
def apiCompanyLenses(code: str) -> dict[str, Any]:
    """다섯 대표 렌즈의 검증된 product bundle을 반환한다."""
    try:
        company = get_company(code)
        from dartlab.story.lensProducts import collectLensProducts, publicLensBundle
        from dartlab.synth.lensContract import validatePublicLensBundle

        bundle = publicLensBundle(collectLensProducts(company))
        if bundle is None:
            raise ValueError("공개 lens bundle을 만들 수 없습니다.")
        validatePublicLensBundle(bundle)
        return bundle
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/index")
def apiCompanyIndex(code: str, request: Request, response: Response):
    """회사 데이터 구조 인덱스 DataFrame."""
    try:
        company = get_company(code)
        data = {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "payload": serializePayload(company.index),
        }
        return etagResponse(request, response, data, maxAge=300, swr=1800)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/panel/init")
def apiCompanyInit(
    code: str,
    request: Request,
    response: Response = None,
):
    """SPA 초기 로드 번들 - panel toc + 첫 절(sectionLeaf) full-period grid.

    grid 는 전체 기간 (frontend 가 window slice + 인접셀 diff 수행) - 백엔드 계산 0.
    """
    try:
        company = getCompany(code)
        toc_data = buildToc(company)

        first_chapter: str | None = None
        first_section_key: str | None = None
        first_section: str | None = None
        chapters = toc_data.get("chapters", [])
        if chapters:
            sections = chapters[0].get("sections", [])
            if sections:
                first_chapter = chapters[0]["chapter"]
                first_section = sections[0]["sectionLeaf"]
                first_section_key = sections[0]["sectionKey"]

        grid = None
        if first_section:
            # window 3 표시 + 직전 1 (프론트 인접셀 diff 용) = 4 기간. full-period(수MB) 회피.
            window = tuple(toc_data.get("periods", [])[:4]) or None
            grid = buildPanelGrid(company, chapter=first_chapter, section=first_section, windowPeriods=window)

        result = {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "toc": toc_data,
            "firstChapter": first_chapter,
            "firstSectionKey": first_section_key,
            "grid": grid,
        }
        return etagResponse(request, response, result, maxAge=300, swr=1800)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/panel/toc")
def apiCompanyToc(
    code: str,
    request: Request,
    response: Response = None,
):
    """목차(TOC) - panel 의 chapter > sectionLeaf > blockLeaf 트리.

    panel 이 SPINE 정렬·라벨링 SSOT 이므로 재정렬 0. diff(hasChanges)는 frontend
    인접셀 비교로 이전 - 백엔드 계산 없음.
    """
    try:
        company = getCompany(code)
        data = buildToc(company)
        return etagResponse(request, response, data, maxAge=300, swr=1800)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/panel")
def apiCompanyPanel(
    code: str,
    request: Request,
    section: str | None = Query(
        None, description="sectionKey ({chapter}␟{sectionLeaf}) - 한 절 grid. 생략 시 전체 격자."
    ),
    periods: str | None = Query(
        None, description="comma-separated 표시 기간 (최신좌측). 생략 시 전체 기간 (full-period)."
    ),
    block: str | None = Query(None, description="blockLeaf - 그 항목 행만 (주석 등 세분 단위). 생략 시 절 전체."),
    response: Response = None,
):
    """panel 의 한 절(section)/항목(block) grid - 항목 × 기간 wide (viewer 본문).

    section: sectionKey ({chapter}␟{sectionLeaf}). 생략 시 전체 격자.
    block: blockLeaf - 주석처럼 세분된 한 항목만 (뭉텅이 스크롤 대신 항목 단위 수평 격자).
    periods: 표시 window (예 "2026Q1,2025Q4,2025Q3"). 생략 시 전체 기간.
    diff/timeline 은 frontend (인접셀 비교 + window slice) - 백엔드 계산 0.
    """
    try:
        company = getCompany(code)
        chapter = None
        section_leaf = None
        if section:
            chapter, section_leaf = splitSectionKey(section)
        window_periods = None
        if periods:
            wp = tuple(p.strip() for p in periods.split(",") if p.strip())
            window_periods = wp or None
        data = buildPanelGrid(company, chapter=chapter, section=section_leaf, block=block, windowPeriods=window_periods)
        return etagResponse(request, response, data, maxAge=120, swr=600)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/viewer2/{topic}")
def apiViewerDoc(
    code: str,
    topic: str,
    request: Request,
    base: str | None = Query(None),
    compare: str | None = Query(None),
    response: Response = None,
):
    """panel text 기반 신구대조 뷰어 - viewer() dict 반환."""
    try:
        company = getCompany(code)
        sec = _panelTextWide(company)
        if sec is None:
            raise HTTPException(status_code=404, detail="panel text 없음")

        if not base:
            periods = sorted(
                [c for c in sec.columns if _PERIOD_COL_RE.fullmatch(c)],
                reverse=True,
            )
            base = periods[0] if periods else None

        from dartlab.reference.docs.viewer import viewer

        doc = viewer(sec, topic, base, compare)
        doc["stockCode"] = company.stockCode
        doc["corpName"] = company.corpName
        doc["topicLabel"] = safeTopicLabel(company, topic)
        return etagResponse(request, response, doc, maxAge=120, swr=600)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/show/{topic}/all")
def apiCompanyShowAll(code: str, topic: str, raw: bool = Query(False)):
    """topic의 전 기간 viewer 블록 일괄 반환."""
    try:
        from dartlab.providers.dart.viewer import (
            serializeViewerBlock,
            serializeViewerTextDocument,
            viewerBlocks,
            viewerTextDocument,
        )

        company = getCompany(code)
        blocks = viewerBlocks(company, topic)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "topic": topic,
            "blocks": [serializeViewerBlock(block) for block in blocks],
            "textDocument": serializeViewerTextDocument(viewerTextDocument(topic, blocks)),
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.post("/api/company/{code}/show/{topic}/{block_idx}/parse")
async def apiParseRawTable(code: str, topic: str, blockIdx: int):
    """원문 테이블 블록을 구조화 DataFrame으로 파싱."""
    try:
        from dartlab.providers.dart.tableAI import parseRawMarkdownBlock
        from dartlab.providers.dart.viewer import viewerBlocks

        company = getCompany(code)
        blocks = viewerBlocks(company, topic)
        target = None
        for block in blocks:
            if block.block == blockIdx and block.kind == "raw_markdown":
                target = block
                break
        if target is None:
            raise HTTPException(status_code=404, detail="raw_markdown 블록이 아님")

        result = await parseRawMarkdownBlock(target.rawMarkdown, topic)
        return {
            "stockCode": company.stockCode,
            "topic": topic,
            "block": blockIdx,
            "parsed": result,
        }
    except HTTPException:
        raise
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/show/{topic}")
def apiCompanyShow(code: str, topic: str, block: int | None = Query(None), raw: bool = Query(False)):
    """topic payload 조회 - show(topic) API 대응."""
    try:
        company = getCompany(code)
        # block(docs 블록 인덱스)은 panel 미지원 - 무시. raw→tag(원본 XML, raw 공시 검색 한정).
        result = company.panel(topic, tag=raw)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "topic": topic,
            "block": block,
            "payload": serializePayload(result),
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/trace/{topic}")
def apiCompanyTrace(code: str, topic: str):
    """source provenance 조회 - trace(topic) API 대응."""
    try:
        company = getCompany(code)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "topic": topic,
            "payload": serializePayload(company.trace(topic)),
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc


@router.get("/api/company/{code}/summary/{topic}")
async def apiCompanyTopicSummary(
    code: str,
    topic: str,
    provider: str | None = None,
    model: str | None = None,
):
    """topic 데이터를 LLM으로 요약하여 SSE 스트리밍 반환."""
    try:
        company = get_company(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc

    try:
        overview = company.panel(topic)
    except (AttributeError, KeyError, TypeError, ValueError):
        try:
            overview = company.show(topic)
        except (AttributeError, KeyError, TypeError, ValueError):
            overview = None
    if overview is None:
        raise HTTPException(status_code=404, detail=f"topic '{topic}' 데이터 없음")

    return EventSourceResponse(
        stream_topic_summary(
            company,
            topic,
            provider=normalizeProviderName(provider) or provider,
            model=model,
        )
    )


@router.get("/api/company/{code}/insights")
def apiCompanyInsights(code: str):
    """7영역 인사이트 등급 (A~F) + 이상 징후."""
    try:
        company = getCompany(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc

    from dartlab.analysis.financial.insight.pipeline import analyzeFinancial as insight_analyze

    try:
        result = insight_analyze(company.stockCode, company=company)
    except HANDLED_API_ERRORS:
        result = None

    if result is None:
        corp = _findCorpMeta(company.stockCode)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "available": False,
            "profile": {
                "stockCode": company.stockCode,
                "corpName": company.corpName,
                "market": corp["market"],
                "sector": corp["sector"],
            },
        }

    def _flagDict(flag):
        return {"level": flag.level, "category": flag.category, "text": flag.text}

    def _insightDict(insight):
        return {
            "grade": insight.grade,
            "summary": insight.summary,
            "details": insight.details,
            "risks": [_flagDict(risk) for risk in insight.risks],
            "opportunities": [_flagDict(opportunity) for opportunity in insight.opportunities],
        }

    def _anomalyDict(anomaly):
        return {
            "severity": anomaly.severity,
            "category": anomaly.category,
            "text": anomaly.text,
            "value": anomaly.value,
        }

    return {
        "stockCode": company.stockCode,
        "corpName": company.corpName,
        "available": True,
        "isFinancial": result.isFinancial,
        "grades": result.grades(),
        "areas": {
            "performance": _insightDict(result.performance),
            "profitability": _insightDict(result.profitability),
            "health": _insightDict(result.health),
            "cashflow": _insightDict(result.cashflow),
            "governance": _insightDict(result.governance),
            "risk": _insightDict(result.risk),
            "opportunity": _insightDict(result.opportunity),
        },
        "anomalies": [_anomalyDict(anomaly) for anomaly in result.anomalies],
        "summary": result.summary,
        "profile": result.profile,
    }


@router.get("/api/company/{code}/network")
def apiCompanyNetwork(code: str, hops: int = 1):
    """관계사 네트워크 그래프 - ego 중심 N-hop."""
    hops = max(1, min(hops, 3))
    try:
        company = getCompany(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc

    try:
        result = company._ensureNetwork()
        if result is None:
            return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}
        data, full = result

        from dartlab.scan.network.export import exportEgo

        ego = exportEgo(data, full, company.stockCode, hops=hops)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "available": True,
            **ego,
        }
    except HANDLED_API_ERRORS:
        return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}


@router.get("/api/company/{code}/scan/{axis}")
def apiCompanyScan(code: str, axis: str):
    """6-Axis 스캔 단일 축 결과 + 시장 내 위치."""
    try:
        company = getCompany(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc

    valid_axes = {"governance", "workforce", "capital", "debt"}

    if axis == "all":
        results = {}
        for current_axis in valid_axes:
            method = getattr(company, current_axis, None)
            if method is None:
                continue
            try:
                df = method()
                if df is not None and not df.is_empty():
                    results[current_axis] = serializePayload(df)
            except HANDLED_API_ERRORS:
                continue
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "available": bool(results),
            "scans": results,
        }

    if axis not in valid_axes:
        raise HTTPException(status_code=422, detail=f"유효한 축: {', '.join(sorted(valid_axes))}, all")

    method = getattr(company, axis, None)
    if method is None:
        return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}

    try:
        df = method()
        if isEmptyDf(df):
            return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "available": True,
            "scanType": axis,
            "payload": serializePayload(df),
        }
    except HANDLED_API_ERRORS:
        return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}


@router.get("/api/company/{code}/scan/position")
def apiCompanyScanPosition(code: str):
    """6-Axis 전체 포지션 요약 - 사전 빌드 스냅샷 기반."""
    from dartlab.scan.builders.kr.snapshot import getScanPosition

    position = getScanPosition(code)
    if position is None:
        raise HTTPException(status_code=404, detail="scan 스냅샷 없음 - buildScanSnapshot() 선행 필요")

    return {
        "stockCode": code,
        "available": True,
        "position": position,
    }


@router.get("/api/company/{code}/insights/unified")
def apiCompanyInsightsUnified(code: str):
    """통합 인사이트 - 등급 + 스캔 + 피어 결합."""
    try:
        company = getCompany(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=guideDetail(exc)) from exc

    from dartlab.scan.builders.kr.payload import buildUnifiedPayload

    try:
        unified = buildUnifiedPayload(company)
    except HANDLED_API_ERRORS:
        unified = {}

    return {
        "stockCode": company.stockCode,
        "corpName": company.corpName,
        "available": bool(unified),
        "areas": unified,
    }
