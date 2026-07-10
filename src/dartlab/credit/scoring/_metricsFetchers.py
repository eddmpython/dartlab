"""credit/scoring/metrics.py 의 7 데이터 수집 헬퍼 — calcAllMetrics 가 호출.

_fetchProfile / _fetchSegmentComposition / _fetchRank / _fetchNotes / _calcSegmentHHI /
_fetchDisclosureRisk / _fetchAuditOpinion — 모두 company 객체에서 도메인 dict (또는 None)
추출. metrics.py 의 god module 분리 결과.

L1.5 scan 의 disclosureRisk/governance.scorer/screen.rank 와 frame 의 _listingDispatch.listing
을 동적 import (credit ↔ scan cross-import 회피).
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════
# notes / sections / scan 데이터 수집
# ═══════════════════════════════════════════════════════════


def _fetchProfile(company) -> dict | None:
    """기업 프로필 (업종, 주요제품) 수집.

    Company.sector + dartlab.listing() 직접 접근.
    cross-dependency 방지: credit ↛ analysis.
    """
    parts: dict[str, str] = {}
    try:
        sectorInfo = company.sector
        if sectorInfo:
            sectorKr = sectorInfo.sector.value
            groupKr = sectorInfo.industryGroup.value
            parts["sector"] = f"섹터: {sectorKr} > {groupKr}"
    except (ValueError, KeyError, AttributeError):
        pass

    try:
        from dartlab._listingDispatch import listing as _listing

        listing = _listing()
        stockCode = getattr(company, "stockCode", "")
        # 상장목록을 못 받는 환경(브라우저는 KRX 로 못 나간다)에서는 0 행 프레임이 온다. 그때
        # 종목코드 컬럼 dtype 이 Null 이라 Series 를 str 과 비교하는 순간 TypeError 가 나고,
        # 그 예외는 아래 except 에 없어 credit 전체가 죽었다. 목록이 비면 맞출 행도 없다.
        if stockCode and listing is not None and listing.height > 0 and "종목코드" in listing.columns:
            row = listing.filter(listing["종목코드"] == stockCode)
            if not row.is_empty() and "주요제품" in row.columns:
                products = row["주요제품"][0]
                if products:
                    parts["products"] = f"주요제품: {products}"
    except (ImportError, ValueError, KeyError):
        pass

    return parts if parts else None


def _fetchSegmentComposition(company) -> dict | None:
    """부문별 매출/이익 구성 수집.

    Plan v10 P2: c.notes 제거 → c.panel("segments") 사용.
    최신 연도 컬럼 하나만 사용하여 연도별 부문명 변경(IM→DX 등) 중복 방지.
    """
    try:
        # show 은퇴 → 공통파서 panel 부문 표 (헤더키 행). 옛 부문×year pivot 과 구조 달라
        # year 컬럼 없으면 아래 yearCols 로직이 graceful None.
        import polars as pl

        from dartlab.providers.dart.panel.text import panelTableRows

        _code = getattr(company, "stockCode", None)
        _r = panelTableRows(_code, sectionPattern="부문") if _code else []
        df = pl.DataFrame(_r) if _r else None
        if df is None or not hasattr(df, "columns"):
            return None

        # DataFrame 구조: 부문(str), 2025(f64), 2024(f64), ...
        # 최신 연도 컬럼 하나만 사용하여 중복 방지
        yearCols = sorted(
            [c for c in df.columns if c.isdigit() and len(c) == 4],
            reverse=True,
        )
        if not yearCols:
            return None
        # 최신 연도에 유효 데이터가 2개 미만이면 차선 연도 사용
        latestYear = yearCols[0]
        for yc in yearCols:
            validCount = sum(
                1
                for row in df.iter_rows(named=True)
                if row.get(yc) is not None and isinstance(row.get(yc), (int, float)) and row.get(yc) > 0
            )
            if validCount >= 2:
                latestYear = yc
                break

        # 부문명 컬럼: 첫 번째 문자열 타입 컬럼
        nameCol = None
        for c in df.columns:
            if c in ("부문", "항목"):
                nameCol = c
                break
        if nameCol is None:
            # fallback: 숫자가 아닌 첫 번째 컬럼
            for c in df.columns:
                if not c.isdigit():
                    nameCol = c
                    break
        if nameCol is None:
            return None

        segments = []
        for row in df.iter_rows(named=True):
            name = row.get(nameCol)
            revenue = row.get(latestYear)
            if not isinstance(name, str) or not name.strip():
                continue
            name = name.strip()
            if not isinstance(revenue, (int, float)) or revenue <= 0:
                continue
            # "합계", "조정", "내부" 행 제외
            if any(skip in name for skip in ("합계", "조정", "내부거래", "상계")):
                continue
            segments.append({"name": name, "revenue": revenue})

        if not segments:
            return None

        segments.sort(key=lambda x: x["revenue"], reverse=True)
        totalRev = sum(s["revenue"] for s in segments)
        if totalRev == 0:
            return None

        return {"segments": segments, "totalRevenue": totalRev}
    except (AttributeError, FileNotFoundError, ValueError, KeyError, TypeError):
        return None


def _fetchRank(company) -> dict | None:
    """업종 내 순위 수집. scan 데이터 없으면 None (스냅샷 빌드 시도 안 함)."""
    try:
        import importlib

        _r = importlib.import_module("dartlab.scan.screen.rank")
        _SNAPSHOT = _r._SNAPSHOT
        _cacheDir = _r._cacheDir

        # 캐시된 스냅샷이 있을 때만 사용 (빌드 시도 X — 수분 소요)
        if _SNAPSHOT is None:
            cachePath = _cacheDir() / "rank_snapshot.parquet"
            if not cachePath.exists():
                return None

        import importlib

        getRankOrBuild = importlib.import_module("dartlab.scan.screen.rank").getRankOrBuild

        stockCode = getattr(company, "stockCode", "")
        if not stockCode:
            return None
        rank = getRankOrBuild(stockCode, verbose=False)
        if rank is None:
            return None
        return {
            "revenueRank": rank.revenueRank,
            "revenueTotal": rank.revenueTotal,
            "revenueRankInSector": rank.revenueRankInSector,
            "revenueSectorTotal": rank.revenueSectorTotal,
            "sizeClass": rank.sizeClass,
            "sector": rank.sector,
            "industryGroup": rank.industryGroup,
        }
    except (ImportError, AttributeError, ValueError, KeyError, OSError, TypeError):
        return None


def _fetchNotes(company, key: str) -> list[dict] | None:
    """notes에서 DataFrame을 dict 리스트로 안전하게 추출."""
    try:
        accessor = getattr(company, "_notesAccessor", None) or getattr(company, "notes", None)
        if accessor is None:
            return None
        df = getattr(accessor, key, None)
        if df is not None and hasattr(df, "to_dicts"):
            return df.to_dicts()
    except (AttributeError, FileNotFoundError, ValueError, KeyError):
        pass
    return None


def _calcSegmentHHI(segmentsData: list[dict] | None) -> float | None:
    """부문별 매출에서 HHI(허핀달-허쉬만 지수) 계산.

    HHI = Σ(부문매출비중²) × 10000
    HHI < 1500: 다각화, 1500-2500: 보통, > 2500: 집중
    """
    if not segmentsData:
        return None

    # segments DataFrame에서 매출 추출
    revenues = []
    for row in segmentsData:
        # 매출액 또는 영업수익 컬럼 탐색
        for k, v in row.items():
            if isinstance(v, (int, float)) and v > 0:
                if any(term in str(k) for term in ["매출", "수익", "revenue"]):
                    revenues.append(v)
                    break

    if len(revenues) < 2:
        return None

    total = sum(revenues)
    if total <= 0:
        return None

    hhi = sum((r / total * 100) ** 2 for r in revenues)
    return round(hhi, 0)


def _fetchDisclosureRisk(company) -> dict | None:
    """scan.disclosureRisk에서 기업별 리스크 신호 추출."""
    try:
        import importlib

        disclosureRisk = importlib.import_module("dartlab.scan.disclosureRisk").disclosureRisk

        result = disclosureRisk(company)
        if result is not None and hasattr(result, "to_dicts"):
            rows = result.to_dicts()
            if rows:
                return rows[0]
    except (ImportError, AttributeError, ValueError, KeyError, TypeError):
        pass
    return None


def _fetchAuditOpinion(company) -> str | None:
    """감사의견 추출 — 적정/한정/부적정/의견거절.

    [성능] panel 공통파서 감사 섹션 텍스트 스캔이 단일 종목만 처리해 빠르므로 1순위.
    company.governance() 호출은 전종목 scan(12s+)을 트리거하므로 마지막 fallback으로만.
    """
    # 1순위: panel 공통파서 — 감사보고서/감사의견 섹션 텍스트 키워드 스캔 (단일 종목, 빠름)
    try:
        import polars as pl

        from dartlab.providers.dart.panel.text import panelTextRows

        _code = getattr(company, "stockCode", None)
        _texts = panelTextRows(_code) if _code else None
        if _texts is not None and not _texts.is_empty():
            _sub = _texts.filter(pl.col("sectionLeaf").str.contains("감사의견|감사보고서|외부감사"))
            text = " ".join(c for c in _sub["contentRaw"].to_list() if c)
            if text:
                if "부적정" in text:
                    return "부적정"
                if "의견거절" in text:
                    return "의견거절"
                if "한정의견" in text or "한정 의견" in text:
                    return "한정"
                # 감사 섹션이 존재하고 명시적 위반 키워드 없으면 적정
                return "적정"
    except (AttributeError, ValueError, KeyError, TypeError):
        pass

    # 2순위: scorer 직접 호출 (있으면)
    try:
        import importlib

        _extractAuditOpinion = importlib.import_module("dartlab.scan.governance.scorer")._extractAuditOpinion

        result = _extractAuditOpinion(company)
        if result:
            return result
    except (ImportError, AttributeError):
        pass

    # 마지막 fallback: governance() — 전종목 scan을 트리거하므로 매우 느림
    # 위 두 경로가 모두 실패한 경우만 사용
    try:
        gov = getattr(company, "governance", None)
        if gov is not None and callable(gov):
            govResult = gov()
            if govResult is not None and hasattr(govResult, "to_dicts"):
                rows = govResult.to_dicts()
                if rows:
                    opinion = rows[0].get("auditOpinion") or rows[0].get("감사의견")
                    if opinion:
                        return opinion
    except (AttributeError, ValueError, KeyError, TypeError):
        pass

    return None


__all__ = [
    "_calcSegmentHHI",
    "_fetchAuditOpinion",
    "_fetchDisclosureRisk",
    "_fetchNotes",
    "_fetchProfile",
    "_fetchRank",
    "_fetchSegmentComposition",
]
