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


def _yearOf(value) -> int | None:
    """기간 값에서 네 자리 회계연도를 읽는다."""
    import re

    match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    return int(match.group()) if match else None


def _fetchAuditOpinionEvidence(company, *, basePeriod: str | None = None) -> dict:
    """DART 구조화 원천에서 최신 연간 감사의견과 provenance 를 가져온다.

    감사 섹션의 존재나 부정 키워드의 부재로 적정을 추론하지 않는다. 구조화
    ``adt_opinion`` 에 네 표준 범주가 명시된 경우만 ``observed`` 이다.
    """
    from dartlab.providers._common.auditOpinion import auditOpinionStatus, normalizeAuditOpinion

    market = str(getattr(company, "market", "KR") or "KR").upper()
    if market not in ("KR", "KOSPI", "KOSDAQ", "KONEX"):
        return {
            "status": "unsupported",
            "opinion": None,
            "rawOpinion": None,
            "assuranceBasis": None,
            "fiscalPeriod": None,
            "filedAt": None,
            "auditor": None,
            "source": {"market": market, "method": None, "rceptNo": None},
        }

    try:
        import warnings

        report = getattr(company, "_report", None)
        if report is None:
            raise AttributeError("report accessor 없음")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = getattr(report, "audit", None)
        if result is None:
            raise AttributeError("audit result 없음")

        years = list(getattr(result, "years", []) or [])
        opinions = list(getattr(result, "opinions", []) or [])
        auditors = list(getattr(result, "auditors", []) or [])
        rceptNos = list(getattr(result, "rceptNos", []) or [])
        cutoff = _yearOf(basePeriod)
        candidates = []
        for i, raw in enumerate(opinions):
            year = _yearOf(years[i]) if i < len(years) else None
            if cutoff is not None and (year is None or year > cutoff):
                continue
            rceptNo = rceptNos[i] if i < len(rceptNos) else None
            candidates.append(
                {
                    "year": year,
                    "raw": raw,
                    "opinion": normalizeAuditOpinion(raw),
                    "status": auditOpinionStatus(raw),
                    "auditor": auditors[i] if i < len(auditors) else None,
                    "rceptNo": rceptNo,
                }
            )

        observed = [row for row in candidates if row["opinion"] is not None]
        selected = max(observed, key=lambda row: (row["year"] or -1, str(row["rceptNo"] or ""))) if observed else None
        if selected is None:
            selected = (
                max(candidates, key=lambda row: (row["year"] or -1, str(row["rceptNo"] or ""))) if candidates else None
            )
        if selected is None:
            raise AttributeError("audit opinion row 없음")

        rceptNo = selected["rceptNo"]
        filedAt = str(rceptNo)[:8] if rceptNo and len(str(rceptNo)) >= 8 else None
        return {
            "status": "observed" if selected["opinion"] is not None else selected["status"],
            "opinion": selected["opinion"],
            "rawOpinion": selected["raw"],
            "assuranceBasis": "audit" if selected["opinion"] is not None else None,
            "fiscalPeriod": str(selected["year"]) if selected["year"] is not None else None,
            "filedAt": filedAt,
            "auditor": selected["auditor"],
            "source": {"market": "KR", "method": "structured", "rceptNo": rceptNo},
        }
    except (AttributeError, ValueError, KeyError, TypeError, IndexError):
        return {
            "status": "missing",
            "opinion": None,
            "rawOpinion": None,
            "assuranceBasis": None,
            "fiscalPeriod": None,
            "filedAt": None,
            "auditor": None,
            "source": {"market": "KR", "method": "structured", "rceptNo": None},
        }


def _fetchAuditOpinion(company, *, basePeriod: str | None = None) -> str | None:
    """명시적으로 관측된 구조화 감사의견만 반환한다."""
    evidence = _fetchAuditOpinionEvidence(company, basePeriod=basePeriod)
    return evidence.get("opinion") if evidence.get("status") == "observed" else None


__all__ = [
    "_calcSegmentHHI",
    "_fetchAuditOpinion",
    "_fetchAuditOpinionEvidence",
    "_fetchDisclosureRisk",
    "_fetchNotes",
    "_fetchProfile",
    "_fetchRank",
    "_fetchSegmentComposition",
]
